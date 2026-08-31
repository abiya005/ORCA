import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# HTTP Request Config
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 15))
MAX_REQUESTS_PER_DOMAIN = int(os.getenv("MAX_REQUESTS_PER_DOMAIN", 500))
USER_AGENT = "DigitalArrestScamResearchBot/1.0 (B.Tech Research Project)"

# Keywords for Filtering
DIGITAL_ARREST_KEYWORDS = [
    "digital arrest", "online arrest", "skype arrest", "video call arrest",
    "fake police call", "cyber crime police impersonation", "cbi impersonation",
    "ed impersonation", "narcotics digital arrest", "customs digital arrest",
    "rbi digital arrest", "fedex digital arrest", "courier digital arrest",
    "money laundering digital arrest", "fake arrest warrant", "video verification fraud",
    "fake cbi", "fake ed officer", "customs clearance scam", "parcel detained scam",
    "fake narcotics control bureau", "trai impersonation", "dot impersonation scam",
    "police video call scam", "supreme court digital arrest", "cyber cell scam call"
]

# Impersonated Authorities for Extraction
AUTHORITIES = [
    "CBI", "ED", "Mumbai Police", "Delhi Police", "Bengaluru Police", 
    "Hyderabad Police", "Kerala Police", "Tamil Nadu Police", "Maharashtra Police",
    "RBI", "Narcotics Bureau", "Customs", "Income Tax Department", "Supreme Court",
    "High Court", "TRAI", "Telecom Department", "Police", "Cybercrime Police"
]

# Scam Scenarios
SCENARIOS = [
    "Money Laundering", "Courier Scam", "Narcotics/Courier Scam", "Video Verification",
    "SIM Card Scam", "Bank Account Scam", "Fake Court Case", "Fake Arrest Warrant",
    "Customs Scam", "Tax Scam", "Police Impersonation", "CBI Impersonation", 
    "ED Impersonation", "KYC Scam", "Multi-Stage Impersonation"
]

# Communication Channels
CHANNELS = [
    "Voice Call", "WhatsApp", "Telegram", "SMS", "Email", "Video Call", "Skype"
]

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
CANDIDATES_CSV = os.path.join(DATA_DIR, "candidates.csv")
FINAL_DATASET_CSV = os.path.join(DATA_DIR, "digital_arrest_dataset.csv")
STATS_FILE = os.path.join(DATA_DIR, "dataset_statistics.json")
