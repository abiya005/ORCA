import pandas as pd
import numpy as np
import os
import pickle
import json
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

datasets_path = r"d:\ORCA\datasets\apk_scam"

print("Loading 475-column datasets...")
adware_df = pd.read_csv(os.path.join(datasets_path, "adware_apk_scams_15000.csv"))
benign_df = pd.read_csv(os.path.join(datasets_path, "benign_apk_scams_15000.csv"))
sms_df = pd.read_csv(os.path.join(datasets_path, "SMS_apk_scams_15000.csv"))

# Get feature columns (excluding non-feature metadata)
metadata_cols = ['sample_id', 'category', 'source', 'is_augmented', 'Class']
feature_columns = [col for col in adware_df.columns if col not in metadata_cols]

print(f"Number of feature columns: {len(feature_columns)}")

# Prepare X and y for the three datasets
X_475 = pd.concat([adware_df[feature_columns], benign_df[feature_columns], sms_df[feature_columns]], ignore_index=True)
y_475 = pd.concat([adware_df['Class'], benign_df['Class'], sms_df['Class']], ignore_index=True)

print(f"Initial shape of X: {X_475.shape}, y: {y_475.shape}")

print("Loading and mapping the banking dataset...")
banking_df = pd.read_csv(os.path.join(datasets_path, "banking_apk_scams_synthetic_15000.csv"))

# Define mapping function
def map_permissions_to_features(perms_str, has_anti_debug, has_anti_vm):
    feature_dict = {col: 0 for col in feature_columns}
    
    if pd.isna(perms_str):
        perms = []
    else:
        perms = [p.strip().lower() for p in perms_str.split(';') if p.strip()]
        
    # Map high-level categories
    # 1. SMS_SEND____
    if any('sms' in p or 'mms' in p for p in perms):
        feature_dict['SMS_SEND____'] = 1
        
    # 2. ACCESS_PERSONAL_INFO___
    personal_keywords = ['contact', 'account', 'profile', 'calendar', 'sms', 'phone', 'call', 'location', 'gps', 'camera', 'audio']
    if any(any(k in p for k in personal_keywords) for p in perms):
        feature_dict['ACCESS_PERSONAL_INFO___'] = 1
        
    # 3. ALTER_PHONE_STATE___
    phone_alter_keywords = ['modify_phone_state', 'call_phone', 'write_settings', 'write_secure_settings', 'system_alert_window', 'bind_accessibility_service', 'bind_device_admin']
    if any(any(k in p for k in phone_alter_keywords) for p in perms):
        feature_dict['ALTER_PHONE_STATE___'] = 1
        
    # 4. NETWORK_ACCESS____
    if any('internet' in p or 'network' in p or 'wifi' in p for p in perms):
        feature_dict['NETWORK_ACCESS____'] = 1
        
    # 5. DEVICE_ACCESS_____
    device_keywords = ['camera', 'record_audio', 'location', 'gps', 'bluetooth', 'nfc', 'vibrate']
    if any(any(k in p for k in device_keywords) for p in perms):
        feature_dict['DEVICE_ACCESS_____'] = 1
        
    # 6. ANTI_DEBUG_____
    if has_anti_debug or has_anti_vm:
        feature_dict['ANTI_DEBUG_____'] = 1
        
    # Match specific column names where possible
    for col in feature_columns:
        col_clean = col.lower().replace('_', '')
        for p in perms:
            p_clean = p.split('.')[-1].lower().replace('_', '')
            if col_clean == p_clean or p_clean in col_clean:
                feature_dict[col] = 1
                
    return feature_dict

# Extract mapping for banking dataset
banking_features_list = []
for idx, row in banking_df.iterrows():
    perms_str = row.get('all_permissions_list', '')
    has_anti_debug = row.get('has_anti_debug_code', 0) == 1 or row.get('has_anti_debug_code', False) is True
    has_anti_vm = row.get('has_anti_vm_code', 0) == 1 or row.get('has_anti_vm_code', False) is True
    feat_dict = map_permissions_to_features(perms_str, has_anti_debug, has_anti_vm)
    banking_features_list.append(feat_dict)

banking_features_df = pd.DataFrame(banking_features_list)
# Ensure columns order matches feature_columns
banking_features_df = banking_features_df[feature_columns]

# Class for Banking scam is 2 (adware=1, banking=2, sms=3, benign=5)
banking_y = pd.Series([2] * len(banking_features_df))

# Combine all datasets
X = pd.concat([X_475, banking_features_df], ignore_index=True)
y = pd.concat([y_475, banking_y], ignore_index=True)

print(f"Final combined shape: X: {X.shape}, y: {y.shape}")
print("Class counts:")
print(y.value_counts())

# Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print("Training Random Forest Classifier...")
clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
clf.fit(X_train, y_train)

# Evaluate model
y_pred = clf.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"\nModel Accuracy: {accuracy:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=["Adware (1)", "Banking (2)", "SMS Scam (3)", "Benign (5)"]))

# Save model and metadata
backend_dir = r"d:\ORCA\backend"
os.makedirs(backend_dir, exist_ok=True)

model_path = os.path.join(backend_dir, "apk_scam_model.pkl")
with open(model_path, "wb") as f:
    pickle.dump(clf, f)
print(f"Model saved to {model_path}")

features_path = os.path.join(backend_dir, "feature_columns.json")
with open(features_path, "w") as f:
    json.dump(feature_columns, f)
print(f"Feature columns saved to {features_path}")

print("Training script execution completed!")
