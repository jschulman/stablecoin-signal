/* Financial Rails pilot: source evidence is usable without a generated summary. */
(function (root) {
  "use strict";
  var stages = ["announced", "pilot", "limited-production", "recurring-production", "paused", "discontinued"];
  var categories = {
    "payment-settlement": "Payments settlement",
    "institutional-treasury": "Institutional treasury",
    "securities-collateral": "Securities and collateral",
    "fund-operations": "Tokenized fund operations"
  };
  function summarize(data, asOf) {
    if (data.schema_version !== 1 || !Array.isArray(data.records)) throw new Error("Invalid Financial Rails source");
    var counts = {}, coverage = {}, overdue = 0;
    stages.forEach(function (stage) { counts[stage] = 0; });
    Object.keys(categories).forEach(function (category) { coverage[category] = 0; });
    var records = data.records.slice().sort(function (a, b) { return a.id.localeCompare(b.id); }).map(function (record) {
      if (stages.indexOf(record.stage) === -1 || !Object.prototype.hasOwnProperty.call(categories, record.category)) throw new Error("Invalid stage or category");
      if ((record.stage === "limited-production" || record.stage === "recurring-production") && !record.stage_evidence.production_observed) throw new Error("Unsupported production claim");
      if (record.stage === "recurring-production" && (record.recurring_evidence.status !== "documented" || new Set(record.recurring_evidence.observation_dates).size < 2)) throw new Error("Unsupported recurring claim");
      var due = new Date(record.reviewed_at + "T00:00:00Z");
      due.setUTCDate(due.getUTCDate() + data.metadata.review_cadence_days);
      var status = asOf > due.toISOString().slice(0, 10) ? "overdue" : "current";
      if (status === "overdue") overdue++;
      counts[record.stage]++;
      coverage[record.category]++;
      return Object.assign({}, record, {review_due: due.toISOString().slice(0, 10), review_status: status});
    });
    return {records: records, stage_counts: counts, category_counts: coverage, overdue_reviews: overdue};
  }
  // Export the pure derivation for contract tests; rendering needs no Chart.js.
  if (typeof module !== "undefined" && module.exports) module.exports = {summarize: summarize};
  if (!root.document) return;
  function node(tag, value, className) {
    var result = document.createElement(tag);
    if (value != null) result.textContent = value;
    if (className) result.className = className;
    return result;
  }
  function field(list, title, value) {
    list.appendChild(node("dt", title));
    list.appendChild(node("dd", value == null ? "Unknown / not reported" : value));
  }
  function render(data) {
    var container = document.getElementById("rails-evidence");
    var now = new Date().toISOString().slice(0, 10);
    var summary = summarize(data, now);
    container.replaceChildren();
    var stats = node("div", null, "rails-stats");
    [
      [summary.records.length, "initiatives in this curated pilot"],
      [summary.stage_counts["recurring-production"], "with repeat production documented"],
      [summary.overdue_reviews, "reviews overdue as of " + now]
    ].forEach(function (stat) {
      var card = node("div", null, "card rails-stat");
      card.appendChild(node("strong", String(stat[0])));
      card.appendChild(node("span", stat[1]));
      stats.appendChild(card);
    });
    container.appendChild(stats);
    var stageLine = stages.map(function (stage) { return stage.replace(/-/g, " ") + ": " + summary.stage_counts[stage]; }).join(" · ");
    container.appendChild(node("p", "Evidence stages — " + stageLine, "rails-note"));
    container.appendChild(node("p", data.metadata.coverage_note, "rails-note"));
    var coverage = node("ul", null, "rails-coverage");
    Object.keys(categories).forEach(function (category) {
      coverage.appendChild(node("li", categories[category] + ": " + (summary.category_counts[category] ? summary.category_counts[category] + " documented initiative(s)" : "unmeasured in this pilot")));
    });
    container.appendChild(coverage);
    var cards = node("div", null, "rails-cards");
    summary.records.forEach(function (record) {
      var card = node("article", null, "card rails-record");
      card.appendChild(node("h3", record.institutions.join(" · ")));
      card.appendChild(node("p", record.stage.replace(/-/g, " ") + " · " + categories[record.category], "rails-stage"));
      card.appendChild(node("p", record.stage_evidence.details));
      var facts = node("dl", null, "rails-facts");
      field(facts, "Event", record.event_date + (record.event_date_precision === "reported-by" ? " (reported by; start date unspecified)" : ""));
      field(facts, "Rail / geography", record.rail + " / " + record.geography);
      field(facts, "Asset / claim", record.asset_legal_claim);
      field(facts, "Workflow", record.use_cases.join("; "));
      field(facts, "Customer experience", record.customer_visibility);
      field(facts, "Repeat use", record.recurring_evidence.status + ": " + record.recurring_evidence.details);
      field(facts, "Volume", record.volume.value === null ? null : record.volume.value + " " + record.volume.unit + " / " + record.volume.period);
      field(facts, "Market denominator", record.volume.denominator);
      field(facts, "Availability", record.operating_evidence.availability);
      field(facts, "Measured cost change", record.operating_evidence.cost_change);
      field(facts, "Measured prefunding change", record.operating_evidence.prefunding_change);
      card.appendChild(facts);
      card.appendChild(node("p", record.volume.note + " " + record.operating_evidence.note, "rails-note"));
      var sources = node("ul", null, "rails-sources");
      record.sources.forEach(function (source) {
        var item = node("li");
        var link = node("a", source.title);
        // The validator requires HTTPS; keep the static renderer safe in isolation.
        if (/^https:\/\//.test(source.url)) link.href = source.url;
        link.rel = "noopener";
        item.appendChild(link);
        item.appendChild(document.createTextNode(" — published " + source.published_date));
        sources.appendChild(item);
      });
      card.appendChild(sources);
      card.appendChild(node("p", "Evidence reviewed " + record.reviewed_at + " · next review " + record.review_due + " · " + record.review_status, "rails-review " + (record.review_status === "overdue" ? "rails-overdue" : "")));
      var implications = node("details", null, "rails-implications");
      implications.appendChild(node("summary", "Potential assurance work — hypotheses"));
      var work = node("ul");
      record.control_implications.forEach(function (item) { work.appendChild(node("li", item)); });
      implications.appendChild(work);
      implications.appendChild(node("p", "Demonstrated procurement: " + record.procurement_evidence.status + ". " + record.procurement_evidence.details));
      card.appendChild(implications);
      card.appendChild(node("p", "Next evidence needed: " + record.next_review_question, "rails-note"));
      cards.appendChild(card);
    });
    container.appendChild(cards);
  }
  fetch("data/rails/evidence.json").then(function (response) {
    if (!response.ok) throw new Error("Evidence unavailable");
    return response.json();
  }).then(render).catch(function () {
    document.getElementById("rails-evidence").textContent = "Financial Rails evidence is unavailable. Missing data does not indicate zero adoption.";
  });
})(typeof window !== "undefined" ? window : globalThis);
