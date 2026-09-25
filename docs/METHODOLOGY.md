# Methodology

How The Stablecoin Signal computes layer statuses, filters volume data, and tracks adoption signals.

## The Interchangeability Ladder

Each of the five consumer-facing layers is rated independently. Backend settlement is assessed separately in the Financial Rails pilot. Neither volume nor an unchanged consumer interface establishes a legal, accounting or tax classification:

| Rating | Criteria |
|--------|----------|
| **Unknown / unmeasured** | Insufficient evidence to assess the consumer threshold |
| **Not Started** | No meaningful activity observed in the stated scope and dated review |
| **Emerging** | Early movers, pilots, announcements — but not broadly available |
| **Established** | Multiple participants, growing adoption, available to general public |
| **Mainstream** | Default behavior, no longer noteworthy |

### Layer Thresholds

| Layer | Threshold for "Established" |
|-------|---------------------------|
| Hold | 3+ top-25 US banks offer stablecoin custody accounts |
| Earn | Major payroll platform (ADP/Gusto/Deel) offers stablecoin disbursement to US W-2 employees |
| Spend | Top-20 US retailer accepts stablecoin payment natively (not through a converter) |
| Borrow | US bank treats USDC as USD-equivalent collateral for lending |
| Invisible | Consumer surveys show <50% know which currency they used for last purchase |

The consumer-awareness threshold currently has no cited survey measurement, so Invisible is unknown. This does not deny backend abstraction: the separate Visa record documents an unchanged cardholder experience. Native retail acceptance remains a consumer measure; processor conversion is allowed in the backend measure.

Layer statuses are updated manually as events occur. The `data/adoption/layers.json` file is the source of truth.

## Financial Rails pilot

### Scope and evidence unit

This curated US-focused pilot tests whether ordinary financial operations use blockchain even when end users see familiar accounts. It covers payment settlement, institutional treasury transfers, securities/collateral workflows and tokenized fund operations as separate categories. The initial two records do not measure the whole market, and no records in a category means unmeasured coverage, not zero adoption.

One record represents a tracked initiative's current evidenced stage. Update its evidence and sources when new events change that stage. Each event has a unique `event_id`; the same multi-workflow event cannot appear twice to inflate activity. A record may list multiple use cases, but has one primary category. There is no cross-category volume total, consumer/backend composite score or market-share calculation. Issuer supply, securities outstanding, gross on-chain transfers, annualized run rates and actual-period settlement flows are different measures and cannot be substituted for each other.

### Validated source contract

Canonical source: `data/rails/evidence.json`, with a checked public curated mirror at `docs/data/rails/evidence.json`. `schema_version` is 1. The standard-library validator in `normalizers/financial_rails.py` rejects missing or unknown fields, wrong types, bad dates, invalid enums, duplicate events and broken source references. Every record carries:

- Stable `id` and unique `event_id`; institutions, rail, asset/legal claim, geography, primary category and use cases.
- Event date plus `exact` or `reported-by` precision; primary sources with HTTPS URL, title and publication date. A press release's publication date is not silently treated as an operation's start date.
- Stage, observed-production boolean, rationale and supporting source references.
- Recurring-evidence status, distinct observation dates and source references.
- Volume value, unit, period, denominator, source references and scope note. Unknown values must be explicit JSON `null`. A reported zero remains numeric zero. A known volume requires its unit, period and source; an unavailable denominator stays null.
- Customer visibility, reported operating availability, measured cost/prefunding outcomes or null, potential control implications, and separately sourced procurement status.
- `reviewed_at` and the next evidence question.

Source review requires checking the cited primary material. This is evidence review, not independent confirmation that a deployment remains in operation. Correctness of a source's assertions still requires editorial judgment; validation cannot establish truth from a URL.

### Stages and assurance interpretation

| Stage | Evidence rule |
|---|---|
| Announced | Intention or future availability; no observed execution claimed |
| Pilot | Test or trial without sufficient evidence of production execution |
| Limited production | Primary source reports actual production activity in a bounded scope |
| Recurring production | Observed production plus at least two distinct dated observations, supported by cited primary sources |
| Paused | Sourced suspension; prior activity does not imply continued operation |
| Discontinued | Sourced termination; retain the record to show reversals |

A production label in marketing text is not enough without an actual reported workflow. A several-hour production event is limited production. Planned launch dates never advance stages. The Visa seed does not allocate its global settlement run rate to named US banks, and the DTCC seed does not allocate firmwide volumes to the tokenization event.

Control implications are explicitly hypotheses about possible assurance work. They are not proof of procurement, RSM eligibility, revenue or an existing engagement. Documented procurement requires a supporting source distinct from an analyst's inference.

### Freshness and publication

Records have a 30-day review cadence. A review becomes overdue on the day after its due date. The page recalculates overdue status from current UTC date, so a stalled build cannot leave a stale review marked current indefinitely. Event date, source publication date and evidence-review date remain visible individually. An old source can have a recent review; neither date is replaced with build time.

`normalizers/financial_rails.py` produces `data/rails/summary.json`. The deterministic contract has `schema_version`, `metadata`, `summary` and `records`. Metadata includes `built_at`, `latest_source_date`, `oldest_review_date`, cadence and scope. Summary includes `record_count`, all six `stage_counts`, four `category_counts`, `overdue_reviews`, `recurring_records` and `unknown_volume_records`. Records preserve all curated fields and add review/source age, review due date and review status. Coverage counts can be zero; unknown financial measurements cannot.

