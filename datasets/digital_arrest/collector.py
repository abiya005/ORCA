import time
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import json
import os
import config
from sources import GoogleNewsRSSSource, DDGSearchSource

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Collector:
    def __init__(self):
        self.sources = [
            GoogleNewsRSSSource(config.DIGITAL_ARREST_KEYWORDS[:5], days_back=30), 
            DDGSearchSource(config.DIGITAL_ARREST_KEYWORDS[:5], max_results=50)
        ]
        
    def fetch_full_text(self, url):
        """Attempts to fetch the full text of an article given its URL."""
        try:
            headers = {"User-Agent": config.USER_AGENT}
            response = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Simple heuristic: get text from paragraphs
            paragraphs = soup.find_all('p')
            text = "\n".join([p.get_text() for p in paragraphs if len(p.get_text()) > 20])
            return text
        except Exception as e:
            logging.warning(f"Failed to fetch full text from {url}: {e}")
            return None

    def collect(self):
        logging.info("Starting collection phase...")
        all_raw_data = []
        
        for source in self.sources:
            logging.info(f"Collecting from {source.name}...")
            count = 0
            for record in source.fetch():
                if count >= config.MAX_REQUESTS_PER_DOMAIN:
                    logging.info(f"Reached max requests for {source.name}")
                    break
                
                # Fetch full text if it's a URL-based source
                full_text = self.fetch_full_text(record["source_url"])
                if full_text:
                    record["raw_content"] = full_text
                
                record["collection_timestamp"] = datetime.now().isoformat()
                all_raw_data.append(record)
                count += 1
                time.sleep(1) # Rate limiting
                
        # Save raw data
        os.makedirs(config.RAW_DATA_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(config.RAW_DATA_DIR, f"raw_collection_{timestamp}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(all_raw_data, f, ensure_ascii=False, indent=2)
            
        logging.info(f"Collection complete. Saved {len(all_raw_data)} records to {filepath}")
        return all_raw_data

if __name__ == "__main__":
    Collector().collect()
