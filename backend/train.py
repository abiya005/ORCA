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
print(f"APK Model saved to {model_path}")

features_path = os.path.join(backend_dir, "feature_columns.json")
with open(features_path, "w") as f:
    json.dump(feature_columns, f)
print(f"Feature columns saved to {features_path}")

# ==============================================================================
# FAKE HR / RECRUITMENT SCAM MODEL TRAINING (NLP TF-IDF + CLASSIFIERS)
# ==============================================================================
print("\n=======================================================")
print("Training Fake HR Scam Detection ML Model...")
print("=======================================================")

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier

fake_hr_dir = r"d:\ORCA\datasets\fake_hr"
texts = []
labels = []       # Ingest Fake HR Scam Dataset files from datasets/fake_hr
scam_categories = ["email_scam", "linkedin_scam", "telegram_scam", "whatsapp_scam"]
platform_labels = []

# Add direct concise scam email samples to enrich email_scam dataset
direct_email_scams = [
    "Dear Candidate, you have been selected for remote data entry role. Pay $250 advance deposit for software equipment via Zelle or wire transfer.",
    "Urgent Remote Job Offer: Work From Home Software Associate - $45/hr. Pay advance deposit of $200 via Zelle to receive home office onboarding laptop package.",
    "Congratulations! You are selected for Data Entry Specialist role. Please submit $150 processing fee via Gift Card or Zelle wire transfer to receive equipment.",
    "Immediate Hiring: Remote Virtual Assistant $35 per hour. To finalize your employment contract, send $300 registration fee via CashApp or Crypto to our vendor.",
    "Job Offer Notice: Online Data Processing Associate $50/hr. Deposit $250 advance fee for training modules before starting work. Contact recruiter now."
]
for des in direct_email_scams:
    for _ in range(5):
        texts.append(des)
        labels.append(1)
        platform_labels.append("email_scam")

for cat in scam_categories:
    cat_folder = os.path.join(fake_hr_dir, cat)
    if os.path.exists(cat_folder):
        files = [f for f in os.listdir(cat_folder) if f.endswith(".txt")]
        print(f"Processing scam dataset '{cat}': found {len(files)} files.")
        for file in files:
            file_path = os.path.join(cat_folder, file)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 30]
                if not paragraphs:
                    paragraphs = [content.strip()]
                for para in paragraphs:
                    texts.append(para)
                    labels.append(1)
                    platform_labels.append(cat)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

# Ingest Benign / Legitimate HR dataset files from datasets/fake_hr/benign_hr
benign_hr_folder = os.path.join(fake_hr_dir, "benign_hr")
benign_texts_raw = []

if os.path.exists(benign_hr_folder):
    b_files = [f for f in os.listdir(benign_hr_folder) if f.endswith(".txt")]
    print(f"Processing benign dataset 'benign_hr': found {len(b_files)} files.")
    for b_file in b_files:
        b_path = os.path.join(benign_hr_folder, b_file)
        try:
            with open(b_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 30]
            if not paragraphs:
                paragraphs = [content.strip()]
            for para in paragraphs:
                benign_texts_raw.append(para)
        except Exception as e:
            print(f"Error reading benign file {b_path}: {e}")

# Add synthetic legitimate corporate & campus recruitment baseline samples
benign_samples = [
    "Campus Placement Opportunity with AvgVa Solutions for the position of Business Development Associate (BDA). Centre for Placements and Career Guidance Christ University. Eligible Batches: All Branches. Mode: Campus recruitment / interview process. Location: As per company requirements. Apply via Google Form link.",
    "Placement Office SOET Christ University Bengaluru. We are pleased to inform you about a Campus Placement Opportunity. Please submit your application before the deadline.",
    "We are seeking a talented Senior Software Engineer to join our engineering team at Google India. You will build scalable microservices using Python and Flask.",
    "Thank you for applying for the Data Analyst role at Microsoft. We reviewed your resume and would like to schedule a 30-minute initial phone screen with our HR representative.",
    "Responsibilities: Design, develop, and maintain secure RESTful APIs. Perform code reviews and write comprehensive automated unit tests.",
    "Our official hiring team will conduct all interviews via Google Meet or in-person at our corporate office. We never request upfront payments or bank details.",
    "Job Requirements: Bachelor's degree in Computer Science or related field, 3+ years experience with React and Node.js. Competitive salary and health benefits included.",
    "Dear Candidate, following up on your application submitted via LinkedIn. Please confirm your availability for a technical interview next Tuesday at 2 PM PST.",
    "Join our enterprise solutions team as a DevOps Specialist. Minimum 4 years experience with Kubernetes, Docker, and AWS Terraform deployments.",
    "Official Career Portal: All job vacancies and application updates are managed exclusively through our verified company portal at careers.microsoft.com.",
    "Position Overview: Product Manager for mobile applications. Lead cross-functional teams of engineers and product designers in agile sprint cycles.",
    "Candidate Invitation: Your background in cybersecurity aligns well with our open Information Security Analyst role. Let us know if you are open to discussing opportunities."
]
benign_texts_raw.extend(benign_samples)

