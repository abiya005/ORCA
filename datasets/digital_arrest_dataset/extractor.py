import re
import logging
from langdetect import detect, LangDetectException
import config

class Extractor:
    def __init__(self):
        pass

    def extract_scam_text(self, text):
        """Extract explicit quoted text or transcripts that might be the scam message."""
        if not text:
            return None
            
        # 1. Look for text in double quotes
        quotes = re.findall(r'"([^"]*)"', text)
        quotes += re.findall(r'“([^”]*)”', text)
        
        # 2. Look for transcript markers like "The message read: ..." or "caller said: ..."
        # Matches patterns like "message was: <text>" or "said: <text>" up to a period or newline
        transcript_patterns = [
            r'message read:\s*([^.\n]+)',
            r'message stated:\s*([^.\n]+)',
            r'caller said:\s*([^.\n]+)',
            r'stating that\s*([^.\n]+)',
            r'told him that\s*([^.\n]+)'
        ]
        
        for pattern in transcript_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            quotes.extend(matches)
        
        # Filter quotes that are long enough to be a message and aren't just names
        candidate_quotes = [q.strip() for q in quotes if len(q.split()) > 5]
        
        if candidate_quotes:
            # Return the longest candidate as it's most likely the full transcript
            return sorted(candidate_quotes, key=len, reverse=True)[0]
        return None

    def extract_field(self, text, keywords_list):
        if not text:
            return None
        text_lower = text.lower()
        for item in keywords_list:
            # Use regex for word boundaries to prevent 'ED' matching 'received'
            pattern = r'\b' + re.escape(item.lower()) + r'\b'
            if re.search(pattern, text_lower):
                return item
        return None

    def detect_language(self, text):
        if not text:
            return "Unknown"
        try:
            lang_code = detect(text)
            lang_map = {'en': 'English', 'hi': 'Hindi', 'ml': 'Malayalam', 'ta': 'Tamil', 'te': 'Telugu', 'kn': 'Kannada', 'bn': 'Bengali', 'mr': 'Marathi'}
            return lang_map.get(lang_code, "Other")
        except LangDetectException:
            return "Unknown"
            
    def determine_risk_level(self, text):
        if not text:
            return "Unknown"
        text_lower = text.lower()
        if any(w in text_lower for w in ["crore", "lakh", "suicide", "surveillance", "extort"]):
            return "Critical"
        if any(w in text_lower for w in ["arrest", "warrant", "freeze", "fir"]):
            return "High"
        if any(w in text_lower for w in ["fine", "fee", "penalty"]):
            return "Medium"
        return "Low"

    def process_record(self, record):
        content = record.get("raw_content", "")
        title = record.get("source_title", "")
        combined = f"{title} {content}"
        
        extracted_text = self.extract_scam_text(content)
        
        return {
            "text": extracted_text, # Will be None/Null if no explicit quote found
            "incident_description": content.strip() if content else None, # For model training when verbatim text is missing
            "label": 1,
            "scam_type": "Digital Arrest",
            "scenario": self.extract_field(combined, config.SCENARIOS),
            "source": record.get("source_type"),
            "language": self.detect_language(extracted_text or content),
            "risk_level": self.determine_risk_level(combined),
            "authority_impersonated": self.extract_field(combined, config.AUTHORITIES),
            "communication_channel": self.extract_field(combined, config.CHANNELS) or "Unknown",
            "source_url": record.get("source_url"),
            "source_name": record.get("source_name"),
            "source_publication_date": record.get("source_publication_date"),
            "collection_timestamp": record.get("collection_timestamp"),
            "source_country": record.get("source_country")
        }

    def extract(self, filtered_records):
        logging.info("Starting extraction phase...")
        extracted_records = []
        for r in filtered_records:
            extracted_records.append(self.process_record(r))
        return extracted_records
