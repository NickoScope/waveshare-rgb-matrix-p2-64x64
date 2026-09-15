# Stock market dashboard on the panel

The owner's brief, 2026-09-15 08:37: a market screen with charts of indices or
chosen tickers, and a chart of the investment portfolio's results with
dividends and with the cost of holding the positions. Tickers are entered in
the web portal; dividend amounts and position fees are pulled in. The period
is adjustable from 2000 to now. "Professional dashboard" level.

His decisions, 08:41–09:14:
- **Fees:** only the funds' own fees (TER). No broker commissions.
- **Positions:** a percentage allocation, one row per ticker with its target
  weight. The purchase price is the price on the entry date, from history.
- **Currency:** each ticker in its own currency; the portfolio in EUR by
  default, USD selectable.
- **Default indices:** S&P 500 `^GSPC`, NASDAQ `^IXIC`, CAC 40 `^FCHI`,
  DAX `^GDAXI`, changeable in the portal.
- **Rebalancing:** an option, every 31 December back to the target weights;
  a checkbox chooses which result the panel shows.
- **Source:** Yahoo Finance, with the risk that it closes one day.
- **Process:** the design went to the LLM council (two consultations, 09:01
  and 09:02), then to him; code only after his approval. Code is judged by
  the audit gate, not the council.
- **Where it runs (09:13): the maths and the data live in Home Assistant.**
  The panel only shows what HA has computed, with the selections made in
  the panel's web portal (period, tickers, currency, rebalance on/off).
- **Cash (09:13, made precise 09:23):** one cash row in the portfolio.
  Dividends paid, extra contributions, and the share of a position whose
  fund did not exist yet all sit in cash. On 31 December, in both modes,
  the cash goes into positions; only the shares of funds that still do not
  trade stay in cash, and each of those goes into its position on the first
  31 December after the fund starts trading.
- **The portal (09:19):** a page of its own, "professional settings but
  light and intuitive, not convoluted".
- **Live during trading (09:19):** not static data; the screen updates as
  fast as the free services deliver. Measured below: once a minute.
- **A tape on top (09:19):** a scrolling line of the main exchanges, open or
  closed, on every market page. The council's "no marquee" rule is
  overridden for this one row by the owner.

Taken as defaults, because he did not say: the initial capital is a setting,
10 000 in the portfolio currency; extra contributions are a setting, 0 by
default; the inception date is a setting, default 2000-01-01.

**Status: v3, waiting for the owner's approval of the previews. No code
written.** The helper that had started the on-device version was stopped;
its worktree `wip/market-board` holds only the saved Yahoo samples.

## Why Home Assistant, after the council

The council was asked with HA as option B and rejected it only because the
owner's rule at the time was "no home server"; on the data side every
councillor called it the most reliable option. The owner chose it himself
at 09:13. What decides it:
- the portfolio is a backtest engine: in Python with pandas it is a day's
  work and easy to test against a reference; on the ESP32 in 40 KB of
  internal heap it is a week with risk, and every error means a reflash;
- when Yahoo closes, the source changes in one Python file, not in firmware;
- daily history from 2000 is kept whole, and every window, both rebalance
  modes, CAGR and drawdown are precomputed; the panel picks a ready curve
  and switches instantly;
- the panel's memory is not involved; the page is as simple as the media
  player's: receive over MQTT, draw.

The rail and flight boards stay direct: there one answer becomes rows, and
that is a different class of task.

## What the councils changed (2026-09-15)

Three models (GPT-5.6, Gemini 3.1 Pro, Grok 4.5) plus a devil's advocate
(DeepSeek V4 Pro), twice: architecture and maths; the dashboard's UI. Both
verdicts, unanimous: not the v1 design. The corrections, kept in v3:

1. **Two clearly named series, never mixed.** PX = prices only; the main
   value = the ledger (positions + cash), which is what the owner's cash
   model gives. `adjclose` is not used for the portfolio at all now, only
   for a total-return benchmark.
2. **Inception is separate from the chart window.** v1 tied the entry to
   the period preset. Inception is a setting; the preset only changes what
   is visible.
3. **FX direction defined.** `EURUSD=X` is USD per EUR: a USD price in EUR
   is `close / EURUSD`.
4. **Rebalancing is a step-by-step ledger simulation**, not a formula.
5. **Fees are an estimate and say so:** `TER DRAG ~`, computed with today's
   TER because the historical TER is not available.