# Match exact 1:1 count of scam samples for perfect dataset balance
target_scam_count = len(texts) # 168
repeated_benign = (benign_texts_raw * (target_scam_count // len(benign_texts_raw) + 1))[:target_scam_count]

for b_text in repeated_benign:
    texts.append(b_text)
    labels.append(0)
    platform_labels.append("benign")

scam_count = sum(labels)
benign_count = len(labels) - scam_count
print(f"Total Fake HR dataset samples: {len(texts)} (Scam: {scam_count}, Benign: {benign_count})")

# Fit TF-IDF Vectorizer & Random Forest Classifiers
vectorizer = TfidfVectorizer(max_features=5000, stop_words="english", ngram_range=(1, 2))
X_tfidf = vectorizer.fit_transform(texts)

scam_clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
scam_clf.fit(X_tfidf, labels)

platform_clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
platform_clf.fit(X_tfidf, platform_labels)

# Save combined model artifact
fake_hr_model_data = {
    'scam_model': scam_clf,
    'platform_model': platform_clf,
    'vectorizer': vectorizer,
    'feature_names': vectorizer.get_feature_names_out().tolist()
}

fake_hr_model_path = os.path.join(backend_dir, "fake_hr_model.pkl")
with open(fake_hr_model_path, "wb") as f:
    pickle.dump(fake_hr_model_data, f)
print(f"Fake HR NLP Model & Vectorizer saved to {fake_hr_model_path}")

# ==============================================================================
# DIGITAL ARREST SCAM MODEL TRAINING (NLP TF-IDF + CLASSIFIER)
# ==============================================================================
print("\n=======================================================")
print("Training Digital Arrest Threat ML Model...")
print("=======================================================")

da_dir = r"d:\ORCA\datasets\digital_arrest"
da_texts = []
da_labels = [] # 1 for Digital Arrest Scam, 0 for Legitimate Legal/Advisory

# Ingest Digital Arrest Threat Raw Data
raw_dir = os.path.join(da_dir, "data", "raw")
if os.path.exists(raw_dir):
    json_files = [f for f in os.listdir(raw_dir) if f.endswith(".json")]
    for jf in json_files:
        jpath = os.path.join(raw_dir, jf)
        try:
            with open(jpath, "r", encoding="utf-8", errors="ignore") as f:
                jdata = json.load(f)
            if isinstance(jdata, list):
                for item in jdata:
                    title = item.get('source_title', '') or item.get('title', '')
                    body = item.get('raw_content', '') or item.get('selftext', '') or item.get('body', '')
                    comb = f"{title} {body}".strip()
                    if len(comb) > 20:
                        da_texts.append(comb)
                        da_labels.append(1)
        except Exception as e:
            pass

# Ingest Benign Legal / Government Public Advisories
benign_legal_dir = os.path.join(da_dir, "benign_legal")
if os.path.exists(benign_legal_dir):
    bl_files = [f for f in os.listdir(benign_legal_dir) if f.endswith(".txt")]
    for bl_file in bl_files:
        bl_path = os.path.join(benign_legal_dir, bl_file)
        try:
            with open(bl_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            for _ in range(30):
                da_texts.append(content)
                da_labels.append(0)
        except Exception as e:
            pass

# Additional synthetic legal/advisory samples
legal_benign_samples = [
    "Ministry of Home Affairs Public Safety Advisory: Law enforcement agencies never arrest citizens digitally or demand money via video calls. Report cybercrime at cybercrime.gov.in or call 1930.",
    "Official High Court Civil Summons: You are hereby directed to appear in person or by advocate at the District Court on the designated hearing date.",
    "Police Station Information Notice: Official communication regarding ongoing investigation. Please visit the local police station during working hours with valid identification."
]
for lbs in legal_benign_samples:
    for _ in range(20):
        da_texts.append(lbs)
        da_labels.append(0)

print(f"Total Digital Arrest dataset samples: {len(da_texts)} (Scam: {sum(da_labels)}, Benign: {len(da_labels) - sum(da_labels)})")

da_vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=3000, stop_words='english')
X_da_tfidf = da_vectorizer.fit_transform(da_texts)

da_clf = LogisticRegression(random_state=42, max_iter=1000, class_weight='balanced')
da_clf.fit(X_da_tfidf, da_labels)

da_model_data = {
    'scam_model': da_clf,
    'vectorizer': da_vectorizer
}

da_model_path = os.path.join(backend_dir, "digital_arrest_model.pkl")
with open(da_model_path, "wb") as f:
    pickle.dump(da_model_data, f)
print(f"Digital Arrest ML Model saved to {da_model_path}")

print("\n=======================================================")
print("Training execution completed successfully for ALL models!")
print("=======================================================")


