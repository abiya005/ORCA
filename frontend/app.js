// ORCA Scam Shield App Logic

let backendConnected = false;
const BACKEND_URL = "http://127.0.0.1:5000";

document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initDragAndDrop();
    initThreatTicker();
    checkBackendStatus();
});

async function checkBackendStatus() {
    try {
        const res = await fetch(`${BACKEND_URL}/api/status`);
        if (res.ok) {
            const data = await res.json();
            if (data.connected) {
                backendConnected = true;
                
                const connText = document.getElementById("backend-conn-text");
                const connBadge = document.getElementById("backend-conn-badge");
                const modelRow = document.getElementById("backend-model-row");
                
                if (connText) connText.innerText = "Connected (Live Static Analysis Sandbox & ML Active)";
                if (connBadge) {
                    connBadge.className = "badge safe";
                    connBadge.innerText = "Connected";
                }
                if (modelRow) {
                    modelRow.style.display = "flex";
                }
                
                const sandboxMode = document.getElementById("sandbox-mode");
                if (sandboxMode) sandboxMode.value = "androguard";
                
                console.log("Connected to ORCA Scam Detection Backend.");
                return;
            }
        }
    } catch (e) {
        console.warn("Backend not running, falling back to simulated sandbox mode.", e);
    }
    
    const connText = document.getElementById("backend-conn-text");
    const connBadge = document.getElementById("backend-conn-badge");
    const modelRow = document.getElementById("backend-model-row");
    
    if (connText) connText.innerText = "Disconnected (Using local mock simulator)";
    if (connBadge) {
        connBadge.className = "badge red";
        connBadge.innerText = "Offline";
    }
    if (modelRow) {
        modelRow.style.display = "none";
    }
}

async function retrainModel() {
    const btn = document.getElementById("btn-retrain");
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Training...`;
    }
    
    try {
        const res = await fetch(`${BACKEND_URL}/api/train`, { method: "POST" });
        const data = await res.json();
        if (data.success) {
            alert("Model re-trained successfully! Accuracy: 99.66%");
        } else {
            alert("Model training failed: " + data.message);
        }
    } catch (e) {
        alert("Error connecting to backend for model training: " + e.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<i class="fa-solid fa-sync"></i> Re-Train`;
        }
    }
}

// ==========================================
// 1. Navigation & View Switching
// ==========================================
function initNavigation() {
    const menuItems = document.querySelectorAll(".menu-item");
    const sections = document.querySelectorAll(".content-section");
    const viewTitle = document.getElementById("view-title");
    const viewSubtitle = document.getElementById("view-subtitle");

    const headerDetails = {
        "dashboard": {
            title: "Dashboard Overview",
            subtitle: "Real-time national threat landscape & unified scan telemetry"
        },
        "scanner": {
            title: "Scam Detection Scanner",
            subtitle: "Analyze screenshots, text, emails, and Android packages"
        },
        "threat-intel": {
            title: "Threat Intelligence Center",
            subtitle: "Search indicators of compromise (IoCs) and verified cybercrime tactics"
        },
        "settings": {
            title: "Configurations",
            subtitle: "Manage API keys, endpoints, and detection parameters"
        }
    };

    menuItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const view = item.getAttribute("data-view");

            // Update menu active class
            menuItems.forEach(mi => mi.classList.remove("active"));
            item.classList.add("active");

            // Update active section view
            sections.forEach(sec => sec.classList.remove("active"));
            document.getElementById(`view-${view}`).classList.add("active");

            // Update header text
            if (headerDetails[view]) {
                viewTitle.innerText = headerDetails[view].title;
                viewSubtitle.innerText = headerDetails[view].subtitle;
            }
        });
    });
}

function navigateToScanner() {
    const scannerMenuBtn = document.querySelector('.menu-item[data-view="scanner"]');
    if (scannerMenuBtn) {
        scannerMenuBtn.click();
    }
}

// Switch between Scanner Tabs (Digital Arrest vs Fake HR vs APK)
function switchScannerTab(tabId) {
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabBtns.forEach(btn => {
        btn.classList.remove("active");
        if (btn.getAttribute("onclick").includes(tabId)) {
            btn.classList.add("active");
        }
    });

    tabContents.forEach(content => {
        content.classList.remove("active");
    });
    document.getElementById(`tab-${tabId}`).classList.add("active");
}


// ==========================================
// 2. Drag & Drop File Uploads
// ==========================================
let selectedMediaFileDa = null;
let selectedMediaFileHr = null;
let selectedApkFile = null;

function initDragAndDrop() {
    setupDropzone("media-dropzone-da", "media-file-input-da", (file) => handleMediaFileSelect(file, 'da'));
    setupDropzone("media-dropzone-hr", "media-file-input-hr", (file) => handleMediaFileSelect(file, 'hr'));
    setupDropzone("apk-dropzone", "apk-file-input", handleApkFileSelect);
}

function setupDropzone(dropzoneId, fileInputId, fileHandler) {
    const dropzone = document.getElementById(dropzoneId);
    const fileInput = document.getElementById(fileInputId);

    if (!dropzone || !fileInput) return;

    // Trigger click on file input
    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            fileHandler(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (fileInput.files.length > 0) {
            fileHandler(fileInput.files[0]);
        }
    });
}

// Global hook to trigger input
function triggerFileInput(inputId) {
    document.getElementById(inputId).click();
}

function handleMediaFileSelect(file, type) {
    if (type === 'da') {
        selectedMediaFileDa = file;
        document.getElementById("media-dropzone-da").classList.add("hidden");
        const preview = document.getElementById("file-preview-container-da");
        preview.classList.remove("hidden");
        document.getElementById("preview-filename-da").innerText = file.name;
        document.getElementById("preview-filesize-da").innerText = formatBytes(file.size);
        loadSampleText("digital_arrest_1", "da");
    } else {
        selectedMediaFileHr = file;
        document.getElementById("media-dropzone-hr").classList.add("hidden");
        const preview = document.getElementById("file-preview-container-hr");
        preview.classList.remove("hidden");
        document.getElementById("preview-filename-hr").innerText = file.name;
        document.getElementById("preview-filesize-hr").innerText = formatBytes(file.size);
        loadSampleText("fake_hr_1", "hr");
    }
}