6. **No frozen FX before 2003-12:** ECB monthly reference rates for
   1999–2003 (ECB Data Portal, series `EXR.M.USD.EUR.SP00.A`; the app
   fetches them, nothing is typed from memory).
7. **Entry and rebalance prices are bar closes**, with the effective date
   reported. With daily data on HA this is the close of the first trading
   day on or after the date.
8. **The portfolio is a hypothetical backtest**; the portal says so.
9. **A provider seam and a versioned store** so the source can change.
10. **A consistent snapshot:** the panel shows nothing half-refreshed; every
    payload carries its as-of.
11. **UI as "a departure board for money":** one primary read per page, the
    house style of the rail and flight boards, as-of on every page, YTD,
    signs with colours, STALE and DATA ERR states, a glossary, number-format
    rules, and a 12-point preview checklist.

Council points that HA makes moot: the on-device TLS heap, the 12 KB task
stack, the JSON peak, the crumb lifetime on the device, the cache CRC on
LittleFS (the panel keeps only the last payloads, small), the trust set of
TLS roots.

## Data source, probed 2026-09-15 08:40 from the Mac

**Yahoo Finance chart API v8**, no key:
`https://query1.finance.yahoo.com/v8/finance/chart/<symbol>?period1=&period2=&interval=1d|1wk|1mo&events=div,split`

| Request | Answer |
|---|---|
| `^GSPC`, `range=max&interval=1mo` | 169 monthly points, 1984-12 → 2026-09, 19.9 KB |
| `^FCHI`, max, monthly | 440 points from 1990-02, 43.8 KB |
| `VOO`, max, monthly | 193 points from 2010-10, **63 dividends, 1 split**, 25.6 KB |
| `AAPL`, 5y, weekly | 262 points, 20 dividends, 31.1 KB |
| `^GSPC`, 1y, daily | 251 points, 26.5 KB |
| `^IXIC`, `period1`=2000-01-01, monthly | 322 points, 35.0 KB |
| `^GDAXI`, same | 322 points, EUR, 33.6 KB |
| `IWDA.AS`, same | 206 points from 2009-08, EUR, no dividends (accumulating), 23.3 KB |
| `EURUSD=X`, same | 275 points, **from 2003-12**, 30.5 KB |

Every answer carries `timestamp[]`, `close[]` (split-adjusted), `adjclose[]`
(split- and dividend-adjusted), `events.dividends` (date, amount, split-
adjusted), `events.splits`, `meta.currency`, `meta.instrumentType`. Checked
on VOO's 2013 1:2 reverse split: close 160.88 pre-split in the data (real
~80), dividend 0.786 (real 0.393). So quantities are never multiplied by
split ratios. Monthly bars are stamped at the month's start and close at its
end; a "today" point is appended.

**Expense ratios** need Yahoo's crumb: `GET /v1/test/getcrumb` on `query2`
worked without a cookie on 2026-09-15; then
`quoteSummary/<symbol>?modules=fundProfile&crumb=`: VOO 0.03 %, SPY 0.0945 %,
IWDA.AS 0.20 %, VWCE.DE none, AAPL none (a stock). A manual TER per symbol
covers the funds Yahoo lacks.

In Python the `yfinance` library wraps all of this, crumb included. The app
uses it; the samples saved on 2026-09-15 stay as test fixtures.

**Not verified:** how long the endpoint stays key-less (Yahoo has already
closed `v7/finance/quote`). On HA the source is one adapter; the store is
versioned; the panel keeps the last payloads.

**Fallbacks probed and rejected:** Stooq (JavaScript challenge, 2026-09-15);
Alpha Vantage (25 calls/day, adjusted series premium; from its pricing page,
not probed).

### Live quotes, probed 2026-09-15 09:19–09:21 CEST (Paris and Frankfurt open)

- `v8/chart?range=1d&interval=1m` for `^GDAXI`, `^FCHI`, `^FTSE`: the last
  1-minute bar and `regularMarketTime` sat **15 minutes behind** the clock
  (lag 902–906 s on every probe), and advanced by one minute between two
  probes 63 s apart. So Yahoo updates the delayed price **once a minute**.
  That is the refresh period during trading: **60 s**.
