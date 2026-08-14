import feedparser
import urllib.parse
from abc import ABC, abstractmethod
import config
import requests
import time
import logging
from datetime import datetime, timedelta

class SourceAdapter(ABC):
    def __init__(self, name, source_type, country="India"):
        self.name = name
        self.source_type = source_type
        self.country = country

    @abstractmethod
    def fetch(self):
        """Fetch data from the source and yield raw records as dicts."""
        pass


class GoogleNewsRSSSource(SourceAdapter):
    def __init__(self, queries, days_back=30):
        super().__init__(name="Google News RSS", source_type="News Report")
        self.queries = queries
        self.days_back = days_back
        self.base_url = "https://news.google.com/rss/search?q={}&hl=en-IN&gl=IN&ceid=IN:en"

    def fetch(self):
        # Implement date range pagination by chunking the search window
        end_date = datetime.now()
        
        for query in self.queries:
            # Chunking into 7-day windows to bypass 100 limit
            for i in range(0, self.days_back, 7):
                window_end = end_date - timedelta(days=i)
                window_start = window_end - timedelta(days=7)
                
                date_query = f"{query} after:{window_start.strftime('%Y-%m-%d')} before:{window_end.strftime('%Y-%m-%d')}"
                url = self.base_url.format(urllib.parse.quote(date_query))
                
                try:
                    feed = feedparser.parse(url)
                    for entry in feed.entries:
                        yield {
                            "source_name": self.name,
                            "source_url": entry.link,
                            "source_type": self.source_type,
                            "source_publication_date": entry.get("published", ""),
                            "source_country": self.country,
                            "source_title": entry.get("title", ""),
                            "raw_content": entry.get("summary", "") or entry.get("description", ""),
                            "language": "English"
                        }
                except Exception as e:
                    logging.warning(f"Error fetching Google News for {date_query}: {e}")
                
                time.sleep(1) # Be nice to Google


from duckduckgo_search import DDGS

class DDGSearchSource(SourceAdapter):
    def __init__(self, queries, max_results=200):
        super().__init__(name="DuckDuckGo Search", source_type="Public Complaint/Forum")
        self.queries = queries
        self.max_results = max_results

    def fetch(self):
        # Searching forums where victims post verbatim complaints
        forum_sites = ["site:consumercomplaints.in", "site:quora.com", "site:reddit.com/r/india"]
        
        with DDGS() as ddgs:
            for base_query in self.queries:
                for site in forum_sites:
                    search_query = f"{base_query} {site}"
                    try:
                        results = ddgs.text(search_query, max_results=self.max_results)
                        for r in results:
                            yield {
                                "source_name": self.name,
                                "source_url": r.get("href"),
                                "source_type": self.source_type,
                                "source_publication_date": "", # DDGS doesn't always provide dates
                                "source_country": self.country,
                                "source_title": r.get("title", ""),
                                "raw_content": r.get("body", ""),
                                "language": "English"
                            }
                    except Exception as e:
                        logging.warning(f"Error fetching DDGS for '{search_query}': {e}")
                    
                    time.sleep(2) # Rate limit protection
