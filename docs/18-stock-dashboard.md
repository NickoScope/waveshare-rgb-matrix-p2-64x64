# Stock market dashboard on the panel

The owner's brief, 2026-09-15 08:37: a market screen with charts of indices or
chosen tickers, and a chart of the investment portfolio's results with
dividends and with the cost of holding the positions. Tickers are entered in
the web portal; dividend amounts and position fees are pulled in. The period
is adjustable from 2000 to now. "Professional dashboard" level.

This page collects what is settled and what is measured. Design decisions
follow the owner's answers to the questions at the end.

## Data source, probed 2026-09-15 08:40 from the Mac

**Yahoo Finance chart API v8**, no key, no login:
`https://query1.finance.yahoo.com/v8/finance/chart/<symbol>?range=<r>&interval=<i>&events=div,split`

| Request | Answer |
|---|---|
| `^GSPC`, `range=max&interval=1mo` | 169 monthly points, 1984-12 → 2026-09, 19.9 KB |
| `^FCHI`, max, monthly | 440 points from 1990-02, 43.8 KB |
| `VOO`, max, monthly | 193 points from 2010-10, **63 dividends, 1 split**, 25.6 KB |
| `AAPL`, 5y, weekly | 262 points, 20 dividends, 31.1 KB |
| `^GSPC`, 1y, daily | 251 points, 26.5 KB |

What every answer carries:
- `timestamp[]`, `open/high/low/close/volume[]`;
- **`adjclose[]`**: the close adjusted for dividends and splits, which is the
  total-return series a "with dividends" chart needs;
- `events.dividends`: each cash dividend with its date and amount;
- `meta.currency`, `meta.instrumentType` (INDEX, ETF, EQUITY).

**Not verified:** how long the endpoint stays open without a key. It is not a
documented public API; Yahoo has closed `v7/finance/quote` to key-less callers
("User is unable to access this feature", seen 2026-09-15) while `v8/chart`
still answers. The design must fail soft: the last lists stay in flash and the
page says how old they are.

**TLS.** `query1.finance.yahoo.com` chains to **DigiCert Global Root G2**,
present in macOS's system root store. To pin, as the rail board pins ISRG.

**Expense ratios**, probed 2026-09-15 08:45: `GET /v1/test/getcrumb` on
`query2.finance.yahoo.com` gave an 11-character crumb (the `fc.yahoo.com`
visit answered 404 and set no cookie, and the crumb worked anyway). Then
`quoteSummary/<symbol>?modules=fundProfile,price&crumb=...`:

| Symbol | Type | Currency | `annualReportExpenseRatio` |
|---|---|---|---|
| VOO | ETF | USD | 0.0003 (0.03 %) |
| SPY | ETF | USD | 0.000945 |
| IWDA.AS | ETF | EUR | 0.002 |
| VWCE.DE | ETF | EUR | **none** |
| AAPL | EQUITY | USD | none, as expected |

So the TER can be pulled for most funds, and the portal needs a manual field
for the ones Yahoo does not carry. Two extra requests per refresh, ~2.5 KB
each. **Not verified:** how long a crumb stays valid, and whether the
crumb-less path keeps working.

**Fallbacks probed and rejected:**
- Stooq CSV: behind a JavaScript proof-of-work challenge now (2026-09-15); not
  reachable from a microcontroller.
- Alpha Vantage: 25 calls/day on the free tier; daily-adjusted series is a
  premium endpoint. Not probed, from its published pricing page. **Not verified.**

## Sizes on the panel

Monthly resolution for 2000 → now is 320 points per ticker. As floats that is
1.3 KB; the JSON answer is 20–45 KB, parsed in PSRAM as the rail board does.
Ten tickers at monthly resolution: under 0.5 MB of PSRAM, of which the panel
has 16 MB. Internal heap is the tight one (~40 KB free); the fetch task follows
the rail board pattern, 12 KB stack, one at a time under the net lock.

## What "cost of holding a position" can mean

| Meaning | Where it comes from | Automatic? |
|---|---|---|
| ETF / fund expense ratio (TER), % a year | Yahoo `fundProfile`, with a crumb | yes, if the crumb flow holds |
| Broker commission per trade | the owner's broker | no: a setting, per trade or per position |
| Custody or account fee, % a year | the owner's broker | no: a global setting |
| Margin interest | the broker | no; out of scope unless asked |

## Open questions for the owner

1. Yahoo as the source, with no key and the risk that it closes one day?
2. "Расходы на обслуживание позиций": the fund's TER pulled automatically,
   plus a manual commission per trade and an annual custody %? Or something
   else?
3. Portfolio positions: ticker, quantity, purchase date, purchase price (or
   the price on that date, filled in). Several lots per ticker?
4. Currency: show each ticker in its own currency (USD, EUR) and the portfolio
   in one (EUR? USD?), converting with `EURUSD=X` history from the same source?
5. Default indices to show before anything is entered: S&P 500, NASDAQ, CAC 40,
   DAX? Others?