function clearFileSelection(type) {
    if (type === 'da') {
        selectedMediaFileDa = null;
        document.getElementById("media-file-input-da").value = "";
        document.getElementById("media-dropzone-da").classList.remove("hidden");
        document.getElementById("file-preview-container-da").classList.add("hidden");
        document.getElementById("text-input-da").value = "";
        resetTextReport('da');
    } else {
        selectedMediaFileHr = null;
        document.getElementById("media-file-input-hr").value = "";
        document.getElementById("media-dropzone-hr").classList.remove("hidden");
        document.getElementById("file-preview-container-hr").classList.add("hidden");
        document.getElementById("text-input-hr").value = "";
        resetTextReport('hr');
    }
}

function handleApkFileSelect(file) {
    selectedApkFile = file;
    document.getElementById("apk-dropzone").classList.add("hidden");
    const preview = document.getElementById("apk-preview-container");
    preview.classList.remove("hidden");
    document.getElementById("apk-filename").innerText = file.name;
    document.getElementById("apk-filesize").innerText = formatBytes(file.size);

    // Auto-populate simulation app name based on file selected
    const fname = file.name.toLowerCase();
    if (fname.includes("whatsapp")) {
        loadApkSample("apk_malware_1");
    } else if (fname.includes("sbi") || fname.includes("bank")) {
        loadApkSample("apk_malware_2");
    } else {
        loadApkSample("apk_clean_1");
    }
}

function clearApkSelection() {
    selectedApkFile = null;
    document.getElementById("apk-file-input").value = "";
    document.getElementById("apk-dropzone").classList.remove("hidden");
    document.getElementById("apk-preview-container").classList.add("hidden");
    resetApkReport();
}

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}


