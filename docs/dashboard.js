/* ============================================================
   The Stablecoin Signal — Dashboard Logic
   Vanilla JS (ES5-compatible), Chart.js v4, no frameworks
   ============================================================ */

(function () {
  "use strict";

  /* ---- Data paths (relative to docs/) ---- */
  var DATA = {
    layers:      "data/adoption/layers.json",
    supply:      "data/onchain/supply.json",
    volume:      "data/onchain/volume.json",
    remittance:  "data/remittance/comparison.json",
    genius:      "data/regulatory/genius_act.json",
    wallets:     "data/onchain/wallets.json",
    reserves:    "data/treasury/reserves.json",
    tax:         "data/tax/status.json",
    yield_rates: "data/yield/rates.json",
    depegs:      "data/depegs/events.json",
    composite:   "data/composite/signal.json"
  };

  /* ---- Chart.js global defaults ---- */
  Chart.defaults.color = "#94a3b8";
  Chart.defaults.borderColor = "#334155";
  Chart.defaults.font.family = "system-ui, -apple-system, sans-serif";
  Chart.defaults.font.size = 11;
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.pointStyleWidth = 8;
  Chart.defaults.plugins.tooltip.backgroundColor = "#1e293b";
  Chart.defaults.plugins.tooltip.borderColor = "#334155";
  Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.plugins.tooltip.cornerRadius = 6;
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.scale.grid = { color: "rgba(51,65,85,0.5)" };

  /* ---- Helpers ---- */
  function fetchJSON(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(r.status + " " + r.statusText);
      return r.json();
    });
  }

  function $(id) {
    return document.getElementById(id);
  }

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    var key;
    if (attrs) {
      for (key in attrs) {
        if (attrs.hasOwnProperty(key)) {
          if (key === "className") {
            node.className = attrs[key];
          } else if (key === "textContent") {
            node.textContent = attrs[key];
          } else if (key === "innerHTML") {
            node.innerHTML = attrs[key];
          } else {
            node.setAttribute(key, attrs[key]);
          }
        }
      }
    }
    if (children) {
      for (var i = 0; i < children.length; i++) {
        if (typeof children[i] === "string") {
          node.appendChild(document.createTextNode(children[i]));
        } else if (children[i]) {
          node.appendChild(children[i]);
        }
      }
    }
    return node;
  }

  function formatBn(n) {
    if (n == null) return "--";
    if (n >= 1000) return "$" + (n / 1000).toFixed(1) + "T";
    return "$" + Number(n).toFixed(1) + "B";
  }

  function formatPct(n) {
    if (n == null) return "--";
    return Number(n).toFixed(2) + "%";
  }

  function statusColor(status) {
    var map = {
      not_started: "#64748b",
      emerging: "#eab308",
      established: "#22c55e",
      mainstream: "#3b82f6"
    };
    return map[status] || "#64748b";
  }

  function showUnavailable(container, msg) {
    container.innerHTML = "";
    container.appendChild(el("div", { className: "unavailable", textContent: msg || "Data not yet available" }));
  }

  /* ---- Chart instance registry (for cleanup) ---- */
  var charts = {};

  function makeChart(canvasId, config) {
    var canvas = $(canvasId);
    if (!canvas) return null;
    if (charts[canvasId]) {
      charts[canvasId].destroy();
    }
    charts[canvasId] = new Chart(canvas, config);
    return charts[canvasId];
  }

  /* ============================================================
     Section 1: The Interchangeability Ladder
     ============================================================ */
  function renderLadder(data) {
    var container = $("ladder-container");
    var canaryPanel = $("canary-panel");

    if (!data || !data.layers) {
      showUnavailable(container, "Ladder data not yet available");
      return;
    }

    container.innerHTML = "";

    /* Sort layers descending (5 at top, 1 at bottom) */
    var layers = data.layers.slice().sort(function (a, b) {
      return b.number - a.number;
    });

    for (var i = 0; i < layers.length; i++) {
      var layer = layers[i];
      var step = el("div", { className: "ladder-step" });

      /* Track column (dot + line) */
      var track = el("div", { className: "ladder-track" });
      track.appendChild(el("div", { className: "ladder-dot dot-" + layer.status }));
      track.appendChild(el("div", { className: "ladder-line" }));
      step.appendChild(track);

      /* Content */
      var content = el("div", { className: "ladder-content" });
      content.appendChild(el("div", { className: "ladder-layer-number", textContent: "Layer " + layer.number }));

      var nameRow = el("div", { className: "ladder-layer-name" });
      nameRow.appendChild(document.createTextNode(layer.name + " "));
      nameRow.appendChild(el("span", {
        className: "status-badge status-" + layer.status,
        textContent: layer.status.replace("_", " ")
      }));
      content.appendChild(nameRow);

      if (layer.key_signal) {
        content.appendChild(el("div", { className: "ladder-signal", textContent: layer.key_signal }));
      }

      step.appendChild(content);
      container.appendChild(step);
    }

    /* Canary panel */
    if (!canaryPanel) return;
    canaryPanel.innerHTML = "";

    if (data.canary) {
      canaryPanel.appendChild(el("div", {
        className: "canary-primary",
        innerHTML: "Primary Canary: " + data.canary.name + " &mdash; <span class=\"status-badge status-" + data.canary.status + "\">" + data.canary.status.replace("_", " ") + "</span>"
      }));

      if (data.canary.description) {
        canaryPanel.appendChild(el("div", {
          className: "ladder-signal",
          textContent: data.canary.description,
          style: "margin-bottom:0.75rem"
        }));
      }
    }

    if (data.secondary_canaries && data.secondary_canaries.length) {
      var list = el("div", { className: "canary-secondary-list" });
      for (var j = 0; j < data.secondary_canaries.length; j++) {
        var sc = data.secondary_canaries[j];
        var badgeCls = "canary-badge";
        if (sc.status === "watching") badgeCls += " watching";
        if (sc.status === "triggered") badgeCls += " triggered";
        list.appendChild(el("span", {
          className: badgeCls,
          textContent: sc.name + (sc.signal ? ": " + sc.signal : "")
        }));
      }
      canaryPanel.appendChild(list);
    }
  }

  /* ============================================================
     Section 2: Supply and Scale
     ============================================================ */
  function renderSupply(data) {
    var milestonesEl = $("supply-milestones");

    if (!data || !data.monthly || !data.monthly.length) {
      showUnavailable($("supply-chart").parentNode, "Supply data not yet available");
      return;
    }

    var monthly = data.monthly;
    var labels = monthly.map(function (d) { return d.date; });
    var usdc = monthly.map(function (d) { return d.usdc || 0; });
    var usdt = monthly.map(function (d) { return d.usdt || 0; });
    var others = monthly.map(function (d) { return d.others || 0; });
    var pctM1 = monthly.map(function (d) { return d.pct_of_m1 || null; });

    makeChart("supply-chart", {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "USDC",
            data: usdc,
            backgroundColor: "rgba(59,130,246,0.4)",
            borderColor: "#3b82f6",
            fill: true,
            tension: 0.3,
            pointRadius: 0,
            order: 3,
            yAxisID: "y"
          },
          {
            label: "USDT",
            data: usdt,
            backgroundColor: "rgba(34,197,94,0.35)",
            borderColor: "#22c55e",
            fill: true,
            tension: 0.3,
            pointRadius: 0,
            order: 2,
            yAxisID: "y"
          },
          {
            label: "Others",
            data: others,
            backgroundColor: "rgba(148,163,184,0.25)",
            borderColor: "#94a3b8",
            fill: true,
            tension: 0.3,
            pointRadius: 0,
            order: 1,
            yAxisID: "y"
          },
          {
            label: "% of M1",
            data: pctM1,
            borderColor: "#eab308",
            backgroundColor: "transparent",
            borderWidth: 2,
            borderDash: [6, 3],
            tension: 0.3,
            pointRadius: 2,
            pointBackgroundColor: "#eab308",
            fill: false,
            order: 0,
            yAxisID: "y1"
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          tooltip: {
            callbacks: {
              label: function (ctx) {
                if (ctx.dataset.yAxisID === "y1") return ctx.dataset.label + ": " + formatPct(ctx.parsed.y);
                return ctx.dataset.label + ": " + formatBn(ctx.parsed.y);
              }
            }
          }
        },
        scales: {
          y: {
            type: "linear",
            position: "left",
            title: { display: true, text: "Supply ($B)" },
            stacked: true,
            beginAtZero: true
          },
          y1: {
            type: "linear",
            position: "right",
            title: { display: true, text: "% of M1" },
            grid: { drawOnChartArea: false },
            beginAtZero: true
          }
        }
      }
    });

    /* Milestones */
    if (milestonesEl && data.milestones) {
      renderMilestones(milestonesEl, data.milestones);
    }
  }

  /* ============================================================
     Section 3: Commercial Adoption
     ============================================================ */
  function renderCommercial(data) {
    var milestonesEl = $("volume-milestones");

    if (!data || !data.monthly || !data.monthly.length) {
      showUnavailable($("commercial-chart").parentNode, "Volume data not yet available");
      return;
    }

    var monthly = data.monthly;
    var labels = monthly.map(function (d) { return d.date; });

    makeChart("commercial-chart", {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Est. Commercial ($B)",
            data: monthly.map(function (d) { return d.estimated_commercial_bn || 0; }),
            backgroundColor: "rgba(59,130,246,0.6)",
            borderColor: "#3b82f6",
            borderWidth: 1,
            borderRadius: 3,
            yAxisID: "y",
            order: 1
          },
          {
            label: "ACH Volume ($B)",
            data: monthly.map(function (d) { return d.ach_volume_bn || 0; }),
            type: "line",
            borderColor: "#94a3b8",
            backgroundColor: "transparent",
            borderWidth: 2,
            borderDash: [4, 2],
            tension: 0.3,
            pointRadius: 0,
            yAxisID: "y",
            order: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          tooltip: {
            callbacks: {
              label: function (ctx) { return ctx.dataset.label + ": " + formatBn(ctx.parsed.y); }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: "Volume ($B)" }
          }
        }
      }
    });

    /* Commercial % of ACH */
    makeChart("commercial-pct-chart", {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Commercial % of ACH",
          data: monthly.map(function (d) { return d.commercial_pct_of_ach || 0; }),
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59,130,246,0.1)",
          fill: true,
          tension: 0.3,
          pointRadius: 2,
          pointBackgroundColor: "#3b82f6"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              label: function (ctx) { return formatPct(ctx.parsed.y); }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: "% of ACH" }
          }
        }
      }
    });

    /* Average transfer size */
    makeChart("transfer-size-chart", {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Avg Transfer Size ($)",
          data: monthly.map(function (d) { return d.avg_transfer_size || 0; }),
          borderColor: "#eab308",
          backgroundColor: "rgba(234,179,8,0.08)",
          fill: true,
          tension: 0.3,
          pointRadius: 2,
          pointBackgroundColor: "#eab308"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            title: { display: true, text: "Avg Size ($)" }
          }
        }
      }
    });

    if (milestonesEl && data.milestones) {
      renderMilestones(milestonesEl, data.milestones);
    }
  }

  /* ============================================================
     Section 4: Cross-Border Remittance
     ============================================================ */
  function renderRemittance(data) {
    var corridorContainer = $("corridor-cards");

    if (!data || !data.quarterly || !data.quarterly.length) {
      showUnavailable($("remittance-chart").parentNode, "Remittance data not yet available");
      return;
    }

    var quarterly = data.quarterly;
    var labels = quarterly.map(function (d) { return d.quarter; });

    /* Stacked bar: providers */
    makeChart("remittance-chart", {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Stablecoin",
            data: quarterly.map(function (d) { return d.stablecoin_bn || 0; }),
            backgroundColor: "rgba(59,130,246,0.7)",
            borderRadius: 2
          },
          {
            label: "Western Union",
            data: quarterly.map(function (d) { return d.western_union_bn || 0; }),
            backgroundColor: "rgba(234,179,8,0.6)",
            borderRadius: 2
          },
          {
            label: "MoneyGram",
            data: quarterly.map(function (d) { return d.moneygram_bn || 0; }),
            backgroundColor: "rgba(34,197,94,0.5)",
            borderRadius: 2
          },
          {
            label: "Wise",
            data: quarterly.map(function (d) { return d.wise_bn || 0; }),
            backgroundColor: "rgba(148,163,184,0.5)",
            borderRadius: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              label: function (ctx) { return ctx.dataset.label + ": " + formatBn(ctx.parsed.y); }
            }
          }
        },
        scales: {
          x: { stacked: true },
          y: { stacked: true, beginAtZero: true, title: { display: true, text: "Volume ($B)" } }
        }
      }
    });

    /* Cost comparison lines */
    makeChart("remittance-cost-chart", {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Stablecoin Cost %",
            data: quarterly.map(function (d) { return d.avg_cost_stablecoin_pct || 0; }),
            borderColor: "#3b82f6",
            backgroundColor: "rgba(59,130,246,0.1)",
            fill: true,
            tension: 0.3,
            pointRadius: 3,
            pointBackgroundColor: "#3b82f6"
          },
          {
            label: "Traditional Cost %",
            data: quarterly.map(function (d) { return d.avg_cost_traditional_pct || 0; }),
            borderColor: "#ef4444",
            backgroundColor: "rgba(239,68,68,0.08)",
            fill: true,
            tension: 0.3,
            pointRadius: 3,
            pointBackgroundColor: "#ef4444"
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              label: function (ctx) { return ctx.dataset.label + ": " + formatPct(ctx.parsed.y); }
            }
          }
        },
        scales: {
          y: { beginAtZero: true, title: { display: true, text: "Cost %" } }
        }
      }
    });

    /* Corridor cards */
    if (corridorContainer && data.corridors && data.corridors.length) {
      corridorContainer.innerHTML = "";
      var displayed = data.corridors.slice(0, 5);
      for (var i = 0; i < displayed.length; i++) {
        var c = displayed[i];
        var trendCls = "trend-stable";
        if (c.trend === "increasing" || c.trend === "growing") trendCls = "trend-up";
        if (c.trend === "decreasing" || c.trend === "declining") trendCls = "trend-down";

        var card = el("div", { className: "corridor-card" }, [
          el("div", { className: "corridor-name", textContent: c.corridor }),
          el("div", { className: "corridor-stat", textContent: "Volume: " + formatBn(c.annual_volume_bn) }),
          el("div", { className: "corridor-stat", textContent: "Stablecoin share: " + formatPct(c.stablecoin_share_pct) }),
          el("div", { className: "corridor-trend " + trendCls, textContent: c.trend || "stable" })
        ]);
        if (c.note) {
          card.appendChild(el("div", { className: "corridor-stat", textContent: c.note, style: "margin-top:0.35rem;font-style:italic" }));
        }
        corridorContainer.appendChild(card);
      }
    }
  }

  /* ============================================================
     Section 5: Acceptance Signals
     ============================================================ */
  function renderAcceptance(geniusData, layersData, compositeData) {
    renderGeniusTimeline(geniusData, compositeData);
    renderEventList(layersData);
    renderRulemakingTable(geniusData);
  }

  function renderGeniusTimeline(data, compositeData) {
    var container = $("genius-timeline");
    var countdownEl = $("genius-countdown");

    if (!data || !data.milestones || !data.milestones.length) {
      if (container) showUnavailable(container, "GENIUS Act data not yet available");
      return;
    }

    container.innerHTML = "";

    for (var i = 0; i < data.milestones.length; i++) {
      var m = data.milestones[i];
      var node = el("div", { className: "timeline-node" });

      var dotCls = "timeline-node-dot dot-";
      if (m.status === "done") dotCls += "established";
      else if (m.status === "in_progress") dotCls += "emerging";
      else dotCls += "not_started";

      node.appendChild(el("div", { className: dotCls }));
      node.appendChild(el("div", { className: "timeline-node-label", textContent: m.milestone }));
      if (m.deadline) {
        node.appendChild(el("div", { className: "timeline-node-date", textContent: m.deadline }));
      }
      container.appendChild(node);
    }

    /* Countdown */
    if (countdownEl && compositeData && compositeData.key_metrics && compositeData.key_metrics.genius_act_days_until_effective != null) {
      var days = compositeData.key_metrics.genius_act_days_until_effective;
      countdownEl.textContent = days + " days until effective";
    }
  }

  function renderEventList(layersData) {
    var container = $("event-list");
    if (!container) return;

    if (!layersData || !layersData.events || !layersData.events.length) {
      showUnavailable(container, "No events recorded yet");
      return;
    }

    container.innerHTML = "";
    var events = layersData.events.slice().sort(function (a, b) {
      return b.date > a.date ? 1 : b.date < a.date ? -1 : 0;
    });

    for (var i = 0; i < events.length; i++) {
      var ev = events[i];
      var item = el("div", { className: "event-item" });
      item.appendChild(el("span", { className: "event-date", textContent: ev.date }));

      var text = el("span", { className: "event-text" });
      text.appendChild(document.createTextNode(ev.event + " "));
      if (ev.layer) {
        text.appendChild(el("span", {
          className: "event-layer-badge status-badge status-emerging",
          textContent: ev.layer
        }));
      }
      item.appendChild(text);
      container.appendChild(item);
    }
  }

  function renderRulemakingTable(data) {
    var container = $("rulemaking-table");
    if (!container) return;

    if (!data || !data.rulemaking_tracker || !data.rulemaking_tracker.length) {
      showUnavailable(container, "No rulemaking data yet");
      return;
    }

    container.innerHTML = "";
    var table = el("table", { className: "data-table" });
    var thead = el("thead");
    var headerRow = el("tr");
    ["Agency", "Stage", "Published", "Next Action"].forEach(function (h) {
      headerRow.appendChild(el("th", { textContent: h }));
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    var tbody = el("tbody");
    for (var i = 0; i < data.rulemaking_tracker.length; i++) {
      var r = data.rulemaking_tracker[i];
      var row = el("tr");
      row.appendChild(el("td", { textContent: r.agency || "--" }));
      row.appendChild(el("td", { textContent: r.stage || "--" }));
      row.appendChild(el("td", { textContent: r.published || "--" }));
      row.appendChild(el("td", { textContent: r.next_action || "--" }));
      tbody.appendChild(row);
    }
    table.appendChild(tbody);
    container.appendChild(table);
  }

  /* ============================================================
     Section 6: Deep Metrics
     ============================================================ */
  function renderWallets(data) {
    if (!data || !data.monthly || !data.monthly.length) {
      showUnavailable($("wallet-chart").parentNode, "Wallet data not yet available");
      return;
    }

    var monthly = data.monthly;
    var labels = monthly.map(function (d) { return d.date; });

    makeChart("wallet-chart", {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Monthly Active (M)",
            data: monthly.map(function (d) { return d.monthly_active_m || 0; }),
            backgroundColor: "rgba(59,130,246,0.6)",
            borderColor: "#3b82f6",
            borderWidth: 1,
            borderRadius: 3,
            yAxisID: "y",
            order: 1
          },
          {
            label: "New Wallets (K)",
            data: monthly.map(function (d) { return d.new_wallets_k || 0; }),
            type: "line",
            borderColor: "#22c55e",
            backgroundColor: "transparent",
            borderWidth: 2,
            tension: 0.3,
            pointRadius: 2,
            pointBackgroundColor: "#22c55e",
            yAxisID: "y1",
            order: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        scales: {
          y: { beginAtZero: true, title: { display: true, text: "Monthly Active (M)" } },
          y1: {
            type: "linear",
            position: "right",
            beginAtZero: true,
            title: { display: true, text: "New Wallets (K)" },
            grid: { drawOnChartArea: false }
          }
        }
      }
    });
  }

  function renderTreasury(data) {
    var milestonesEl = $("treasury-milestones");

    if (!data || !data.monthly || !data.monthly.length) {
      showUnavailable($("treasury-chart").parentNode, "Treasury data not yet available");
      return;
    }

    var monthly = data.monthly;
    var labels = monthly.map(function (d) { return d.date; });

    makeChart("treasury-chart", {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Stablecoin T-Bill Holdings ($B)",
            data: monthly.map(function (d) { return d.total_stablecoin_tbill_bn || 0; }),
            borderColor: "#3b82f6",
            backgroundColor: "rgba(59,130,246,0.1)",
            fill: true,
            tension: 0.3,
            pointRadius: 2,
            pointBackgroundColor: "#3b82f6",
            yAxisID: "y"
          },
          {
            label: "% of T-Bill Market",
            data: monthly.map(function (d) { return d.pct_of_market || 0; }),
            borderColor: "#eab308",
            backgroundColor: "transparent",
            borderWidth: 2,
            borderDash: [6, 3],
            tension: 0.3,
            pointRadius: 2,
            pointBackgroundColor: "#eab308",
            fill: false,
            yAxisID: "y1"
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          tooltip: {
            callbacks: {
              label: function (ctx) {
                if (ctx.dataset.yAxisID === "y1") return ctx.dataset.label + ": " + formatPct(ctx.parsed.y);
                return ctx.dataset.label + ": " + formatBn(ctx.parsed.y);
              }
            }
          }
        },
        scales: {
          y: { beginAtZero: true, title: { display: true, text: "Holdings ($B)" } },
          y1: {
            type: "linear",
            position: "right",
            beginAtZero: true,
            title: { display: true, text: "% of Market" },
            grid: { drawOnChartArea: false }
          }
        }
      }
    });

    if (milestonesEl && data.milestones) {
      renderMilestones(milestonesEl, data.milestones);
    }
  }

  function renderTax(data) {
    var container = $("tax-status-panel");
    if (!container) return;

    if (!data) {
      showUnavailable(container, "Tax data not yet available");
      return;
    }

    container.innerHTML = "";

    /* Friction display */
    var friction = data.current_friction || "unknown";
    var frictionDisplay = el("div", { className: "tax-friction-display" });
    frictionDisplay.appendChild(el("div", { className: "tax-friction-label", textContent: "Current Tax Friction" }));
    frictionDisplay.appendChild(el("div", {
      className: "tax-friction-value friction-" + friction,
      textContent: friction.charAt(0).toUpperCase() + friction.slice(1)
    }));
    container.appendChild(frictionDisplay);

    /* Signals list */
    if (data.signals && data.signals.length) {
      var list = el("ul", { className: "tax-signals-list" });
      for (var i = 0; i < data.signals.length; i++) {
        var s = data.signals[i];
        var li = el("li");
        li.appendChild(el("span", { textContent: s.signal }));
        var statusCls = "status-badge status-";
        if (s.status === "passed" || s.status === "done" || s.status === "resolved") statusCls += "established";
        else if (s.status === "in_progress" || s.status === "pending") statusCls += "emerging";
        else statusCls += "not_started";
        li.appendChild(el("span", { className: statusCls, textContent: s.status || "--" }));
        list.appendChild(li);
      }
      container.appendChild(list);
    }
  }

  function renderYield(data) {
    var container = $("yield-table");
    if (!container) return;

    if (!data || !data.current || !data.current.length) {
      showUnavailable(container, "Yield data not yet available");
      return;
    }

    container.innerHTML = "";

    var fedRate = data.fed_funds_rate;
    if (fedRate != null) {
      container.appendChild(el("div", {
        className: "corridor-stat",
        textContent: "Fed Funds Rate: " + formatPct(fedRate),
        style: "margin-bottom:0.75rem;font-weight:600;color:#f1f5f9"
      }));
    }

    var table = el("table", { className: "data-table" });
    var thead = el("thead");
    var headerRow = el("tr");
    ["Platform", "Asset", "APY", "Type"].forEach(function (h) {
      headerRow.appendChild(el("th", { textContent: h }));
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    var tbody = el("tbody");
    for (var i = 0; i < data.current.length; i++) {
      var r = data.current[i];
      var row = el("tr");
      row.appendChild(el("td", { textContent: r.platform || "--" }));
      row.appendChild(el("td", { textContent: r.asset || "--" }));
      row.appendChild(el("td", { textContent: formatPct(r.apy_pct) }));
      row.appendChild(el("td", { textContent: r.type || "--" }));
      tbody.appendChild(row);
    }
    table.appendChild(tbody);
    container.appendChild(table);
  }

  function renderDepegs(data) {
    var container = $("depeg-list");
    if (!container) return;

    if (!data || !data.events || !data.events.length) {
      showUnavailable(container, "No depeg events recorded");
      return;
    }

    container.innerHTML = "";
    var events = data.events.slice().sort(function (a, b) {
      return b.date > a.date ? 1 : b.date < a.date ? -1 : 0;
    });

    for (var i = 0; i < events.length; i++) {
      var ev = events[i];
      var item = el("div", { className: "event-item" });
      item.appendChild(el("span", { className: "event-date", textContent: ev.date }));

      var text = el("span", { className: "event-text" });
      var sevCls = "severity-" + (ev.severity || "moderate").toLowerCase();
      text.appendChild(el("strong", { textContent: ev.asset, className: sevCls }));
      text.appendChild(document.createTextNode(" low: $" + (ev.low_price || "--") + " | " + (ev.duration_days || "?") + " days"));
      if (ev.cause) {
        text.appendChild(el("br"));
        text.appendChild(document.createTextNode(ev.cause));
      }
      item.appendChild(text);
      container.appendChild(item);
    }
  }

  /* ============================================================
     Shared: Milestone Renderer
     ============================================================ */
  function renderMilestones(container, milestones) {
    if (!container || !milestones || !milestones.length) return;
    container.innerHTML = "";
    for (var i = 0; i < milestones.length; i++) {
      var m = milestones[i];
      var statusCls = "milestone-tag milestone-" + (m.status === "passed" || m.status === "done" ? "done" : m.status === "in_progress" ? "in_progress" : "pending");
      var label = m.threshold || m.milestone || "";
      if (m.date) label += " (" + m.date + ")";
      container.appendChild(el("span", { className: statusCls, textContent: label }));
    }
  }

  /* ============================================================
     Footer: Data Freshness & Last Updated
     ============================================================ */
  function renderFooter(allData) {
    var freshnessEl = $("footer-freshness");
    var updatedEl = $("last-updated");

    if (!freshnessEl) return;

    var sources = [
      { name: "Supply", data: allData.supply },
      { name: "Volume", data: allData.volume },
      { name: "Remittance", data: allData.remittance },
      { name: "Wallets", data: allData.wallets },
      { name: "Treasury", data: allData.reserves },
      { name: "Regulatory", data: allData.genius }
    ];

    var indicators = el("div", { className: "freshness-indicators" });
    var latestDate = null;

    for (var i = 0; i < sources.length; i++) {
      var src = sources[i];
      var loaded = src.data != null;
      var dot = el("span", {
        className: "freshness-dot" + (loaded ? "" : " stale"),
        textContent: src.name + (loaded ? " loaded" : " pending")
      });
      indicators.appendChild(dot);

      if (loaded && src.data.metadata && src.data.metadata.last_updated) {
        var d = src.data.metadata.last_updated;
        if (!latestDate || d > latestDate) latestDate = d;
      }
    }

    freshnessEl.innerHTML = "";
    freshnessEl.appendChild(indicators);

    if (updatedEl && latestDate) {
      updatedEl.textContent = "Last updated: " + latestDate;
    }
  }

  /* ============================================================
     Master: Load and Render All
     ============================================================ */
  function loadAll() {
    var keys = Object.keys(DATA);
    var promises = keys.map(function (key) {
      return fetchJSON(DATA[key]).catch(function () {
        return null;
      });
    });

    Promise.all(promises).then(function (results) {
      var d = {};
      for (var i = 0; i < keys.length; i++) {
        d[keys[i]] = results[i];
      }

      renderLadder(d.layers);
      renderSupply(d.supply);
      renderCommercial(d.volume);
      renderRemittance(d.remittance);
      renderAcceptance(d.genius, d.layers, d.composite);
      renderWallets(d.wallets);
      renderTreasury(d.reserves);
      renderTax(d.tax);
      renderYield(d.yield_rates);
      renderDepegs(d.depegs);
      renderFooter(d);
    });
  }

  /* ---- Boot ---- */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadAll);
  } else {
    loadAll();
  }
})();
