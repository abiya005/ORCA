import logging

class Validator:
    def __init__(self):
        pass

    def validate_record(self, record):
        """Validates a candidate record to ensure it meets minimum criteria."""
        if not record.get("source_url"):
            return False, "Missing source URL"
            
        # Ensure we are not passing completely empty/irrelevant scenarios if required,
        # but the main thing is that we do not fabricate 'text'.
        # If 'text' is present, we trust the extractor for now but mark for review.
        
        return True, "Valid Candidate"

    def validate(self, extracted_records):
        logging.info("Starting validation phase...")
        validated_candidates = []
        for r in extracted_records:
            is_valid, reason = self.validate_record(r)
            if is_valid:
                r["verified"] = 0
                r["needs_human_review"] = 1
                validated_candidates.append(r)
            else:
                logging.debug(f"Rejected record from {r.get('source_url')} reason: {reason}")
                
        logging.info(f"Validated {len(validated_candidates)} candidate records.")
        return validated_candidates