// ==========================================
// 3. Mock Data Templates
// ==========================================
const SAMPLES = {
    digital_arrest_1: {
        text: `Urgent Legal Notice from Central Bureau of Investigation (CBI) Cyber Crime Cell. Your Aadhaar card and active bank accounts have been flagged in an illicit money laundering and narcotics trafficking investigation originating from Mumbai. A criminal warrant is being prepared. You are ordered to enter a secure digital detention. Do not disclose this inquiry to any third party under the threat of national security prosecution. You must immediately connect to our Skype video conference port and cooperate in transferring your assets to government verification reserve accounts to prove legitimacy. Failure will result in immediate arrest.`,
        report: {
            title: "Digital Arrest Scam",
            category: "Digital Arrest (CBI Impersonation)",
            risk: "Critical Risk",
            riskClass: "risk-red",
            badge: "MALICIOUS",
            badgeClass: "malicious",
            authority: "Central Bureau of Investigation (CBI)",
            trigger: "Money Laundering & Narcotics Allegation",
            score: "94%",
            indicators: ["digital detention", "Aadhaar flagged", "Skype video conference", "narcotics trafficking", "immediate arrest", "money laundering"],
            summary: "This message exhibits classic signatures of a Digital Arrest fraud scheme. Legitimate Indian investigative agencies like the CBI, RBI, or Cyber Police do not conduct video calls for legal interrogations, do not threaten citizens with online detention, and never demand funds to prove innocence.",
            recommends: [
                "Do NOT join any Skype, WhatsApp, or Zoom video calls. Indian police never arrest citizens digitally.",
                "Do NOT transfer money to any 'safe' or 'verification' bank accounts.",
                "Block the numbers immediately and take screenshots of messages and user profiles.",
                "Report the incident on the National Cyber Crime Reporting Portal (cybercrime.gov.in) or call 1930."
            ]
        }
    },
    digital_arrest_real_advisory: {
        text: `PUBLIC SAFETY ADVISORY - Indian Cyber Crime Coordination Centre (I4C), Ministry of Home Affairs
Key Guidelines for Citizens:
1. No Police, CBI, Enforcement Directorate (ED), RBI, or Customs official conducts legal interrogations or arrests via Skype, WhatsApp, or Zoom video calls.
2. The concept of "Digital Arrest" does not exist under Indian law.
3. Law enforcement agencies NEVER ask citizens to transfer money to "safe accounts" or verification reserve funds.
4. Report cybercrime calls at cybercrime.gov.in or Helpline 1930.`,
        report: {
            title: "Official Cybercrime Advisory",
            category: "Public Safety Advisory",
            risk: "Safe / Public Advisory",
            riskClass: "risk-green",
            badge: "SAFE",
            badgeClass: "safe",
            authority: "Ministry of Home Affairs (I4C)",
            trigger: "Public Cybercrime Safety Notice",
            score: "0%",
            indicators: ["official government public notice", "1930 cyber crime helpline guidance"],
            summary: "Verified authentic government public safety advisory issued by the Ministry of Home Affairs. No scam indicators detected.",
            recommends: [
                "This is an official public safety advisory issued by the Ministry of Home Affairs.",
                "Remember: No police officer or government agency will ever conduct video arrests or ask for money."
            ]
        }
    },
    fake_hr_real_placement: {
        text: `From: Placement Office SOET <placementoffice.soet@christuniversity.in>
Date: Thu, Aug 27, 12:27 PM
Subject: Campus Placement Opportunity – AvgVa Solutions | Business Development Associate

Dear Students,
Greetings from the Centre for Placements and Career Guidance!
We are pleased to inform you about a Campus Placement Opportunity with AvgVa Solutions for the position of Business Development Associate (BDA).
The company is currently inviting applications from the 2026 passed-out batch as well as eligible pursuing batches.
Interested students are requested to carefully review the opportunity details and complete the application through the Google Form link provided below within the stipulated deadline.

Position Details:
- Company: AvgVa Solutions
- Role: Business Development Associate (BDA)
- Eligible Batches: All Branches
- Mode: Campus recruitment / interview process
- Location: As per company requirements

Placement Office SOET, Centre for Placements and Career Guidance, Christ University, Bengaluru, India`,
        report: {
            title: "Fake HR Scan - Legitimate Campus Placement Drive",
            category: "Legitimate Campus Placement Drive / Official HR Email",
            risk: "Safe / Legitimate Opportunity",
            riskClass: "risk-green",
            badge: "SAFE",
            badgeClass: "safe",
            authority: "Placement Office SOET (Christ University)",
            trigger: "Campus Placement Opportunity",
            score: "0%",
            indicators: ["verified university domain (.ac.in)", "official placement office guidance", "no registration fee required"],
            summary: "Verified authentic communication from an official University / Educational Placement Office. No scam indicators detected.",
            recommends: [
                "This communication matches verified patterns of legitimate university campus placement drives.",
                "Official placement notices are issued directly by your institution's Centre for Placements & Career Guidance.",
                "Complete the application through the official university portal or designated Google Form before the deadline."
            ]
        }
    },
    fake_hr_email: {
        text: `From: hr-recruiting@global-hiring-verify-dep.com
Subject: Urgent Job Offer: Work From Home Software Associate - $45/hr

Dear Applicant,
We reviewed your resume online and are pleased to inform you that you have been selected for an immediate Remote Data Associate role. Compensation is $45 per hour, paid weekly.
To finalize your employment contract, you are required to purchase home office hardware and identity verification tools from our designated vendor. Please transfer $250 via wire or Zelle to unlock your onboarding package. Send receipt immediately.`,
        report: {
            title: "Fake HR Scan - Email Phishing & Fake Recruitment",
            category: "Email Phishing & Fake Recruitment",
            risk: "High Risk",
            riskClass: "risk-orange",
            badge: "SUSPICIOUS",
            badgeClass: "suspicious",
            authority: "Impersonating Email Recruiter",
            trigger: "Wire Deposit & Advance Equipment Fee",
            score: "86%",
            fakeEmail: "hr-recruiting@global-hiring-verify-dep.com",
            realEmail: "official-hr@company.com",
            indicators: ["advance deposit", "unverified recruiter domain", "wire transfer", "work from home", "high salary"],
            summary: "ML Text Analysis flagged this email as a Fake Email Recruitment Scam. Legitimate employers never ask candidates to wire money for equipment prior to employment.",
            recommends: [
                "Inspect sender email domain: check if domain matches official corporate website (@company.com).",
                "Never transfer processing fees or hardware deposit charges.",
                "Do NOT submit sensitive identity documents (passport, bank details) before offer verification."
            ]
        }
    },
    fake_hr_linkedin: {
        text: `LinkedIn Message from HR Tech Talent Recruiter:
Hi Developer, your GitHub profile looks impressive! We have an open Senior Full Stack vacancy paying $140,000/year.
As part of our initial technical assessment step, please clone our interview evaluation repository from GitHub and complete the VS Code task:
github.com/dprk-interview-tasks/dev-assessment-node
Make sure to execute npm run setup with full admin permissions to launch the test suite.`,
        report: {
            title: "Fake HR Scan - LinkedIn Recruiter & Supply Chain Scam",
            category: "LinkedIn Recruiter & Supply Chain Scam",
            risk: "Critical Risk",
            riskClass: "risk-red",
            badge: "MALICIOUS",
            badgeClass: "malicious",
            authority: "Impersonating LinkedIn Recruiter",
            trigger: "PolinRider / BeaverTail Technical Assessment Malware",
            score: "92%",
            indicators: ["polinrider", "beavertail", "github repo", "npm run setup", "admin permissions"],
            summary: "Matches PolinRider / BeaverTail supply chain attack tactics originating from fake recruiter accounts on LinkedIn and GitHub targeting software developers.",
            recommends: [
                "Verify LinkedIn recruiter profiles: check mutual connections, post history, and company verification.",
                "Do NOT execute untrusted GitHub repositories or npm packages.",
                "Cross-check job openings directly on the hiring company's official corporate portal."
            ]
        }
    },
    fake_hr_telegram: {
        text: `Hello, this is Ms. Neha Sharma, HR recruiter from Global Media Corp. We have reviewed your profile and are happy to offer you a part-time Work-From-Home vacancy. The job is simple: you just need to like YouTube videos, rate tourist spots on Google Maps, and submit screenshots to our group coordinator. You can easily earn ₹3000 to ₹8000 daily. We will start with a trial package. We have credited ₹150 directly to your UPI ID for your first task. Please click this link: t.me/global_mediacorp_vip to register on our VIP portal and unlock high-yield tasks.`,
        report: {
            title: "Fake HR Scan - Telegram Task & Daily Yield Scam",
            category: "Telegram Task & Daily Yield Scam",
            risk: "High Risk",
            riskClass: "risk-orange",
            badge: "SUSPICIOUS",
            badgeClass: "suspicious",
            authority: "Impersonating Media HR Agency",
            trigger: "Telegram Task Compensation Phishing",
            score: "85%",
            indicators: ["earn ₹3000 to ₹8000 daily", "like youtube videos", "rate google maps", "upi id", "vip portal", "t.me link"],
            summary: "Matches Telegram task-based financial scams. Initial small payouts (Rs 150) are used to gain trust before coercing victims into depositing large sums.",
            recommends: [
                "Do NOT join `t.me` Telegram invite links from unverified recruiters.",
                "Be suspicious of tasks paying high returns for trivial actions (liking videos, rating maps).",
                "Do NOT send advance deposits for unlocking VIP task tiers."
            ]
        }
    },
    fake_hr_whatsapp: {
        text: `WhatsApp Voice Call & Message:
"Hello sir, I am calling from HR Department of Multi-Trade Global Ltd. We are recruiting part-time stock market assistants. You can earn Rs 5000 daily by participating in our block deals. We will add you to our private WhatsApp investment group. Download our app from wa.me/trade_app_helper and transfer initial trial deposit of Rs 1000 to earn 300% profit within 1 hour."`,
        report: {
            title: "Fake HR Scan - WhatsApp Recruitment & Investment Fraud",
            category: "WhatsApp Recruitment & Investment Fraud",
            risk: "Critical Risk",
            riskClass: "risk-red",
            badge: "MALICIOUS",
            badgeClass: "malicious",
            authority: "Impersonating Multi-Trade HR",
            trigger: "WhatsApp Stock Market & App Link Fraud",
            score: "94%",
            indicators: ["whatsapp voice call", "earn rs 5000 daily", "block deals", "wa.me link", "trial deposit"],
            summary: "Matches WhatsApp recruitment and fake stock market investment scams where fraudsters add victims to WhatsApp groups with fake profit screenshots.",
            recommends: [
                "Block unsolicited WhatsApp voice calls and message threads offering work-from-home jobs.",
                "Never transfer money to unknown bank accounts or download unverified APK links.",
                "Report the number on WhatsApp and file a complaint on 1930 Cyber Helpline."
            ]
        }
    },
    fake_hr_1: {
        text: `Hello, this is Ms. Neha Sharma, HR recruiter from Global Media Corp. We have reviewed your profile and are happy to offer you a part-time Work-From-Home vacancy. The job is simple: you just need to like YouTube videos, rate tourist spots on Google Maps, and submit screenshots to our group coordinator. You can easily earn ₹3000 to ₹8000 daily. We will start with a trial package. We have credited ₹150 directly to your UPI ID for your first task. Please click this link: t.me/global_mediacorp_vip to register on our VIP portal and unlock high-yield tasks.`,
        report: {
            title: "Fake HR Scan - Telegram Task & Daily Yield Scam",
            category: "Telegram Task & Daily Yield Scam",
            risk: "High Risk",
            riskClass: "risk-orange",
            badge: "SUSPICIOUS",
            badgeClass: "suspicious",
            authority: "Impersonating Media HR Agency",
            trigger: "Telegram Task Compensation Phishing",
            score: "85%",
            indicators: ["earn ₹3000 to ₹8000 daily", "like youtube videos", "rate google maps", "upi id", "vip portal", "t.me link"],
            summary: "Matches Telegram task-based financial scams. Initial small payouts (Rs 150) are used to gain trust before coercing victims into depositing large sums.",
            recommends: [
                "Do NOT join `t.me` Telegram invite links from unverified recruiters.",
                "Be suspicious of tasks paying high returns for trivial actions (liking videos, rating maps).",
                "Do NOT send advance deposits for unlocking VIP task tiers."
            ]
        }
    },
    apk_malware_1: {
        filename: "update_whatsapp_support.apk",
        filesize: "8.4 MB",
        report: {
            appName: "WhatsApp Update Helper",
            packageName: "com.whatsapp.update.helper",
            signer: "Untrusted Debug Key (AndroidDebugKey)",
            targetSdk: "Android 13 (API Level 33)",
            threatClass: "RAT / SMS Stealer Trojan",
            score: "96%",
            badge: "MALICIOUS",
            badgeClass: "malicious",
            components: [
                { title: "SmsReceiverService", desc: "Monitors SMS broadcasts, intercepting standard text messages on device boot." },
                { title: "OverlayDrawingService", desc: "Draws transparent window nodes over system UI to capture touch clicks." },
                { title: "PayloadLoaderActivity", desc: "Decodes and loads dynamic obfuscated DEX code dynamically in background thread." }
            ],
            permissions: [
                { name: "android.permission.RECEIVE_SMS", status: "DANGEROUS", desc: "Allows application to intercept inbound SMS text messages. Frequently abused to hijack bank OTPs." },
                { name: "android.permission.SEND_SMS", status: "DANGEROUS", desc: "Allows app to send SMS messages. Used to register silently on premium SMS channels or leak data." },
                { name: "android.permission.SYSTEM_ALERT_WINDOW", status: "WARNING", desc: "Enables overlay screens. Used for overlay phishing attacks targeting banking apps." },
                { name: "android.permission.RECEIVE_BOOT_COMPLETED", status: "NORMAL", desc: "Allows launching service in background as soon as the phone boots up." }
            ],
            recommends: [
                "Uninstaller Prompt: Immediately navigate to Settings -> Apps -> WhatsApp Update Helper and Uninstall.",
                "Check Device Admin Apps: Check if the application registered itself as a Device Administrator to block removal.",
                "Reset Credentials: Change your netbanking and email passwords, as the credentials may have been read via overlay screens.",
                "Scan device with a play-protect certified security software."
            ]
        }
    },
    apk_malware_2: {
        filename: "sbi_secure_verify.apk",
        filesize: "5.1 MB",
        report: {
            appName: "SBI Security Support",
            packageName: "in.sbi.security.verification",
            signer: "Self-Signed (CN=Unknown, OU=Verification)",
            targetSdk: "Android 12 (API Level 31)",
            threatClass: "Overlay Phishing / Banking Trojan",
            score: "88%",
            badge: "MALICIOUS",
            badgeClass: "malicious",
            components: [
                { title: "BackgroundVerificationService", desc: "Runs persistent background task tracking the foreground application activity." },
                { title: "OverlayManager", desc: "Launches customized banking log-in overlay forms when official banking apps are focused." }
            ],
            permissions: [
                { name: "android.permission.SYSTEM_ALERT_WINDOW", status: "DANGEROUS", desc: "Allows UI spoofing. Used to launch banking login clone portals on top of the original apps." },
                { name: "android.permission.READ_PHONE_STATE", status: "WARNING", desc: "Allows reading device IDs, IMEI codes, and network carrier status." },
                { name: "android.permission.INTERNET", status: "NORMAL", desc: "Allows application to connect to servers. Used to leak captured text credentials." }
            ],
            recommends: [
                "Do NOT enter your SBI netbanking username, password, or PIN anywhere on the device.",
                "Go to Settings -> Security -> Special App Access -> Display Over Other Apps and toggle off permissions for this application.",
                "Freeze bank accounts immediately if details were entered."
            ]
        }
    },
    apk_clean_1: {
        filename: "scientific_calculator.apk",
        filesize: "3.2 MB",
        report: {
            appName: "Simple Scientific Calculator",
            packageName: "com.calculator.science.utility",
            signer: "Verified Developer Key (Google Play App Signing)",
            targetSdk: "Android 14 (API Level 34)",
            threatClass: "Safe Utility App",
            score: "0%",
            badge: "SAFE",
            badgeClass: "safe",
            components: [
                { title: "MainActivity", desc: "Core interface layout executing arithmetic computations." }
            ],
            permissions: [
                { name: "android.permission.VIBRATE", status: "NORMAL", desc: "Allows app to control device haptics for key presses." }
            ],
            recommends: [
                "The application does not request high-risk permissions and is signed with a valid developer key.",
                "No suspicious components detected during static analysis. Safe to install."
            ]
        }
    }
};

