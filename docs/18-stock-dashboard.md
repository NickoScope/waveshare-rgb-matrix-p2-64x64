# Stock market dashboard on the panel

The owner's brief, 2026-09-15 08:37: a market screen with charts of indices or
chosen tickers, and a chart of the investment portfolio's results with
dividends and with the cost of holding the positions. Tickers are entered in
the web portal; dividend amounts and position fees are pulled in. The period
is adjustable from 2000 to now. "Professional dashboard" level.

His answers, 08:41–08:43:
- **Fees:** only the funds' own fees (TER) for now. No broker commissions.
- **Positions:** ticker, quantity, purchase date. The purchase price is the
  price on that date, from the history.

- **Currency:** each ticker in its own currency (08:44). The portfolio
  currency he did not name: EUR by default, converted with Yahoo's `EURUSD=X`
  history, USD selectable.
- **Default indices:** S&P 500 `^GSPC`, NASDAQ `^IXIC`, CAC 40 `^FCHI`,
  DAX `^GDAXI`, changeable in the portal (08:44).

Taken as defaults, because he did not say and each has one sensible reading:
- **Source:** Yahoo Finance, no key. The only source probed that works from a
  microcontroller and carries dividends.
- **Lots:** one row is one purchase; the same ticker may appear in several
  rows.

Status: **designed; the firmware is being built by a helper on
`wip/market-board`** (started 2026-09-15 ~09:00). Nothing on the panel yet.

## Data source, probed 2026-09-15 08:40 from the Mac

**Yahoo Finance chart API v8**, no key, no login:
`https://query1.finance.yahoo.com/v8/finance/chart/<symbol>?period1=<epoch>&period2=<epoch>&interval=<i>&events=div,split`

| Request | Answer |
|---|---|
| `^GSPC`, `range=max&interval=1mo` | 169 monthly points, 1984-12 → 2026-09, 19.9 KB |
| `^FCHI`, max, monthly | 440 points from 1990-02, 43.8 KB |
| `VOO`, max, monthly | 193 points from 2010-10, **63 dividends, 1 split**, 25.6 KB |
| `AAPL`, 5y, weekly | 262 points, 20 dividends, 31.1 KB |
| `^GSPC`, 1y, daily | 251 points, 26.5 KB |
| `^IXIC`, `period1`=2000-01-01, monthly | 322 points, 2000-01 → 2026-09, 35.0 KB |
| `^GDAXI`, same | 322 points, EUR, 33.6 KB |
| `IWDA.AS`, same | 206 points from 2009-08, EUR, no dividends (accumulating), 23.3 KB |
| `EURUSD=X`, same | 275 points, **from 2003-12**, 30.5 KB |

What every answer carries:
- `timestamp[]`, `open/high/low/close/volume[]`;
- **`adjclose[]`**: the close adjusted for dividends and splits, which is the
  total-return series a "with dividends" chart needs;
- `events.dividends`: each cash dividend with its date and amount;
  `events.splits` with numerator and denominator;
- `meta.currency`, `meta.instrumentType` (INDEX, ETF, EQUITY, CURRENCY),
  `meta.exchangeTimezoneName`.

**Not verified:** how long the endpoint stays open without a key. It is not a
documented public API; Yahoo has closed `v7/finance/quote` to key-less callers
("User is unable to access this feature", seen 2026-09-15) while `v8/chart`
still answers. The design fails soft: the last series stay in flash and the
page says how old they are.

**TLS.** `query1.finance.yahoo.com` chains to **DigiCert Global Root G2**
(sha256 fingerprint `CB:3C:CB:B7:60:31:E5:E0:13:8F:8D:D3:9A:23:F9:DE:47:FF:C3:5E:43:C1:14:4C:EA:27:D4:6A:5A:B1:CB:5F`,
valid to 2038-01-15), present in macOS's system root store. Pinned, as the
rail board pins the ISRG roots.

**Expense ratios**, probed 08:45: `GET /v1/test/getcrumb` on
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
for the ones Yahoo does not carry. **Not verified:** how long a crumb stays
valid, and whether the crumb-less path keeps working.

**Fallbacks probed and rejected:**
- Stooq CSV: behind a JavaScript proof-of-work challenge now (2026-09-15); not
  reachable from a microcontroller.
- Alpha Vantage: 25 calls/day on the free tier; daily-adjusted series is a
  premium endpoint. From its pricing page, not probed. **Not verified.**

## A fact that shapes the fee figure

**A fund's price is already net of its TER.** The fee is taken from the fund's
assets every day, so the chart drawn from Yahoo's prices is the return after
fees. Subtracting the TER again would count it twice. The dashboard therefore:
- draws the real curves, which are net of fees;
- shows **"fees paid"** as an estimate for information: for each month,
  position value × TER / 12, summed over the period;