- **US exchanges not yet measured** (closed at probe time): to check at
  15:35 CEST whether Yahoo's US prices are real-time or delayed. A one-time
  scheduled check is set.
- `meta.currentTradingPeriod.regular` gives each symbol's session start and
  end in UTC (Paris 07:00–15:30Z, New York 13:30–20:00Z, Tokyo
  00:00–06:30Z), and `regularMarketTime`, `regularMarketPrice`,
  `chartPreviousClose`, `regularMarketDayHigh/Low`, `fiftyTwoWeekHigh/Low`.
- **One request for many symbols:** `v7/finance/spark?symbols=A,B,C&range=1d&interval=5m`
  answered for seven symbols at once, 15 KB in 0.35 s, with the same meta.
  So the live poll is **one spark request a minute** for every symbol on the
  panel, only while at least one of their exchanges is open, plus one
  `v8/chart` 1-minute request for the ticker shown on the TICKER page for
  its intraday line.
- **Rate limits:** Yahoo publishes none for these endpoints. One request a
  minute is within what `yfinance` users do daily; on a 429 the app backs
  off to 5 min, then 15. **Not verified** over days.

### Exchange open/closed, for the tape

Two sources, cross-checked: the `exchange_calendars` Python package
(sessions and holidays for XNYS, XNAS, XPAR, XETR, XLON, XAMS, XTKS, ...)
and Yahoo's `currentTradingPeriod`. A session that the calendar says is
open while `regularMarketTime` has not moved for 20 minutes is shown as
STALE, not OPEN. The tape carries: NYSE, NASDAQ, LSE, XETRA, EURONEXT (Paris
and Amsterdam), TOKYO by default; the owner chooses in the portal.

## Ready-made Home Assistant integrations, checked 2026-09-15 09:30

The owner asked what exists already, official or on HACS.

**Official (core), category Finance**, from the docs repository's front
matter (`ha_category: Finance`): alpha_vantage, bitcoin, blockchain,
coinbase, currencylayer, etherscan, fints, firefly_iii, fixer, kraken,
monarch_money, monzo, nordpool, openexchangerates, ripple, simplefin,
starlingbank. For stocks that is **Alpha Vantage alone** (a key, 25
calls/day on the free tier; adjusted history is a premium endpoint per its
pricing page, not probed). The rest is crypto, banking and FX rates with
keys. Nothing gives daily history from 2000 or dividend events.

**HACS, from the store index cached on the owner's HA** (none installed):

| Repository | Stars, last push, licence | What it does | For us |
|---|---|---|---|
| `iprak/yahoofinance` | 122, 2026-04, MIT | Yahoo quotes as sensors: `regularMarket*`, 52-week, dividend rate and yield, `target_currency`; `scan_interval` ≥ 30 s (default 6 h); "Delayed Quote" | quotes only; no history, no dividend events |
| `derspe/ha-easy-stock` | 18, 2026-09-08, MIT | Yahoo quotes, a Lovelace sparkline card, 1M/YTD/1Y charts from daily closes, currency conversion, no key | a nice HA dashboard card, if the owner wants stocks in HA's own UI |
| `Chreece/HA-Investment` | 0, 2026-09-12, MIT | a private portfolio with lots and cost basis; dividends, cash and rebalancing are "on the roadmap" | too new; the parts we need are not built |
| `ad-ha/atw` | 8, 2025-02, GPL-3.0 | virtual buy/sell wallet on Yahoo and CoinGecko | no dividends, no backtest; GPL |
| `nuggetz/ha-tradepulse` | 0, new | real-time US prices, news, insider trades; Finnhub key optional | no history |
| `T-leco/investing_portfolio`, `cubinet-code/ha-parqet-companion`, `MichelFR/ha_ghostfolio`, `FaserF/ha-traderepublic`, `Smart-Home-Assistant-UK/homeassistant-trading212`, `Poshy163/HomeAssistant-Sharesight`, `jippi/hass-nordnet`, `custom-components/sensor.avanza_stock` | small | readers of a real account at one broker or portfolio service | only if the owner wants his real broker account on the panel one day |

