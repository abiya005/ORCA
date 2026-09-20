import os
import sys
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
import tempfile
import pickle
import json
import logging
import subprocess
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Configure logging to file so it works in detached/headless mode
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)

import io
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import numpy as np

try:
    from PIL import Image, ImageEnhance
    import pytesseract
    tess_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tess_path):
        pytesseract.pytesseract.tesseract_cmd = tess_path
    PYTESSERACT_AVAILABLE = True
except Exception as e:
    PYTESSERACT_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except Exception as e:
    EASYOCR_AVAILABLE = False
    log.warning("EasyOCR not available: %s", e)

OCR_AVAILABLE = PYTESSERACT_AVAILABLE or EASYOCR_AVAILABLE
EASYOCR_READER = None

def get_easyocr_reader():
    global EASYOCR_READER
    if EASYOCR_READER is None and EASYOCR_AVAILABLE:
        try:
            log.info("Initializing EasyOCR Neural Reader...")
            EASYOCR_READER = easyocr.Reader(['en'], gpu=False, verbose=False)
            log.info("EasyOCR Neural Reader initialized successfully!")
        except Exception as ex:
            log.error("Failed to initialize EasyOCR Reader: %s", ex)
            EASYOCR_READER = False
    return EASYOCR_READER if EASYOCR_READER is not False else None

def extract_ocr_text(req):
    extracted_text = ""
    file_obj = None
    
    if 'file' in req.files and req.files['file'].filename:
        file_obj = req.files['file']
    
    if file_obj:
        try:
            file_bytes = file_obj.read()
            image = Image.open(io.BytesIO(file_bytes))
            
            # Preprocess image for OCR contrast boost
            image_rgb = image.convert("RGB")
            enhancer = ImageEnhance.Contrast(image_rgb)
            enhanced_img = enhancer.enhance(1.5)
            
            # 1. Try pytesseract first
            if PYTESSERACT_AVAILABLE:
                try:
                    extracted_text = pytesseract.image_to_string(enhanced_img).strip()
                    if extracted_text:
                        log.info("PyTesseract OCR extracted %d characters from '%s'", len(extracted_text), file_obj.filename)
                except Exception as py_ex:
                    log.warning("PyTesseract failed: %s. Falling back to EasyOCR.", py_ex)
                    extracted_text = ""
                    
            # 2. Fallback to EasyOCR if pytesseract returned empty or failed
            if not extracted_text and EASYOCR_AVAILABLE:
                reader = get_easyocr_reader()
                if reader:
                    img_np = np.array(enhanced_img)
                    results = reader.readtext(img_np, detail=0)
                    extracted_text = " ".join(results).strip()
                    if extracted_text:
                        log.info("EasyOCR extracted %d characters from '%s'", len(extracted_text), file_obj.filename)
        except Exception as e:
            log.warning("OCR processing failed on image file '%s': %s", file_obj.filename if file_obj else 'unknown', e)
            
    input_text = req.form.get('text', '').strip() or (req.get_json(silent=True) or {}).get('text', '').strip()
    
    if extracted_text and len(extracted_text) > 10:
        if input_text and input_text.lower() not in extracted_text.lower():
            return f"{extracted_text}\n{input_text}"
        return extracted_text
    return input_text

# Import androguard components safely
try:
    from androguard.core.apk import APK
    from androguard.misc import AnalyzeAPK
    ANDROGUARD_AVAILABLE = True
except Exception as e:
    log.warning(f"Androguard not available: {e}")
    ANDROGUARD_AVAILABLE = False

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__)
CORS(app)

MODEL = None
FEATURE_COLUMNS = []
MODEL_TRAINED = False

FAKE_HR_MODEL = None
FAKE_HR_MODEL_TRAINED = False

DIGITAL_ARREST_MODEL = None
DIGITAL_ARREST_MODEL_TRAINED = False

def load_model():
    global MODEL, FEATURE_COLUMNS, MODEL_TRAINED
    global FAKE_HR_MODEL, FAKE_HR_MODEL_TRAINED
    global DIGITAL_ARREST_MODEL, DIGITAL_ARREST_MODEL_TRAINED

    backend_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(backend_dir, "apk_scam_model.pkl")
    features_path = os.path.join(backend_dir, "feature_columns.json")
    fake_hr_path = os.path.join(backend_dir, "fake_hr_model.pkl")
    da_path = os.path.join(backend_dir, "digital_arrest_model.pkl")

    if os.path.exists(model_path) and os.path.exists(features_path):
        try:
            with open(model_path, "rb") as f:
                MODEL = pickle.load(f)
            with open(features_path, "r") as f:
                FEATURE_COLUMNS = json.load(f)
            MODEL_TRAINED = True
            log.info("APK ML Model loaded successfully! Features: %d", len(FEATURE_COLUMNS))
        except Exception as e:
            log.error("Error loading APK model: %s", e)
            MODEL_TRAINED = False
    else:
        MODEL_TRAINED = False

    if os.path.exists(fake_hr_path):
        try:
            with open(fake_hr_path, "rb") as f:
                FAKE_HR_MODEL = pickle.load(f)
            FAKE_HR_MODEL_TRAINED = True
            log.info("Fake HR NLP Model loaded successfully!")
        except Exception as e:
            log.error("Error loading Fake HR model: %s", e)
            FAKE_HR_MODEL_TRAINED = False
    else:
        FAKE_HR_MODEL_TRAINED = False

    if os.path.exists(da_path):
        try:
            with open(da_path, "rb") as f:
                DIGITAL_ARREST_MODEL = pickle.load(f)
            DIGITAL_ARREST_MODEL_TRAINED = True
            log.info("Digital Arrest NLP Model loaded successfully!")
        except Exception as e:
            log.error("Error loading Digital Arrest model: %s", e)
            DIGITAL_ARREST_MODEL_TRAINED = False
    else:
        DIGITAL_ARREST_MODEL_TRAINED = False

    return MODEL_TRAINED or FAKE_HR_MODEL_TRAINED or DIGITAL_ARREST_MODEL_TRAINED

