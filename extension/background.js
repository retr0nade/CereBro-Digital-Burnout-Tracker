// == SITE CATEGORY CONFIG ==
const siteCategories = {
  "leetcode.com": "focus",
  "github.com": "focus",
  "youtube.com": "distraction",
  "twitter.com": "distraction"
  // ...add more as you wish
};

// == GLOBALS (ONLY IN-MEMORY FOR LIVE TAB TIMING) ==
let activeTabs = {};    // tabId: { start, domain, total }
let lastTabId = null;

function getDomain(url) {
  try { return new URL(url).hostname; } catch { return "unknown"; }
}
function now() { return Date.now(); }

// == SESSION STORAGE RESET ONLY ON EXTENSION INSTALL/RELOAD ==
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    tabSwitches: 0,
    erraticClicks: [],
    ytLoops: [],
    tabOpenTimes: [],
    navHistory: {},
    siteVisitHistory: {},
    siteCategoryStats: { focus: 0, distraction: 0, other: 0 }
  });
});

// == CORE TAB TIME & CATEGORY LOGIC ==
chrome.tabs.onActivated.addListener((activeInfo) => {
  const t = now();
  if (lastTabId !== null && activeTabs[lastTabId]) {
    const dt = t - activeTabs[lastTabId].start;
    activeTabs[lastTabId].total += dt;
    categorize(activeTabs[lastTabId].domain, dt);
  }
  chrome.tabs.get(activeInfo.tabId, (tab) => {
    const url = tab.url || "about:blank";
    const domain = getDomain(url);
    if (!activeTabs[activeInfo.tabId]) {
      activeTabs[activeInfo.tabId] = { start: t, domain, total: 0 };
    }
    activeTabs[activeInfo.tabId].start = t;
    lastTabId = activeInfo.tabId;

    // Increment tab switches in persistent storage
    chrome.storage.local.get({ tabSwitches: 0 }, data => {
      chrome.storage.local.set({ tabSwitches: data.tabSwitches + 1 });
    });
  });
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete") {
    const url = tab.url || "about:blank";
    const domain = getDomain(url);
    activeTabs[tabId] = { start: now(), domain, total: 0 };

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
        });
      }
    });
  }
});

chrome.tabs.onRemoved.addListener((tabId) => {
  if (activeTabs[tabId]) {
    const t = now();
    const dt = t - activeTabs[tabId].start;
    activeTabs[tabId].total += dt;
    categorize(activeTabs[tabId].domain, dt);
    delete activeTabs[tabId];
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
      });
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
});

// == PERIODIC SYNC: PUSH ALL (NEVER RESET ANY STATS!) ==
setInterval(() => {
  chrome.storage.local.get([
    'tabSwitches', 'erraticClicks', 'ytLoops', 'tabOpenTimes', 'navHistory',
    'siteVisitHistory', 'siteCategoryStats', 'scrollBursts',
    'typingBursts', 'idleEvents'
  ], stats => {
    // Compile live usage (active tabs)
    const t = now();
    let usage = {};
    for (let tabId in activeTabs) {
      const rec = activeTabs[tabId];
      usage[tabId] = {
        domain: rec.domain,
        total: rec.total + (lastTabId == tabId ? (t - rec.start) : 0),
        start: rec.start
      };
    }

    const payload = {
      usage, // now a dict, not array
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

    fetch("http://localhost:5005/api/track", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    }).catch(() => {});
  });
}, 5000);

// == UI DATA PROVIDER: ALL-STATS SNAPSHOT ==
chrome.runtime.onMessage.addListener((req, sender, sendResponse) => {
  if (req.type === "getStats") {
    chrome.storage.local.get([
      'tabSwitches', 'erraticClicks', 'ytLoops', 'tabOpenTimes', 'navHistory',
      'siteVisitHistory', 'siteCategoryStats', 'scrollBursts',
      'typingBursts', 'idleEvents'
    ], stats => {
      // Add latest tab timing data
      const t = now();
      let usage = {};
      for (let tabId in activeTabs) {
        const rec = activeTabs[tabId];
        usage[tabId] = {
          domain: rec.domain,
          total: rec.total + (lastTabId == tabId ? (t - rec.start) : 0),
          start: rec.start
        };
      }
      sendResponse(Object.assign({}, stats, { usage }));
    });
    return true; // For async sendResponse
  }
});
