// ORCA Scam Shield App Logic

document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initDragAndDrop();
    initThreatTicker();
});

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
    fake_hr_1: {
        text: `Hello, this is Ms. Neha Sharma, HR recruiter from Global Media Corp. We have reviewed your profile and are happy to offer you a part-time Work-From-Home vacancy. The job is extremely simple: you just need to like YouTube videos, rate tourist spots on Google Maps, and submit screenshots to our group coordinator. You can easily earn ₹3000 to ₹8000 daily. We will start with a trial package. We have credited ₹150 directly to your UPI ID for your first task. Please click this link: t.me/global_mediacorp_vip to register on our VIP portal and unlock high-yield tasks. No experience required.`,
        report: {
            title: "Fake Recruitment Scam",
            category: "Fake Recruitment (Telegram Task Scam)",
            risk: "High Risk",
            riskClass: "risk-orange",
            badge: "SUSPICIOUS",
            badgeClass: "suspicious",
            authority: "Impersonating Media Agencies (Global Media Corp)",
            trigger: "Task Compensation Phishing",
            score: "78%",
            indicators: ["earn ₹3000 to ₹8000 daily", "like YouTube videos", "HR recruiter", "UPI ID", "VIP portal", "t.me/global_mediacorp_vip"],
            summary: "The content matches the footprint of a Telegram task-based financial scam. It begins with tiny payouts (Rs 150) to build trust, followed by coercion to join VIP channels where victims are duped into sending large deposits to fake cryptocurrency portals under the guise of 'welfare tasks.'",
            recommends: [
                "Do NOT join the Telegram link or register on unverified crypto portals.",
                "Be highly skeptical of job offers that pay high salaries for trivial tasks like liking videos.",
                "Do NOT send any advance deposits or payments for upgrading job levels.",
                "Report the UPI ID and mobile number to your bank to freeze potential money mule channels."
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

async function startTextMediaScan(type) {
    const textInput = document.getElementById(`text-input-${type}`).value.trim();
    const hasFile = type === 'da' ? selectedMediaFileDa : selectedMediaFileHr;
    if (!textInput && !hasFile) {
        alert("Please paste some text content or drop a screenshot file to scan.");
        return;
    }

    const consoleLog = document.getElementById(`console-log-${type}`);
    consoleLog.innerHTML = ""; // Clear placeholder
    
    // Identify if the input text matches any pattern
    const activeReport = type === 'da' ? SAMPLES.digital_arrest_1.report : SAMPLES.fake_hr_1.report;

    await writeConsoleLine(`console-log-${type}`, `orca-scanner --analyze-${type}`, "cmd", 0);
    await writeConsoleLine(`console-log-${type}`, "Initializing AI Threat Engine connection...", "info", 300);
    
    if (hasFile) {
        await writeConsoleLine(`console-log-${type}`, `Processing uploaded file payload: ${hasFile.name}`, "info", 400);
        await writeConsoleLine(`console-log-${type}`, `Simulating optical character recognition (OCR) on canvas nodes...`, "info", 500);
        await writeConsoleLine(`console-log-${type}`, `OCR parsed block: "${textInput ? textInput.substring(0,60) + '...' : 'Extracted text content from screenshot image'}..."`, "success", 600);
    } else {
        await writeConsoleLine(`console-log-${type}`, `Parsing raw message text stream... (${textInput.length} chars)`, "info", 200);
    }

    await writeConsoleLine(`console-log-${type}`, `Running context scoring vector via LLM prompting...`, "info", 400);
    await writeConsoleLine(`console-log-${type}`, `Scanning text signatures matching cybercrime CSV repositories...`, "info", 300);

    // Print out matching threat flags
    activeReport.indicators.forEach(async (ind, index) => {
        await writeConsoleLine(`console-log-${type}`, `Threat flag matched: "${ind}"`, "warn", 200 + (index * 100));
    });

    // Pause for calculations
    setTimeout(async () => {
        await writeConsoleLine(`console-log-${type}`, `Scam model threat index rating calculated: ${activeReport.score}`, "success", 100);
        await writeConsoleLine(`console-log-${type}`, `Scan trace complete. Transporting telemetry values to UI.`, "success", 300);

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
            incrementStats(activeReport.badge === 'MALICIOUS');
        }, 600);

    }, 1500);
}

async function startApkScan() {
    const preview = document.getElementById("apk-preview-container");
    const sampleKey = preview.getAttribute("data-sample") || "apk_malware_1";
    const data = SAMPLES[sampleKey].report;

    const consoleLog = document.getElementById("apk-console-log");
    consoleLog.innerHTML = "";

    await writeConsoleLine("apk-console-log", `orca-sandbox --run-static-checks --package="${data.packageName}"`, "cmd", 0);
    await writeConsoleLine("apk-console-log", `Spawning isolated static android container...`, "info", 200);
    await writeConsoleLine("apk-console-log", `Decompressing zip archive manifest assets...`, "info", 400);
    await writeConsoleLine("apk-console-log", `AndroidManifest.xml successfully resolved. Package identified: ${data.packageName}`, "success", 300);
    await writeConsoleLine("apk-console-log", `Target Android SDK: ${data.targetSdk}`, "info", 200);
    
    // Developer signing certificate check
    if (data.badge === 'SAFE') {
        await writeConsoleLine("apk-console-log", `Verifying signing keys: Valid signature (${data.signer})`, "success", 400);
    } else {
        await writeConsoleLine("apk-console-log", `Verifying signing keys: WARNING! ${data.signer}`, "error", 400);
    }

    await writeConsoleLine("apk-console-log", `Extracting application permissions...`, "info", 300);

    // Permission logging
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

    // Components logging
    for (let comp of data.components) {
        await writeConsoleLine("apk-console-log", `Flagged component: ${comp.title} - ${comp.desc.substring(0, 30)}...`, "warn", 250);
    }

    setTimeout(async () => {
        await writeConsoleLine("apk-console-log", `Computing threat scoring matrix: Sandbox Threat Index = ${data.score}`, "success", 100);
        await writeConsoleLine("apk-console-log", `Destroying sandbox container. Building UI report structure...`, "success", 400);

        setTimeout(() => {
            // Render Report
            document.getElementById("apk-console").classList.add("hidden");
            const reportEl = document.getElementById("apk-report");
            reportEl.classList.remove("hidden");

            // Populate Report
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

            // Components List
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

            // Permissions Table
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

            // Recommendations
            const recContainer = document.getElementById("apk-recommendations");
            recContainer.innerHTML = "";
            data.recommends.forEach(rec => {
                const li = document.createElement("li");
                li.innerText = rec;
                recContainer.appendChild(li);
            });

            // Increment stats count on dashboard overview
            incrementStats(data.badge === 'MALICIOUS', true);

        }, 600);
    }, 2000);
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