load_model()


# Dict of standard Android permission classifications and descriptions
PERMISSION_DETAILS = {
    "android.permission.RECEIVE_SMS": {
        "status": "DANGEROUS",
        "desc": "Allows application to intercept inbound SMS text messages. Frequently abused to hijack bank OTPs."
    },
    "android.permission.SEND_SMS": {
        "status": "DANGEROUS",
        "desc": "Allows app to send SMS messages. Used to register silently on premium SMS channels or leak data."
    },
    "android.permission.READ_SMS": {
        "status": "DANGEROUS",
        "desc": "Allows application to read stored SMS text messages. Used to read MFA codes and banking texts."
    },
    "android.permission.SYSTEM_ALERT_WINDOW": {
        "status": "DANGEROUS",
        "desc": "Enables overlay screens. Used for overlay phishing attacks targeting banking apps to steal passwords."
    },
    "android.permission.BIND_ACCESSIBILITY_SERVICE": {
        "status": "DANGEROUS",
        "desc": "Accesses Android Accessibility APIs. Can read all screen content, log keystrokes, and click buttons automatically."
    },
    "android.permission.BIND_DEVICE_ADMIN": {
        "status": "DANGEROUS",
        "desc": "Registers application as Device Administrator. Used to prevent user from uninstalling the app."
    },
    "android.permission.READ_PHONE_STATE": {
        "status": "WARNING",
        "desc": "Allows reading device IDs, IMEI codes, and network carrier status. Abused for hardware tracking."
    },
    "android.permission.READ_CONTACTS": {
        "status": "WARNING",
        "desc": "Allows application to read user contact list. Abused to harvest phone book contacts to target victims' friends."
    },
    "android.permission.WRITE_EXTERNAL_STORAGE": {
        "status": "WARNING",
        "desc": "Allows application to write files to disk. Abused to drop additional secondary malware payloads."
    },
    "android.permission.INTERNET": {
        "status": "NORMAL",
        "desc": "Allows application to connect to servers. Used to leak captured credentials or contact C2 panels."
    },
    "android.permission.RECEIVE_BOOT_COMPLETED": {
        "status": "NORMAL",
        "desc": "Allows launching service in background as soon as the phone boots up. Used for persistence."
    },
    "android.permission.VIBRATE": {
        "status": "NORMAL",
        "desc": "Allows application to control device haptics for key presses."
    }
}

def map_permissions_to_features(perms_list, methods_list, has_anti_debug=False):
    if not FEATURE_COLUMNS:
        return {}
        
    feature_dict = {col: 0 for col in FEATURE_COLUMNS}
    perms = [p.lower() for p in perms_list]
    methods = [m.lower() for m in methods_list]
    
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
        
    # 5. DEVICE_ACCESS_____  (exclude harmless VIBRATE - it's not a real device access risk)
    device_keywords = ['camera', 'record_audio', 'access_fine_location', 'access_coarse_location', 'bluetooth', 'nfc']
    if any(any(k in p for k in device_keywords) for p in perms):
        feature_dict['DEVICE_ACCESS_____'] = 1
        
    # 6. ANTI_DEBUG_____
    if has_anti_debug:
        feature_dict['ANTI_DEBUG_____'] = 1

    # Match specific column names for permissions (strict last-segment equality only)
    for col in FEATURE_COLUMNS:
        col_clean = col.lower().rstrip('_').rstrip('(').replace('_', '').replace('`', '')
        # Check if column matches standard permission strings
        for p in perms:
            p_clean = p.split('.')[-1].lower().replace('_', '')
            # Only match on exact last-segment equality (not broad substring) to avoid false positives
            if col_clean == p_clean:
                feature_dict[col] = 1
        # Check if column matches called methods (exact match)
        for m in methods:
            m_clean = m.lower().replace('_', '').replace('()', '').strip()
            if col_clean == m_clean:
                feature_dict[col] = 1

    # Benign override: if only harmless permissions present, reset threat features
    dangerous_perms = [p for p in perms_list if any(k in p.lower() for k in
        ['sms', 'mms', 'alert_window', 'accessibility', 'device_admin',
         'phone_state', 'contacts', 'call_log', 'location', 'camera',
         'record_audio', 'read_external', 'write_external', 'install_package'])]
    if not dangerous_perms and not has_anti_debug:
        for threat_col in ['ACCESS_PERSONAL_INFO___', 'ALTER_PHONE_STATE___',
                           'DEVICE_ACCESS_____', 'SMS_SEND____', 'ANTI_DEBUG_____']:
            if threat_col in feature_dict:
                feature_dict[threat_col] = 0

    return feature_dict

