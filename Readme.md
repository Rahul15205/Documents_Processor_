# Document Processing with LLMs

This project processes legal contracts from the CUAD dataset and extracts three important clauses along with a concise summary. This version uses a fast, optimized approach with regex pre-filtering and four Groq API calls per PDF (Termination, Confidentiality, Liability, Summary). It provides very high accuracy and avoids Groq rate limits while keeping processing under 20–30 seconds per PDF.

## 🚀 Features

- Fast clause extraction using Groq's Llama 3.1 8B Instant
- Regex-based section filtering for speed
- Extracts three verbatim clauses:
  - Termination
  - Confidentiality
  - Liability
- Generates a 100–150 word summary
- Outputs JSON and CSV
- Zero rate limiting and fully free with Groq

## 📦 Installation

### 1. Clone the repository

git clone your-repo-url

cd project-folder


### 2. Install dependencies

pip install -r requirements.txt


### 3. Add Groq API key

Create a `.env` file:
GROQ_API_KEY=your_key_here

Get your key at: https://console.groq.com/keys

## 📁 Project Structure

project/

│── contract_pipeline.py

│── README.md

│── requirements.txt

│

├── data/

│ └── contracts/ # place your PDFs here

│

└── output/

├── contracts_extracted.json

└── contracts_extracted.csv

## 📥 Input Data

Download CUAD from:
https://zenodo.org/records/4595826  
Extract any 50 PDFs and place them in:
data/contracts/

## ▶️ Running the Pipeline

python contract_pipeline.py --input_dir data/contracts --out_json output/contracts_extracted.json --out_csv output/contracts_extracted.csv


## 📊 Output Format

{
"contract_id": "Contract_001",
"summary": "This agreement establishes...",
"termination": "12. Termination...",
"confidentiality": "The Receiving Party agrees...",
"liability": "Except for gross negligence..."
}


## ⚡ How It Works 
1. PDF → text using pdfplumber
2. Text normalized
3. Regex extracts relevant 1–2 page sections
4. Four Groq calls:
   - extract termination clause
   - extract confidentiality clause
   - extract liability clause
   - generate 100–150 word summary  
     This keeps prompts extremely small and reduces speed per contract from minutes to seconds.

## 📊 Performance

| Metric            | Old Version | Fast Version |
| ----------------- | ----------- | ------------ |
| API calls per PDF | 40–60       | 4            |
| Speed per PDF     | 5–6 min     | 18–30 sec    |
| Rate limits       | Many        | None         |
| Cost              | High        | Free         |

## 🛠 Requirements

pdfplumber

groq

pandas

tqdm

python-dotenv

## 🧪 Troubleshooting

**Slow speed:** Ensure the model is `llama-3.1-8b-instant`.  
**Rate limits:** This optimized version avoids them.  
**Invalid clause output:** The script filters down to relevant sections automatically.