- can draw the gross-of-fees curve as a dashed line, off by default.

## Design

### Module

`src/market/`, behind `-DMARKET_ENABLED`. Needs the knob build
(`CONTROL_ENCODER_ENABLED`) like the other pages; refused without it. Pages
`PAGE_MARKET_*` after `PAGE_RAILBOARD`; portal key `PANEL_KEY_MARKET`.

| File | Job |
|---|---|
| `market_model.h/.cpp` | series store, portfolio maths; plain C++, host-testable |
| `yahoo_direct.h/.cpp`, `yahoo_roots.h` | the fetch task, the crumb, the parser |
| `market_page.cpp` | the four pages and the knob |
| `market_settings.h` | NVS namespace `market` |
| `README.md` | the contract, the API, what is measured |

### Data on the panel

- **Series** per symbol, in PSRAM: `ts[]`, `close[]`, `adjclose[]` as
  `uint32/float/float`, dividends `(ts, amount)`, splits `(ts, ratio)`, meta
  (currency, type, name, TER, fetched-at). At most 1400 points.
- **Resolution by period:** up to 2 years weekly (`1wk`), longer monthly
  (`1mo`). At 128 px wide, more would not show.
- **Cache** on LittleFS, `/market/<symbol>.bin`, written after every good
  fetch and read at boot, so the page shows at once and survives reboots.
- **Fetch policy:** only while a market page is on screen (the owner's rule
  for every board), when the cache is older than `refreshH` (default 6 h),
  and after a portal save. One symbol at a time, under the net lock, task on
  core 0 at priority 0 with a 12 KB stack, body in PSRAM (cap 128 KB), parsed
  with an ArduinoJson filter that keeps only the fields above. TER once per 30
  days per fund.
- **Internal heap gate:** as the rail board, no fetch under 28 KB free.

### Portfolio maths

For a lot `(symbol, qty0, date)`:
- `t0` = first point at or after `date`; `p0 = close[t0]`.
- `qty(t)` = `qty0` × product of split ratios between `t0` and `t`.
- Value in the portfolio currency: `qty(t) × close(t) × fx(t)`, where `fx`
  converts the symbol's currency (EUR = 1; USD via `EURUSD=X`; others
  refused with a message in the portal).
- Total return with dividends reinvested: `value0 × adjclose(t)/adjclose(t0)
  × fx(t)/fx(t0)`.
- Cash dividends received: sum over dividends after `t0` of
  `amount × qty(at that date) × fx`.
- Fees paid (estimate): sum over months of `value(t) × TER / 12`.
- Portfolio curves are sums over lots; the cost basis is the sum of `value0`.
- Before 2003-12 there is no EUR/USD history from this source; a lot older
  than that uses the first rate and the page says "FX from 2003".

### Pages, 128×64

Four pages, the knob steps them; the carousel gives each 20 s.

1. **Overview**: four tiles of 64×32, one per index: name, last, period
   change in green/red, a sparkline of the period.
2. **Ticker detail**, one per chosen ticker: header with the name, the last
   price and the period change; a line chart with the period's high and low
   labelled; year ticks along the bottom; the period label ("2000→", "5Y").
3. **Portfolio**: header "PORTFOLIO €123,456 +48.2%"; two lines, price value
   and total return with dividends; footer "DIV €4,210  FEES €312".
4. **Holdings**: one row per symbol: symbol, weight %, return %, in the rail
   board's row style, looping when they overflow.

Knob: rotate steps the pages; click enters; inside, rotate steps the period
preset (1Y, 3Y, 5Y, 10Y, since 2000) and a toast names it.

### Portal card "Market"

- tickers: up to 8 rows, symbol plus an optional display name;
- positions: up to 16 rows: symbol, quantity, purchase date;
- period: start year 2000..now, and the presets;
- portfolio currency: EUR or USD;
- refresh, hours; gross-of-fees line on/off;
- TER override per symbol, %, for funds Yahoo does not carry;
- diagnostics: per symbol the points, the fetched-at, the last HTTP code,
  the crumb state; heap before and min during the last fetch.
- `GET /api/market`, `POST /api/market` JSON only, as the other cards.

### Checks

- `tools/market/market_host_test.cpp` + `check_market.py`: the parser and the
  maths against a Python reference on the samples saved from today's probes.
- `tools/market/render.py`: the four pages from the same constants, PNG
  previews at 6× and 1:1, committed.
- Flag matrix rows: "market + knob" builds; "market without the knob" is
  refused; market joins "everything".

## Measured on the panel

Nothing yet. To measure: fetch time per symbol, JSON peak, internal heap min
during a fetch, the render time of the chart pages, the cache read at boot.
