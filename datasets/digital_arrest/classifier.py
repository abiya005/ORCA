import logging
import config

class Classifier:
    def __init__(self):
        self.keywords = config.DIGITAL_ARREST_KEYWORDS

    def is_relevant(self, text):
        """Determine if text is actually about Digital Arrest scams."""
        if not text:
            return False
            
        text_lower = text.lower()
        
        # Must contain at least one keyword
        for keyword in self.keywords:
            if keyword in text_lower:
                # Check negative keywords to avoid false positives (e.g. real physical arrests)
                if "physically arrested" in text_lower or "police physically arrested" in text_lower:
                    if "scam" not in text_lower and "fake" not in text_lower:
                        return False
                return True
                
        return False

    def filter_records(self, raw_records):
        logging.info("Starting filtering phase...")
        filtered = []
        for record in raw_records:
            title = record.get("source_title", "")
            content = record.get("raw_content", "")
            combined_text = f"{title} {content}"
            
            if self.is_relevant(combined_text):
                filtered.append(record)
                
        logging.info(f"Filtered {len(raw_records)} down to {len(filtered)} relevant records.")
        return filtered
