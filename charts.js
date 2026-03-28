// ============================================================
// charts.js — StudyTrack AI — Dashboard Charts (Chart.js 4)
// ============================================================

/**
 * Initialize both dashboard charts.
 * Called from dashboard.html after passing Flask data as JSON.
 *
 * @param {Array}  subjectData  - [{name, color, done, total, progress}]
 * @param {Array}  logDates     - ["2024-01-01", ...]
 * @param {Array}  logMinutes   - [45, 60, ...]
 */
function initDashboardCharts(subjectData, logDates, logMinutes) {

  // ── Detect theme for chart colors ──────────────────────
  const isDark  = document.documentElement.getAttribute("data-theme") !== "light";
  const txtClr  = isDark ? "#9090c0" : "#4a4a8a";
  const gridClr = isDark ? "#2d2d5544" : "#d0d0ee44";

  // ── 1. Subject Breakdown — Doughnut Chart ──────────────
  const subjectCtx = document.getElementById("subjectChart");
  if (subjectCtx && subjectData.length > 0) {
    new Chart(subjectCtx, {
      type: "doughnut",
      data: {
        labels:   subjectData.map(function (s) { return s.name; }),
        datasets: [{
          data:             subjectData.map(function (s) { return s.total || 1; }),
          backgroundColor: subjectData.map(function (s) { return s.color + "cc"; }),
          borderColor:     subjectData.map(function (s) { return s.color; }),
          borderWidth:     2,
          hoverOffset:     8,
        }]
      },
      options: {
        responsive:         true,
        maintainAspectRatio: false,
        cutout:             "65%",
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              color:     txtClr,
              font:      { family: "'DM Sans', sans-serif", size: 12 },
              padding:   12,
              boxWidth:  14,
              boxHeight: 14,
            }
          },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                var s = subjectData[ctx.dataIndex];
                return " " + s.name + ": " + s.done + "/" + s.total + " tasks (" + s.progress + "%)";
              }
            }
          }
        }
      }
    });
  } else if (subjectCtx) {
    // No subjects: show a placeholder message
    subjectCtx.parentElement.innerHTML =
      '<p style="text-align:center; color:var(--text-muted); padding:60px 0;">Add subjects to see your breakdown!</p>';
  }

  // ── 2. Weekly Activity — Bar Chart ─────────────────────
  const activityCtx = document.getElementById("activityChart");
  if (activityCtx) {
    // Format dates nicely (e.g. "Mon 3")
    var labels = logDates.map(function (d) {
      if (!d) return "";
      var date  = new Date(d + "T00:00:00");
      var days  = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
      return days[date.getDay()] + " " + date.getDate();
    });

    new Chart(activityCtx, {
      type: "bar",
      data: {
        labels:   labels.length > 0 ? labels  : ["No data yet"],
        datasets: [{
          label:           "Minutes Studied",
          data:            logMinutes.length > 0 ? logMinutes : [0],
          backgroundColor: "rgba(99, 102, 241, 0.6)",
          borderColor:     "#6366f1",
          borderWidth:     2,
          borderRadius:    6,
          hoverBackgroundColor: "rgba(99, 102, 241, 0.85)",
        }]
      },
      options: {
        responsive:          true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                return " " + ctx.parsed.y + " minutes";
              }
            }
          }
        },
        scales: {
          x: {
            grid:  { color: gridClr },
            ticks: { color: txtClr, font: { family: "'DM Sans', sans-serif", size: 11 } }
          },
          y: {
            beginAtZero: true,
            grid:  { color: gridClr },
            ticks: {
              color: txtClr,
              font:  { family: "'DM Sans', sans-serif", size: 11 },
              callback: function (v) { return v + "m"; }
            }
          }
        }
      }
    });
  }
}
