import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, Optional
import pdfplumber
from tqdm import tqdm
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


# PDF → TEXT EXTRACTION

def extract_text_from_pdf(path: Path) -> str:
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            text_parts.append(text)
    return "\n\n".join(text_parts)

def normalize_text(txt: str) -> str:
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    txt = re.sub(r"Page\s+\d+\s+of\s+\d+", "", txt, flags=re.IGNORECASE)
    return txt.strip()


# GROQ LLM WRAPPER

from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("❌ Missing GROQ_API_KEY in environment variables")

def call_groq(system_prompt: str, user_prompt: str, max_tokens=3000):
    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",     
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print("Groq Error:", e)
        return ""


# FAST CLAUSE FILTERING (Regex)
# Takes large contract → extracts only relevant 1000–1500 chars

def find_relevant_section(text: str, clause_type: str) -> str:
    patterns = {
        "termination": r"(termination[\s\S]{0,1800})",
        "confidentiality": r"(confidential[\s\S]{0,1800})",
        "liability": r"(liabilit[\s\S]{0,1800})"
    }

    pattern = patterns.get(clause_type.lower())
    if pattern:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)

    # fallback: return first 2000 chars
    return text[:2000]


# LLM-BASED CLAUSE EXTRACTION (1 CALL PER CLAUSE)

CLAUSE_SYSTEM_PROMPT = (
    "You are a legal contract clause extractor. "
    "Return ONLY the exact clause text, verbatim, as it appears in the contract. "
    "If not found, return an empty string. Do not paraphrase."
)

def extract_clause(full_text: str, clause_type: str) -> str:
    filtered = find_relevant_section(full_text, clause_type)

    user_prompt = f"""
Extract the {clause_type} clause verbatim from the text below.
Return ONLY the original clause text. No explanation.

Text:
\"\"\"{filtered}\"\"\"
"""
    return call_groq(CLAUSE_SYSTEM_PROMPT, user_prompt, max_tokens=800)


# SUMMARY (1 CALL)

SUMMARY_SYSTEM_PROMPT = (
    "You are an expert legal summarizer. "
    "Write a 100–150 word summary including: purpose, obligations, risks."
)

def summarize_contract(full_text: str) -> str:
    short = full_text[:5000]   # Fast + enough content

    user_prompt = f"""
Write a clear 100–150 word summary including purpose, both parties' obligations, and risks.

Contract:
\"\"\"{short}\"\"\"
"""
    return call_groq(SUMMARY_SYSTEM_PROMPT, user_prompt, max_tokens=400)


# MAIN CONTRACT PROCESSING LOGIC

def process_contract(pdf_path: Path) -> Dict[str, Optional[str]]:
    contract_id = pdf_path.stem
    raw = extract_text_from_pdf(pdf_path)
    full_text = normalize_text(raw)

    termination = extract_clause(full_text, "termination")
    confidentiality = extract_clause(full_text, "confidentiality")
    liability = extract_clause(full_text, "liability")

    summary = summarize_contract(full_text)

    return {
        "contract_id": contract_id,
        "summary": summary,
        "termination": termination,
        "confidentiality": confidentiality,
        "liability": liability
    }


# CLI ENTRY

def main(input_dir: str, out_json: str, out_csv: Optional[str]):
    input_dir = Path(input_dir)
    pdfs = sorted(input_dir.glob("*.pdf"))

    rows = []
    for pdf in tqdm(pdfs, desc="Processing PDFs"):
        try:
            rows.append(process_contract(pdf))
        except Exception as e:
            print(f"Error processing {pdf.name}: {e}")

    # Save JSON
    with open(out_json, "w", encoding="utf8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    # Save CSV
    if out_csv:
        pd.DataFrame(rows).to_csv(out_csv, index=False)

    print(f"🎉 Done! Processed {len(rows)} PDFs → {out_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--out_json", required=True)
    parser.add_argument("--out_csv", default=None)
    args = parser.parse_args()
    main(args.input_dir, args.out_json, args.out_csv)
