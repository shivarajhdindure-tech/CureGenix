"""PDB-to-UniProt identity evidence parsing and conservative resolution."""

from __future__ import annotations

from collections import defaultdict


def parse_pdb_identity(lines) -> dict:
    """Extract protein chains and DBREF mappings; `_` represents a blank PDB chain."""
    chains = set()
    records = []
    warnings = []
    malformed_chains = set()
    unsupported_extended_records = False

    for line_number, line in enumerate(lines, start=1):
        record_type = line[:6]
        if record_type == "ATOM  ":
            if len(line) > 21:
                raw_chain = line[21:22]
                chains.add("_" if raw_chain == " " else raw_chain)
        elif record_type in {"DBREF1", "DBREF2"}:
            unsupported_extended_records = True
            warnings.append(
                f"{record_type.strip()} records are present; extended DBREF accession mapping is not parsed."
            )
        elif record_type == "DBREF ":
            if len(line) < 32:
                chain = line[12:13] if len(line) > 12 else ""
                chain = "_" if chain == " " else chain
                malformed_chains.add(chain)
                warnings.append("Truncated DBREF record does not include its database field.")
                records.append({
                    "record": "DBREF", "source": "uploaded PDB DBREF record",
                    "line_number": line_number, "raw_record": line.rstrip("\r\n"),
                    "chain_id": chain, "database": None, "accession": None,
                    "valid": False,
                })
                continue
            database = line[26:32].strip().upper()
            if not database:
                chain = line[12:13] if len(line) > 12 else ""
                chain = "_" if chain == " " else chain
                malformed_chains.add(chain)
                warnings.append("Malformed DBREF record has an empty database field.")
                records.append({
                    "record": "DBREF", "source": "uploaded PDB DBREF record",
                    "line_number": line_number, "raw_record": line.rstrip("\r\n"),
                    "chain_id": chain, "database": None, "accession": None,
                    "valid": False,
                })
                continue
            if database != "UNP":
                continue
            chain = line[12:13] if len(line) > 12 else ""
            if chain == " ":
                chain = "_"
            accession = line[33:41].strip().upper() if len(line) >= 41 else ""
            pdb_begin = line[14:18].strip() if len(line) >= 18 else ""
            pdb_end = line[20:24].strip() if len(line) >= 24 else ""
            ranges_valid = pdb_begin.isdigit() and pdb_end.isdigit() and int(pdb_begin) <= int(pdb_end)
            if not chain or not accession or not ranges_valid:
                malformed_chains.add(chain)
                warnings.append("Malformed UniProt DBREF record lacks a usable chain, accession, or residue range.")
                records.append({
                    "record": "DBREF",
                    "source": "uploaded PDB DBREF record",
                    "line_number": line_number,
                    "raw_record": line.rstrip("\r\n"),
                    "chain_id": chain,
                    "database": "UNP",
                    "accession": accession or None,
                    "pdb_sequence_begin": pdb_begin or None,
                    "pdb_sequence_begin_insertion_code": line[18:19].strip() if len(line) >= 19 else None,
                    "pdb_sequence_end": pdb_end or None,
                    "pdb_sequence_end_insertion_code": line[24:25].strip() if len(line) >= 25 else None,
                    "database_id": line[42:54].strip() if len(line) >= 54 else None,
                    "database_sequence_begin": line[55:60].strip() if len(line) >= 60 else None,
                    "database_sequence_begin_insertion_code": line[60:61].strip() if len(line) >= 61 else None,
                    "database_sequence_end": line[62:67].strip() if len(line) >= 67 else None,
                    "database_sequence_end_insertion_code": line[67:68].strip() if len(line) >= 68 else None,
                    "valid": False,
                })
                continue
            records.append({
                "record": "DBREF",
                "source": "uploaded PDB DBREF record",
                "line_number": line_number,
                "raw_record": line.rstrip("\r\n"),
                "chain_id": chain,
                "database": "UNP",
                "accession": accession,
                "pdb_sequence_begin": line[14:18].strip() if len(line) >= 18 else None,
                "pdb_sequence_begin_insertion_code": line[18:19].strip() if len(line) >= 19 else None,
                "pdb_sequence_end": line[20:24].strip() if len(line) >= 24 else None,
                "pdb_sequence_end_insertion_code": line[24:25].strip() if len(line) >= 25 else None,
                "database_id": line[42:54].strip() if len(line) >= 54 else None,
                "database_sequence_begin": line[55:60].strip() if len(line) >= 60 else None,
                "database_sequence_begin_insertion_code": line[60:61].strip() if len(line) >= 61 else None,
                "database_sequence_end": line[62:67].strip() if len(line) >= 67 else None,
                "database_sequence_end_insertion_code": line[67:68].strip() if len(line) >= 68 else None,
                "valid": True,
            })

    by_chain = defaultdict(set)
    for item in records:
        if item["valid"]:
            by_chain[item["chain_id"]].add(item["accession"])

    if not records and not unsupported_extended_records:
        warnings.append("No usable UniProt DBREF annotation was found in the uploaded PDB.")

    return {
        "chain_ids": sorted(chains),
        "dbref_chain_ids": sorted({item["chain_id"] for item in records if item["chain_id"]}),
        "dbref_records": records,
        "chain_accessions": {
            chain: sorted(accessions) for chain, accessions in sorted(by_chain.items())
        },
        "uniprot_accessions": sorted({
            accession for accessions in by_chain.values() for accession in accessions
        }),
        "malformed_dbref_chains": sorted(malformed_chains),
        "warnings": list(dict.fromkeys(warnings)),
    }


