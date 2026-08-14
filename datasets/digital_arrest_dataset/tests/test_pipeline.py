import pytest
import sys
import os

# Ensure we can import the pipeline modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extractor import Extractor
from validator import Validator
from classifier import Classifier
from deduplicator import Deduplicator

def test_classifier():
    classifier = Classifier()
    
    # Positive case
    assert classifier.is_relevant("Man falls victim to digital arrest scam by fake CBI officers.") == True
    
    # Negative case (physical arrest)
    assert classifier.is_relevant("Police physically arrested the suspect yesterday.") == False
    
    # Empty case
    assert classifier.is_relevant("") == False

def test_extractor():
    extractor = Extractor()
    
    text1 = 'The victim received a call. The caller said "You are under digital arrest for money laundering." The victim lost 5 lakh rupees.'
    
    # Test quote extraction
    assert extractor.extract_scam_text(text1) == "You are under digital arrest for money laundering."
    
    text2 = 'The police report noted the caller said: your fedex parcel contains drugs and you are under digital arrest. The victim panicked.'
    assert extractor.extract_scam_text(text2) == "your fedex parcel contains drugs and you are under digital arrest"
    
    # Test record processing
    record = {
        "raw_content": text1,
        "source_type": "News Report",
        "source_title": "Fake Police Call Scam"
    }
    
    extracted = extractor.process_record(record)
    assert extracted["text"] == "You are under digital arrest for money laundering."
    assert extracted["scam_type"] == "Digital Arrest"
    assert extracted["risk_level"] == "Critical" # due to 'lakh'
    assert extracted["authority_impersonated"] == "Police" # from 'Fake Police Call Scam' title
    assert extracted["scenario"] == "Money Laundering"

def test_validator():
    validator = Validator()
    
    valid_record = {"source_url": "http://example.com/news/1", "text": "Scam message"}
    invalid_record = {"text": "Scam message"} # Missing URL
    
    assert validator.validate_record(valid_record)[0] == True
    assert validator.validate_record(invalid_record)[0] == False

def test_deduplicator():
    deduplicator = Deduplicator()
    
    records = [
        {"source_url": "http://example.com/article1", "text": "A"},
        {"source_url": "http://example.com/article1", "text": "B"}, # Duplicate URL
        {"source_url": "http://example.com/article2", "text": "A"}  # Duplicate Text
    ]
    
    unique = deduplicator.deduplicate(records)
    assert len(unique) == 1
    assert unique[0]["source_url"] == "http://example.com/article1"
    assert unique[0]["text"] == "A"
