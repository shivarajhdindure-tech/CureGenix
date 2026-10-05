"""
PDB Parser Service — Python wrapper around the Node.js pdb2json-parser.

Calls the CLI (node cli.js <pdb_file>) and reads back the AlphaFold-compatible
JSON output produced by extract-summary.js.
"""

import subprocess
import json
import os


# Resolve parser directory relative to *this* file so it works no matter
# where the FastAPI process is started from.
# parse-pdb/ lives alongside backend/ inside ai-drug-discovery/
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PARSER_DIR = os.path.normpath(os.path.join(_THIS_DIR, "..", "..", "parse-pdb"))
OUTPUT_PATH = os.path.join(PARSER_DIR, "output.json")


def parse_pdb_file(pdb_file_path: str) -> dict:
    """
    Parse a PDB file using the Node.js parser.

    Parameters
    ----------
    pdb_file_path : str
        Absolute path to the .pdb file to parse.

    Returns
    -------
    dict
        AlphaFold-query-compatible parsed protein data with keys:
        input_type, protein, structure_summary, metadata.

    Raises
    ------
    RuntimeError
        If the Node.js parser exits with a non-zero code or the output
        cannot be read.
    """
    abs_pdb = os.path.abspath(pdb_file_path)

    if not os.path.isfile(abs_pdb):
        raise FileNotFoundError(f"PDB file not found: {abs_pdb}")

    import shutil
    node_exe = "node"
    if not shutil.which("node"):
        playwright_node = os.path.expanduser(r"~\AppData\Local\ms-playwright-go\1.50.1\node.exe")
        if os.path.exists(playwright_node):
            node_exe = playwright_node
        else:
            raise RuntimeError("Node.js is not installed or not found in PATH.")

    try:
        result = subprocess.run(
            [node_exe, "cli.js", abs_pdb],
            cwd=PARSER_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Parser failed (exit {result.returncode}): {result.stderr.strip()}")

        # Read the JSON output written by the CLI
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            parsed_data = json.load(f)

        return parsed_data

    except subprocess.TimeoutExpired:
        raise RuntimeError("PDB parser timed out after 30 seconds")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Parser produced invalid JSON: {e}")
    except FileNotFoundError as e:
        raise RuntimeError(f"PDB parsing error: {e}")
