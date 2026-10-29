"""Milestone 6 evaluation: preserved M5 baseline, revised gate, real PDB cases."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.target_generation_policy import authorize_target_generation
from backend.services.target_identity import parse_pdb_identity
from backend.services.target_sequence import extract_pdb_chain_sequences, validate_chain_sequence
from scripts.evaluate_target_identity_policy import evaluate_cases


OUT = ROOT / "docs" / "target_identity_policy_m6"
REAL = OUT / "real_pdb"
FIXTURES = ROOT / "docs" / "target_identity_policy_fixtures.json"


def fasta_sequence(path: Path) -> str:
    return "".join(line.strip() for line in path.read_text(encoding="utf-8").splitlines() if not line.startswith(">"))


def evaluate_synthetic() -> dict:
    manifest = json.loads(FIXTURES.read_text(encoding="utf-8"))
    m5 = evaluate_cases(manifest, ROOT)
    rows = []
    diagnostic_rows = []
    for row in m5["cases"]:
        if not str(row.get("case_id", "")).startswith("synthetic_"):
            diagnostic_rows.append({
                "case_id": row["case_id"], "category": row.get("category"),
                "label_confidence": row.get("label_confidence"),
                "milestone5_generation_allowed": bool(row.get("actual_generation_allowed")),
                "sequence_validation": row.get("validation"),
                "scope": "real/source-conflict diagnostic only; excluded from synthetic and real-source performance counts",
            })
            continue
        validation = row.get("validation") or {}
        generation = authorize_target_generation(
            row.get("actual_state"), validation,
            selected_chain_id="A", uniprot_accession="P00533",
            independent_structure_evidence=None,
        )
        # These fixtures deliberately lack independently sourced per-case PDB/SIFTS evidence.
        expected = bool(row.get("expected_generation_allowed"))
        rows.append({
            "case_id": row["case_id"], "category": row.get("category"),
            "expected_generation_allowed": expected,
            "milestone5_generation_allowed": bool(row.get("actual_generation_allowed")),
            "milestone6_generation_allowed": generation["allowed"],
            "milestone6_policy_state": generation["policy_state"],
            "milestone6_reason": generation["reason"],
            "sequence_validation": validation,
            "label_scope": "synthetic constructed scenario; not biological performance evidence",
        })
    return {
        "case_count": len(rows),
        "m5_false_acceptances": [r["case_id"] for r in rows if not r["expected_generation_allowed"] and r["milestone5_generation_allowed"]],
        "m6_false_acceptances": [r["case_id"] for r in rows if not r["expected_generation_allowed"] and r["milestone6_generation_allowed"]],
        "m5_false_rejections": [r["case_id"] for r in rows if r["expected_generation_allowed"] and not r["milestone5_generation_allowed"]],
        "m6_false_rejections": [r["case_id"] for r in rows if r["expected_generation_allowed"] and not r["milestone6_generation_allowed"]],
        "cases": rows,
        "diagnostic_only": diagnostic_rows,
    }


def evaluate_real() -> dict:
    refs = {accession: fasta_sequence(REAL / f"{accession}.fasta") for accession in ("P00533", "P04626")}
    definitions = [
        {"pdb": "1M17", "chain": "A", "accession": "P00533", "kind": "kinase-domain construct", "expected": True, "entity_json": "1M17_entity_1.json", "instance_json": "1M17_A_instance.json"},
        {"pdb": "3PP0", "chain": "A", "accession": "P04626", "kind": "engineered kinase-domain construct", "expected": True, "entity_json": "3PP0_entity_1.json", "instance_json": "3PP0_A_instance.json"},
        {"pdb": "3PP0", "chain": "B", "accession": "P04626", "kind": "engineered kinase-domain construct, second chain", "expected": True, "entity_json": "3PP0_entity_1.json", "instance_json": "3PP0_B_instance.json"},
        {"pdb": "3PP0", "chain": "A", "accession": "P00533", "kind": "wrong-target negative control (HER2 structure supplied as EGFR)", "expected": False, "entity_json": "3PP0_entity_1.json", "instance_json": "3PP0_A_instance.json"},
    ]
    rows = []
    for item in definitions:
        pdb_lines = (REAL / f"{item['pdb']}.pdb").read_text(encoding="utf-8", errors="replace").splitlines()
        parsed = parse_pdb_identity(pdb_lines)
        chain_sequence = extract_pdb_chain_sequences(pdb_lines, parsed["chain_ids"]).get(item["chain"], {})
        entity = json.loads((REAL / item["entity_json"]).read_text(encoding="utf-8"))
        instance = json.loads((REAL / item["instance_json"]).read_text(encoding="utf-8"))
        refs_in_entity = (entity.get("rcsb_polymer_entity_container_identifiers") or {}).get("reference_sequence_identifiers") or []
        mappings = [x for x in refs_in_entity if x.get("database_name") == "UniProt"]
        matching = [x for x in mappings if str(x.get("database_accession") or "").upper() == item["accession"]]
        dbref_accessions = parsed["chain_accessions"].get(item["chain"], [])
        observed_accession = dbref_accessions[0] if len(dbref_accessions) == 1 else None
        observed = validate_chain_sequence(chain_sequence, refs[item["accession"]]) if chain_sequence else {"identity_state": "insufficient_sequence_evidence", "candidate_generation_allowed": False}
        entity_sequence = (entity.get("entity_poly") or {}).get("pdbx_seq_one_letter_code_can") or ""
        entity_validation = validate_chain_sequence(chain_sequence, entity_sequence) if chain_sequence and entity_sequence else {}
        instance_ids = instance.get("rcsb_polymer_entity_instance_container_identifiers") or {}
        instance_auth_chain = str(instance_ids.get("auth_asym_id") or "")
        mapping = matching[0] if len(matching) == 1 else {}
        independent = {
            "status": "verified" if len(matching) == 1 and instance_auth_chain == item["chain"] else "mismatch",
            "pdb_id": item["pdb"], "requested_pdb_id": item["pdb"],
            "auth_chain_id": instance_auth_chain, "mapping": mapping,
            "entity_sequence_validation": entity_validation,
        }
        linked = observed_accession == item["accession"]
        state = observed.get("identity_state") if linked else "identity_mismatch"
        decision = authorize_target_generation(
            state, observed, selected_chain_id=item["chain"],
            uniprot_accession=item["accession"], independent_structure_evidence=independent,
        )
        # Include source annotations for an auditable label independent of sequence alignment.
        seqadv = [line.rstrip() for line in pdb_lines if line.startswith("SEQADV") and line[12:13] == item["chain"]]
        dbrefs = [line.rstrip() for line in pdb_lines if line.startswith("DBREF ") and line[12:13] == item["chain"]]
        row = {
            **item,
            "observed_chain_sequence": chain_sequence.get("sequence"),
            "reference_sequence_source": f"UniProt REST FASTA {item['accession']}",
            "reference_sequence": refs[item["accession"]],
            "observed_dbref_records": dbrefs,
            "pdb_seqadv_records": seqadv,
            "rcsb_mapping": mapping,
            "rcsb_instance_auth_chain_id": instance_auth_chain,
            "rcsb_entity_sequence": entity_sequence,
            "uniprot_validation": observed,
            "entity_sequence_validation": entity_validation,
            "generation_authorization": decision,
            "expected_generation_allowed": item["expected"],
            "actual_generation_allowed": decision["allowed"],
            "independent_label_basis": "RCSB polymer entity UniProt/SIFTS mapping plus matching author-chain instance; expected status is not derived from sequence identity score.",
            "source_urls": [
                f"https://www.rcsb.org/structure/{item['pdb']}",
                f"https://data.rcsb.org/rest/v1/core/polymer_entity_instance/{item['pdb']}/{item['chain']}",
                f"https://data.rcsb.org/rest/v1/core/polymer_entity/{item['pdb']}/1",
                f"https://rest.uniprot.org/uniprotkb/{item['accession']}.fasta",
            ],
        }
        rows.append(row)
    return {
        "case_count": len(rows), "unique_pdb_entries": sorted({row["pdb"] for row in rows}),
        "false_acceptances": [row["pdb"] + ":" + row["chain"] + " as " + row["accession"] for row in rows if not row["expected_generation_allowed"] and row["actual_generation_allowed"]],
        "false_rejections": [row["pdb"] + ":" + row["chain"] + " as " + row["accession"] for row in rows if row["expected_generation_allowed"] and not row["actual_generation_allowed"]],
        "cases": rows,
    }


def build_report(results: dict) -> str:
    synthetic = results["synthetic"]
    real = results["real_world"]
    lines = [
        "# Milestone 6 — Real-World Identity Validation and Safer Generation Gating", "",
        "## Baseline and revised policy", "",
        "Milestone 5 baseline is preserved under `baseline/` and was reproduced before this change. Its sequence thresholds and classifications are unchanged. The revised product gate allows exact full sequence correspondence as before. Partial sequence support requires independent RCSB/SIFTS chain-to-UniProt evidence, a PDB ID from the uploaded HEADER, an exact author-chain match, and passing sequence support against the RCSB entity sequence. Externally verified accession alone never authorizes generation.", "",
        "| Dataset | M5 false accepts | M6 false accepts | M5 false rejects | M6 false rejects |",
        "|---|---:|---:|---:|---:|",
        f"| Synthetic constructed scenarios (n={synthetic['case_count']}) | {len(synthetic['m5_false_acceptances'])} | {len(synthetic['m6_false_acceptances'])} | {len(synthetic['m5_false_rejections'])} | {len(synthetic['m6_false_rejections'])} |",
        f"| Real source-labeled chain cases (n={real['case_count']}, entries={len(real['unique_pdb_entries'])}) | — | {len(real['false_acceptances'])} | — | {len(real['false_rejections'])} |", "",
        "Synthetic examples are policy stress tests and are not biological-performance estimates. The existing 1CRN source-conflict diagnostic is excluded from these totals and from the separately curated real-source dataset. Real cases are only two PDB entries (three positive chain records plus one wrong-target negative control), so they are development/evidence checks, not an independent validation cohort.", "",
        "## Synthetic false-acceptance cases", "",
        f"M5 false accepts: {', '.join(synthetic['m5_false_acceptances']) or 'none'}.",
        f"M6 false accepts: {', '.join(synthetic['m6_false_acceptances']) or 'none'}.",
        f"M6 false rejections against the constructed labels: {', '.join(synthetic['m6_false_rejections']) or 'none'}.", "",
        "The close-homolog and short exact-fragment cases have no independent structure-to-target evidence in the synthetic fixtures and are blocked. Partial synthetic cases that were labeled allowable are also blocked absent such evidence; this is the conservative tradeoff and must not be interpreted as calibrated sensitivity.", "",
        "M5 1CRN source-conflict diagnostic: `real_1crn_chain_a_p01542` remains separately reported in JSON under `diagnostics`; it is not scored because its fixture explicitly records a source conflict.", "",
        "## Real-source cases", "",
        "| PDB chain | Supplied accession | DBREF | RCSB/SIFTS | UniProt identity | Reference coverage | Decision | Expected |",
        "|---|---|---|---|---:|---:|---|---|",
    ]
    for case in real["cases"]:
        val = case["uniprot_validation"]
        rows = [x.get("database_accession") for x in case["rcsb_mapping"] and [case["rcsb_mapping"]] or []]
        lines.append(
            f"| {case['pdb']}:{case['chain']} | {case['accession']} | {', '.join(case.get('observed_dbref_records', [])) or 'none'} | {rows[0] if rows else 'no match'} | {val.get('identity_percent', 0):.2f}% | {val.get('reference_sequence_coverage', 0):.1%} | {'allow' if case['actual_generation_allowed'] else 'deny'} | {'allow' if case['expected_generation_allowed'] else 'deny'} |"
        )
    lines.extend([
        "", "RCSB PDB/UniProt mapping and PDB SEQADV annotations supply the labels independently of the alignment score. 1M17 is an EGFR kinase-domain construct mapped to P00533; 3PP0 is an engineered HER2 kinase-domain construct with chains A/B mapped to P04626 and documented engineered substitutions. The 3PP0-as-P00533 row is a close-family wrong-target control.", "",
        "## Reproduction and limitations", "",
        "Run with `.venv-win\\Scripts\\python.exe scripts\\evaluate_target_identity_policy_m6.py`. Unit tests use deterministic mocked RCSB responses; the versioned files in `real_pdb/` are source snapshots fetched from RCSB and UniProt during manual curation. The application uses the live RCSB Data API only for partial sequence support; network failures, malformed API responses, chain remapping, or accession conflicts fail closed. API availability and the PDB API's author/label chain mapping remain operational limitations.", "",
        "The real fixture labels and source snapshot checksums are recorded in `real_world_fixture_manifest.json`; the full per-case evaluation is in `milestone6_results.json`.", "",
        "This policy validates chain-to-target identity evidence only. It does not validate a binding pocket, ligand pose, binding affinity, target engagement, efficacy, or a quantum advantage.", "",
        "## Sources", "",
        "- [RCSB 1M17](https://www.rcsb.org/structure/1M17); [RCSB 3PP0](https://www.rcsb.org/structure/3PP0)",
        "- [RCSB Data API](https://data.rcsb.org/)",
        "- [UniProt P00533](https://www.uniprot.org/uniprotkb/P00533/entry); [UniProt P04626](https://www.uniprot.org/uniprotkb/P04626/entry)", "",
    ])
    return "\n".join(lines)


def run(json_output: Path, markdown_output: Path) -> dict:
    source_files = [
        "1M17.pdb", "3PP0.pdb", "1M17_A_instance.json", "1M17_entity_1.json",
        "3PP0_A_instance.json", "3PP0_B_instance.json", "3PP0_entity_1.json",
        "P00533.fasta", "P04626.fasta",
    ]
    results = {
        "schema_version": "1.0.0",
        "evaluation": "CureGenix M6 target identity policy",
        "python_version": sys.version,
        "platform": platform.platform(),
        "source_snapshot_accessed_date": "2026-10-26",
        "source_snapshots": [
            {"path": f"real_pdb/{name}", "sha256": hashlib.sha256((REAL / name).read_bytes()).hexdigest(), "bytes": (REAL / name).stat().st_size}
            for name in source_files
        ],
        "baseline_reproduction": json.loads((OUT / "baseline" / "reproduced_results.json").read_text(encoding="utf-8"))["summary"],
        "policy": {
            "sequence_thresholds_changed": False,
            "exact_full_sequence_requires": "selected-chain DBREF and exact UniProt lookup already established by the identity resolver; full correspondence, no substitutions or gaps",
            "partial_sequence_requires": "same-chain RCSB/SIFTS UniProt mapping, matching uploaded HEADER PDB ID and author chain, plus observed-chain support against RCSB entity sequence",
            "network_failure_behavior": "fail closed for partial-support generation",
        },
        "synthetic": evaluate_synthetic(),
        "real_world": evaluate_real(),
    }
    results["diagnostics"] = results["synthetic"].pop("diagnostic_only")
    manifest = {
        "dataset_version": "1.0.0",
        "curated_on": "2026-10-26",
        "labeling_method": "RCSB PDB polymer-entity UniProt/SIFTS mapping and author-chain instance identity; labels are not derived from sequence alignment metrics.",
        "limitations": [
            "Only two unique PDB entries; not an independent validation cohort.",
            "3PP0 chains A and B share one polymer entity and are not independent biological examples.",
            "The 3PP0 wrong-target case is a useful related-kinase negative control, not a broad homolog benchmark.",
            "Structure-to-accession identity does not prove target function, pocket validity, binding, or activity.",
        ],
        "source_snapshots": results["source_snapshots"],
        "cases": results["real_world"]["cases"],
    }
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_output.write_text(build_report(results), encoding="utf-8")
    (OUT / "real_world_fixture_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, default=OUT / "milestone6_results.json")
    parser.add_argument("--markdown-output", type=Path, default=OUT / "milestone6_report.md")
    args = parser.parse_args()
    results = run(args.json_output, args.markdown_output)
    print(json.dumps({"synthetic": {key: results["synthetic"][key] for key in ("case_count", "m5_false_acceptances", "m6_false_acceptances", "m6_false_rejections")}, "real_world": {key: results["real_world"][key] for key in ("case_count", "false_acceptances", "false_rejections")}, "json": str(args.json_output), "report": str(args.markdown_output)}, indent=2))


if __name__ == "__main__":
    main()
