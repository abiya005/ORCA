import logging
from urllib.parse import urlparse

class Deduplicator:
    def __init__(self):
        pass

    def deduplicate(self, records):
        logging.info("Starting deduplication phase...")
        seen_urls = set()
        seen_texts = set()
        unique_records = []
        
        for r in records:
            url = r.get("source_url")
            text = r.get("text")
            
            # Normalize URL to avoid www vs non-www duplicates, basic heuristic
            clean_url = None
            if url:
                parsed = urlparse(url)
                clean_url = parsed.netloc + parsed.path
                
            if clean_url and clean_url in seen_urls:
                continue
                
            if text and text in seen_texts:
                continue
                
            if clean_url:
                seen_urls.add(clean_url)
            if text:
                seen_texts.add(text)
                
            unique_records.append(r)
            
        logging.info(f"Deduplication complete. Retained {len(unique_records)} unique records.")
        return unique_records
