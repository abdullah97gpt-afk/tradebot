/**
 * TradingView Lightweight Charts integration.
 * Renders a price chart with entry / SL / TP price lines.
 */

/* global LightweightCharts */

let _chart       = null;
let _candleSeries = null;
let _slLine      = null;
let _tpLine      = null;
let _entryLine   = null;

/**
 * Initialise the chart inside the given container element.
 * @param {HTMLElement} container
 */
export function initChart(container) {
  _chart = LightweightCharts.createChart(container, {
    width:  container.clientWidth,
    height: container.clientHeight || 320,
    layout: {
      background: { type: "solid", color: "#070B14" },
      textColor:  "#94A3B8",
    },
    grid: {
      vertLines: { color: "#1E293B" },
      horzLines: { color: "#1E293B" },
    },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
    rightPriceScale: {
      borderColor: "#1E293B",
    },
    timeScale: {
      borderColor: "#1E293B",
      timeVisible: true,
      secondsVisible: false,
    },
  });

  _candleSeries = _chart.addCandlestickSeries({
    upColor:          "#00FF9D",
    downColor:        "#FF5370",
    borderUpColor:    "#00FF9D",
    borderDownColor:  "#FF5370",
    wickUpColor:      "#00FF9D",
    wickDownColor:    "#FF5370",
  });

  // Auto-resize
  const ro = new ResizeObserver(() => {
    if (_chart) {
      _chart.applyOptions({
        width:  container.clientWidth,
        height: container.clientHeight || 320,
      });
    }
  });
  ro.observe(container);

  return _chart;
}

/**
 * Feed an array of OHLCV objects into the chart.
 * @param {Array<{time:number, open:number, high:number, low:number, close:number}>} candles
 */
export function setCandles(candles) {
  if (!_candleSeries) return;
  _candleSeries.setData(candles);
  if (_chart) _chart.timeScale().fitContent();
}

/**
 * Update chart price lines for current signal levels.
 * @param {{ entry: number|null, stop_loss: number|null, take_profit: number|null, signal: string }} signal
 */
export function updateSignalLines(signal) {
  if (!_chart || !_candleSeries) return;

  // Remove old lines
  [_entryLine, _slLine, _tpLine].forEach((line) => {
    if (line) {
      try { _candleSeries.removePriceLine(line); } catch (_) {}
    }
  });

  if (!signal || signal.signal === "WAIT") return;

  const isBuy = signal.signal === "BUY";

  if (signal.entry) {
    _entryLine = _candleSeries.createPriceLine({
      price:     signal.entry,
      color:     "#00C8FF",
      lineWidth: 2,
      lineStyle: LightweightCharts.LineStyle.Solid,
      axisLabelVisible: true,
      title: "ENTRY",
    });
  }

  if (signal.stop_loss) {
    _slLine = _candleSeries.createPriceLine({
      price:     signal.stop_loss,
      color:     "#FF5370",
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      axisLabelVisible: true,
      title: "SL",
    });
  }

  if (signal.take_profit) {
    _tpLine = _candleSeries.createPriceLine({
      price:     signal.take_profit,
      color:     "#00FF9D",
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      axisLabelVisible: true,
      title: "TP",
    });
  }
}
