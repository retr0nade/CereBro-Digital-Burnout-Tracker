function pad(n) {
  return n < 10 ? '0' + n : n;
}

function formatTime(ms) {
  const seconds = Math.floor(ms / 1000);
  const mins = Math.floor(seconds / 60);
  const hours = Math.floor(mins / 60);
  
  if (hours > 0) {
    return `${hours}h ${mins % 60}m`;
  } else if (mins > 0) {
    return `${mins}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
}

function animateValue(element, start, end, duration) {
  element.classList.add('updating');
  
  const range = end - start;
  let current = start;
  const increment = range / (duration / 16);
  
  function step() {
    current += increment;
    if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
      current = end;
    }
    
    element.textContent = Math.round(current);
    
    if (current !== end) {
      requestAnimationFrame(step);
    } else {
      setTimeout(() => {
        element.classList.remove('updating');
      }, 600);
    }
  }
  step();
}

function triggerCardPulse(cardElement) {
  if (cardElement) {
    cardElement.style.animation = 'none';
    setTimeout(() => {
      cardElement.style.animation = 'cardSlideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
    }, 10);
  }
}

function updateFocusBar(stats) {
  const total = stats.focus + stats.distraction + stats.other;
  if (total === 0) return;
  
  const focusPercent = (stats.focus / total) * 100;
  const distractionPercent = (stats.distraction / total) * 100;
  const otherPercent = (stats.other / total) * 100;
  
  document.getElementById('focusBar').style.width = focusPercent + '%';
  document.getElementById('distractionBar').style.width = distractionPercent + '%';
  document.getElementById('otherBar').style.width = otherPercent + '%';
  
  document.getElementById('focusTime').textContent = formatTime(stats.focus);
  document.getElementById('distractionTime').textContent = formatTime(stats.distraction);
  document.getElementById('otherTime').textContent = formatTime(stats.other);
}

let lastStats = {
  time: 0, 
  tabSwitches: 0, 
  clicks: 0, 
  ytLoops: 0,
  tabOpenPerMin: 0,
  rapidNav: 0,
  repeatSites: 0,
  scrollBursts: 0,
  typingBursts: 0,
  idleEvents: 0
};

// Global counters for extended metrics
let scrollBurstCount = 0;
let typingBurstCount = 0;
let idleEventCount = 0;
let rapidNavCount = 0;

function setStats(stats) {
  // Core metrics
  let tab = Object.values(stats.usage || {})[0];
  let seconds = tab ? Math.floor((tab.total + (Date.now() - tab.start)) / 1000) : 0;
  let mins = Math.floor(seconds/60), secs = seconds % 60;
  document.getElementById("timeOnTab").textContent = pad(mins) + ":" + pad(secs);

  // Animate main stats if changed
  if (stats.tabSwitches !== lastStats.tabSwitches) {
    animateValue(
      document.getElementById("tabSwitches"), 
      lastStats.tabSwitches, 
      stats.tabSwitches, 
      500
    );
    triggerCardPulse(document.getElementById("tabSwitches").closest('.stat-card'));
  }
  
  if (stats.erraticClicks && stats.erraticClicks.length !== lastStats.clicks) {
    animateValue(
      document.getElementById("clicks"), 
      lastStats.clicks, 
      stats.erraticClicks.length, 
      500
    );
    triggerCardPulse(document.getElementById("clicks").closest('.stat-card'));
  }
  
  if (stats.ytLoops && stats.ytLoops.length !== lastStats.ytLoops) {
    animateValue(
      document.getElementById("ytLoops"), 
      lastStats.ytLoops, 
      stats.ytLoops.length, 
      500
    );
    triggerCardPulse(document.getElementById("ytLoops").closest('.stat-card'));
  }

  // Extended metrics
  if (stats.tabOpenPerMin !== lastStats.tabOpenPerMin) {
    animateValue(
      document.getElementById("tabOpenPerMin"),
      lastStats.tabOpenPerMin,
      stats.tabOpenPerMin || 0,
      400
    );
  }

  // Count rapid navigation events
  if (stats.navHistory) {
    let currentRapidNav = 0;
    Object.values(stats.navHistory).forEach(history => {
      if (history.length > 3) currentRapidNav++;
    });
    if (currentRapidNav !== rapidNavCount) {
      animateValue(document.getElementById("rapidNav"), rapidNavCount, currentRapidNav, 400);
      rapidNavCount = currentRapidNav;
    }
  }

  // Count repeat site visits
  if (stats.siteVisitHistory) {
    let repeatCount = 0;
    Object.values(stats.siteVisitHistory).forEach(visits => {
      if (visits.length >= 5) repeatCount++;
    });
    animateValue(document.getElementById("repeatSites"), 0, repeatCount, 400);
  }

  // Update focus distribution
  if (stats.siteCategoryStats) {
    updateFocusBar(stats.siteCategoryStats);
  }

  // Placeholder for scroll/typing/idle (these would come from content script messages)
  document.getElementById("scrollBursts").textContent = scrollBurstCount;
  document.getElementById("typingBursts").textContent = typingBurstCount;
  document.getElementById("idleEvents").textContent = idleEventCount;

  // Update stored values
  lastStats = {
    tabSwitches: stats.tabSwitches || 0,
    clicks: stats.erraticClicks ? stats.erraticClicks.length : 0,
    ytLoops: stats.ytLoops ? stats.ytLoops.length : 0,
    tabOpenPerMin: stats.tabOpenPerMin || 0,
    rapidNav: rapidNavCount,
    repeatSites: Object.values(stats.siteVisitHistory || {}).filter(visits => visits.length >= 5).length,
    scrollBursts: scrollBurstCount,
    typingBursts: typingBurstCount,
    idleEvents: idleEventCount
  };
}

function addInteractiveEffects() {
  // Add click effects to all cards
  document.querySelectorAll('.stat-card, .mini-card').forEach(card => {
    card.addEventListener('click', () => {
      card.style.transform = 'scale(0.95)';
      setTimeout(() => {
        card.style.transform = '';
      }, 150);
    });
  });

  // Add hover effects
  document.querySelectorAll('.stat-card, .mini-card').forEach(card => {
    card.addEventListener('mouseenter', () => {
      const icon = card.querySelector('.stat-icon, .mini-icon');
      if (icon) {
        icon.style.filter = 'drop-shadow(0 4px 8px rgba(255,255,255,0.3))';
      }
    });
    
    card.addEventListener('mouseleave', () => {
      const icon = card.querySelector('.stat-icon, .mini-icon');
      if (icon) {
        icon.style.filter = '';
      }
    });
  });
}

function refresh() {
  chrome.runtime.sendMessage({type: "getStats"}, (stats) => {
    if (stats) {
      setStats(stats);
    }
  });
}

// Initialize with enhanced entrance animation
document.addEventListener('DOMContentLoaded', () => {
  // Staggered fade-in for sections
  const sections = ['header', 'stats-grid', 'extended-stats', 'focus-bar-container', 'status-bar'];
  sections.forEach((className, index) => {
    const el = document.querySelector('.' + className);
    if (el) {
      el.style.opacity = '0';
      el.style.transform = 'translateY(20px)';
      
      setTimeout(() => {
        el.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
        el.style.opacity = '1';
        el.style.transform = 'translateY(0)';
      }, index * 150);
    }
  });
  
  addInteractiveEffects();
  refresh();
});

// Listen for background script messages (for real-time updates)
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'scrollBehavior') {
    scrollBurstCount += message.bursts || 0;
    document.getElementById("scrollBursts").textContent = scrollBurstCount;
  }
  if (message.type === 'typingBurst') {
    typingBurstCount++;
    document.getElementById("typingBursts").textContent = typingBurstCount;
  }
  if (message.type === 'tabIdle' || message.type === 'noScroll' || message.type === 'typingIdle') {
    idleEventCount++;
    document.getElementById("idleEvents").textContent = idleEventCount;
  }
});

// Update every second
setInterval(refresh, 1000);
