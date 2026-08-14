# Digital Arrest Dataset Collection Pipeline

## Project Objective
This project is a B.Tech final-year cybersecurity project designed to create a research-grade, non-synthetic dataset of real-world "Digital Arrest" scam incidents. 

## Non-Synthetic Data Policy
**The final dataset contains only source-backed incidents. Synthetic examples are not included in the dataset.**
The core philosophy is to extract information that is explicitly supported by the collected source text. If information is absent, it is stored as `NULL`. No LLM hallucination or synthetic generation is permitted.

## Digital Arrest Definition
A "Digital Arrest" scam involves criminals impersonating law enforcement (Police, CBI, ED) or officials (Customs, Telecom Dept), claiming the victim's identity is implicated in a crime (money laundering, illegal parcels). They often coerce victims into remaining on a video call (Skype, WhatsApp) while demanding money to "clear" their name.

## Data Sources
- **News Reports**: Google News RSS feeds using carefully selected queries.
- Can be expanded to use GDELT, NewsAPI, and HTML scraping of official advisories (CERT-In, Police Portals).

## Collection Methodology
- The pipeline fetches raw documents from source adapters.
- It applies rate limiting, timeouts, and robust error handling to ensure ethical scraping.

## Extraction Methodology
- **Filter**: Articles are keyword-filtered to ensure relevance to "Digital Arrest" context (ignoring real physical arrests).
- **Extract**: Uses regex and keyword mapping to extract structured fields (scenarios, authorities, risk levels). Explicit quotes are extracted as the "scam text".
- **Deduplicate**: Removes duplicates based on URLs and exact text matches.

## Human Verification Methodology
- The pipeline outputs candidates to `data/candidates.csv` with `verified=0` and `needs_human_review=1`.
- A human researcher reviews the source URL and the extracted text. If accurate, they set `verified=1`.
- The `curate` command then promotes these to `data/digital_arrest_dataset.csv`.

## Dataset Schema
- `id`: Unique identifier
- `text`: Exact scam text/message quoted from the source (or NULL)
- `label`: 1 for verified
- `scam_type`: Always "Digital Arrest"
- `scenario`: e.g., Money Laundering, Courier Scam
- `source`: e.g., News Report
- `language`: e.g., English, Hindi
- `risk_level`: Low, Medium, High, Critical
- `authority_impersonated`: e.g., CBI, Police
- `communication_channel`: e.g., Voice Call, WhatsApp
- `source_url`: URL of the source
- `source_name`, `source_publication_date`, `collection_timestamp`, `source_country`, `verified`, `needs_human_review`.

## Installation
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in API keys if required.

## Running the Pipeline
You can run individual stages:
- `python main.py collect`
- `python main.py extract`
- `python main.py validate`
- `python main.py curate`

Or run the full automated sequence:
- `python main.py pipeline`

## Limitations
- Extraction heavily relies on formatting (e.g., quotes) to find exact text.
- Fallbacks to full HTML scraping can be fragile if sites change structure.

## Ethical Considerations
- This pipeline implements backoffs and respects rate limits.
- PII is not actively collected, but researchers should redact it during the human validation phase if found in public reports.