**Installed on the owner's word, 09:31–09:45:** `derspe/ha-easy-stock`
v0.5.0 through HACS, HA restarted, four config entries (S&P 500 `^GSPC`,
NASDAQ `^IXIC`, CAC 40 `^FCHI`, DAX `^GDAXI`; entities `sensor.s_p_500`,
`sensor.nasdaq`, `sensor.cac_40`, `sensor.dax`; `scan_interval` 900 s, the
integration's default, changeable per entry under Configure), and a new
dashboard **Биржа** (`/stock-market/indices`) with the `easy-stock-card`
(currency RAW, 1-day range, medium tiles) and four tile cards showing the
value, the day's change and the market state; at 09:40 a second section
"Фонды" with VOO (`sensor.voo`, USD) and IWDA.AS (`sensor.iwda`, EUR), their
own currencies. Indices work: CAC and DAX
reported `REGULAR` and `price_is_live: true` during the Paris session. Not
yet looked at in a browser. Adding a ticker is Settings → Devices &
Services → Add integration → Easy Stock → symbol.

**Conclusion.** Nothing computes what the brief asks for: a percentage
allocation bought at a date, dividends into cash, a yearly rebalance,
windows from 2000. That stays our AppDaemon app on `yfinance`. Two things
are reusable: `yfinance` itself (history, dividends, TER, quotes, crumb
handled), and, should the owner want the numbers in HA's own dashboards
too, `ha-easy-stock` for a card. A second Yahoo client from HACS for the
live quotes would add nothing our app does not already do.

## A fact that shapes the fee figure

**A fund's price is already net of its TER.** The fee is taken from the fund's
assets every day, so a curve drawn from prices is the return after fees.
Subtracting the TER again would count it twice. So: the curves stay as they
are; `TER DRAG ~` is shown as an estimate (position value × TER × years,
summed by day, with today's TER); a gross-of-fees line is a counterfactual
(`net × exp(TER × years held)`), dashed, labelled EST, off by default.

## Design v3

### Where things live

| Part | Where | Job |
|---|---|---|
| **The app** `matrix_market.py` | AppDaemon on HA, beside `flight_board.py` and `matrix_media.py`; needs `yfinance`, `pandas`, `exchange_calendars` added to the add-on's `python_packages` (the owner's change in the add-on options) | fetch daily history and dividends, keep the store, compute every window and both modes, poll live quotes during sessions, publish retained payloads over MQTT |
| **The store** | `/addon_configs/a0d7b954_appdaemon/market/` | one Parquet or CSV file per symbol, daily bars from 2000, FX, TER; the ECB table; a `manifest.json` with versions and fetched-at |
| **The page** `src/market/` | the panel, behind `-DMARKET_ENABLED`, needs `MQTT_BUS_ENABLED` and the knob | receive, keep the last payloads in PSRAM and in LittleFS, draw the four pages, the knob |
| **The portal card** | the panel's web portal | the selections; publishes the config; shows the app's status |

### MQTT contract, under `nickoscope_matrix/<dev>/market/`

`<dev>` is the panel's id, as the media player uses (`d20ec8` today).

From the panel, retained:
- `config` `{"v":1, "indices":[..≤8], "tickers":[..≤8], "portfolio":{"capital":10000,
  "currency":"EUR", "inception":"2000-01-01", "contrib":{"amount":0,"every":"year"},
  "rebalance":true, "positions":[{"sym":"VOO","w":50.0,"entry":null},...],
  "ter":{"VWCE.DE":0.22}}, "presets":["YTD","1Y","3Y","5Y","10Y","MAX"]}`.
  A change makes the app recompute and republish.

From the app, retained:
- `status` `{"v":1,"asof":"2026-09-14","fetched":"2026-09-15T07:02Z","state":"ok|stale|error",
  "err":"","symbols":{"VOO":{"asof":"2026-09-12","bars":6700,"ter":0.0003,"terSrc":"yahoo"},...}}`
- `index/<sym>/<preset>` and `ticker/<sym>/<preset>`:
  `{"v":1,"sym":"VOO","name":"VOO","cur":"USD","preset":"5Y","from":"2021-09-13","to":"2026-09-12",
  "last":548.2,"chg":0.124,"hi":552.1,"lo":327.4,"n":128,"min":327.4,"max":552.1,"pts":"<base64>"}`
  where `pts` is 128 `uint16` values scaled between `min` and `max` (256 B,
  344 B in base64), sampled at equal time steps across the window.
- `portfolio/<mode>/<preset>` for `mode` in `hold`, `rebal`:
  `{"v":1,"cur":"EUR","preset":"5Y","from":..,"to":..,"value":123456.0,"chg":0.482,
  "sinceStart":1.85,"cagr":0.071,"mdd":-0.23,"div":4210.0,"terDrag":312.0,"cash":150.0,
  "n":128,"min":..,"max":..,"pts":"<base64>","px":"<base64>","bench":"<base64>","gross":"<base64>"}`
- `holdings/<mode>` `{"v":1,"asof":..,"rows":[{"sym":"VOO","tgt":50.0,"now":53.1,"ret":0.52,
  "entry":"2015-01-02"},...],"cash":{"now":1.2}}`
- `live` (retained, every 60 s while any watched exchange is open):
  `{"v":1,"ts":..,"q":{"^GSPC":{"last":7619.98,"prev":7656.98,"day":-0.0048,"state":"OPEN","asof":..},...}}`
  under 1 900 B for 16 symbols (the app drops the day high/low first).
- `intraday/<sym>` (retained, every 60 s while that exchange is open, only
  for the symbol the panel has selected on TICKER, which the panel publishes
  in `config.ticker`): 128 points across the session, same `pts` encoding.
- `tape` (retained, on every state change and every 15 min):
  `{"v":1,"ts":..,"x":[{"n":"NYSE","s":"OPEN","t":"20:00"},{"n":"LSE","s":"CLOSED","t":"08:00"},...]}`
  where `t` is the next change, in the panel's local time.
- `ha`: `online` / `offline`, the app's will, as the media app does.

Sizes: every payload under 1 900 B, the bus's limit (checked by the app,
which drops the optional lines first). Topics: at most 16 symbols × 6
presets + 2 × 6 + 2 + 2 = 112 retained topics, all under one wildcard
subscription.

