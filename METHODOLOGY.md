# Methodology

How The Stablecoin Signal computes layer statuses, filters volume data, and tracks adoption signals.

## The Interchangeability Ladder

Each of the five layers is rated independently:

| Rating | Criteria |
|--------|----------|
| **Not Started** | No meaningful activity in this layer |
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

Layer statuses are updated manually as events occur. The `data/adoption/layers.json` file is the source of truth.

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
3. Same-entity transfers (treasury management)
4. Arbitrage patterns (rapid round-trip transfers)

### What's Included

- Person-to-person transfers
- Person-to-merchant transfers
- Payroll disbursements
- B2B payments
- Cross-border remittances

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
| Adoption events | Manual curation | Weekly | ~1 day |
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
