# The Stablecoin Signal

Dashboard tracking consumer stablecoin use and blockchain adoption inside ordinary financial operations.

**Live dashboard:** [jschulman.github.io/stablecoin-signal](https://jschulman.github.io/stablecoin-signal)

## The Thesis

Consumer stablecoin adoption and backend financial adoption can move independently. The original ladder tracks the former. The Financial Rails pilot tracks sourced payments, treasury, securities, collateral and fund workflows, including operations that leave the customer experience unchanged. Neither view establishes cash, accounting or tax equivalence.

## The Interchangeability Ladder

| Layer | Name | Status | What It Means |
|-------|------|--------|--------------|
| 1 | **Hold** | Emerging | Banks custody stablecoins alongside USD |
| 2 | **Earn** | Emerging | Payroll platforms disburse stablecoins |
| 3 | **Spend** | Emerging | Merchants accept stablecoins directly |
| 4 | **Borrow** | Not Started | Banks treat USDC as USD-equivalent collateral |
| 5 | **Invisible** | Unmeasured | Consumer currency-awareness threshold lacks a cited survey |

The ladder is a consumer hypothesis, not a gate that institutional adoption must pass. Its legacy assessment remains dated May 29, 2026; the scoped Invisible correction is dated September 25. Backend evidence appears independently at [Financial Rails](https://jschulman.github.io/stablecoin-signal/#financial-rails).

## What This Tracks

| Signal | Source | Update Frequency |
|--------|--------|-----------------|
| Stablecoin Supply vs. M1 | DefiLlama, FRED API | Daily / Monthly |
| Commercial Payment Volume vs. ACH | Curated estimates, Nacha | Quarterly |
| Cross-Border Remittance | World Bank, WU/MGI earnings | Quarterly |
| Wallet Growth & Usage | On-chain data, exchange reports | Monthly |
| Merchant / Payroll / Banking Signals | Manual curation | Weekly |
| GENIUS Act Implementation | Federal Register, agency sites | Weekly |
| Treasury Market Integration | Circle/Tether reports, Treasury.gov | Monthly |
| Tax Treatment | IRS guidance, legislation | Event-driven |
| Stablecoin Yield | Platform rates, DeFi protocols | Weekly |
| Depeg Events | Historical price data | Event-driven |

## The Canary

**Primary:** When a major US payroll platform allows employers to pay in stablecoins and employees to spend without converting, the off-ramp has started dissolving.

**Secondary canaries:**
- Tax equivalence — IRS treats regulated stablecoins as cash equivalents
- Stablecoin > Western Union — Cross-border displacement proven (triggered Q3 2025)
- 1% of ACH — Commercial payment rail competition is real (triggered Dec 2024)
- Top-25 bank custody — Traditional financial system has absorbed stablecoins

## Architecture

```
collectors/           Python scripts fetching live data
  onchain_supply.py     DefiLlama + FRED M1 (daily)
  fed_money_supply.py   FRED M1SL series (monthly)
  regulatory_milestones.py  GENIUS Act status (weekly)
normalizers/
  composite_signal.py   Layer status + key metrics computation
  financial_rails.py    Strict evidence validation + deterministic pilot summary
  build_dashboard.py   Offline validate, generate and copy entry point
data/                 Curated JSON data files (trigger files)
  onchain/              Supply, volume, wallets
  remittance/           Cross-border comparison
  adoption/             Interchangeability layers + events
  rails/                Curated financial-operations evidence + generated summary
  regulatory/           GENIUS Act milestones
  treasury/             T-bill reserve holdings
  tax/                  IRS treatment status
  yield/                Platform rates
  depegs/               Historical depeg events
  composite/            Computed signal
docs/                 Static dashboard (GitHub Pages)
.github/workflows/    Automated collection schedules
```

## How It Updates

**Automated:** GitHub Actions run collectors daily/weekly/monthly and the common dashboard build. Curated data changes run validation and a build on push. Existing branch/docs publication is preserved. These jobs do not research or advance evidence-review dates automatically.

**Manual (trigger files):** Edit any JSON in `data/`, push, and the dashboard rebuilds. Key files:
- `data/rails/evidence.json` — Add or review dated primary evidence; keep the curated `docs/data/rails/evidence.json` mirror identical for source-only previews
- `data/adoption/layers.json` — Update layer statuses, add events
- `data/regulatory/genius_act.json` — Update GENIUS Act milestones
- `data/tax/status.json` — Update IRS guidance
- `data/onchain/volume.json` — Add commercial volume estimates
- `data/remittance/comparison.json` — Add quarterly remittance data

## Financial Rails pilot

The initial records cover Visa settlement for two US banks (December 2025) and DTCC's July 2026 production event. Both are classified as limited production. The sources do not establish sustained usage for these scopes. Cohort volume, market denominators and demonstrated assurance procurement remain unknown. The pilot is selected coverage, not a representative panel or market adoption index.

The schema and conditional evidence requirements are enforced by `normalizers/financial_rails.py` using Python's standard library. No new dependencies are required. Stages include announced, pilot, limited-production, recurring-production, paused and discontinued. Production needs observed execution; recurring production also needs dated repeat evidence. Planned dates never promote records automatically.

```sh
python3 -m unittest discover -s tests
node tests/rails.test.cjs
python3 normalizers/financial_rails.py --validate-only --as-of 2026-09-25
python3 normalizers/build_dashboard.py --as-of 2026-09-25
```

The last command refreshes generated data and copies the methodology and public data into `docs/`. Omit `--as-of` to use today's UTC date. Repeating it for the same evidence and date produces the same rails summary. Source-only previews work without generated rails JSON: `docs/rails.js` reads the curated evidence directly and computes review age using the browser's UTC date. The generated summary is ignored locally; the existing automation can commit it as publishing output.

Serve `docs/` over HTTP to preview. Financial Rails does not depend on Chart.js loading. The public summary contract is documented in [METHODOLOGY.md](METHODOLOGY.md#financial-rails-pilot).

## Design Principles

- **Data, not opinion.** The dashboard presents signals. It does not advocate for stablecoins.
- **US market focus.** Stablecoin adoption varies radically by geography.
- **Interchangeability, not volume.** Gross stablecoin volume ($27.6T in 2024) is mostly DeFi. We track *commercial* adoption.
- **Reproducible.** Every data point links to its source.
- **Not investment advice.** Nothing on the dashboard is a recommendation.

## Family

| Dashboard | Tracks | Question |
|-----------|--------|----------|
| [The Displacement Curve](https://jschulman.github.io/displacement-curve) | AI disruption of professional services | Where are we on the displacement curve? |
| [The Quantum Qanary](https://jschulman.github.io/quantum-qanary) | Quantum progress toward Q-Day | How close are we to Q-Day? |
| **The Stablecoin Signal** | USD/stablecoin interchangeability | When does the off-ramp disappear? |

## Methodology

See [METHODOLOGY.md](METHODOLOGY.md) for how commercial volume is estimated, layer statuses are determined, and data sources are documented.

## License

MIT