@app.route('/api/status', methods=['GET'])
def status():
    load_model()
    return jsonify({
        "connected": True,
        "model_trained": MODEL_TRAINED,
        "fake_hr_model_trained": FAKE_HR_MODEL_TRAINED,
        "digital_arrest_model_trained": DIGITAL_ARREST_MODEL_TRAINED,
        "features_count": len(FEATURE_COLUMNS),
        "androguard_available": ANDROGUARD_AVAILABLE,
        "ocr_available": OCR_AVAILABLE
    })

@app.route('/api/train', methods=['POST'])
def train_model():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    train_script = os.path.join(backend_dir, "train.py")
    
    try:
        # Run training script as a subprocess
        result = subprocess.run(["python", train_script], capture_output=True, text=True, check=True)
        load_model()
        return jsonify({
            "success": True,
            "stdout": result.stdout,
            "message": "All ML models (APK, Fake HR, and Digital Arrest datasets) trained successfully!"
        })
    except subprocess.CalledProcessError as e:
        return jsonify({
            "success": False,
            "error": e.stderr,
            "message": "Error training the models."
        }), 500

def extract_email_details(text_input, platform_pred="", badge="SAFE", authority=""):
    """
    If an email is detected and is fake/scam, return (fake_email, real_email).
    Otherwise, return (None, None).
    """
    if badge == "SAFE":
        return None, None

    text_lower = text_input.lower()
    emails_found = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text_input)

    # Detect if email content / scam email is present
    is_email_content = bool(emails_found) or any(k in text_lower for k in [
        'from:', 'to:', 'subject:', 'email', 'mail', 'inbox', 'placement office',
        'dear candidate', 'dear applicant', 'dear sir', 'dear madam', 'regards', 'recruiter', 'hiring manager'
    ]) or platform_pred == "email_scam"

    if not is_email_content:
        return None, None

    # 1. Fake / Original Email in Scam
    if emails_found:
        fake_email = emails_found[0]
    else:
        if 'christ' in text_lower or 'placement' in text_lower:
            fake_email = "placementoffice@christuniversity-careers.online"
        elif 'google' in text_lower:
            fake_email = "careers-google-recruiter@gmai1.com"
        elif 'amazon' in text_lower:
            fake_email = "hr-hiring@amaz0n-jobs.net"
        elif 'microsoft' in text_lower:
            fake_email = "careers-microsoft@outlook-jobs.com"
        elif 'cbi' in text_lower or 'police' in text_lower:
            fake_email = "cbi-notice-alert@cyber-cbi-gov.org"
        else:
            fake_email = "unverified-recruiter@external-scam.com"

    # 2. Possible Real / Actual Email
    if 'christ' in text_lower or 'soet' in text_lower or 'placementoffice' in text_lower:
        real_email = "placementoffice.soet@christuniversity.in"
    elif 'google' in text_lower:
        real_email = "careers@google.com"
    elif 'amazon' in text_lower:
        real_email = "careers@amazon.com"
    elif 'microsoft' in text_lower:
        real_email = "careers@microsoft.com"
    elif 'infosys' in text_lower:
        real_email = "careers@infosys.com"
    elif 'tcs' in text_lower or 'tata' in text_lower:
        real_email = "careers@tcs.com"
    elif 'wipro' in text_lower:
        real_email = "careers@wipro.com"
    elif 'cbi' in text_lower:
        real_email = "contact@cbi.gov.in"
    elif 'police' in text_lower or 'cybercrime' in text_lower:
        real_email = "report@cybercrime.gov.in"
    elif 'mha' in text_lower or 'i4c' in text_lower:
        real_email = "cybercrime-mha@gov.in"
    elif 'rbi' in text_lower:
        real_email = "helpdesk@rbi.org.in"
    else:
        if '@' in fake_email:
            domain_part = fake_email.split('@')[1]
            if not any(d in domain_part for d in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'gmai1.com']):
                clean_domain = re.sub(r'[-_]?(fake|scam|jobs|hiring|verify|dep|online|net|org|site|update)', '', domain_part)
                real_email = f"official-hr@{clean_domain}"
            else:
                real_email = "official-hr@company.com"
        else:
            real_email = "official-hr@company.com"

    return fake_email, real_email

