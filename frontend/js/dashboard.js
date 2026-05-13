/**
 * Dashboard controller.
 * Wires Supabase data + realtime events to DOM updates.
 */

import { fetchLatestSignals, subscribeToSignals, checkConnection } from "./supabase.js";
import { initChart, setCandles, updateSignalLines } from "./charts.js";

// ─────────────────────────────────────────────────────────────────────────────
// DOM refs
// ─────────────────────────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);

const DOM = {
  signalBadge:     $("signal-badge"),
  signalText:      $("signal-text"),
  confidenceBar:   $("confidence-bar"),
  confidenceVal:   $("confidence-val"),
  entryVal:        $("entry-val"),
  slVal:           $("sl-val"),
  tpVal:           $("tp-val"),
  rrVal:           $("rr-val"),
  trendVal:        $("trend-val"),
  volatilityVal:   $("volatility-val"),
  newsImpactVal:   $("news-impact-val"),
  reasonsList:     $("reasons-list"),
  historyBody:     $("history-body"),
  lastUpdated:     $("last-updated"),
  connectionDot:   $("connection-dot"),
  connectionLabel: $("connection-label"),
  chartContainer:  $("chart-container"),
};

// ─────────────────────────────────────────────────────────────────────────────
// Init
// ─────────────────────────────────────────────────────────────────────────────
export async function initDashboard() {
  // Chart
  if (DOM.chartContainer) {
    initChart(DOM.chartContainer);
  }

  // Run a quick connectivity check before subscribing
  const { ok, error: connError } = await checkConnection();
  if (!ok) {
    setConnectionStatus(false);
    console.error("[dashboard] Supabase connection failed:", connError);
  }

  // Load initial snapshot
  await loadSignals();

  // Realtime subscription — onStatusChange keeps the dot accurate
  subscribeToSignals(
    (newSignal) => {
      setConnectionStatus(true);
      prependSignalToHistory(newSignal);
      renderLatestSignal(newSignal);
      updateSignalLines(newSignal);
      flashUpdateIndicator();
    },
    (status) => {
      setConnectionStatus(status === "SUBSCRIBED");
    }
  );

  // Fallback polling in case realtime drops
  setInterval(loadSignals, APP_CONFIG.app.refreshInterval);
}

// ─────────────────────────────────────────────────────────────────────────────
// Load and render
// ─────────────────────────────────────────────────────────────────────────────
async function loadSignals() {
  const signals = await fetchLatestSignals(APP_CONFIG.app.historyLimit);
  if (!signals.length) return;

  renderLatestSignal(signals[0]);
  renderHistory(signals);
  updateSignalLines(signals[0]);
  setLastUpdated();
}

function renderLatestSignal(signal) {
  if (!signal) return;

  const isWait = signal.signal === "WAIT";
  const isBuy  = signal.signal === "BUY";

  // Signal badge
  if (DOM.signalBadge) {
    DOM.signalBadge.className = "signal-badge " + getSignalClass(signal.signal);
  }
  if (DOM.signalText) {
    DOM.signalText.textContent = signal.signal;
  }

  // Confidence
  const conf = signal.confidence ?? 0;
  if (DOM.confidenceBar) {
    DOM.confidenceBar.style.width = conf + "%";
    DOM.confidenceBar.style.background = getConfidenceColor(conf);
  }
  if (DOM.confidenceVal) DOM.confidenceVal.textContent = conf + "%";

  // Entry / SL / TP / RR
  if (DOM.entryVal) DOM.entryVal.textContent = isWait ? "—" : formatPrice(signal.entry);
  if (DOM.slVal)    DOM.slVal.textContent    = isWait ? "—" : formatPrice(signal.stop_loss);
  if (DOM.tpVal)    DOM.tpVal.textContent    = isWait ? "—" : formatPrice(signal.take_profit);
  if (DOM.rrVal)    DOM.rrVal.textContent    = isWait ? "—" : (signal.risk_reward ? "1:" + signal.risk_reward : "—");

  // Meta badges
  renderBadge(DOM.trendVal,      signal.trend,       trendClass(signal.trend));
  renderBadge(DOM.volatilityVal, signal.volatility,  volClass(signal.volatility));
  renderBadge(DOM.newsImpactVal, signal.news_impact, newsClass(signal.news_impact));

  // Reasons
  if (DOM.reasonsList) {
    const reasons = Array.isArray(signal.reasons) ? signal.reasons : [];
    DOM.reasonsList.innerHTML = reasons.length
      ? reasons.map((r) => `<li class="reason-item"><span class="reason-dot"></span>${escHtml(r)}</li>`).join("")
      : `<li class="reason-item text-slate-500">No reasons provided.</li>`;
  }

  setLastUpdated(signal.created_at);
}