`normalizers/build_dashboard.py` validates before generating and copying public data. Daily, weekly, monthly and curated-push workflows use it. The consumer composite retains its underlying source dates separately from `built_at`; rebuilding does not make old consumer assessments current. The browser can render curated evidence without a generated summary. Tests verify invalid production claims, source/date validity, missing versus zero values, overdue boundaries, event deduplication, stage stability and static rendering calculations.

## Volume Filtering — Critical Methodology

### The Problem

Gross stablecoin transfer volume ($27.6 trillion in 2024) is not comparable to ACH or Visa. Most of that volume is DeFi protocol interactions, exchange-to-exchange transfers, arbitrage, and treasury management.

### The Approach (v1)

For the initial version, commercial volume estimates are **curated from published sources**, not computed from raw on-chain data. Sources include:

- Visa Onchain Analytics reports
- Brevan Howard digital asset research
- a16z State of Crypto annual reports
- Circle transparency and usage reports

### What's Excluded from "Commercial" Estimates

1. Transfers to/from known smart contract addresses (DEX routers, lending protocols, bridges)
2. Transfers to/from known exchange hot wallets
3. Same-entity transfers (treasury management; tracked separately as institutional financial activity when evidence exists)
4. Arbitrage patterns (rapid round-trip transfers)

### What's Included

- Person-to-person transfers
- Person-to-merchant transfers
- Payroll disbursements
- B2B payments
- Cross-border remittances

Treasury transfers and excluded smart-contract workflows may be economically meaningful institutional activity. Their exclusion only defines this consumer/commercial estimate; Financial Rails can record them under a separately scoped category without adding them to the ACH comparison.

### Transparency Rules

1. **Both raw and filtered numbers are published.** Users can see the difference.
2. **The methodology is documented.** You're reading it.
3. **The estimate is acknowledged as imperfect.** This is a best-effort approximation.
4. **Ranges are preferred over point estimates** where uncertainty is high.

Display format:
```
Estimated Commercial Volume: $132B/quarter
(filtered from $3,550B gross volume — 3.7% of total)
```

## Stablecoin Supply vs. M1

- **Stablecoin supply:** Total market capitalization of US-issued and major stablecoins (USDC, USDT, others) from DefiLlama Stablecoins API.
- **M1 money supply:** Federal Reserve M1SL series from FRED API. M1 includes currency in circulation, demand deposits, and other liquid deposits.
- **Ratio:** Total stablecoin supply / M1 money supply, expressed as a percentage.

Milestones are set at 1%, 2%, 5%, and 10% of M1.

## ACH Comparison

- **ACH data:** Nacha quarterly reports and Federal Reserve FedACH statistics. ACH processed approximately $77 trillion across ~31 billion transactions in 2023.
- **Comparison metric:** Estimated commercial stablecoin volume / ACH volume, expressed as a percentage.
- **Important note:** This comparison is directional, not precise. ACH includes all electronic fund transfers (payroll, bill pay, B2B). The stablecoin commercial estimate includes only a subset of comparable payment types.

## Cross-Border Remittance

- **Traditional providers:** Western Union and MoneyGram quarterly earnings reports (publicly traded: WU, MGI). Wise (WISE.L) quarterly transfer volumes.
- **Stablecoin estimates:** Curated from Circle cross-border reports, exchange geographic data, and academic research.
- **World Bank data:** Bilateral Remittance Matrix (annual) for total US outbound volume.
- **Cost comparison:** World Bank Remittance Prices Worldwide database for traditional costs; stablecoin costs estimated from average transaction fees across chains.

## Treasury Market Integration

- **Circle:** Monthly transparency reports disclosing reserve composition (primarily short-term Treasuries and repo agreements).
- **Tether:** Quarterly attestation reports from BDO Italia.
- **T-bill market:** Total outstanding Treasury bills from Treasury.gov TreasuryDirect data.
- **Ratio:** Total stablecoin T-bill holdings / total outstanding T-bills.

## Tax Treatment

Tax treatment signals are tracked as binary milestones. Current status is assessed qualitatively:

| Friction Level | Criteria |
|---------------|----------|
| **High** | Every stablecoin conversion is a taxable event (current state) |
| **Medium** | De minimis exemption exists for small transactions |
| **Low** | Regulated stablecoins treated as cash equivalents by IRS |
| **None** | No tax distinction between USD and regulated stablecoins |

## Data Freshness

| Data Type | Source | Frequency | Lag |
|-----------|--------|-----------|-----|
| Stablecoin supply | DefiLlama API | Daily | ~1 hour |
| M1 money supply | FRED API | Monthly | ~2 weeks |
| Commercial volume | Curated estimates | Quarterly | ~1 month |
| ACH volume | Nacha reports | Quarterly | ~2 months |
| Remittance | World Bank + earnings | Quarterly | ~2 months |
| Adoption events | Manual curation | Weekly target; inspect actual dates | Varies |
| Financial Rails | Primary-source review | Every 30 days per record | Source, event and review dates shown separately |
| GENIUS Act milestones | Federal Register | Weekly | ~1 day |
| Treasury reserves | Issuer reports | Monthly | ~2 weeks |
| Tax treatment | IRS publications | Event-driven | ~1 day |
| Yield rates | Platform websites | Weekly | ~1 day |

## What This Dashboard Is Not

- **Not pro-stablecoin advocacy.** If adoption stalls, the dashboard shows that.
- **Not investment advice.** Nothing is a recommendation to buy, hold, or use stablecoins.
- **Not a stablecoin comparison tool.** It tracks aggregate adoption, not individual issuer quality.
- **Not global.** US market only.
- **Not real-time.** Designed for tracking trends over months and years.