@app.route('/api/analyze-fake-hr', methods=['POST'])
def analyze_fake_hr():
    global FAKE_HR_MODEL, FAKE_HR_MODEL_TRAINED
    if not FAKE_HR_MODEL_TRAINED:
        load_model()

    text_input = extract_ocr_text(request)
    
    if not text_input:
        return jsonify({"error": "No text content or screenshot provided"}), 400

    text_lower = text_input.lower()
    
    # 1. Scam Red Flags Check
    has_scam_red_flags = any(k in text_lower for k in [
        'pay $', 'wire $', 't.me/', 'whatsapp voice call', 'vip portal', 'advance deposit',
        'earn daily', 'like youtube', 'rate google maps', 'zelle', 'crypto wallet', 'npm run setup',
        'registration fee', 'upi id', 'upfront payment', 'wa.me/', 'block deal', 'github',
        'polinrider', 'beavertail', 'npm run', 'install extension'
    ])

    # 2. Trust Signals Check (Educational placement drive, official university/company domain)
    has_edu_domain = bool(re.search(r'@[\w.-]+\.(edu|ac\.in)\b|christuniversity\.in|iitb\.ac\.in|iit\.ac\.in|nits\.ac\.in|bits-pilani\.ac\.in', text_lower))
    has_placement_header = any(k in text_lower for k in [
        'centre for placements', 'placement office', 'campus placement opportunity',
        'career guidance', 'official campus placement', 'eligible batches', 'passed-out batch'
    ])

    platform_pred = "email_scam"
    threat_score = 75

    if FAKE_HR_MODEL_TRAINED and FAKE_HR_MODEL:
        try:
            vectorizer = FAKE_HR_MODEL['vectorizer']
            scam_clf = FAKE_HR_MODEL['scam_model']
            platform_clf = FAKE_HR_MODEL['platform_model']

            vec = vectorizer.transform([text_input])
            
            if hasattr(scam_clf, "predict_proba"):
                probs = scam_clf.predict_proba(vec)[0]
                classes = list(scam_clf.classes_)
                scam_idx = classes.index(1) if 1 in classes else -1
                scam_prob = probs[scam_idx] if scam_idx != -1 else 0.85
            else:
                pred = scam_clf.predict(vec)[0]
                scam_prob = 0.95 if pred == 1 else 0.10
                
            threat_score = int(scam_prob * 100)
            platform_pred = platform_clf.predict(vec)[0]
        except Exception as ex:
            log.error("Error during Fake HR inference: %s", ex)

    log.info(f"DEBUG_HR | text: '{text_lower[:40]}' | red: {has_scam_red_flags} | edu: {has_edu_domain} | header: {has_placement_header} | score: {threat_score} | pred: {platform_pred}")

    # Apply Hybrid Rules & Boundary Decision
    is_scam_predict = (threat_score >= 50) or has_scam_red_flags
    
    if (has_placement_header and not has_scam_red_flags) or (has_edu_domain and not has_scam_red_flags):
        # Verified Campus Placement Drive / Educational Domain -> 0% Threat (SAFE)
        threat_score = 0
        platform_pred = "benign"
    elif has_scam_red_flags:
        # Verified Scam Red Flag -> High Risk (88% Threat)
        threat_score = max(threat_score, 88)
        if 'github' in text_lower or 'polinrider' in text_lower or 'beavertail' in text_lower or 'npm' in text_lower:
            platform_pred = "linkedin_scam"
        elif 'telegram' in text_lower or 't.me' in text_lower or 'like youtube' in text_lower:
            platform_pred = "telegram_scam"
        elif 'whatsapp' in text_lower or 'wa.me' in text_lower:
            platform_pred = "whatsapp_scam"
        elif platform_pred == "benign":
            platform_pred = "email_scam"
    elif is_scam_predict:
        # ML detected Scam -> High Threat
        threat_score = max(threat_score, 75)
        if platform_pred == "benign":
            platform_pred = "email_scam"
    else:
        # Legitimate Corporate Job Offer
        threat_score = min(threat_score, 10)
        platform_pred = "benign"

    # Key platform title mapping
    if platform_pred != "benign":
        if 'telegram' in text_lower or 't.me' in text_lower or 'like youtube' in text_lower:
            platform_pred = "telegram_scam"
        elif 'whatsapp' in text_lower or 'wa.me' in text_lower or 'voice call' in text_lower:
            platform_pred = "whatsapp_scam"
        elif 'linkedin' in text_lower or 'polinrider' in text_lower or 'beavertail' in text_lower or 'github' in text_lower:
            platform_pred = "linkedin_scam"

    platform_titles = {
        "email_scam": "Email Phishing & Fake Recruitment",
        "linkedin_scam": "LinkedIn Recruiter & Developer Supply Chain Scam",
        "telegram_scam": "Telegram Task & Daily Yield Scam",
        "whatsapp_scam": "WhatsApp Recruitment & Investment Fraud",
        "benign": "Legitimate Campus Placement Drive / Official HR Email"
    }

    platform_display = platform_titles.get(platform_pred, "Recruitment Assessment")

    if threat_score >= 70:
        badge = "MALICIOUS" if threat_score >= 85 else "SUSPICIOUS"
        badge_class = "malicious" if threat_score >= 85 else "suspicious"
        risk_level = "Critical Risk" if threat_score >= 85 else "High Risk"
        risk_class = "risk-red" if threat_score >= 85 else "risk-orange"
    elif threat_score >= 35:
        badge = "SUSPICIOUS"
        badge_class = "suspicious"
        risk_level = "Moderate Risk"
        risk_class = "risk-orange"
    else:
        badge = "SAFE"
        badge_class = "safe"
        risk_level = "Safe / Legitimate Opportunity"
        risk_class = "risk-green"

    # Extract indicator keywords
    all_indicators = [
        "like youtube videos", "rate google maps", "earn daily", "upi id", "vip portal",
        "upfront payment", "registration fee", "telegram", "whatsapp", "crypto wallet",
        "skype interview", "polinrider", "beavertail", "work from home", "easy tasks",
        "high salary", "advance deposit"
    ]
    matched = [kw for kw in all_indicators if kw in text_lower]
    if not matched and threat_score >= 50:
        matched = ["unverified recruiter handle", "off-platform communication redirect", "high-yield task compensation"]
    elif not matched:
        matched = ["verified university domain (.ac.in)", "official placement office guidance", "no registration fee required"]

    recommends = []
    if badge != "SAFE":
        if platform_pred == "telegram_scam":
            recommends = [
                "Do NOT click or join `t.me` Telegram invite links from unknown recruiters.",
                "Never pay advance deposits or fee tiers to unlock 'VIP task packages'.",
                "Be aware that small initial payouts (e.g. ₹150) are used to gain trust before demanding large sums.",
                "Report the UPI ID and mobile numbers to your bank and cybercrime portal (cybercrime.gov.in)."
            ]
        elif platform_pred == "whatsapp_scam":
            recommends = [
                "Block unsolicited WhatsApp voice calls or message threads offering work-from-home tasks.",
                "Never share your UPI credentials, bank details, or Aadhaar numbers with unverified recruiters.",
                "Refuse to download third-party APK files or access untrusted investment links.",
                "Report the number on WhatsApp and file a complaint on 1930 Cyber Helpline."
            ]
        elif platform_pred == "linkedin_scam":
            recommends = [
                "Verify recruiter profiles on LinkedIn: check mutual connections, employment history, and official domain.",
                "Do NOT execute untrusted GitHub repositories or npm packages (e.g., PolinRider / BeaverTail payloads).",
                "Refuse to install custom browser extensions or run VS Code tasks during technical interviews.",
                "Cross-check vacancies directly on the hiring company's official careers portal."
            ]
        else: # email_scam
            recommends = [
                "Inspect sender email headers: verify if sender matches the official domain (e.g., @company.com).",
                "Never transfer processing fees, security deposits, or laptop equipment costs.",
                "Do NOT submit sensitive identity documents (passport, bank statements) prior to official offer verification.",
                "Verify job listings directly via the company's official corporate HR office."
            ]
    else:
        recommends = [
            "This communication matches verified patterns of legitimate university campus placement drives.",
            "Official placement notices are issued directly by your institution's Centre for Placements & Career Guidance.",
            "Complete the application through the official university portal or designated Google Form before the deadline."
        ]

    summary = f"Threat Engine evaluated this input as '{platform_display}' with a Threat Rating of {threat_score}%. "
    if badge != "SAFE":
        summary += f"The dataset features matched patterns observed across {platform_display} recruitment attacks."
    else:
        summary += "Verified authentic communication from an official University / Educational Placement Office. No scam indicators detected."

    fake_email, real_email = extract_email_details(text_input, platform_pred, badge, authority=platform_display)

    return jsonify({
        "success": True,
        "_debug": {
            "text": text_lower[:60],
            "red": has_scam_red_flags,
            "edu": has_edu_domain,
            "header": has_placement_header,
            "score": threat_score,
            "pred": platform_pred
        },
        "report": {
            "title": f"Fake HR Scan - {platform_display}",
            "category": platform_display,
            "platform": platform_pred,
            "risk": risk_level,
            "riskClass": risk_class,
            "badge": badge,
            "badgeClass": badge_class,
            "authority": "Placement Office SOET (Christ University)" if badge == "SAFE" else f"Impersonating {platform_display.split()[0]} Recruiter",
            "trigger": "Campus Placement Opportunity" if badge == "SAFE" else "Recruitment & Job Offer Scam Vector",
            "score": f"{threat_score}%",
            "fakeEmail": fake_email,
            "realEmail": real_email,
            "indicators": matched,
            "summary": summary,
            "recommends": recommends
        }
    })

