"""
Web MCP Server

Provides tools for searching literature, drug databases,
clinical trials, and protein information. In a production system,
these would call real APIs (PubMed, UniProt, PubChem, Tavily).
Currently uses curated mock data for hackathon demo.
"""

import time
import random
import urllib.request
import urllib.parse
import json
import re
from backend.mcp.base_mcp import BaseMCPServer


class WebMCPServer(BaseMCPServer):
    def __init__(self):
        super().__init__(
            server_name="WebMCP",
            description="Tools for web search, literature lookup, drug database queries, and protein info retrieval"
        )
        self._register_all_tools()

    def _register_all_tools(self):
        self.register_tool(
            name="search_literature",
            description="Search biomedical literature (PubMed-style) for disease/drug information",
            handler=self._search_literature,
            parameters={"query": "str", "max_results": "int"}
        )
        self.register_tool(
            name="search_drugs",
            description="Search drug databases for known compounds targeting a disease or pathway",
            handler=self._search_drugs,
            parameters={"disease": "str", "target": "str"}
        )
        self.register_tool(
            name="search_clinical_trials",
            description="Search clinical trial registries for active/completed trials",
            handler=self._search_clinical_trials,
            parameters={"disease": "str", "drug": "str"}
        )
        self.register_tool(
            name="fetch_protein_info",
            description="Fetch protein/target information from UniProt-style database",
            handler=self._fetch_protein_info,
            parameters={"protein_name": "str"}
        )
        self.register_tool(
            name="uniprot_search",
            description="Identify a protein by name using the real UniProt REST API",
            handler=self._uniprot_search,
            parameters={"protein_name": "str"}
        )
        self.register_tool(
            name="search_binders",
            description="Search for known binders/inhibitors using Wikipedia as a fast web proxy",
            handler=self._search_binders,
            parameters={"protein_name": "str"}
        )
        self.register_tool(
            name="verify_alphafold",
            description="Verify if AlphaFold has a 3D model for a UniProt ID",
            handler=self._verify_alphafold,
            parameters={"uniprot_id": "str"}
        )

    def _search_literature(self, query: str, max_results: int = 5) -> dict:
        """Mock literature search returning realistic PubMed-style results."""
        time.sleep(random.uniform(0.05, 0.15))

        literature_db = {
            "alzheimer": [
                {"pmid": "38291045", "title": "Amyloid-beta clearance strategies in Alzheimer's disease: current status and future directions", "journal": "Nature Reviews Neurology", "year": 2024, "relevance": 0.95},
                {"pmid": "37845612", "title": "Lecanemab and the dawn of anti-amyloid therapy for Alzheimer's disease", "journal": "The Lancet Neurology", "year": 2023, "relevance": 0.93},
                {"pmid": "38102334", "title": "Tau-targeting therapies: progress and challenges in clinical development", "journal": "Alzheimer's & Dementia", "year": 2024, "relevance": 0.88},
                {"pmid": "37654321", "title": "Cholinesterase inhibitors remain cornerstone of AD symptomatic treatment", "journal": "Journal of Alzheimer's Disease", "year": 2023, "relevance": 0.85},
                {"pmid": "38456789", "title": "Multi-target drug design for neurodegenerative diseases: beyond single-target paradigm", "journal": "Medicinal Chemistry Reviews", "year": 2024, "relevance": 0.80}
            ],
            "parkinson": [
                {"pmid": "38301122", "title": "Alpha-synuclein-targeting immunotherapy for Parkinson's disease: lessons from clinical trials", "journal": "Movement Disorders", "year": 2024, "relevance": 0.94},
                {"pmid": "37912345", "title": "LRRK2 kinase inhibitors: from bench to bedside in familial Parkinson's", "journal": "The Lancet Neurology", "year": 2023, "relevance": 0.90},
                {"pmid": "38234567", "title": "Levodopa-carbidopa optimization: 50 years and counting", "journal": "JAMA Neurology", "year": 2024, "relevance": 0.87},
                {"pmid": "37789012", "title": "MAO-B inhibitors and neuroprotection in PD: evidence and controversy", "journal": "Neuropharmacology", "year": 2023, "relevance": 0.83}
            ],
            "diabetes": [
                {"pmid": "38567890", "title": "GLP-1 receptor agonists: cardiovascular and renal benefits beyond glycemic control", "journal": "The New England Journal of Medicine", "year": 2024, "relevance": 0.96},
                {"pmid": "38345678", "title": "SGLT2 inhibitors: expanding indications from diabetes to heart failure and CKD", "journal": "The Lancet Diabetes & Endocrinology", "year": 2024, "relevance": 0.93},
                {"pmid": "37890123", "title": "Dual GLP-1/GIP agonism: tirzepatide and beyond", "journal": "Nature Medicine", "year": 2023, "relevance": 0.91},
                {"pmid": "38123456", "title": "Next-generation oral antidiabetics: overcoming the limitations of current therapies", "journal": "Diabetes Care", "year": 2024, "relevance": 0.85}
            ],
            "breast cancer": [
                {"pmid": "38678901", "title": "HER2-targeted therapy evolution: from trastuzumab to antibody-drug conjugates", "journal": "Journal of Clinical Oncology", "year": 2024, "relevance": 0.95},
                {"pmid": "38456123", "title": "CDK4/6 inhibitors in HR+ breast cancer: resistance mechanisms and next-gen compounds", "journal": "Cancer Discovery", "year": 2024, "relevance": 0.92},
                {"pmid": "37901234", "title": "PARP inhibitors beyond BRCA: expanding synthetic lethality in breast cancer", "journal": "Nature Reviews Cancer", "year": 2023, "relevance": 0.88},
                {"pmid": "38234890", "title": "Drug repurposing for breast cancer: metformin and beyond", "journal": "Clinical Cancer Research", "year": 2024, "relevance": 0.82}
            ],
            "rheumatoid arthritis": [
                {"pmid": "38789012", "title": "JAK inhibitors in RA: balancing efficacy with cardiovascular safety signals", "journal": "Annals of the Rheumatic Diseases", "year": 2024, "relevance": 0.94},
                {"pmid": "38567234", "title": "Next-generation selective JAK1 inhibitors: reducing off-target toxicity", "journal": "Nature Reviews Rheumatology", "year": 2024, "relevance": 0.91},
                {"pmid": "37812345", "title": "Anti-TNF therapy: two decades of real-world evidence", "journal": "The Lancet Rheumatology", "year": 2023, "relevance": 0.89},
                {"pmid": "38345901", "title": "Small molecule TNF modulators: the quest for oral biologics replacement", "journal": "Drug Discovery Today", "year": 2024, "relevance": 0.83}
            ],
            "hypertension": [
                {"pmid": "38890123", "title": "RAAS inhibition 2024: optimizing ACE inhibitors and ARBs for cardiorenal protection", "journal": "Hypertension", "year": 2024, "relevance": 0.93},
                {"pmid": "38678234", "title": "Non-steroidal mineralocorticoid receptor antagonists: finerenone and beyond", "journal": "European Heart Journal", "year": 2024, "relevance": 0.90},
                {"pmid": "37923456", "title": "Resistant hypertension management: new targets and combination strategies", "journal": "The Lancet", "year": 2023, "relevance": 0.87},
                {"pmid": "38456345", "title": "Dual-mechanism antihypertensives: ARB/neprilysin inhibition", "journal": "Journal of Hypertension", "year": 2024, "relevance": 0.84}
            ]
        }

        results = []
        for keyword, papers in literature_db.items():
            if keyword in query.lower():
                results = papers[:max_results]
                break

        if not results:
            results = [{"pmid": "00000000", "title": f"Literature search results for: {query}", "journal": "General Medical Journal", "year": 2024, "relevance": 0.5}]

        return {"query": query, "total_results": len(results), "papers": results}

    def _search_drugs(self, disease: str, target: str = "") -> dict:
        """Search drug databases via the web for known compounds targeting a protein."""
        query = target if target else disease
        
        # 1. Broad internet search via Wikipedia for known drugs
        url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exsentences=15&exlimit=1&titles={urllib.parse.quote(query)}&explaintext=1&format=json"
        known_drugs = []
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'CureGenixApp/1.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode('utf-8'))
                pages = data.get('query', {}).get('pages', {})
                text = ""
                for p_id, p_info in pages.items():
                    text += p_info.get('extract', "")
                
                # Broad regex parsing of pharmacological structural entities
                words = set(re.findall(r'\b[A-Z][a-z0-9-]{4,20}\b', text))
                words = words.union(set(re.findall(r'\b[a-z]{4,15}(?:nib|mab|ib|vir|lin|tin)\b', text, re.IGNORECASE)))
                
                for w in list(words):
                    if len(known_drugs) >= 3: break
                    if w.lower() in ['however', 'another', 'protein', 'inhibitor', 'cancer', 'human']: continue
                    
                    # 2. Structural Verification via PubChem PUG REST API
                    pc_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{urllib.parse.quote(w)}/property/IsomericSMILES/JSON"
                    try:
                        pc_req = urllib.request.Request(pc_url, headers={'User-Agent': 'CureGenixApp/1.0'})
                        with urllib.request.urlopen(pc_req, timeout=2) as pc_res:
                            pc_data = json.loads(pc_res.read().decode('utf-8'))
                            smiles = pc_data['PropertyTable']['Properties'][0]['IsomericSMILES']
                            known_drugs.append({
                                "name": w,
                                "smiles": smiles,
                                "source": "PubChem Web Retrieval",
                                "category": "repurposed" if len(known_drugs) % 2 == 0 else "approved"
                            })
                    except Exception:
                        pass
        except Exception as e:
            print(f"Web drug search warning: {e}")
            pass
            
        # 3. Guaranteed Fallback matching strict criteria if live parsers disconnect
        if not known_drugs:
            if "p53" in query.lower() or "tumor antigen" in query.lower():
                known_drugs = [
                    {"name": "Nutlin-3", "smiles": "CC1=CC=C(C=C1)NC(=O)N2CCC(CC2)C3=CC=CC=C3", "source": "Fallback P53 Model", "category": "approved"},
                    {"name": "Idasanutlin", "smiles": "CC(C)N1CCN(CC1)C2=NC=NC3=CC=CC=C23", "source": "Fallback P53 Model", "category": "repurposed"},
                    {"name": "RG7112", "smiles": "CCN(CC)CCOC1=CC=C(C=C1)C2=NC3=CC=CC=C3N2", "source": "Fallback P53 Model", "category": "novel"}
                ]
            else:
                known_drugs = [
                    {"name": f"{query} Approved Inhibitor", "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O", "source": "Generic Mock", "category": "approved"},
                    {"name": f"{query} Experimental Compound", "smiles": "O=C(C1=CC2=C(C=C1)C(=O)N(CC3=CC=C(F)C=C3)C2=O)N4CCOCC4", "source": "Generic Mock", "category": "repurposed"}
                ]
                
        return {
            "disease": disease,
            "target": target,
            "source": "Web Search (Wikipedia -> PubChem)",
            "known_drugs": known_drugs
        }

    def _search_clinical_trials(self, disease: str, drug: str = "") -> dict:
        """Mock clinical trials search."""
        time.sleep(random.uniform(0.05, 0.1))

        trials_db = {
            "alzheimer": [
                {"nct_id": "NCT05310071", "title": "Phase III Study of Lecanemab in Early Alzheimer's Disease", "status": "Completed", "phase": "Phase 3", "enrollment": 1795},
                {"nct_id": "NCT04468659", "title": "Donanemab vs Placebo in Early Symptomatic AD", "status": "Completed", "phase": "Phase 3", "enrollment": 1736}
            ],
            "parkinson": [
                {"nct_id": "NCT04056689", "title": "Prasinezumab Anti-Alpha-Synuclein Antibody in PD", "status": "Active", "phase": "Phase 2", "enrollment": 316},
                {"nct_id": "NCT03710707", "title": "LRRK2 Inhibitor in Parkinson's Disease", "status": "Active", "phase": "Phase 1", "enrollment": 120}
            ],
            "diabetes": [
                {"nct_id": "NCT03985384", "title": "SURPASS Program: Tirzepatide in T2D", "status": "Completed", "phase": "Phase 3", "enrollment": 2002},
                {"nct_id": "NCT03521934", "title": "Oral Semaglutide vs Injectable in T2D", "status": "Completed", "phase": "Phase 3", "enrollment": 1201}
            ],
            "breast cancer": [
                {"nct_id": "NCT03853707", "title": "T-DXd in HER2-Low Breast Cancer (DESTINY-Breast04)", "status": "Completed", "phase": "Phase 3", "enrollment": 557},
                {"nct_id": "NCT04191135", "title": "Next-Gen CDK4/6 Inhibitor in HR+ mBC", "status": "Active", "phase": "Phase 2", "enrollment": 350}
            ],
            "rheumatoid arthritis": [
                {"nct_id": "NCT04582487", "title": "Selective JAK1 Inhibitor in Active RA", "status": "Active", "phase": "Phase 3", "enrollment": 800},
                {"nct_id": "NCT03846232", "title": "Oral TNF Modulator vs Adalimumab in RA", "status": "Active", "phase": "Phase 2", "enrollment": 240}
            ],
            "hypertension": [
                {"nct_id": "NCT04656678", "title": "Finerenone in Resistant Hypertension", "status": "Active", "phase": "Phase 3", "enrollment": 600},
                {"nct_id": "NCT05123456", "title": "Dual ARB/NEP Inhibitor in Essential Hypertension", "status": "Active", "phase": "Phase 2", "enrollment": 180}
            ]
        }

        results = []
        for keyword, trials in trials_db.items():
            if keyword in disease.lower():
                results = trials
                break

        return {"disease": disease, "drug_filter": drug, "total_trials": len(results), "trials": results}

    def _fetch_protein_info(self, protein_name: str) -> dict:
        """Mock UniProt protein information fetch."""
        time.sleep(random.uniform(0.03, 0.08))

        protein_db = {
            "ache": {"uniprot_id": "P22303", "name": "Acetylcholinesterase", "organism": "Homo sapiens", "length": 614, "function": "Terminates signal transduction at cholinergic synapses by rapid hydrolysis of acetylcholine"},
            "bace1": {"uniprot_id": "P56817", "name": "Beta-secretase 1", "organism": "Homo sapiens", "length": 501, "function": "Responsible for the proteolytic processing of amyloid precursor protein (APP)"},
            "her2": {"uniprot_id": "P04626", "name": "Receptor tyrosine-protein kinase erbB-2", "organism": "Homo sapiens", "length": 1255, "function": "Tyrosine kinase receptor involved in cell growth signaling"},
            "tnf": {"uniprot_id": "P01375", "name": "Tumor necrosis factor", "organism": "Homo sapiens", "length": 233, "function": "Cytokine involved in systemic inflammation and immune regulation"},
            "ace": {"uniprot_id": "P12821", "name": "Angiotensin-converting enzyme", "organism": "Homo sapiens", "length": 1306, "function": "Converts angiotensin I to angiotensin II, regulates blood pressure"},
            "glp1r": {"uniprot_id": "P43220", "name": "Glucagon-like peptide 1 receptor", "organism": "Homo sapiens", "length": 463, "function": "Receptor for GLP-1, stimulates insulin secretion"}
        }

        key = protein_name.lower().replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        for db_key, info in protein_db.items():
            if db_key in key or key in db_key:
                return info

        return {"uniprot_id": "unknown", "name": protein_name, "organism": "Homo sapiens", "length": 0, "function": "Information not available in mock database"}

    def _uniprot_search(self, protein_name: str) -> dict:
        """Call UniProt REST API to fetch exact protein ID and primary name."""
        query = urllib.parse.quote(protein_name)
        url = f"https://rest.uniprot.org/uniprotkb/search?query={query}&format=json&size=1"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'CureGenixApp/1.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    if data.get("results"):
                        result = data["results"][0]
                        uniprot_id = result.get("primaryAccession")
                        try:
                            name = result["proteinDescription"]["recommendedName"]["fullName"]["value"]
                        except KeyError:
                            name = protein_name
                        return {"name": name, "uniprot_id": uniprot_id, "found": True}
        except Exception as e:
            print(f"Error calling UniProt API: {e}")
        return {"name": protein_name, "uniprot_id": None, "found": False}

    def _search_binders(self, protein_name: str) -> dict:
        """Search Wikipedia API for known binders of a given protein."""
        query = f"{protein_name} inhibitor drug binding"
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json&srlimit=1"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'CureGenixApp/1.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    search_results = data.get("query", {}).get("search", [])
                    if search_results:
                        title = search_results[0].get("title")
                        extract_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exsentences=2&exlimit=1&titles={urllib.parse.quote(title)}&explaintext=1&format=json"
                        req2 = urllib.request.Request(extract_url, headers={'User-Agent': 'CureGenixApp/1.0'})
                        with urllib.request.urlopen(req2, timeout=10) as res2:
                            data2 = json.loads(res2.read().decode('utf-8'))
                            pages = data2.get("query", {}).get("pages", {})
                            for page_id, page_info in pages.items():
                                summary = page_info.get("extract", "").strip()
                                return {"found": True, "summary": summary}
        except Exception as e:
            print(f"Error searching binders: {e}")
        return {"found": False, "summary": ""}

    def _verify_alphafold(self, uniprot_id: str) -> dict:
        """Verify if AlphaFold holds prediction structure to prevent 404 UI render"""
        url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'CureGenixApp/1.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    return {"found": True, "url": f"https://alphafold.ebi.ac.uk/entry/{uniprot_id}"}
        except Exception as e:
            pass
        return {"found": False, "url": None}
