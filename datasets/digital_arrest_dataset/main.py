import argparse
import logging
import sys
import json
import os
import config

from collector import Collector
from classifier import Classifier
from extractor import Extractor
from validator import Validator
from deduplicator import Deduplicator
from dataset_writer import DatasetWriter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def print_stats(stats):
    print("\n" + "="*50)
    print("DATASET STATISTICS")
    print("="*50)
    for key, val in stats.items():
        print(f"{key}: {val}")
    print("="*50 + "\n")

    os.makedirs(os.path.dirname(config.STATS_FILE), exist_ok=True)
    with open(config.STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Digital Arrest Scams Dataset Pipeline")
    parser.add_argument("command", choices=["collect", "extract", "validate", "curate", "pipeline"],
                        help="Command to run")

    args = parser.parse_args()
    
    stats = {
        "Total sources queried": 0,
        "Total documents collected": 0,
        "Digital Arrest documents": 0,
        "Duplicates removed": 0,
        "Candidates requiring review": 0,
        "Verified records": 0,
        "Candidates with real text": 0,
        "Candidates without text": 0,
    }

    if args.command in ["collect", "pipeline"]:
        collector = Collector()
        raw_data = collector.collect()
        stats["Total documents collected"] = len(raw_data)
        
        # Save raw data path for next steps if running sequentially
        with open(os.path.join(config.RAW_DATA_DIR, "latest.json"), 'w') as f:
            json.dump(raw_data, f)
            
        if args.command == "collect":
            print_stats(stats)
            return

    if args.command in ["extract", "pipeline"]:
        try:
            with open(os.path.join(config.RAW_DATA_DIR, "latest.json"), 'r') as f:
                raw_data = json.load(f)
        except FileNotFoundError:
            logging.error("No raw data found. Run 'collect' first.")
            sys.exit(1)
            
        classifier = Classifier()
        filtered_data = classifier.filter_records(raw_data)
        stats["Digital Arrest documents"] = len(filtered_data)
        
        extractor = Extractor()
        extracted_data = extractor.extract(filtered_data)
        
        with open(os.path.join(config.RAW_DATA_DIR, "extracted.json"), 'w') as f:
            json.dump(extracted_data, f)
            
        if args.command == "extract":
            print_stats(stats)
            return

    if args.command in ["validate", "pipeline"]:
        try:
            with open(os.path.join(config.RAW_DATA_DIR, "extracted.json"), 'r') as f:
                extracted_data = json.load(f)
        except FileNotFoundError:
            logging.error("No extracted data found. Run 'extract' first.")
            sys.exit(1)
            
        deduplicator = Deduplicator()
        unique_data = deduplicator.deduplicate(extracted_data)
        stats["Duplicates removed"] = len(extracted_data) - len(unique_data)
        
        validator = Validator()
        validated_candidates = validator.validate(unique_data)
        
        writer = DatasetWriter()
        writer.write_candidates(validated_candidates)
        
        stats["Candidates requiring review"] = len(validated_candidates)
        stats["Candidates with real text"] = sum(1 for c in validated_candidates if c.get("text"))
        stats["Candidates without text"] = sum(1 for c in validated_candidates if not c.get("text"))
        
        if args.command == "validate":
            print_stats(stats)
            return

    if args.command in ["curate", "pipeline"]:
        writer = DatasetWriter()
        writer.curate_dataset()
        print_stats(stats) # Curate stats would need a read back from the DB ideally, but keeping simple here.

if __name__ == "__main__":
    main()