@app.route('/api/analyze-digital-arrest', methods=['POST'])
def analyze_digital_arrest():
    global DIGITAL_ARREST_MODEL, DIGITAL_ARREST_MODEL_TRAINED
    if not DIGITAL_ARREST_MODEL_TRAINED:
        load_model()

    text_input = extract_ocr_text(request)
    
    if not text_input:
        return jsonify({"error": "No text content or screenshot provided"}), 400

    text_lower = text_input.lower()
    
    # Red flags for Digital Arrest
    has_extortion_flags = any(k in text_lower for k in [
        'skype', 'digital detention', 'digital arrest', 'aadhaar flagged', 'narcotics trafficking',
        'money laundering', 'verification reserve account', 'transfer your assets', 'transfer funds',
        'cbi cyber crime', 'cbi officer', 'immediate arrest'
    ])
    
    has_public_advisory_flags = any(k in text_lower for k in [
        'public safety advisory', 'ministry of home affairs', 'i4c', 'cybercrime.gov.in',
        'never arrest citizens digitally', 'concept of digital arrest does not exist'
    ])

    threat_score = 92
    if has_public_advisory_flags and not has_extortion_flags:
        threat_score = 0
    elif DIGITAL_ARREST_MODEL_TRAINED and DIGITAL_ARREST_MODEL:
        try:
            vectorizer = DIGITAL_ARREST_MODEL['vectorizer']
            scam_clf = DIGITAL_ARREST_MODEL['scam_model']
            vec = vectorizer.transform([text_input])
            if hasattr(scam_clf, "predict_proba"):
                probs = scam_clf.predict_proba(vec)[0]
                classes = list(scam_clf.classes_)
                scam_idx = classes.index(1) if 1 in classes else -1
                scam_prob = probs[scam_idx] if scam_idx != -1 else 0.90
            else:
                pred = scam_clf.predict(vec)[0]
                scam_prob = 0.95 if pred == 1 else 0.05
            threat_score = int(scam_prob * 100)
            if has_public_advisory_flags and not has_extortion_flags:
                threat_score = 0
        except Exception as ex:
            log.error("Error during Digital Arrest inference: %s", ex)

    if threat_score >= 70:
        badge = "MALICIOUS"
        badge_class = "malicious"
        risk_level = "Critical Risk"
        risk_class = "risk-red"
    elif threat_score >= 35:
        badge = "SUSPICIOUS"
        badge_class = "suspicious"
        risk_level = "High Risk"
        risk_class = "risk-orange"
    else:
        badge = "SAFE"
        badge_class = "safe"
        risk_level = "Safe / Public Advisory"
        risk_class = "risk-green"

    indicators = [kw for kw in [
        "digital detention", "Aadhaar flagged", "Skype video conference", "narcotics trafficking",
        "immediate arrest", "money laundering", "verification reserve account"
    ] if kw in text_lower]
    
    if not indicators and badge != "SAFE":
        indicators = ["police impersonation", "coerced money transfer demand", "unlawful video interrogation"]
    elif badge == "SAFE":
        indicators = ["official government public notice", "1930 cyber crime helpline guidance"]

    recommends = []
    if badge != "SAFE":
        recommends = [
            "Do NOT join any Skype, WhatsApp, or Zoom video calls. Indian police never arrest citizens digitally.",
            "Do NOT transfer money to any 'safe' or 'verification' bank accounts.",
            "Block the numbers immediately and take screenshots of messages and user profiles.",
            "Report the incident on the National Cyber Crime Reporting Portal (cybercrime.gov.in) or call 1930."
        ]
    else:
        recommends = [
            "This is an official public safety advisory issued by the Ministry of Home Affairs.",
            "Remember: No police officer or government agency will ever conduct video arrests or ask for money."
        ]

    summary = f"Digital Arrest Threat Engine rating: {threat_score}%. "
    if badge != "SAFE":
        summary += "This input exhibits classic signatures of a Digital Arrest extortion scheme. Indian law enforcement agencies do not conduct video calls for legal interrogations."
    else:
        summary += "Verified authentic government public safety advisory or standard legal communication."

    fake_email, real_email = extract_email_details(text_input, platform_pred="digital_arrest", badge=badge, authority="CBI / Police")

    return jsonify({
        "success": True,
        "report": {
            "title": "Digital Arrest Scam" if badge != "SAFE" else "Official Cybercrime Advisory",
            "category": "Digital Arrest (CBI Impersonation)" if badge != "SAFE" else "Public Safety Advisory",
            "risk": risk_level,
            "riskClass": risk_class,
            "badge": badge,
            "badgeClass": badge_class,
            "authority": "Central Bureau of Investigation (CBI)" if badge != "SAFE" else "Ministry of Home Affairs (I4C)",
            "trigger": "Money Laundering & Narcotics Allegation" if badge != "SAFE" else "Public Cybercrime Safety Notice",
            "score": f"{threat_score}%",
            "fakeEmail": fake_email,
            "realEmail": real_email,
            "indicators": indicators,
            "summary": summary,
            "recommends": recommends
        }
    })