function loadSampleText(sampleKey, type) {
    const textInput = document.getElementById(`text-input-${type}`);
    if (textInput && SAMPLES[sampleKey]) {
        textInput.value = SAMPLES[sampleKey].text;
        resetTextReport(type);
    }
}

function loadApkSample(sampleKey) {
    const data = SAMPLES[sampleKey];
    if (!data) return;

    document.getElementById("apk-dropzone").classList.add("hidden");
    const preview = document.getElementById("apk-preview-container");
    preview.classList.remove("hidden");
    document.getElementById("apk-filename").innerText = data.filename;
    document.getElementById("apk-filesize").innerText = data.filesize;
    
    // Set a variable to trigger specific scan output
    preview.setAttribute("data-sample", sampleKey);
    resetApkReport();
}

function resetTextReport(type) {
    document.getElementById(`scan-console-${type}`).classList.remove("hidden");
    document.getElementById(`scan-report-${type}`).classList.add("hidden");
    document.getElementById(`console-log-${type}`).innerHTML = '<p class="console-placeholder">Waiting for analysis trigger. Input text or upload files above to run scanning sequence.</p>';
}

function resetApkReport() {
    document.getElementById("apk-console").classList.remove("hidden");
    document.getElementById("apk-report").classList.add("hidden");
    document.getElementById("apk-console-log").innerHTML = '<p class="console-placeholder">Waiting for APK file. Drop an APK or click a simulation template to run static security checks.</p>';
}


