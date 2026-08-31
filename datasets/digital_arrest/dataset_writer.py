import pandas as pd
import logging
import os
import config

class DatasetWriter:
    def __init__(self):
        self.columns = [
            "id", "text", "incident_description", "label", "scam_type", "scenario", "source", 
            "language", "risk_level", "authority_impersonated", 
            "communication_channel", "source_url", "source_name", 
            "source_publication_date", "collection_timestamp", 
            "source_country", "verified", "needs_human_review"
        ]

    def write_candidates(self, candidates):
        if not candidates:
            logging.info("No candidates to write.")
            return

        df = pd.DataFrame(candidates)
        # Ensure all columns exist
        for col in self.columns:
            if col not in df.columns:
                df[col] = None
        
        # Add IDs if not present
        if 'id' not in df.columns or df['id'].isnull().all():
            df['id'] = range(1, len(df) + 1)
            
        # Reorder columns
        df = df[self.columns]
        
        # Append or write new
        os.makedirs(os.path.dirname(config.CANDIDATES_CSV), exist_ok=True)
        if os.path.exists(config.CANDIDATES_CSV):
            existing_df = pd.read_csv(config.CANDIDATES_CSV)
            # Make sure we don't duplicate existing candidates (simple URL check)
            existing_urls = set(existing_df['source_url'].dropna())
            new_df = df[~df['source_url'].isin(existing_urls)]
            
            # Start new IDs where old left off
            if not new_df.empty:
                max_id = existing_df['id'].max() if not existing_df.empty else 0
                new_df['id'] = range(int(max_id) + 1, int(max_id) + 1 + len(new_df))
                
            combined = pd.concat([existing_df, new_df], ignore_index=True)
            combined.to_csv(config.CANDIDATES_CSV, index=False)
            logging.info(f"Appended {len(new_df)} new candidates to {config.CANDIDATES_CSV}")
        else:
            df.to_csv(config.CANDIDATES_CSV, index=False)
            logging.info(f"Wrote {len(df)} candidates to {config.CANDIDATES_CSV}")

    def curate_dataset(self):
        """Reads candidates.csv, extracts verified=1 rows, and saves to final dataset."""
        if not os.path.exists(config.CANDIDATES_CSV):
            logging.warning("No candidates.csv found to curate.")
            return

        df = pd.read_csv(config.CANDIDATES_CSV)
        verified_df = df[df['verified'] == 1].copy()
        
        if verified_df.empty:
            logging.info("No verified records found in candidates.csv.")
            return
            
        # Final dataset format might drop 'verified' and 'needs_human_review'
        final_cols = [c for c in self.columns if c not in ['verified', 'needs_human_review']]
        verified_df = verified_df[final_cols]
        
        verified_df.to_csv(config.FINAL_DATASET_CSV, index=False)
        logging.info(f"Curated {len(verified_df)} records into {config.FINAL_DATASET_CSV}")

