
# 🧠 CereBro – Mental Burnout Tracker

**CereBro** is a two-part digital wellness tool that helps detect early signs of burnout by tracking user activity, both in the browser and on the desktop.

It consists of:

- A **Chrome Extension** for real-time browser behavior monitoring.
- A **Desktop App** for logging, analytics, and deeper insights.

---

## ✅ Current Features

### 🌐 Chrome Extension

Tracks browser-based behavioral patterns in real time:

- **Time spent per tab** with cumulative totals
- **Tab switches** and tab-switch frequency counter
- **YouTube activity monitoring** (detects loops and binge sessions)
- **Click behavior analysis** (erratic or rapid clicking detection)
- **Inactivity detection** (based on scroll, clicks, and typing)
- **Focus meter** that visualizes active focus vs distraction
- **Live dashboard** in the popup UI with:
  - Real-time metrics
  - Focus time animation
  - Stats breakdown by tab and category

All data is stored locally in the browser and never leaves the user’s device.

---

### 💻 Desktop App

Runs a local Python Flask server to receive and store metrics:

- Accepts POST requests from the extension
- Saves all activity data into a unified SQLite database (`cerebro.db`)
- Provides endpoints for querying historical usage
- Base Flask + SQLite stack (no external dependencies)

This allows long-term storage and future analytics that go beyond the browser session.

---

## 🔧 Ongoing Developments

The following features are actively being worked on:

### 🧠 Desktop Analytics & Insights
- **Daily/weekly usage summaries**
- **Trend visualizations** for focus, distraction, and stress signals
- **Idle time vs active time analytics**
- **Multi-app tracking support** (combine browser + PC data)

### 🤖 AI-Powered Features
- AI model to provide **personalized mental wellness insights**
- Detection of **burnout risk** based on patterns
- **Adaptive interventions** like:
  - Focus reminders
  - Break suggestions
  - Customizable nudges based on behavior

### 🌐 Cross-App Awareness
- Tracking of **desktop application usage** alongside browser behavior
- Unified analytics across all digital activities
- Plans for full integration with PC activity monitor (e.g., active window logging, app usage time)

### 🛠️ Other Planned Improvements
- Toggle between **light/dark themes** in the popup UI
- Export usage reports as CSV/PDF
- Configurable thresholds for alerting user
- Backend plugin system for custom AI modules

---

## 🚀 Getting Started

### 1. Chrome Extension

- Go to `chrome://extensions`
- Enable “Developer Mode”
- Click **Load unpacked** and select the `burnout-tracker-extension` folder

### 2. Desktop App (Optional but Recommended)

#### Install Dependencies

Choose the appropriate requirements file for your operating system:

**Windows:**
```bash
cd desktop-app/backend
pip install -r requirements-windows.txt
```

**macOS:**
```bash
cd desktop-app/backend
pip install -r requirements-macos.txt
```

**Linux:**
```bash
cd desktop-app/backend
pip install -r requirements-linux.txt
```

#### Run the Application

```bash
python app_service.py
```

Runs locally at: `http://localhost:5005`

The extension will start sending browser metrics to this endpoint automatically.

---

## 📂 Folder Structure

```
desktop-app/
├── backend/
│   ├── app_service.py      # Main Python daemon/server
│   ├── cerebro.db          # Unified SQLite database for all metrics
│   ├── cerebro_db.py       # Database interface and schema
│   ├── migrate_old_data.py # Migration script for legacy data
│   ├── metrics/
│   │   ├── apps.py         # Active app/window monitor (cross-plat)
│   │   ├── idle.py         # Idle time tracking
│   │   ├── input.py        # Keyboard/mouse event hooks
│   │   ├── screen.py       # Screen time, brightness, screenshot
│   │   ├── audio.py        # Audio level (microphone)
│   │   └── util.py         # Utility functions
│   ├── data/
│   │   └── models.py       # Legacy SQLite DB schemas (deprecated)
│   ├── api/
│   │   └── routes.py       # Flask/FastAPI with all endpoints
│   ├── settings.json       # Default/active user preferences
│   └── requirements.txt
├── src-tauri/
│   └── (Tauri config and rust backend bridge)
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── Preferences.tsx
│   │   ├── Dashboard.tsx
│   │   ├── ScreenTime.tsx
│   │   ├── MetricsCard.tsx
│   │   ├── FocusBar.tsx
│   │   └── ... (other components)
│   ├── tailwind.config.js
│   └── ...
├── README.md
└── (other auxiliary files)
extension/
├── manifest.json
├── background.js
├── content.js
├── popup.html
├── popup.js
└── icons/


```

---

## 🗄️ Unified Database Structure

The application now uses a single unified SQLite database (`cerebro.db`) that contains all tracking data:

### Database Tables

1. **app_usage** - Application and window usage tracking
   - `id`, `app_name`, `start_time`, `end_time`, `duration`

2. **idle_periods** - User inactivity periods
   - `id`, `start_time`, `end_time`, `duration`

3. **input_activity** - Keyboard and mouse activity
   - `id`, `timestamp`, `keypress_count`, `mouse_click_count`

4. **focus_sessions** - Focus timer sessions
   - `id`, `start_time`, `end_time`, `was_interrupted`, `duration`

5. **breaks** - Break periods and types
   - `id`, `start_time`, `end_time`, `type`

6. **browser_activity** - Browser tab and domain activity
   - `id`, `domain`, `url`, `start_time`, `end_time`, `duration`

### Migration

The `migrate_old_data.py` script automatically imports data from legacy database files into the unified structure. All trackers have been updated to use the new unified database interface.

---

## 🧩 Adding More Metrics

Want to track more?  
Extend `content.js` and `background.js` using the same `chrome.runtime.sendMessage` → `chrome.storage.local` patterns.  
Ex: track site types, form fill behaviors, social media reactions, or page “rage clicks”.

---

## 👀 Customizing the UI

- All UI styles are in `popup.css`.
- Animated SVG, grid layout, and metrics display are all in `popup.html` and `popup.js`.
- Switch out icons, add new metrics, or reskin with your color scheme!

---

## 🚨 Troubleshooting

- **Popup not syncing/stats missing?**  
  Reload the extension and Chrome. Ensure your background and content scripts have no console errors in `chrome://extensions`.
- **Communication errors?**  
  [Read these tips »](https://developer.chrome.com/docs/extensions/mv3/messaging/)
- **No data sent to desktop app?**  
  Make sure your local server is running and accessible at `http://localhost:5005`.
- **Installation issues?**  
  Make sure you're using the correct requirements file for your operating system. The original `requirements.txt` includes all dependencies for all platforms, but platform-specific files are recommended for cleaner installations.


---

## 🛡 Privacy First

CereBro is **fully local** by design.

- No data is ever uploaded or synced externally
- All analytics run on-device
- Extension uses only browser storage and local HTTP

---

## 💬 Contact & Contributions

This is an evolving project. Contributions, feedback, and forks are welcome.

Feel free to open an issue

---

MIT License • Built with focus, for your focus.
