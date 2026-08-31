"""Patch script: replace the ML inference block in app.py with pre-ML heuristic guard."""
import re

path = r"d:\ORCA\backend\app.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

OLD_BLOCK = '''    # 2. Run Machine Learning Inference
    threat_class = "Safe Utility App"
    score = "0%"
    badge = "SAFE"
    badge_class = "safe"
    
    if MODEL_TRAINED:
        # Construct feature vector
        feat_dict = map_permissions_to_features(permissions, methods_called, has_anti_debug)
        # Vectorize matching feature_columns
        feat_vec = [feat_dict.get(col, 0) for col in FEATURE_COLUMNS]
        
        # Predict
        pred_class = MODEL.predict([feat_vec])[0]
        probs = MODEL.predict_proba([feat_vec])[0]
        class_indices = list(MODEL.classes_)
        
        # Mapping class IDs (1=Adware, 2=Banking, 3=SMS, 5=Benign)
        # Calculate threat score
        benign_idx = class_indices.index(5) if 5 in class_indices else -1
        if benign_idx != -1:
            benign_prob = probs[benign_idx]
            threat_prob = 1.0 - benign_prob
            score = f"{int(threat_prob * 100)}%"
        else:
            score = "99%"
            
        if pred_class == 1:
            threat_class = "Adware / Spyware Trojan"
            badge = "MALICIOUS"
            badge_class = "malicious"
        elif pred_class == 2:
            threat_class = "Overlay Phishing / Banking Trojan"
            badge = "MALICIOUS"
            badge_class = "malicious"
        elif pred_class == 3:
            threat_class = "RAT / SMS Stealer Trojan"
            badge = "MALICIOUS"
            badge_class = "malicious"
        else:
            threat_class = "Safe Utility App"
            badge = "SAFE"
            badge_class = "safe"
            score = "0%"'''

NEW_BLOCK = '''    # 2. Run Machine Learning Inference
    threat_class = "Safe Utility App"
    score = "0%"
    badge = "SAFE"
    badge_class = "safe"

    # Pre-ML heuristic gate: apps with zero dangerous permissions AND no anti-debug
    # are definitively safe -- skip ML to avoid all-zero vector false positives
    DANGEROUS_PERM_KEYWORDS = [
        'receive_sms', 'send_sms', 'read_sms', 'system_alert_window',
        'bind_accessibility_service', 'bind_device_admin', 'read_phone_state',
        'read_contacts', 'write_external_storage', 'receive_boot_completed',
        'install_packages', 'process_outgoing_calls', 'read_call_log',
        'write_call_log', 'get_accounts', 'use_credentials',
    ]
    has_dangerous_perms = any(
        any(k in p.lower() for k in DANGEROUS_PERM_KEYWORDS)
        for p in permissions
    )

    if not has_dangerous_perms and not has_anti_debug:
        # Definitively safe - no suspicious permissions or evasion techniques
        threat_class = "Safe Utility App"
        badge = "SAFE"
        badge_class = "safe"
        score = "0%"
    elif MODEL_TRAINED:
        # Construct feature vector and run ML classification
        feat_dict = map_permissions_to_features(permissions, methods_called, has_anti_debug)
        feat_vec = [feat_dict.get(col, 0) for col in FEATURE_COLUMNS]

        pred_class = MODEL.predict([feat_vec])[0]
        probs = MODEL.predict_proba([feat_vec])[0]
        class_indices = list(MODEL.classes_)

        # Calculate threat score (1 - benign probability)
        benign_idx = class_indices.index(5) if 5 in class_indices else -1
        if benign_idx != -1:
            benign_prob = probs[benign_idx]
            threat_prob = 1.0 - benign_prob
            score = f"{int(threat_prob * 100)}%"
        else:
            score = "99%"

        if pred_class == 1:
            threat_class = "Adware / Spyware Trojan"
            badge = "MALICIOUS"
            badge_class = "malicious"
        elif pred_class == 2:
            threat_class = "Overlay Phishing / Banking Trojan"
            badge = "MALICIOUS"
            badge_class = "malicious"
        elif pred_class == 3:
            threat_class = "RAT / SMS Stealer Trojan"
            badge = "MALICIOUS"
            badge_class = "malicious"
        else:
            threat_class = "Safe Utility App"
            badge = "SAFE"
            badge_class = "safe"
            score = "0%"'''

if OLD_BLOCK in content:
    content = content.replace(OLD_BLOCK, NEW_BLOCK, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Patch applied successfully.")
else:
    print("ERROR: Could not find target block. No changes made.")
    # Show first 100 chars around the expected location
    idx = content.find("# 2. Run Machine Learning")
    print(f"Found marker at index {idx}")
    print(repr(content[idx:idx+200]))
