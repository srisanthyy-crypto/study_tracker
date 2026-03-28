// ============================================================
// main.js — StudyTrack AI — Core JavaScript
// Handles: modals, dark/light theme, sidebar, study timer
// ============================================================

/* ── Theme Toggle ──────────────────────────────────────── */
(function () {
  // Load saved theme on page load
  const saved = localStorage.getItem("st-theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
  updateThemeIcon(saved);
})();

function toggleTheme() {
  const html    = document.documentElement;
  const current = html.getAttribute("data-theme");
  const next    = current === "dark" ? "light" : "dark";
  html.setAttribute("data-theme", next);
  localStorage.setItem("st-theme", next);
  updateThemeIcon(next);
}

function updateThemeIcon(theme) {
  const btn = document.getElementById("themeToggle");
  if (btn) btn.textContent = theme === "dark" ? "🌙" : "☀️";
}


/* ── Sidebar (Mobile) ──────────────────────────────────── */
function toggleSidebar() {
  document.getElementById("sidebar").classList.toggle("open");
  document.getElementById("overlay").classList.toggle("open");
}


/* ── Modal Helpers ─────────────────────────────────────── */
function openModal(id) {
  document.getElementById(id).classList.add("open");
  document.body.style.overflow = "hidden";
}

function closeModal(id) {
  document.getElementById(id).classList.remove("open");
  document.body.style.overflow = "";
}

// Close modal on overlay click
document.addEventListener("click", function (e) {
  if (e.target.classList.contains("modal-overlay")) {
    e.target.classList.remove("open");
    document.body.style.overflow = "";
  }
});

// Close modal with Escape key
document.addEventListener("keydown", function (e) {
  if (e.key === "Escape") {
    document.querySelectorAll(".modal-overlay.open").forEach(function (m) {
      m.classList.remove("open");
    });
    document.body.style.overflow = "";
  }
});


/* ── Pomodoro Study Timer ──────────────────────────────── */
let timerInterval  = null;
let timerSeconds   = 25 * 60;   // Default: 25 min
let timerRunning   = false;
let timerMinutes   = 25;

function setTimer(minutes, btn) {
  // Reset and set new time
  clearInterval(timerInterval);
  timerRunning = false;
  timerMinutes = minutes;
  timerSeconds = minutes * 60;
  updateTimerDisplay();

  // Update active preset button
  document.querySelectorAll(".timer-preset").forEach(function (b) {
    b.classList.remove("active");
  });
  if (btn) btn.classList.add("active");
}

function startTimer() {
  if (timerRunning) return;
  timerRunning = true;

  timerInterval = setInterval(function () {
    if (timerSeconds <= 0) {
      clearInterval(timerInterval);
      timerRunning = false;
      playBeep();
      // Log study session via API
      logStudySession(timerMinutes);
      alert("⏰ Session complete! Great work! Your study time has been logged.");
      resetTimer();
      return;
    }
    timerSeconds--;
    updateTimerDisplay();
  }, 1000);
}

function pauseTimer() {
  clearInterval(timerInterval);
  timerRunning = false;
}

function resetTimer() {
  clearInterval(timerInterval);
  timerRunning = false;
  timerSeconds = timerMinutes * 60;
  updateTimerDisplay();
}

function updateTimerDisplay() {
  const el = document.getElementById("timerDisplay");
  if (!el) return;
  const m = Math.floor(timerSeconds / 60);
  const s = timerSeconds % 60;
  el.textContent = String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");

  // Color changes: normal → amber → red
  if (timerSeconds <= 60) {
    el.style.color = "#ef4444";
  } else if (timerSeconds <= 5 * 60) {
    el.style.color = "#f59e0b";
  } else {
    el.style.color = "var(--accent)";
  }
}

function playBeep() {
  // Simple Web Audio API beep
  try {
    const ctx  = new (window.AudioContext || window.webkitAudioContext)();
    const osc  = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 1);
  } catch (e) {
    // Audio not supported — silent fail
  }
}

function logStudySession(minutes) {
  // POST to Flask API to record study time
  fetch("/api/log_study", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ minutes: minutes })
  })
  .then(function (r) { return r.json(); })
  .then(function (data) {
    console.log("Study logged. Streak:", data.streak);
  })
  .catch(function (err) { console.error("Log error:", err); });
}


/* ── Auto-highlight active nav link ────────────────────── */
document.addEventListener("DOMContentLoaded", function () {
  // Set min date on deadline inputs to today
  const today = new Date().toISOString().split("T")[0];
  document.querySelectorAll('input[type="date"]').forEach(function (inp) {
    // Only set min for add forms, not edit forms
    if (!inp.value) inp.min = today;
  });
});
