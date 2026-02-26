# The Stablecoin Signal

Real-time dashboard tracking when US dollars and stablecoins become functionally interchangeable.

**Live dashboard:** [jschulman.github.io/stablecoin-signal](https://jschulman.github.io/stablecoin-signal)

## The Thesis

There is a tipping point when converting between USDC and USD becomes unnecessary. The dashboard tracks the signals indicating how close we are to that moment.

## The Interchangeability Ladder

| Layer | Name | Status | What It Means |
|-------|------|--------|--------------|
| 1 | **Hold** | Emerging | Banks custody stablecoins alongside USD |
| 2 | **Earn** | Emerging | Payroll platforms disburse stablecoins |
| 3 | **Spend** | Emerging | Merchants accept stablecoins directly |
| 4 | **Borrow** | Not Started | Banks treat USDC as USD-equivalent collateral |
| 5 | **Invisible** | Not Started | Apps abstract the difference away |

Layer 5 is the tipping point. The dashboard tracks how each layer is developing.

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
data/                 Curated JSON data files (trigger files)
  onchain/              Supply, volume, wallets
  remittance/           Cross-border comparison
  adoption/             Interchangeability layers + events
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

**Automated:** GitHub Actions run collectors daily/weekly/monthly.

**Manual (trigger files):** Edit any JSON in `data/`, push, and the dashboard rebuilds. Key files:
- `data/adoption/layers.json` — Update layer statuses, add events
- `data/regulatory/genius_act.json` — Update GENIUS Act milestones
- `data/tax/status.json` — Update IRS guidance
- `data/onchain/volume.json` — Add commercial volume estimates
- `data/remittance/comparison.json` — Add quarterly remittance data

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