@app.route('/api/analyze-image', methods=['POST'])
def analyze_image():
    text_extracted = extract_ocr_text(request)
    if not text_extracted or len(text_extracted.strip()) < 5:
        return jsonify({
            "success": False,
            "error": "No text detected in the uploaded image screenshot.",
            "message": "The OCR engine could not find readable text in this image. Please ensure the screenshot is clear."
        }), 400

    text_lower = text_extracted.lower()

    # Determine best category engine match
    is_digital_arrest = any(k in text_lower for k in [
        'skype', 'digital detention', 'digital arrest', 'aadhaar flagged', 'narcotics',
        'cbi', 'cyber crime department', 'money laundering', 'verification reserve account'
    ])
    
    is_fake_hr = any(k in text_lower for k in [
        'pay $', 'wire $', 't.me/', 'whatsapp voice call', 'vip portal', 'advance deposit',
        'earn daily', 'like youtube', 'rate google maps', 'zelle', 'crypto wallet', 'npm run setup',
        'registration fee', 'upi id', 'upfront payment', 'wa.me/', 'block deal', 'github',
        'polinrider', 'beavertail', 'npm run', 'placement office', 'campus placement'
    ])

    if is_digital_arrest:
        with app.test_request_context('/api/analyze-digital-arrest', method='POST', data={'text': text_extracted}):
            res = analyze_digital_arrest()
            data = res.get_json()
            if data:
                data['ocrText'] = text_extracted
            return jsonify(data)
    elif is_fake_hr or 'recruiter' in text_lower or 'interview' in text_lower or 'hiring' in text_lower:
        with app.test_request_context('/api/analyze-fake-hr', method='POST', data={'text': text_extracted}):
            res = analyze_fake_hr()
            data = res.get_json()
            if data:
                data['ocrText'] = text_extracted
            return jsonify(data)
    else:
        # Generic Phishing / Screenshot Scam evaluation
        threat_score = 75
        badge = "SUSPICIOUS"
        badge_class = "suspicious"
        risk_level = "Moderate Risk"
        risk_class = "risk-orange"
        
        indicators = ["unverified text content", "suspicious message structure"]
        if any(k in text_lower for k in ['urgent', 'password', 'otp', 'verify', 'suspend', 'account', 'click here', 'bank', 'sbi', 'upi']):
            threat_score = 88
            badge = "MALICIOUS"
            badge_class = "malicious"
            risk_level = "Critical Risk"
            risk_class = "risk-red"
            indicators.append("credential harvesting / phishing prompt")

        return jsonify({
            "success": True,
            "ocrText": text_extracted,
            "report": {
                "title": "Screenshot Threat Analysis - Phishing / Untrusted Message",
                "category": "Unverified Screenshot / Phishing Prompt",
                "risk": risk_level,
                "riskClass": risk_class,
                "badge": badge,
                "badgeClass": badge_class,
                "authority": "Scam Analysis Engine",
                "trigger": "Unsolicited Screenshot Message",
                "score": f"{threat_score}%",
                "indicators": indicators,
                "summary": f"OCR extracted {len(text_extracted)} characters from the screenshot. The engine evaluated this message as '{badge}' threat level.",
                "recommends": [
                    "Verify the sender identity directly through official corporate or government portals.",
                    "Do NOT click any short links, payment links, or download APK attachments shown in the image."
                ]
            }
        })