function renderHistory(signals) {
  if (!DOM.historyBody) return;
  DOM.historyBody.innerHTML = signals
    .map((s, i) => historyRow(s, i))
    .join("");
}

function prependSignalToHistory(signal) {
  if (!DOM.historyBody) return;
  const row = historyRow(signal, 0);
  DOM.historyBody.insertAdjacentHTML("afterbegin", row);
  // Keep max rows
  const rows = DOM.historyBody.querySelectorAll("tr");
  if (rows.length > APP_CONFIG.app.historyLimit) {
    rows[rows.length - 1].remove();
  }
}

function historyRow(s, index) {
  const time = s.created_at ? formatTime(s.created_at) : "—";
  const sigClass = getSignalClass(s.signal);
  const conf = s.confidence ?? 0;
  return `
    <tr class="history-row ${index === 0 ? "row-latest" : ""}">
      <td class="td-time">${time}</td>
      <td><span class="badge-sm ${sigClass}">${s.signal}</span></td>
      <td class="td-price">${formatPrice(s.entry)}</td>
      <td class="td-price sl-color">${formatPrice(s.stop_loss)}</td>
      <td class="td-price tp-color">${formatPrice(s.take_profit)}</td>
      <td class="td-rr">${s.risk_reward ? "1:" + s.risk_reward : "—"}</td>
      <td class="td-conf">
        <div class="conf-mini-wrap">
          <div class="conf-mini-bar" style="width:${conf}%; background:${getConfidenceColor(conf)}"></div>
        </div>
        <span>${conf}%</span>
      </td>
    </tr>`;
}

// ─────────────────────────────────────────────────────────────────────────────
// UI helpers
// ─────────────────────────────────────────────────────────────────────────────
function renderBadge(el, text, cls) {
  if (!el) return;
  el.className = "meta-badge " + cls;
  el.textContent = text ?? "—";
}

function setConnectionStatus(connected) {
  if (DOM.connectionDot) {
    DOM.connectionDot.className = "conn-dot " + (connected ? "conn-live" : "conn-off");
  }
  if (DOM.connectionLabel) {
    DOM.connectionLabel.textContent = connected ? "LIVE" : "OFFLINE";
  }
}

function setLastUpdated(isoString) {
  if (!DOM.lastUpdated) return;
  if (isoString) {
    DOM.lastUpdated.textContent = "Updated " + formatTime(isoString);
  } else {
    DOM.lastUpdated.textContent = "Updated " + new Date().toLocaleTimeString();
  }
}

function flashUpdateIndicator() {
  if (!DOM.signalBadge) return;
  DOM.signalBadge.classList.add("flash");
  setTimeout(() => DOM.signalBadge.classList.remove("flash"), 600);
}

// ─────────────────────────────────────────────────────────────────────────────
// Formatters
// ─────────────────────────────────────────────────────────────────────────────
function formatPrice(val) {
  if (val === null || val === undefined || val === "") return "—";
  return parseFloat(val).toFixed(2);
}

function formatTime(isoString) {
  try {
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return isoString;
  }
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// ─────────────────────────────────────────────────────────────────────────────
// CSS class maps
// ─────────────────────────────────────────────────────────────────────────────
function getSignalClass(signal) {
  return { BUY: "badge-buy", SELL: "badge-sell", WAIT: "badge-wait" }[signal] ?? "badge-wait";
}

function getConfidenceColor(conf) {
  if (conf >= 75) return "#00FF9D";
  if (conf >= 50) return "#FFD166";
  return "#FF5370";
}

function trendClass(trend) {
  return { BULLISH: "badge-green", BEARISH: "badge-red", NEUTRAL: "badge-gray" }[trend] ?? "badge-gray";
}

function volClass(vol) {
  return { LOW: "badge-green", MEDIUM: "badge-yellow", HIGH: "badge-red" }[vol] ?? "badge-gray";
}

function newsClass(impact) {
  return { LOW: "badge-green", MEDIUM: "badge-yellow", HIGH: "badge-red" }[impact] ?? "badge-gray";
}