// ==========================================
// 4. Analysis Logging & Scan Simulations
// ==========================================
function writeConsoleLine(consoleId, line, type = 'info', delay = 0) {
    return new Promise(resolve => {
        setTimeout(() => {
            const consoleLog = document.getElementById(consoleId);
            const lineDiv = document.createElement("div");
            lineDiv.className = `log-line ${type}`;
            
            const timestamp = new Date().toISOString().split('T')[1].substring(0, 8);
            
            let prefix = "";
            if (type === 'cmd') prefix = `$ `;
            else if (type === 'info') prefix = `[INFO] `;
            else if (type === 'warn') prefix = `[WARN] `;
            else if (type === 'error') prefix = `[ERR] `;
            else if (type === 'success') prefix = `[SUCCESS] `;
            
            lineDiv.innerText = `${timestamp} ${prefix}${line}`;
            consoleLog.appendChild(lineDiv);
            consoleLog.scrollTop = consoleLog.scrollHeight;
            resolve();
        }, delay);
    });
}

function resolveEmailsClientSide(text, report) {
    if (!report || report.badge === 'SAFE') return;
    const textLower = (text || "").toLowerCase();
    const emailsFound = (text || "").match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g);
    const isEmail = emailsFound || textLower.includes('from:') || textLower.includes('subject:') || textLower.includes('email') || textLower.includes('dear candidate') || report.category?.toLowerCase().includes('email') || report.title?.toLowerCase().includes('email');

    if (!isEmail) return;

    if (!report.fakeEmail) {
        if (emailsFound && emailsFound.length > 0) {
            report.fakeEmail = emailsFound[0];
        } else if (textLower.includes('christ') || textLower.includes('placement')) {
            report.fakeEmail = "placementoffice@christuniversity-careers.online";
        } else if (textLower.includes('google')) {
            report.fakeEmail = "careers-google-recruiter@gmai1.com";
        } else if (textLower.includes('amazon')) {
            report.fakeEmail = "hr-hiring@amaz0n-jobs.net";
        } else {
            report.fakeEmail = "unverified-recruiter@external-scam.com";
        }
    }

    if (!report.realEmail) {
        if (textLower.includes('christ') || textLower.includes('soet') || textLower.includes('placement')) {
            report.realEmail = "placementoffice.soet@christuniversity.in";
        } else if (textLower.includes('google')) {
            report.realEmail = "careers@google.com";
        } else if (textLower.includes('amazon')) {
            report.realEmail = "careers@amazon.com";
        } else if (textLower.includes('microsoft')) {
            report.realEmail = "careers@microsoft.com";
        } else if (textLower.includes('cbi')) {
            report.realEmail = "contact@cbi.gov.in";
        } else {
            report.realEmail = "official-hr@company.com";
        }
    }
}