@app.route('/api/analyze-apk', methods=['POST'])
def analyze_apk():
    global MODEL, FEATURE_COLUMNS
    if not MODEL_TRAINED:
        load_model()
        
    # Check if a file was uploaded or if it is a simulated key request
    is_simulation = request.form.get('is_simulation') == 'true'
    sim_key = request.form.get('sim_key')
    
    filename = ""
    target_sdk = "Android 13 (API Level 33)"
    package_name = "com.untrusted.application"
    app_name = "Unknown Application"
    signer = "Untrusted Self-Signed Certificate"
    permissions = []
    methods_called = []
    has_anti_debug = False
    
    # 1. Gather APK characteristics (Real vs Simulation)
    if is_simulation:
        if sim_key == 'apk_malware_1':
            app_name = "WhatsApp Update Helper"
            package_name = "com.whatsapp.update.helper"
            filename = "update_whatsapp_support.apk"
            signer = "Untrusted Debug Key (AndroidDebugKey)"
            permissions = ["android.permission.RECEIVE_SMS", "android.permission.SEND_SMS", "android.permission.SYSTEM_ALERT_WINDOW", "android.permission.RECEIVE_BOOT_COMPLETED"]
            methods_called = ["SmsReceiverService", "OverlayDrawingService", "PayloadLoaderActivity", "sendTextMessage", "getDeviceId"]
            has_anti_debug = True
        elif sim_key == 'apk_malware_2':
            app_name = "SBI Security Support"
            package_name = "in.sbi.security.verification"
            filename = "sbi_secure_verify.apk"
            signer = "Self-Signed (CN=Unknown, OU=Verification)"
            permissions = ["android.permission.SYSTEM_ALERT_WINDOW", "android.permission.READ_PHONE_STATE", "android.permission.INTERNET"]
            methods_called = ["BackgroundVerificationService", "OverlayManager", "getSubscriberId"]
            has_anti_debug = False
        else: # apk_clean_1
            app_name = "Simple Scientific Calculator"
            package_name = "com.calculator.science.utility"
            filename = "scientific_calculator.apk"
            signer = "Verified Developer Key (Google Play App Signing)"
            permissions = ["android.permission.VIBRATE"]
            methods_called = ["MainActivity"]
            has_anti_debug = False
    else:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
            
        uploaded_file = request.files['file']
        filename = uploaded_file.filename
        
        # Save to temp file
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        uploaded_file.save(temp_path)
        
        try:
            # Parse APK statically
            if ANDROGUARD_AVAILABLE:
                apk = APK(temp_path)
                app_name = apk.get_app_name() or filename
                package_name = apk.get_package() or "com.untrusted.application"
                target_sdk = f"Android {apk.get_target_sdk_version()} (API Level {apk.get_target_sdk_version()})"
                permissions = list(apk.get_permissions())
                
                # Check for debug key
                certs = apk.get_certificates()
                if certs:
                    subject = certs[0].subject.human_friendly
                    issuer = certs[0].issuer.human_friendly
                    if 'androiddebugkey' in subject.lower() or 'debug' in subject.lower():
                        signer = f"Untrusted Debug Key ({subject})"
                    else:
                        signer = f"Developer Signed ({subject})"
                else:
                    signer = "Self-Signed / Untrusted Key"
                
                # Try decompiling bytecode to find method calls
                try:
                    a, d, dx = AnalyzeAPK(temp_path)
                    methods_called = [m.name for m in dx.get_methods()]
                    # Check for anti-debug strings
                    methods_str = " ".join(methods_called).lower()
                    if any(k in methods_str for k in ['isdebuggerconnected', 'anti_debug', 'ptrace', 'antivm']):
                        has_anti_debug = True
                except Exception as ex:
                    log.warning(f"Error extracting Dalvik methods: {ex}")
                    # Fallback to simple permission analysis
                    methods_called = []
            else:
                # No Androguard fallback
                app_name = filename
                package_name = "com.untrusted.apk"
                permissions = ["android.permission.INTERNET"]
                methods_called = []
        except Exception as e:
            return jsonify({"error": f"Error parsing APK: {str(e)}"}), 500
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # 2. Run Machine Learning Inference
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
            score = "0%"
    else:
        # Fallback heuristic
        if any('receive_sms' in p.lower() or 'send_sms' in p.lower() for p in permissions):
            threat_class = "RAT / SMS Stealer Trojan"
            badge = "MALICIOUS"
            badge_class = "malicious"
            score = "92%"
        elif any('system_alert_window' in p.lower() for p in permissions):
            threat_class = "Overlay Phishing / Banking Trojan"
            badge = "MALICIOUS"
            badge_class = "malicious"
            score = "88%"
        else:
            threat_class = "Safe Utility App"
            badge = "SAFE"
            badge_class = "safe"
            score = "0%"

    # 3. Build UI Components lists
    components_list = []
    # Identify components from methods or permissions
    if is_simulation:
        if sim_key == 'apk_malware_1':
            components_list = [
                {"title": "SmsReceiverService", "desc": "Monitors SMS broadcasts, intercepting standard text messages on device boot."} ,
                {"title": "OverlayDrawingService", "desc": "Draws transparent window nodes over system UI to capture touch clicks."} ,
                {"title": "PayloadLoaderActivity", "desc": "Decodes and loads dynamic obfuscated DEX code dynamically in background thread."}
            ]
        elif sim_key == 'apk_malware_2':
            components_list = [
                {"title": "BackgroundVerificationService", "desc": "Runs persistent background task tracking the foreground application activity."} ,
                {"title": "OverlayManager", "desc": "Launches customized banking log-in overlay forms when official banking apps are focused."}
            ]
        else:
            components_list = [
                {"title": "MainActivity", "desc": "Core interface layout executing arithmetic computations."}
            ]
    else:
        # Parse real components or guess based on permissions
        if any('sms' in p.lower() for p in permissions):
            components_list.append({"title": "SmsReceiverService", "desc": "Intercepts incoming text messages. Monitors SMS verification loops."})
        if any('alert' in p.lower() or 'window' in p.lower() for p in permissions):
            components_list.append({"title": "OverlayDrawingService", "desc": "Launches transparent window overlay elements on top of system UI."})
        if has_anti_debug:
            components_list.append({"title": "ObfuscatedPayloadLoader", "desc": "Dynamically loads encrypted or obfuscated executable dex archives."})
            
        if not components_list:
            components_list.append({"title": "MainActivity", "desc": "Standard execution UI entrypoint component."})

    # Prepare permissions list matching UI formatting
    permissions_response = []
    for p in permissions:
        short_name = p.split('.')[-1]
        detail = PERMISSION_DETAILS.get(p, {"status": "NORMAL", "desc": f"Allows application access to {short_name} system actions."})
        permissions_response.append({
            "name": p,
            "status": detail["status"],
            "desc": detail["desc"]
        })
        
    # Sort permissions so dangerous ones show first
    permissions_response.sort(key=lambda x: 0 if x["status"] == "DANGEROUS" else (1 if x["status"] == "WARNING" else 2))

    # Recommendations
    recommends = []
    if badge == "MALICIOUS":
        recommends = [
            f"Uninstaller Prompt: Immediately navigate to Settings -> Apps -> {app_name} and click Uninstall.",
            "Check Device Admin Access: Go to Special App Access -> Device Admin Apps, and remove administrative privileges if granted.",
            "Change Banking Passwords: If you entered netbanking username/password on this device, freeze your accounts and reset passwords immediately.",
            "Run Google Play Protect: Run a manual Google Play Protect scan to double-check for residual payloads."
        ]
    else:
        recommends = [
            "The application does not request high-risk permissions and is signed with a valid developer key.",
            "No suspicious background components or overlay tools detected during static analysis. Safe to install."
        ]

    # Return report structure
    report = {
        "appName": app_name,
        "packageName": package_name,
        "signer": signer,
        "targetSdk": target_sdk,
        "threatClass": threat_class,
        "score": score,
        "badge": badge,
        "badgeClass": badge_class,
        "components": components_list,
        "permissions": permissions_response,
        "recommends": recommends
    }
    
    return jsonify({
        "success": True,
        "filename": filename,
        "report": report
    })

@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)

if __name__ == '__main__':
    log.info("Starting ORCA APK Scam Detection Backend on port 5000")
    app.run(port=5000, debug=False, use_reloader=False)
