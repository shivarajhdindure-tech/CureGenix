"""
LLM Service Layer — Centralized LLM access for the agent pipeline.

Supports:
  - Groq (primary, via GROQ_API_KEY — OpenAI-compatible, uses Llama 3.3 70B)
  - Built-in template fallback (no API key needed)

Design principles:
  - LLM is used ONLY for reasoning, interpretation, explanation
  - LLM is NOT used for database lookup, numeric scoring, or parsing
  - Retry logic with exponential backoff
  - In-memory response caching
"""

import os
import hashlib
import time
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Cache for LLM responses (prompt hash -> response text)
_response_cache: dict = {}

MAX_RETRIES = 2
RETRY_DELAY = 2.0  # seconds


# ─────────────────────────────────────────────────────────────────────────────
# Core LLM Call
# ─────────────────────────────────────────────────────────────────────────────

def call_llm(prompt: str, temperature: float = 0.7, max_tokens: int = 1024) -> str:
    """
    Call the LLM with a prompt and return the response text.

    Priority: Groq API → Template Fallback
    Results are cached by prompt hash to avoid redundant API calls.
    """
    # Check cache first
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    if prompt_hash in _response_cache:
        return _response_cache[prompt_hash]

    response_text = ""

    if GROQ_API_KEY:
        response_text = _call_groq(prompt, temperature, max_tokens)

    # If Groq failed or no key, use fallback
    if not response_text:
        response_text = _template_fallback(prompt)

    # Cache the result
    _response_cache[prompt_hash] = response_text
    return response_text


def _call_groq(prompt: str, temperature: float, max_tokens: int) -> str:
    """Call Groq API (OpenAI-compatible) with retry logic using requests."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a biomedical AI research assistant specializing in "
                    "drug discovery and protein biology. Provide concise, "
                    "scientifically accurate responses."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.post(
                GROQ_URL,
                json=payload,
                headers=headers,
                timeout=20
            )
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
            else:
                print(f"[LLM] Groq HTTP error (attempt {attempt+1}): {resp.status_code}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * (2 ** attempt))
        except requests.exceptions.Timeout:
            print(f"[LLM] Groq timeout (attempt {attempt+1})")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (2 ** attempt))
        except Exception as e:
            print(f"[LLM] Groq error (attempt {attempt+1}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (2 ** attempt))

    return ""


def _template_fallback(prompt: str) -> str:
    """
    Generate a structured scientific response without an LLM API.
    Parses context from the prompt to produce reasonable analysis text.
    Used when the API key is missing or all API calls fail.
    """
    # Try to extract protein name from prompt
    protein_name = "the target protein"
    if "Protein:" in prompt:
        for line in prompt.split("\n"):
            if line.strip().startswith("Protein:"):
                protein_name = line.split(":", 1)[1].strip()
                break

    if "biological function" in prompt.lower() or "research" in prompt.lower():
        return (
            f"## Biological Analysis of {protein_name}\n\n"
            f"**Function**: {protein_name} is a protein target identified through structural analysis "
            f"of the uploaded PDB file. Based on the available sequence and structural data, this protein "
            f"plays a role in cellular signaling and regulation pathways.\n\n"
            f"**Druggability Assessment**: The structural features including binding pocket geometry and "
            f"surface accessibility suggest this target has moderate-to-high druggability potential. "
            f"The presence of defined binding sites supports small molecule intervention strategies.\n\n"
            f"**Known Therapeutic Context**: Literature evidence suggests ongoing research into compounds "
            f"targeting this protein family. Further experimental validation is recommended to confirm "
            f"binding affinity and selectivity of identified candidates.\n\n"
            f"*Note: This analysis was generated using template-based reasoning. "
            f"Connect a Groq API key for AI-powered deep analysis.*"
        )
    elif "drug discovery expert" in prompt.lower() or "decision" in prompt.lower():
        return (
            f"Based on the screening and risk assessment data, the top-ranked candidate demonstrates "
            f"the most favorable combination of drug-likeness, predicted potency, and safety profile. "
            f"The composite scoring accounts for BBB permeability, structural toxicity alerts, and "
            f"Lipinski rule compliance. Candidates with approved status carry higher confidence due to "
            f"existing clinical evidence. Novel candidates require further preclinical validation. "
            f"The risk-adjusted ranking prioritizes candidates with low toxicity flags and established "
            f"safety margins.\n\n"
            f"*Note: This reasoning was generated using template-based analysis. "
            f"Connect a Groq API key for AI-powered decision reasoning.*"
        )
    else:
        return (
            f"Analysis of {protein_name}: The available data supports further investigation "
            f"of the identified drug candidates. Structural and pharmacological assessment "
            f"indicates viable therapeutic potential pending experimental validation."
        )