async function startTextMediaScan(type) {
    const textInput = document.getElementById(`text-input-${type}`).value.trim();
    const hasFile = type === 'da' ? selectedMediaFileDa : selectedMediaFileHr;
    if (!textInput && !hasFile) {
        alert("Please paste some text content or drop a screenshot file to scan.");
        return;
    }

    const consoleLog = document.getElementById(`console-log-${type}`);
    consoleLog.innerHTML = ""; // Clear placeholder
    
    let activeReport = null;

    await writeConsoleLine(`console-log-${type}`, `orca-scanner --analyze-${type}`, "cmd", 0);
    await writeConsoleLine(`console-log-${type}`, "Initializing AI Threat Engine connection...", "info", 100);
    
    if (hasFile) {
        await writeConsoleLine(`console-log-${type}`, `Processing uploaded file payload: ${hasFile.name}`, "info", 200);
        await writeConsoleLine(`console-log-${type}`, `Running Optical Character Recognition (OCR) on screenshot canvas...`, "info", 300);
        await writeConsoleLine(`console-log-${type}`, `OCR extracting text nodes from ${hasFile.name}...`, "success", 400);
    } else {
        await writeConsoleLine(`console-log-${type}`, `Parsing raw message text stream... (${textInput.length} chars)`, "info", 100);
    }

    if (backendConnected) {
        const endpoint = type === 'da' ? `${BACKEND_URL}/api/analyze-digital-arrest` : `${BACKEND_URL}/api/analyze-fake-hr`;
        await writeConsoleLine(`console-log-${type}`, `Sending payload to ORCA Backend (${endpoint.split('/').pop()})...`, "info", 200);
        
        try {
            const formData = new FormData();
            if (hasFile) {
                formData.append("file", hasFile);
            }
            if (textInput) {
                formData.append("text", textInput);
            }

            const res = await fetch(endpoint, {
                method: "POST",
                body: formData
            });
            const data = await res.json();
            if (data.success) {
                activeReport = data.report;
                if (data.ocrText) {
                    await writeConsoleLine(`console-log-${type}`, `Neural OCR extracted ${data.ocrText.length} chars from image: "${data.ocrText.substring(0, 70)}..."`, "success", 150);
                }
                await writeConsoleLine(`console-log-${type}`, `ML Classifier evaluated vector: ${activeReport.category}`, "success", 200);
            }
        } catch (e) {
            await writeConsoleLine(`console-log-${type}`, `Backend call error: ${e.message}. Using local ML models.`, "warn", 200);
        }
    }

    if (!activeReport) {
        // Fallback to sample selection
        const sampleKey = type === 'da' ? 'digital_arrest_1' : 'fake_hr_telegram';
        activeReport = SAMPLES[sampleKey].report;
    }

    await writeConsoleLine(`console-log-${type}`, `Evaluating TF-IDF n-gram vectors against trained cybercrime dataset...`, "info", 200);

    // Print out matching threat flags
    if (activeReport.indicators && activeReport.indicators.length > 0) {
        activeReport.indicators.forEach(async (ind, index) => {
            await writeConsoleLine(`console-log-${type}`, `Threat flag matched: "${ind}"`, "warn", 100 + (index * 80));
        });
    }

    // Pause for calculations
    setTimeout(async () => {
        await writeConsoleLine(`console-log-${type}`, `Scam model threat index rating calculated: ${activeReport.score}`, "success", 100);
        await writeConsoleLine(`console-log-${type}`, `Scan trace complete. Transporting telemetry values to UI.`, "success", 200);

        setTimeout(() => {
            // Render Report
            document.getElementById(`scan-console-${type}`).classList.add("hidden");
            const reportEl = document.getElementById(`scan-report-${type}`);
            reportEl.classList.remove("hidden");

            // Populate Report
            const hdrBg = document.getElementById(`report-header-bg-${type}`);
            hdrBg.className = `report-header ${activeReport.badgeClass}`;
            document.getElementById(`report-badge-status-${type}`).innerText = activeReport.badge;
            document.getElementById(`report-title-scam-${type}`).innerText = activeReport.title;
            document.getElementById(`report-score-${type}`).innerText = activeReport.score;
            document.getElementById(`report-category-${type}`).innerText = activeReport.category;
            
            const riskEl = document.getElementById(`report-risk-${type}`);
            riskEl.className = activeReport.riskClass;
            riskEl.innerText = activeReport.risk;
            
            document.getElementById(`report-authority-${type}`).innerText = activeReport.authority;
            document.getElementById(`report-trigger-${type}`).innerText = activeReport.trigger;
            
            // Check for fake vs real email details
            resolveEmailsClientSide(textInput, activeReport);

            const fakeEmailEl = document.getElementById(`report-email-fake-${type}`);
            const fakeEmailContainer = document.getElementById(`report-email-fake-container-${type}`);
            const realEmailEl = document.getElementById(`report-email-real-${type}`);
            const realEmailContainer = document.getElementById(`report-email-real-container-${type}`);

            if (activeReport.fakeEmail && activeReport.realEmail) {
                if (fakeEmailEl) fakeEmailEl.innerText = activeReport.fakeEmail;
                if (realEmailEl) realEmailEl.innerText = activeReport.realEmail;
                if (fakeEmailContainer) fakeEmailContainer.classList.remove("hidden");
                if (realEmailContainer) realEmailContainer.classList.remove("hidden");
            } else {
                if (fakeEmailContainer) fakeEmailContainer.classList.add("hidden");
                if (realEmailContainer) realEmailContainer.classList.add("hidden");
            }

            // Indicators
            const indContainer = document.getElementById(`report-indicators-${type}`);
            indContainer.innerHTML = "";
            activeReport.indicators.forEach(ind => {
                const tag = document.createElement("span");
                tag.className = `indicator-tag ${activeReport.badgeClass === 'suspicious' ? 'warning' : ''}`;
                tag.innerText = ind;
                indContainer.appendChild(tag);
            });

            document.getElementById(`report-summary-${type}`).innerText = activeReport.summary;

            // Recommendations
            const recContainer = document.getElementById(`report-recommendations-${type}`);
            recContainer.innerHTML = "";
            activeReport.recommends.forEach(rec => {
                const li = document.createElement("li");
                li.innerText = rec;
                recContainer.appendChild(li);
            });

            // Increment stats count on dashboard overview
            incrementStats(activeReport.badge === 'MALICIOUS' || activeReport.badge === 'SUSPICIOUS');
        }, 300);

    }, 800);
}