def resolve_target_identity(
    structure_evidence: dict,
    selected_chain_id: str | None,
    selected_uniprot_id: str | None,
    lookup_result: dict | None,
) -> dict:
    """Resolve identity. Only one-chain DBREF + exact UniProt match is linked."""
    evidence = structure_evidence or {}
    chain_ids = list(evidence.get("chain_ids") or [])
    chain_accessions = evidence.get("chain_accessions") or {}
    selected_chain = (selected_chain_id or "").strip()
    selected_accession = (selected_uniprot_id or "").strip().upper()
    warnings = list(evidence.get("warnings") or [])
    state = "unresolved"
    source = None
    linked_accession = None
    lookup = lookup_result or {"status": "not_attempted", "found": False}

    if len(chain_ids) > 1 and not selected_chain:
        state = "ambiguous"
        warnings.append("The PDB contains multiple chains; select a target chain before identity can be resolved.")
    elif selected_chain and selected_chain not in chain_ids:
        state = "identity_mismatch"
        warnings.append(f"Selected chain {selected_chain!r} is not present in the uploaded PDB.")
    else:
        chain = selected_chain or (chain_ids[0] if len(chain_ids) == 1 else None)
        chain_mappings = list(chain_accessions.get(chain, [])) if chain is not None else []
        all_mappings = set(evidence.get("uniprot_accessions") or [])

        if chain in (evidence.get("malformed_dbref_chains") or []):
            state = "ambiguous"
            warnings.append(f"Chain {chain!r} has a malformed UniProt DBREF annotation.")
        elif len(chain_mappings) > 1:
            state = "ambiguous"
            warnings.append(f"Chain {chain!r} has conflicting UniProt DBREF accessions.")
        elif selected_accession and all_mappings and selected_accession not in chain_mappings:
            state = "identity_mismatch"
            warnings.append(
                f"The supplied accession is not mapped by DBREF to selected chain {chain!r}."
            )
        else:
            dbref_accession = chain_mappings[0] if len(chain_mappings) == 1 else None
            candidate_accession = selected_accession or dbref_accession
            if dbref_accession:
                source = "PDB DBREF record for selected chain"
                linked_accession = dbref_accession
                state = "unresolved"  # upgrades only after exact UniProt verification
            elif candidate_accession:
                source = "user-selected UniProt accession; no matching chain DBREF"
                state = "externally_verified" if lookup.get("found") and str(lookup.get("uniprot_id") or "").upper() == candidate_accession else "unresolved"
            else:
                warnings.append("No reliable UniProt accession is available for the selected chain.")

            if candidate_accession and lookup.get("found") and str(lookup.get("uniprot_id") or "").upper() == candidate_accession:
                if dbref_accession == candidate_accession:
                    state = "structure_linked"
                elif not all_mappings:
                    state = "externally_verified"
                    warnings.append("The accession resolves in UniProt but is not linked to the uploaded chain by DBREF.")
            elif candidate_accession:
                warnings.append(
                    f"UniProt lookup did not verify {candidate_accession} (status: {lookup.get('status', 'unknown')})."
                )

    return {
        "identity_state": state,
        "uniprot_id": (
            linked_accession if state == "structure_linked"
            else selected_accession if state == "externally_verified"
            else None
        ),
        "selected_uniprot_id": selected_accession or None,
        "selected_chain_id": selected_chain or (chain_ids[0] if len(chain_ids) == 1 else None),
        "chain_ids": chain_ids,
        "chain_accessions": chain_accessions,
        "dbref_records": evidence.get("dbref_records", []),
        "identity_source": source,
        "uniprot_lookup": lookup,
        "warnings": list(dict.fromkeys(warnings)),
        "candidate_generation_allowed": state == "structure_linked",
        "structure_match_scope": (
            "PDB chain DBREF cross-reference plus exact UniProt accession lookup"
            if state == "structure_linked"
            else "Structure-to-accession match not established"
        ),
    }
