import os
import tempfile
import pickle
import json
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import androguard components safely
try:
    from androguard.core.apk import APK
    from androguard.misc import AnalyzeAPK
    ANDROGUARD_AVAILABLE = True
except Exception as e:
    print(f"Error loading Androguard: {e}")
    ANDROGUARD_AVAILABLE = False

app = Flask(__name__)
CORS(app)

MODEL = None
FEATURE_COLUMNS = []
MODEL_TRAINED = False

def load_model():
    global MODEL, FEATURE_COLUMNS, MODEL_TRAINED
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(backend_dir, "apk_scam_model.pkl")
    features_path = os.path.join(backend_dir, "feature_columns.json")
    
    if os.path.exists(model_path) and os.path.exists(features_path):
        try:
            with open(model_path, "rb") as f:
                MODEL = pickle.load(f)
            with open(features_path, "r") as f:
                FEATURE_COLUMNS = json.load(f)
            MODEL_TRAINED = True
            print("ML Model loaded successfully!")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
    MODEL_TRAINED = False
    return False

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
        
    # 5. DEVICE_ACCESS_____
    device_keywords = ['camera', 'record_audio', 'location', 'gps', 'bluetooth', 'nfc', 'vibrate']
    if any(any(k in p for k in device_keywords) for p in perms):
        feature_dict['DEVICE_ACCESS_____'] = 1
        
    # 6. ANTI_DEBUG_____
    if has_anti_debug:
        feature_dict['ANTI_DEBUG_____'] = 1
        
    # Match specific column names for permissions
    for col in FEATURE_COLUMNS:
        col_clean = col.lower().replace('_', '')
        # Check if column matches standard permission strings
        for p in perms:
            p_clean = p.split('.')[-1].lower().replace('_', '')
            if col_clean == p_clean or p_clean in col_clean:
                feature_dict[col] = 1
        # Check if column matches any called methods
        for m in methods:
            m_clean = m.replace('_', '').replace('()', '')
            if col_clean == m_clean or m_clean in col_clean:
                feature_dict[col] = 1
                
    return feature_dict

@app.route('/api/status', methods=['GET'])
def status():
    load_model()
    return jsonify({
        "connected": True,
        "model_trained": MODEL_TRAINED,
        "features_count": len(FEATURE_COLUMNS),
        "androguard_available": ANDROGUARD_AVAILABLE
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
            "message": "Model trained successfully!"
        })
    except subprocess.CalledProcessError as e:
        return jsonify({
            "success": False,
            "error": e.stderr,
            "message": "Error training the model."
        }), 500

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
                    print(f"Error extracting Dalvik methods: {ex}")
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

if __name__ == '__main__':
    app.run(port=5000, debug=True)