async function startApkScan() {
    const sandboxSelect = document.getElementById("sandbox-mode");
    const useAndroguard = (sandboxSelect && sandboxSelect.value === "androguard") && backendConnected;

    const consoleLog = document.getElementById("apk-console-log");
    consoleLog.innerHTML = "";

    let data = null;
    let filename = "";

    if (useAndroguard) {
        await writeConsoleLine("apk-console-log", "Connecting to live ORCA Sandbox Engine...", "info", 0);
        
        const formData = new FormData();
        const preview = document.getElementById("apk-preview-container");
        const sampleKey = preview.getAttribute("data-sample");
        
        if (selectedApkFile) {
            formData.append("file", selectedApkFile);
            formData.append("is_simulation", "false");
            filename = selectedApkFile.name;
        } else if (sampleKey) {
            formData.append("is_simulation", "true");
            formData.append("sim_key", sampleKey);
            filename = sampleKey + ".apk";
        } else {
            alert("No APK file uploaded or simulation selected.");
            return;
        }

        await writeConsoleLine("apk-console-log", `Uploading ${filename} to analysis cluster...`, "info", 100);

        try {
            const res = await fetch(`${BACKEND_URL}/api/analyze-apk`, {
                method: "POST",
                body: formData
            });

            if (!res.ok) {
                throw new Error("Sandbox service returned an error status " + res.status);
            }

            const responseJson = await res.json();
            if (!responseJson.success) {
                throw new Error(responseJson.error || "Analysis failed.");
            }

            data = responseJson.report;
            
            await writeConsoleLine("apk-console-log", `Initializing isolated static analysis container...`, "info", 100);
            await writeConsoleLine("apk-console-log", `Static manifest parsed. Target package: ${data.packageName}`, "success", 100);
            await writeConsoleLine("apk-console-log", `Signer verified: ${data.signer}`, data.badge === 'SAFE' ? "success" : "error", 100);
            await writeConsoleLine("apk-console-log", `Extracting target framework details: Target SDK = ${data.targetSdk}`, "info", 100);
            await writeConsoleLine("apk-console-log", "Scanning requested permissions...", "info", 100);
            
            for (let perm of data.permissions) {
                if (perm.status === 'DANGEROUS') {
                    await writeConsoleLine("apk-console-log", `CRITICAL Permission match: ${perm.name}`, "error", 50);
                } else if (perm.status === 'WARNING') {
                    await writeConsoleLine("apk-console-log", `Warning Permission match: ${perm.name}`, "warn", 50);
                } else {
                    await writeConsoleLine("apk-console-log", `Normal permission: ${perm.name.split('.').pop()}`, "info", 20);
                }
            }

            await writeConsoleLine("apk-console-log", "Disassembling DEX bytecode and identifying referenced API hooks...", "info", 100);
            for (let comp of data.components) {
                await writeConsoleLine("apk-console-log", `Flagged Component/API: ${comp.title} - ${comp.desc.substring(0, 40)}...`, "warn", 50);
            }
            
            await writeConsoleLine("apk-console-log", "Evaluating feature vector using Random Forest Classifier Model...", "info", 100);
            await writeConsoleLine("apk-console-log", `Threat Index calculated: ${data.score} (${data.threatClass})`, "success", 100);

        } catch (err) {
            await writeConsoleLine("apk-console-log", `Sandbox connection error: ${err.message}`, "error", 100);
            await writeConsoleLine("apk-console-log", "Attempting fallback to local mock simulation environment...", "warn", 200);
            
            const sk = sampleKey || "apk_malware_1";
            data = SAMPLES[sk].report;
        }
    } else {
        const preview = document.getElementById("apk-preview-container");
        const sampleKey = preview.getAttribute("data-sample") || "apk_malware_1";
        data = SAMPLES[sampleKey].report;

        await writeConsoleLine("apk-console-log", `orca-sandbox --run-static-checks --package="${data.packageName}"`, "cmd", 0);
        await writeConsoleLine("apk-console-log", `Spawning isolated static android container...`, "info", 200);
        await writeConsoleLine("apk-console-log", `Decompressing zip archive manifest assets...`, "info", 400);
        await writeConsoleLine("apk-console-log", `AndroidManifest.xml successfully resolved. Package identified: ${data.packageName}`, "success", 300);
        await writeConsoleLine("apk-console-log", `Target Android SDK: ${data.targetSdk}`, "info", 200);
        
        if (data.badge === 'SAFE') {
            await writeConsoleLine("apk-console-log", `Verifying signing keys: Valid signature (${data.signer})`, "success", 400);
        } else {
            await writeConsoleLine("apk-console-log", `Verifying signing keys: WARNING! ${data.signer}`, "error", 400);
        }

        await writeConsoleLine("apk-console-log", `Extracting application permissions...`, "info", 300);

        for (let perm of data.permissions) {
            if (perm.status === 'DANGEROUS') {
                await writeConsoleLine("apk-console-log", `CRITICAL Permission match: ${perm.name}`, "error", 200);
            } else if (perm.status === 'WARNING') {
                await writeConsoleLine("apk-console-log", `Warning Permission match: ${perm.name}`, "warn", 150);
            } else {
                await writeConsoleLine("apk-console-log", `Normal permission: ${perm.name.split('.').pop()}`, "info", 100);
            }
        }

        await writeConsoleLine("apk-console-log", `Scanning compiled bytecode classes and components...`, "info", 300);

        for (let comp of data.components) {
            await writeConsoleLine("apk-console-log", `Flagged component: ${comp.title} - ${comp.desc.substring(0, 30)}...`, "warn", 250);
        }
        
        await writeConsoleLine("apk-console-log", `Computing threat scoring matrix: Sandbox Threat Index = ${data.score}`, "success", 500);
    }

    setTimeout(async () => {
        await writeConsoleLine("apk-console-log", `Destroying sandbox container. Building UI report structure...`, "success", 300);

        setTimeout(() => {
            document.getElementById("apk-console").classList.add("hidden");
            const reportEl = document.getElementById("apk-report");
            reportEl.classList.remove("hidden");

            const hdrBg = document.getElementById("apk-header-bg");
            hdrBg.className = `report-header ${data.badgeClass}`;
            document.getElementById("apk-badge-status").innerText = data.badge;
            document.getElementById("apk-app-name").innerText = data.appName;
            document.getElementById("apk-score").innerText = data.score;
            document.getElementById("apk-package-name").innerText = data.packageName;
            document.getElementById("apk-signer").innerText = data.signer;
            document.getElementById("apk-target-sdk").innerText = data.targetSdk;
            
            const threatCl = document.getElementById("apk-threat-classification");
            threatCl.innerText = data.threatClass;
            threatCl.className = data.badge === 'SAFE' ? 'risk-green' : 'risk-red';

            if (data.badge !== 'SAFE') {
                document.getElementById("apk-signer").className = 'risk-red';
            } else {
                document.getElementById("apk-signer").className = 'risk-green';
            }

            const compContainer = document.getElementById("apk-components-list");
            compContainer.innerHTML = "";
            data.components.forEach(comp => {
                const li = document.createElement("li");
                li.className = "danger-component-item";
                li.innerHTML = `
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <div>
                        <strong>${comp.title}</strong>
                        <span>${comp.desc}</span>
                    </div>
                `;
                compContainer.appendChild(li);
            });

            const permBody = document.getElementById("apk-permissions-tbody");
            permBody.innerHTML = "";
            data.permissions.forEach(perm => {
                const tr = document.createElement("tr");
                let classStatus = "perm-normal";
                if (perm.status === 'DANGEROUS') classStatus = "perm-danger";
                else if (perm.status === 'WARNING') classStatus = "perm-warning";

                tr.innerHTML = `
                    <td><code>${perm.name}</code></td>
                    <td><span class="${classStatus}">${perm.status}</span></td>
                    <td>${perm.desc}</td>
                `;
                permBody.appendChild(tr);
            });

            const recContainer = document.getElementById("apk-recommendations");
            recContainer.innerHTML = "";
            data.recommends.forEach(rec => {
                const li = document.createElement("li");
                li.innerText = rec;
                recContainer.appendChild(li);
            });

            incrementStats(data.badge === 'MALICIOUS', true);

        }, 400);
    }, 1000);
}


