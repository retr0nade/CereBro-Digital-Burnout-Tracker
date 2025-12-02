// == SITE CATEGORY CONFIG ==
const siteCategories = {
  "leetcode.com": "focus",
  "github.com": "focus",
  "youtube.com": "distraction",
  "twitter.com": "distraction"
  // ...add more as you wish
};

// == STATE MANAGEMENT ==
// In-memory cache of state, populated on startup
let state = {
  activeTabs: {},
  lastTabId: null,
};

function getDomain(url) {
  try { return new URL(url).hostname; } catch { return "unknown"; }
}
function now() { return Date.now(); }

// Load state on startup
async function loadState() {
  try {
    const data = await chrome.storage.local.get(['activeTabs', 'lastTabId']);
    if (data.activeTabs) state.activeTabs = data.activeTabs;
    if (data.lastTabId) state.lastTabId = data.lastTabId;
    console.log("State loaded:", state);
  } catch (e) {
    console.error("Failed to load state:", e);
  }
}

// Save state helper
function saveState() {
  chrome.storage.local.set({
    activeTabs: state.activeTabs,
    lastTabId: state.lastTabId
  });
}

// Initialize
loadState();

// == ALARMS (KEEP ALIVE & SYNC) ==
// Create alarm for periodic sync (approx every 5 seconds)
chrome.alarms.create("syncLoop", { periodInMinutes: 0.083 });

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "syncLoop") {
    syncData();
  }
});

// == SESSION STORAGE RESET ONLY ON EXTENSION INSTALL ==
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    tabSwitches: 0,
    erraticClicks: [],
    ytLoops: [],
    tabOpenTimes: [],
    navHistory: {},
    siteVisitHistory: {},
    siteCategoryStats: { focus: 0, distraction: 0, other: 0 },
    activeTabs: {},
    lastTabId: null
  });
  state.activeTabs = {};
  state.lastTabId = null;
});

// == CORE TAB TIME & CATEGORY LOGIC ==
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  // Ensure state is loaded
  if (!state.activeTabs) await loadState();

  const t = now();
  if (state.lastTabId !== null && state.activeTabs[state.lastTabId]) {
    const dt = t - state.activeTabs[state.lastTabId].start;
    state.activeTabs[state.lastTabId].total += dt;
    categorize(state.activeTabs[state.lastTabId].domain, dt);
  }

  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    const url = tab.url || "about:blank";
    const domain = getDomain(url);

    if (!state.activeTabs[activeInfo.tabId]) {
      state.activeTabs[activeInfo.tabId] = { start: t, domain, total: 0 };
    }
    state.activeTabs[activeInfo.tabId].start = t;
    state.lastTabId = activeInfo.tabId;

    saveState();

    // Increment tab switches
    chrome.storage.local.get({ tabSwitches: 0 }, data => {
      chrome.storage.local.set({ tabSwitches: data.tabSwitches + 1 });
    });
  } catch (e) {
    // Tab might be closed or inaccessible
    console.log("Tab access error:", e);
  }
});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete") {
    if (!state.activeTabs) await loadState();

    const url = tab.url || "about:blank";
    const domain = getDomain(url);

    // Update active tab info
    state.activeTabs[tabId] = {
      start: now(),
      domain,
      total: state.activeTabs[tabId]?.total || 0
    };
    saveState();

    // --- Repeated visits ---
    chrome.storage.local.get({ siteVisitHistory: {} }, data => {
      let visitHistory = data.siteVisitHistory;
      if (!visitHistory[domain]) visitHistory[domain] = [];
      visitHistory[domain].push(now());
      visitHistory[domain] = visitHistory[domain].filter(ts => now() - ts < 600000);
      chrome.storage.local.set({ siteVisitHistory: visitHistory });

      if (visitHistory[domain].length >= 5) {
        chrome.runtime.sendMessage({
          type: "repeatSite",
          domain,
          count: visitHistory[domain].length
        }).catch(() => { });
      }
    });
  }
});

chrome.tabs.onRemoved.addListener(async (tabId) => {
  if (!state.activeTabs) await loadState();

  if (state.activeTabs[tabId]) {
    const t = now();
    const dt = t - state.activeTabs[tabId].start;
    state.activeTabs[tabId].total += dt;
    categorize(state.activeTabs[tabId].domain, dt);

    delete state.activeTabs[tabId];
    if (state.lastTabId === tabId) state.lastTabId = null;

    saveState();
  }
});

// == CATEGORIZE DOMAIN TIME ==
function categorize(domain, ms) {
  chrome.storage.local.get({ siteCategoryStats: { focus: 0, distraction: 0, other: 0 } }, data => {
    const cat = siteCategories[domain] || "other";
    let stats = { ...data.siteCategoryStats };
    stats[cat] = (stats[cat] || 0) + ms;
    chrome.storage.local.set({ siteCategoryStats: stats });
  });
}