The app republishes everything after its daily fetch, after a `config`
change, and every 6 h as a keepalive (`status` only when nothing changed).

### The app

- **HA entities too** (owner, 09:40: "а создания дашборда портфеля там
  нет?"): the app publishes sensors for HA's own dashboards: portfolio
  value, return over the default window and since inception, CAGR, max
  drawdown, DIV, TER drag, cash share, the mode, and one sensor per holding
  (current share, return since entry), plus the exchange states. A
  "Портфель" view on the HA dashboard "Биржа" shows the value line from
  the app's series, the key figures and the holdings table. The settings
  stay in the panel's portal; HA only displays.
- **Live loop:** every 60 s while any watched exchange is open: one spark
  request for all symbols, one chart request for the selected ticker;
  publishes `live`, `intraday/<sym>`, and `tape` when a state changes.
  Outside sessions nothing is polled; `tape` still updates at each
  open/close from the calendar.
- **Fetch:** once a day at 07:00 local, and on a `config` change: daily
  bars, dividends and splits per symbol from 2000 (or the listing), FX
  `EURUSD=X`, TER via `yfinance`'s fund info, the ECB 1999–2003 monthly
  rates once. Retries with back-off; a failed symbol keeps its store and is
  marked in `status`.
- **Store:** one file per symbol; append only new bars; a full refetch when
  a split or a corporate action changes past closes (detected by comparing
  the last 30 stored closes).
- **Timeline:** trading days of the portfolio currency's calendar; each
  series carried forward from its last bar on or before the day; nothing
  interpolated; a symbol exists from its first bar.
- **Windows:** YTD (from the last trading day of the previous year), 1Y,
  3Y, 5Y, 10Y, MAX (from the inception date). Downsampled to 128 points by
  taking the last bar of each equal time slice.

### Portfolio maths, v3: the ledger

Settings: capital `C`, currency, inception `S`, contributions (amount and
period), positions `(sym, w, entry)`, rebalance on/off. `X_s(d)` = portfolio
currency per unit of `s`'s currency on day `d`.

- **Start:** `cash = C` on the first trading day ≥ `S`. For every position
  whose fund has a bar on that day and whose entry (if set) has come:
  `qty_s = C × w_s / (close_s × X_s)`, `cash −= C × w_s`. The weight of a
  position that does not exist yet stays in cash.
- **Each day:** `V_px(d) = Σ qty_s × close_s(d) × X_s(d)` (positions only);
  `V(d) = V_px(d) + cash`. Dividends with an ex-date on `d`:
  `cash += amount × qty_s × X_s(d)`, `DIV += the same`. Contributions on
  their day: `cash += amount`. `TERdrag += qty_s × close_s × X_s × TER_s /
  252` for every fund position.
- **31 December** (the last trading day of the year), in both modes, the
  cash is put to work at the close:
  - **HOLD:** no selling. All cash except the reserved shares goes into the
    positions that trade, in proportion to their target weights.
  - **REBAL:** `V = V_px + cash − reserved`; every position that trades is
    set to `V × w_s / Σ w_trading` (buying or selling at the close).
  - **Reserved cash** = `(C + contributions so far) × Σ w_not_yet_listed`;
    a fund that has started trading by this 31 December is bought now
    (HOLD: with its reserved share; REBAL: through the rebalance) and stops
    being reserved.
  The effective date is reported. No transaction costs, no taxes.
- **Reported per window:** `value` at the end, `chg` = value at the end ÷
  value at the window's start − 1, `sinceStart` = value ÷ (C + contributions)
  − 1, `cagr` when the window ≥ 3 years, `mdd` = the deepest fall of `V`
  from a previous peak inside the window, `div`, `terDrag`, `cash` share.
- **Lines:** `pts` = `V`; `px` = a second run of the same ledger with the
  dividends dropped (the "without dividends" line); `bench` = the first
  index from the same start, price index scaled to `C` (S&P 500 has a
  total-return twin `^SP500TR` on Yahoo; if it answers, the app uses it and
  says so); `gross` = the EST counterfactual, off by default.

**Before the portfolio page is coded:** the app's numbers for a three-fund
allocation are compared with an independent tool (the owner's Excel, or
Portfolio Visualizer) within 0.1 % on the end value.

### Pages, 128×64

House style: black ground; amber headings; white primary; dim
(110/122/128) secondary; green/red only for signed changes, never pure
0/255; amber `STALE`, red `DATA ERR`; at most four semantic colours on a
page. Fonts: 5×7 for primary text, 2× for the one key number, Picopixel
only for secondary rows and the footer. Numbers: tabular, right-aligned;
thousands separators; `12.3K`, `1.24M` when a value would not fit; one
decimal on percentages under 100, none above; a sign always. No motion
except an optional one-shot line draw under 0.5 s on entry; no blinking last
point, no sweep.

**The tape**, rows 0–6 on every market page: `NYSE OPEN  LSE CLOSED  XETRA
OPEN  EURONEXT OPEN  TOKYO CLOSED`, Picopixel, OPEN in green, CLOSED dim,
PRE/POST amber, STALE amber; scrolling 1 px per frame at 20 fps, one loop
every ~20 s. The page area is rows 8–63.

**Live state:** while a symbol's exchange is OPEN its last price carries a
small green mark and the change next to it is the DAY change against the
previous close; the window change stays in its own place. When CLOSED the
label reads CLOSE with the as-of date. On TICKER a thin intraday line of
the session can be shown under the window chart.

1. **MARKETS**: heading `MARKETS` + `AS OF 14 SEP`; the primary index:
   mnemonic (SPX, NDX, CAC, DAX), last at 2×, `+1.2%` for the window, a
   48×16 sparkline; three secondary rows `NDX  26 186  +0.8%`. Click, then
   rotate: which index is primary.
2. **TICKER** (one page; rotate inside it steps the ticker): heading `VOO`
   + window tag; `548.2 USD` at 2× and `+12.4%`; one close-line chart, 128
   wide × ~30 high, three time ticks; footer `HI 552  LO 327` + as-of.
3. **PORTFOLIO**: heading `PORTFOLIO EUR` + `REBAL`/`HOLD` + as-of; `123.5K`
   at 2× and `+48.2%`; one bright value line, the no-dividend line dim
   (setting), the benchmark dim; footer `DIV 4.2K  TER~ 0.3K  CASH 1%`.
4. **HOLDINGS**: heading `HOLDINGS 1/2` + window; rows `VOO  40→43%  +52%`,
   a `CASH` row last; four rows a page, rotate inside pages.

Knob: rotate browses pages; click enters; inside, rotate steps the window
preset (YTD, 1Y, 3Y, 5Y, 10Y, MAX), global for the market pages, shown in a
fixed status row for 1.5 s; on TICKER a second click switches rotate to the
ticker list; click again or 10 s of quiet leaves. The carousel shows the four
pages 20 s each. The preset and the ticker choice are the panel's, kept in
NVS; every preset is already on hand, so switching is instant.

### Glossary

| Label | Meaning |
|---|---|
| LAST | the last available close, with its date; never "live" |
| % | the change over the selected window: last ÷ first in the window − 1, with its sign |
| PX / "no DIV" | the same ledger with dividends dropped |
| DIV | cash distributions received after entry, at Yahoo's event date |
| TER DRAG ~ | estimated cost of the funds' expense ratios; an estimate with today's TER |
| HI / LO | the highest and lowest close in the window |
| CASH | the cash row: dividends, contributions, and the shares of funds not yet listed, until 31 December |
| YTD … MAX | the chart window; MAX = from the inception date |
| AS OF | the date of the oldest series on the page; STALE when older than 3 trading days; DATA ERR when the app reports an error and nothing is stored |
| REBAL / HOLD | which model the page shows |
| TGT → NOW | target weight → current share |

### The panel side

- `src/market/market_model.*`: the payloads decoded into PSRAM; the last
  payloads written to LittleFS `/market/last.bin` so a reboot with HA down
  still shows the page with its as-of.
- `src/market/market_page.cpp`: the four pages and the knob.
- The portal page **Market**, a page of its own in the sidebar (not a card
  in the Panel group), in three plain blocks and one folded "Advanced":
  **Watch** (indices and tickers as chips: type a symbol, add; the app's
  status marks an unknown one), **Portfolio** (the allocation table with a
  live sum bar, capital, currency, inception, the rebalance switch, both end
  values side by side), **Display** (window default, tape exchanges, the
  lines on/off, refresh), and under Advanced: contributions, TER overrides,
  the backtest note, diagnostics. Same JSON API. The page's own JS and CSS
  ship gzipped like the rest of the portal. Indices and tickers ≤ 8 each
  (symbol + display name),
  positions (≤ 16: symbol, target %, optional entry; the sum shown and
  capped at 100 %), capital, currency, inception, contributions, rebalance
  on/off, the lines on/off, TER override per symbol, the app's status per
  symbol, both end values side by side, and a note: hypothetical backtest,
  no taxes, no commissions. `GET/POST /api/market`, JSON only.
- Bus limits: the media merge raised handlers and subscriptions to 8; the
  market page takes one of each.

### Checks before the panel

- `tools/market/market_ref.py` (the same maths, standalone) against the
  app's `compute()` on the saved samples and on synthetic cases: a two-asset
  drift where HOLD and REBAL differ by a hand-checked amount; a late
  listing; FX both ways; a dividend on a rebalance day; contributions.
- The golden match with an independent tool, above.
- `tools/market/render.py`: the four pages from the layout constants, PNG at
  6× and 1:1, with worst-case strings (an 8-character symbol, a six-figure
  negative, `+1,245%`, STALE, DATA ERR, no dividends, a short history).
- `tools/market/check_market.py`: payload sizes under 1 900 B for the largest
  config; the panel's decoder against the app's encoder.
- Flag matrix rows: "market + bus + knob" builds; "market without the bus"
  and "without the knob" are refused; market joins "everything".

### Preview checklist (the council's, merged)

1. The primary number reads from 3 m in 2 s.
2. No more than two large numbers on a page.
3. The window tag is always visible.
4. AS OF, STALE or DATA ERR is always visible.
5. Every change carries a sign; zero is not green.
6. The main line and the no-dividend line cannot be confused.
7. Consistent with the rail and flight boards: black, amber headings, white
   primary.
8. At most four semantic colours on a page.
9. Nothing written inside the chart; HI/LO in the footer.
10. No motion that imitates a live feed.
11. Picopixel only for secondary text.
12. Number formats do not jump between frames; worst-case strings fit.

Then on the panel, from 1.5, 3 and 4 m, by day and in the evening.

## Phases

1. **Previews** of the four pages from `render.py` with real numbers from
   the Python reference on the saved samples → the owner approves against
   the checklist.
2. **The app** with the reference maths, the store, the publisher; the
   golden match.
3. **The panel page and the portal card**; flag matrix; audit gate; flash;
   measure.

## Measured on the panel

Nothing yet. To measure: payload sizes as received, PSRAM for the decoded
set, render time of the chart pages, the boot with HA down.
