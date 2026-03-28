# StudyTrack AI — Complete Setup Guide
## AI-Based Study Progress Tracker & Student Assistant

---

## 📁 Project Structure

```
study_tracker/
├── app.py                    ← Flask backend (main file)
├── requirements.txt          ← Python dependencies
├── study_tracker.db          ← SQLite database (auto-created)
│
├── static/
│   ├── css/
│   │   └── style.css         ← All styles (dark/light mode)
│   └── js/
│       ├── main.js           ← Theme, modals, sidebar, timer
│       ├── charts.js         ← Chart.js dashboard charts
│       └── chatbot.js        ← Chat UI logic
│
├── templates/
│   ├── base.html             ← Shared layout + sidebar
│   ├── login.html            ← Login page
│   ├── signup.html           ← Sign up page
│   ├── dashboard.html        ← Main dashboard + charts
│   ├── subjects.html         ← Subject manager
│   ├── tasks.html            ← Task manager
│   ├── notes.html            ← Notes manager
│   └── chatbot.html          ← AI chatbot interface
│
└── android/
    ├── MainActivity.java     ← Android WebView activity
    ├── activity_main.xml     ← Android layout
    └── AndroidManifest.xml   ← App permissions & config
```

---

## 🖥️ HOW TO RUN ON LAPTOP (Windows/Linux/Mac)

### Step 1: Install Python 3
Download from https://python.org (version 3.9 or later)

### Step 2: Navigate to project folder
```bash
cd path/to/study_tracker
```

### Step 3: Create a virtual environment (recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 4: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Run the app
```bash
python app.py
```

### Step 6: Open in browser
```
http://127.0.0.1:5000
```

Sign up → sample data is added automatically!

---

## 📱 HOW TO RUN ON TERMUX (Android Phone)

Termux lets you run Flask directly on your phone.

### Step 1: Install Termux
Download from F-Droid (NOT Play Store — it's outdated):
https://f-droid.org/packages/com.termux/

### Step 2: Update packages
```bash
pkg update && pkg upgrade
```

### Step 3: Install Python
```bash
pkg install python
```

### Step 4: Install pip packages
```bash
pip install flask werkzeug
```

### Step 5: Copy project files to Termux
Method 1: USB cable → copy to /sdcard → mv to ~/
Method 2: Git clone if hosted on GitHub
```bash
# From Termux:
cp -r /sdcard/study_tracker ~/
cd ~/study_tracker
```

### Step 6: Run the app
```bash
python app.py
```

### Step 7: Open in phone browser
```
http://localhost:5000
```

Or from another device on same Wi-Fi:
```
http://<phone-ip>:5000
```
Find your phone IP with: `ip addr show wlan0`

---

## 🤖 ANDROID APP SETUP (WebView)

### Prerequisites
- Android Studio (download from developer.android.com)
- Java JDK 11 or later

### Step 1: Create new Android project
- Open Android Studio
- New Project → Empty Activity
- Package name: `com.studytrack.app`
- Language: Java
- Min SDK: API 21 (Android 5.0)

### Step 2: Replace files
Copy these files into your Android project:

| File in android/ folder       | Destination in Android Studio         |
|-------------------------------|---------------------------------------|
| MainActivity.java             | app/src/main/java/com/studytrack/app/ |
| activity_main.xml             | app/src/main/res/layout/             |
| AndroidManifest.xml           | app/src/main/                         |

### Step 3: Set the IP address
Open `MainActivity.java` and update line:
```java
private static final String WEB_APP_URL = "http://192.168.1.10:5000";
```

Replace `192.168.1.10` with your PC's local IP address.

**Find your PC's IP:**
- Windows: Open CMD → `ipconfig` → look for "IPv4 Address"
- Linux:  `ip a` → look for `inet` under `wlan0` or `eth0`

### Step 4: Add AppCompat dependency
In `app/build.gradle`, add to `dependencies {}`:
```gradle
implementation 'androidx.appcompat:appcompat:1.6.1'
```

### Step 5: Run the app
1. Make sure Flask is running on your PC
2. Connect phone via USB or use Android Emulator
3. Click ▶ Run in Android Studio
4. App opens and loads your Flask app!

---

## ✨ FEATURES OVERVIEW

| Feature                  | Description                                         |
|--------------------------|-----------------------------------------------------|
| 🔐 Authentication        | Signup/Login with hashed passwords (werkzeug)       |
| 📚 Subjects              | Add subjects with color labels, view progress       |
| ✅ Tasks                 | Add/edit/delete with deadlines, mark complete       |
| 📝 Notes                 | Markdown-friendly notes linked to subjects          |
| 📊 Dashboard             | Charts (doughnut + bar), stats, streak badge        |
| 🤖 AI Chatbot            | Rule-based assistant with 8 response categories     |
| 🔥 Streak Tracker        | Tracks consecutive study days                       |
| ⏱️ Pomodoro Timer        | Built-in 25/10/5 min study timer with logging       |
| 🌙 Dark/Light Mode       | Toggle button, preference saved in localStorage     |
| 📱 Responsive            | Works on mobile, tablet, and desktop                |

---

## 🚀 FUTURE IMPROVEMENTS

1. **Push notifications** — remind users of upcoming deadlines
2. **Cloud sync** — use PostgreSQL + deploy on Render/Railway
3. **AI with GPT API** — replace rule-based chatbot with real AI
4. **PDF export** — export notes as PDF
5. **Collaborative study** — share subjects/tasks with classmates
6. **Spaced repetition** — flashcard system for notes
7. **Google Calendar sync** — import/export deadlines
8. **Progressive Web App (PWA)** — installable without Android Studio

---

## 🛠️ TECH STACK SUMMARY

| Layer     | Technology        |
|-----------|-------------------|
| Frontend  | HTML5, CSS3, JS   |
| Fonts     | Syne + DM Sans    |
| Charts    | Chart.js 4.4      |
| Backend   | Python Flask 3.0  |
| Database  | SQLite (built-in) |
| Auth      | werkzeug hashing  |
| Android   | Java + WebView    |

---

Made with ❤️ for B.Tech college project submission.