// == NEW TAB OPEN FREQUENCY ==
chrome.tabs.onCreated.addListener(tab => {
  chrome.storage.local.get({ tabOpenTimes: [] }, data => {
    let times = data.tabOpenTimes;
    times.push(now());
    times = times.filter(ts => now() - ts < 60000);
    chrome.storage.local.set({ tabOpenTimes: times });
  });
});

// == RAPID NAVIGATION (webNavigation permission!) ==
chrome.webNavigation.onCommitted.addListener(details => {
  chrome.storage.local.get({ navHistory: {} }, data => {
    let nh = data.navHistory;
    if (!nh[details.tabId]) nh[details.tabId] = [];
    nh[details.tabId].push({ url: details.url, ts: now() });
    nh[details.tabId] = nh[details.tabId].filter(h => now() - h.ts < 30000);
    chrome.storage.local.set({ navHistory: nh });
    if (nh[details.tabId].length > 3) {
      chrome.runtime.sendMessage({
        type: "rapidNav",
        tabId: details.tabId,
        urls: nh[details.tabId].map(h => h.url)
      }).catch(() => { });
    }
  });
});

// == INCOMING CONTENT EVENTS, ALL PERSISTENT ==
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "erraticClick") {
    chrome.storage.local.get({ erraticClicks: [] }, data => {
      let arr = data.erraticClicks;
      arr.push({ url: msg.url, time: now() });
      chrome.storage.local.set({ erraticClicks: arr });
    });
  }
  if (msg.type === "ytLoop") {
    chrome.storage.local.get({ ytLoops: [] }, data => {
      let arr = data.ytLoops;
      arr.push({ url: msg.url, time: now() });
      chrome.storage.local.set({ ytLoops: arr });
    });
  }
  if (msg.type === "scrollBehavior") {
    chrome.storage.local.get({ scrollBursts: 0 }, data => {
      chrome.storage.local.set({ scrollBursts: data.scrollBursts + (msg.bursts || 0) });
    });
  }
  if (msg.type === "typingBurst") {
    chrome.storage.local.get({ typingBursts: 0 }, data => {
      chrome.storage.local.set({ typingBursts: data.typingBursts + 1 });
    });
  }
  if (msg.type === "tabIdle" || msg.type === "noScroll" || msg.type === "typingIdle") {
    chrome.storage.local.get({ idleEvents: 0 }, data => {
      chrome.storage.local.set({ idleEvents: data.idleEvents + 1 });
    });
  }

  // == UI DATA PROVIDER: ALL-STATS SNAPSHOT ==
  if (msg.type === "getStats") {
    chrome.storage.local.get([
      'tabSwitches', 'erraticClicks', 'ytLoops', 'tabOpenTimes', 'navHistory',
      'siteVisitHistory', 'siteCategoryStats', 'scrollBursts',
      'typingBursts', 'idleEvents'
    ], stats => {
      // Add latest tab timing data
      const t = now();
      let usage = {};
      for (let tabId in state.activeTabs) {
        const rec = state.activeTabs[tabId];
        usage[tabId] = {
          domain: rec.domain,
          total: rec.total + (state.lastTabId == tabId ? (t - rec.start) : 0),
          start: rec.start
        };
      }
      sendResponse(Object.assign({}, stats, { usage }));
    });
    return true; // For async sendResponse
  }
});

// == SYNC FUNCTION ==
function syncData() {
  chrome.storage.local.get([
    'tabSwitches', 'erraticClicks', 'ytLoops', 'tabOpenTimes', 'navHistory',
    'siteVisitHistory', 'siteCategoryStats', 'scrollBursts',
    'typingBursts', 'idleEvents'
  ], stats => {
    // Compile live usage (active tabs)
    const t = now();
    let usage = {};

    for (let tabId in state.activeTabs) {
      const rec = state.activeTabs[tabId];
      usage[tabId] = {
        domain: rec.domain,
        total: rec.total + (state.lastTabId == tabId ? (t - rec.start) : 0),
        start: rec.start
      };
    }

    const payload = {
      usage,
      tabSwitches: stats.tabSwitches || 0,
      erraticClicks: stats.erraticClicks || [],
      ytLoops: stats.ytLoops || [],
      tabOpenPerMin: (stats.tabOpenTimes || []).length,
      navHistory: stats.navHistory || {},
      siteVisitHistory: stats.siteVisitHistory || {},
      siteCategoryStats: stats.siteCategoryStats || { focus: 0, distraction: 0, other: 0 },
      scrollBursts: stats.scrollBursts || 0,
      typingBursts: stats.typingBursts || 0,
      idleEvents: stats.idleEvents || 0,
      ts: t
    };

    fetch("http://localhost:5005/api/extension_data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).catch((error) => {
      // console.log("Desktop app not running or connection failed:", error.message);
    });
  });
}