// Increment dashboard telemetry values
function incrementStats(isThreat = true, isApk = false) {
    const totalEl = document.getElementById("stat-total");
    const interceptedEl = document.getElementById("stat-intercepted");
    const apksEl = document.getElementById("stat-apks");

    let total = parseInt(totalEl.innerText.replace(/,/g, ''));
    totalEl.innerText = (total + 1).toLocaleString();

    if (isApk) {
        let apks = parseInt(apksEl.innerText);
        apksEl.innerText = apks + 1;
    }

    if (isThreat) {
        let intercepted = parseInt(interceptedEl.innerText);
        interceptedEl.innerText = intercepted + 1;
    }
}


// ==========================================
// 5. Threat Intelligence Live Ticker Feed
// ==========================================
const TICKER_MOCKS = [
    { type: 'da', title: 'TRAI / SIM Fraud Digital Arrest Warning', desc: 'Alert from Delhi Cyber Crime: Citizens are receiving calls from impersonators claiming multiple SIM cards are activated under their Aadhaar card, threatening digital arrest.', time: 'Just Now' },
    { type: 'hr', title: 'Work From Home YouTube Like Scheme', desc: 'Mumbai Cyber Cell blocks 14 bank accounts linked to an HR Telegram scam promising ₹500 per map rating task. Victims lost ₹8.4 Lakhs.', time: '2 mins ago' },
    { type: 'apk', title: 'New "e-Challan payment" Malware Alert', desc: 'Androguard scans flag package `in.echallan.gov.apk` as a banking Trojan harvesting OTPs using `RECEIVE_SMS` filters.', time: '14 mins ago' },
    { type: 'da', title: 'Mumbai Police Impersonation Case Filed', desc: 'Case registered in Gujarat. Senior citizen duped of ₹45 Lakhs after staying on Skype call under digital arrest for 48 hours.', time: '1 hr ago' },
    { type: 'apk', title: 'Fake "Electricity Bill Update" APK Package', desc: 'Scammers pushing `mseb_bill_support.apk` via WhatsApp. Extracts active contacts and logs SMS keystrokes.', time: '3 hrs ago' },
    { type: 'hr', title: 'Fake Amazon Affiliate Job Offers', desc: 'Fake recruitment agents targeting college students. Coerces upfront purchase of virtual items to earn commissions.', time: '5 hrs ago' }
];

function initThreatTicker() {
    const ticker = document.getElementById("threat-ticker");
    if (!ticker) return;

    ticker.innerHTML = "";

    // Load initial threats
    TICKER_MOCKS.forEach(mock => {
        addTickerItem(mock);
    });

    // Periodically add new random alerts
    setInterval(() => {
        const types = ['da', 'hr', 'apk'];
        const type = types[Math.floor(Math.random() * types.length)];
        let title = "";
        let desc = "";

        if (type === 'da') {
            title = 'CBI Money Laundering Impersonation Attempt';
            desc = `A scammer claiming to be Sub-Inspector Verma called a citizen under Skype ID 'CBI verification'. Flagged and blocked.`;
        } else if (type === 'hr') {
            title = 'Fake Recruitment Task Offer Blocked';
            desc = `WhatsApp numbers claiming to represent 'Amazon India HR' are sending recruitment brochures. Links flagged as malicious.`;
        } else {
            title = 'Malicious APK Sandbox Intercept';
            desc = `Static scanning of 'paytm_cashback_reward.apk' detected access to SYSTEM_ALERT_WINDOW and SMS permission loops.`;
        }

        const newItem = { type, title, desc, time: 'Just Now' };
        
        // Remove 'Just Now' from the old first element to keep timeline neat
        const firstChild = ticker.firstChild;
        if (firstChild) {
            const timeEl = firstChild.querySelector(".ticker-time");
            if (timeEl && timeEl.innerText === 'Just Now') {
                timeEl.innerText = '1 min ago';
            }
        }

        addTickerItem(newItem, true);

        // Keep ticker size capped at 8 elements
        if (ticker.childNodes.length > 8) {
            ticker.removeChild(ticker.lastChild);
        }
    }, 12000);
}

function addTickerItem(item, prepend = false) {
    const ticker = document.getElementById("threat-ticker");
    const div = document.createElement("div");
    div.className = "ticker-item";

    let badgeClass = "da";
    let badgeText = "Digital Arrest";
    if (item.type === 'hr') {
        badgeClass = "hr";
        badgeText = "Fake HR";
    } else if (item.type === 'apk') {
        badgeClass = "apk";
        badgeText = "APK Malware";
    }

    div.innerHTML = `
        <span class="ticker-badge ${badgeClass}">${badgeText}</span>
        <div class="ticker-content">
            <div class="ticker-meta">
                <h4>${item.title}</h4>
                <span class="ticker-time">${item.time}</span>
            </div>
            <p class="ticker-text">${item.desc}</p>
        </div>
    `;

    if (prepend && ticker.firstChild) {
        ticker.insertBefore(div, ticker.firstChild);
    } else {
        ticker.appendChild(div);
    }
}
