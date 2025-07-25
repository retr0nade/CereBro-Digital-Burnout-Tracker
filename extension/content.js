// ----------- ERRATIC CLICKING: Multiple quick clicks within 2 seconds -----------
let clickTimes = [];
document.addEventListener("click", () => {
  const now = Date.now();
  clickTimes.push(now);
  clickTimes = clickTimes.filter(t => now - t < 2000);
  if (clickTimes.length >= 5) {
    chrome.runtime.sendMessage({ type: "erraticClick", url: window.location.href });
    clickTimes = [];
  }
});

// ----------- YOUTUBE LOOP DETECTION: Detect repeated video loops -----------
if (/youtube\.com/.test(location.hostname)) {
  let lastVideoId = null;
  let loopCount = 0;
  setInterval(() => {
    const player = document.querySelector('video');
    if (player) {
      const currentVideoId = new URLSearchParams(location.search).get("v");
      if (
        currentVideoId &&
        currentVideoId === lastVideoId &&
        player.currentTime < 2 &&
        !player.paused
      ) {
        // Video restarted at the beginning
        loopCount++;
        if (loopCount === 2) {
          chrome.runtime.sendMessage({ type: "ytLoop", url: location.href });
          loopCount = 0;
        }
      }
      if (currentVideoId !== lastVideoId) {
        lastVideoId = currentVideoId;
        loopCount = 0;
      }
    }
  }, 1000);
}

// ----------- SCROLL BEHAVIOR: Fast/erratic/repeated scrolls, inactivity -----------
let lastScrollY = window.scrollY;
let lastScrollTime = Date.now();
let scrollBursts = 0;
let scrollToTopCount = 0;
let lastAtTop = false;
let noScrollTimer = null;

window.addEventListener('scroll', () => {
  const now = Date.now();
  const deltaY = Math.abs(window.scrollY - lastScrollY);
  const deltaT = now - lastScrollTime;

  // Fast/erratic scroll
  if (deltaY > 300 && deltaT < 300) scrollBursts++;

  // Repeated scroll to top
  if (window.scrollY === 0) {
    if (!lastAtTop) scrollToTopCount++;
    lastAtTop = true;
  } else {
    lastAtTop = false;
  }

  lastScrollY = window.scrollY;
  lastScrollTime = now;

  clearTimeout(noScrollTimer);
  noScrollTimer = setTimeout(() => {
    // Tab has had no scroll for 1 minute
    chrome.runtime.sendMessage({ type: "noScroll", url: window.location.href });
  }, 60000);
});

// Every 15 seconds, send scroll burst/top details if any
setInterval(() => {
  if (scrollBursts > 0 || scrollToTopCount > 0) {
    chrome.runtime.sendMessage({
      type: "scrollBehavior",
      url: window.location.href,
      bursts: scrollBursts,
      scrollToTop: scrollToTopCount
    });
    scrollBursts = 0;
    scrollToTopCount = 0;
  }
}, 15000);

// ----------- TYPING BURSTS, SPEED, INACTIVITY -----------
let typingTimestamps = [];
let lastTypedTime = null;

function analyzeTyping(e) {
  const now = Date.now();
  typingTimestamps.push(now);
  typingTimestamps = typingTimestamps.filter(t => now - t < 10000);

  if (typingTimestamps.length >= 30) {
    chrome.runtime.sendMessage({
      type: "typingBurst",
      url: window.location.href,
      ts: now
    });
    typingTimestamps = [];
  }
  lastTypedTime = now;
}

document.addEventListener('keydown', e => {
  if (
    e.target.tagName === 'INPUT' ||
    e.target.tagName === 'TEXTAREA' ||
    e.target.isContentEditable
  ) {
    analyzeTyping(e);
  }
});

// Typing inactivity (>60s)
setInterval(() => {
  if (lastTypedTime && Date.now() - lastTypedTime > 60000) {
    chrome.runtime.sendMessage({ type: "typingIdle", url: window.location.href });
    lastTypedTime = null;
  }
}, 10000);

// ----------- TAB IDLE (No input/scroll/move for >60s) -----------
let lastActiveInput = Date.now();
function resetActivity() { lastActiveInput = Date.now(); }
document.addEventListener('mousemove', resetActivity, true);
document.addEventListener('keydown', resetActivity, true);
document.addEventListener('scroll', resetActivity, true);
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) resetActivity();
});
setInterval(() => {
  if (
    document.visibilityState === "visible" &&
    Date.now() - lastActiveInput > 60000
  ) {
    chrome.runtime.sendMessage({ type: "tabIdle", url: window.location.href });
    lastActiveInput = Date.now();
  }
}, 10000);

// NOTE: This content script emits all metrics to the background script, which
// is now responsible for persisting counters via chrome.storage.local.
// Do not reset or clear counters in content.js; make the background.js authoritative.
