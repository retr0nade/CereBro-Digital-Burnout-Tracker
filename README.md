# 🧠 CereBro – Advanced Digital Burnout Tracker

**Digital wellness, redefined.**  
A privacy-first Chrome extension that analyzes your browsing, focus, and behavioral patterns to surface actionable insights—and prevent digital burnout.

---

## 🚀 Features

- **Session-long tracking** – Stats persist until browser/extension is restarted.
- **All major digital wellness metrics:**
  - ⏱️ Time spent per tab
  - 🔄 Tab switch frequency
  - ⚡ Erratic/rapid clicking (“stress signals”)
  - 🔁 YouTube repeat/binge detection
  - 💨 Scroll bursts & inactivity tracking
  - ⌨️ Typing bursts and idle detection
  - 📱 New tabs/min
  - 🔄 Rapid URL navigation within the same tab
  - 🔁 Repeated visits to same site
  - 🟢 Focus vs distraction site time rolls up with live “focus bar”
- **Animated, ultra-modern popup UI with real-time stats and visualizations**
- **Local-only privacy:** All metrics are processed and retained on your device; nothing leaves your PC unless explicitly sent to your own backend or desktop app.


---

## ⚡ Installation

1. **Clone/Download this Repository**

git clone https://github.com/yourusername/burnout-tracker-extension.git
cd burnout-tracker-extension


2. **Load Unpacked in Chrome**
- Go to `chrome://extensions`
- Enable “Developer mode”
- Click **Load unpacked** and select this project folder.

3. **[Optional] Run Your Local Server**
- If using the desktop Python app/server: Start your Flask/API backend (see below).

---

## 🔧 Project Structure

```bash
burnout-tracker-extension/
├── manifest.json
├── background.js
├── content.js
├── popup.html
├── popup.js
├── popup.css
├── icons/
│ ├── icon16.png
│ ├── icon48.png
│ └── icon128.png
└── README.md
```


---

## 📝 Usage

- Open the extension popup from the Chrome toolbar to view your real-time wellness dashboard.
- All statistics are persistently tracked.
- Connect to your desktop “wellness server” (e.g., Python/Flask on `localhost:5005`) for advanced analytics/reports.
- **No stats are reset mid-session**—metrics accumulate until Chrome or the extension is restarted.

---

## 🛡️ Permissions & Privacy

- **Tab, storage, and navigation permissions** are used _only_ for on-device analytics.
- _No browsing content is ever uploaded unless you connect your own desktop analytics server._
- **Reset**: Stats clear only on browser/extension reload. Manual data export/delete can be added as needed.

---

## 🛠️ Backend/Desktop Integration (Optional)

If you want persistent, historical stats beyond your Chrome session, use the [provided Flask+SQLite desktop app](docs/desktop-integration.md) or build your own.  
The extension POSTs all data to `http://localhost:5005/api/track` every 5 seconds by default.

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

---

## 🌱 Credits

- UI inspired by modern productivity apps and burnout-aware design
- All code MIT licensed—use, fork, contribute, or remix as you wish!

---

## ☎️ Questions?

Open an issue or discussion on this repo—or just [contact me](mailto:your.email@example.com) if you have suggestions or want to help improve burnout tracking for everyone.
