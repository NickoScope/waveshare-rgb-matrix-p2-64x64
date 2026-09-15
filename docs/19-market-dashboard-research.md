# Market dashboards: how the professionals do it (research)

Research for the market screen and portfolio pages of doc 18, done
2026-09-15 10:00–11:00 on the owner's request: (1) how professional
terminals and portfolio trackers lay out a market and portfolio dashboard;
(2) which open-source projects have maths or layouts worth borrowing;
(3) what investors on Reddit and the Bogleheads forum say they want; (4) the
finance methodology behind return figures; (5) an inventory of every setting
such a dashboard exposes, with a Core / Advanced / Skip verdict; (6) ten
improvements to the v3 design, ranked.

Nothing from doc 18 is repeated here: the four pages, the ledger with the
cash row and the 31 December rebalance, the MQTT contract, the Yahoo probes
and the settings already listed there are taken as given. Every claim below
carries its source; "not verified" marks what could not be read first-hand.
Stars and licences are from `gh api repos/<owner>/<repo>` on 2026-09-15.

**How the sources were read.** bogleheads.org answers 403 to any fetch from
this Mac (direct, with a browser User-Agent, and through the Wayback Machine
for 2024–2026 captures); the wiki pages were read from 2021–2022 Wayback
captures and one page through a third-party fetcher. portfoliovisualizer.com
resolves to 0.0.0.0 here (blocked locally), so its FAQ was read through the
same fetcher. Reddit was read through the `.rss` feeds, 45 s apart, with
retries on 429. The rest was fetched directly; PDFs were converted with
`pdftotext`.

## 1. How professionals lay out market and portfolio dashboards

### Terminals

**Bloomberg.** Amber-on-black "started that way for the simple reason that
color monitors were rare in the 1980s"; Bloomberg kept it as a brand mark,
and "a number of competitors have adopted similar black screens" ([Ted Merz,
2021](https://ted-merz.com/2021/06/26/amber-on-black/), a Bloomberg news
executive). The Terminal's default is green for "up" and red for "down";
Bloomberg's UX team estimates 20 000 of its users have red-green colour
vision deficiency, found in its usability lab that "clients were more
accurate, reported greater confidence, and preferred the alternative and
high contrast color sets", and shipped two CVD schemes that use **blue for
up and red for down while keeping amber for non-semantic text**; milder CVD
users struggled mostly with "thinner red and green lines", moderate CVD with
"darker colors on dark backgrounds" ([Bloomberg UX, 2021](https://www.bloomberg.com/company/stories/designing-the-terminal-for-color-accessibility/)).
For portfolios, Bloomberg's PORT function is organised as past / present /
future: a Performance tab with cumulative performance against the benchmark
over a changeable time frame; attribution split into allocation, selection
and currency effects; an intraday view "relative to the prior day's close
prices" that names "today's top and bottom return contributors"
([PORT brochure](https://data.bloomberglp.com/professional/sites/4/Portfolio_and_Risk_Analytics_Brochure4.pdf)).

**TradingView.** A watchlist row shows "Last price, Price change, Percent
price change, and Price change during extended hours"; a table view adds
columns ([Mastering the TradingView watchlists](https://www.tradingview.com/support/solutions/43000745825-mastering-the-tradingview-watchlists/)).
A delayed symbol carries a small **"D"** marker next to the symbol; a
real-time one carries nothing ([TradingView support](https://www.tradingview.com/support/solutions/43000698958-alerts-based-on-real-time-and-non-real-time-symbols/),
from the page summary; not read in full).

**Koyfin.** Portfolio rows: Market Value = quantity × price; Total Gain/Loss
in money and percent; "Annualized Returns (CAGR)" per position; Weight; a
"Weight Adjusted Sum" summary row for portfolio-level returns; input columns
are grey, derived columns white; summary rows can show max, min, average,
median, percentiles, market-cap-weighted averages ([Koyfin help: portfolio
tools](https://www.koyfin.com/help/portfolio-tools-functionality/),
[Mastering portfolio tracking](https://www.koyfin.com/help/mastering-portfolio-tracking-with-koyfin/)).

**LSEG Workspace (ex-Refinitiv Eikon).** Only the product page was reachable
([LSEG](https://www.lseg.com/en/data-analytics/products/workspace)); its
portfolio views are **not verified** here.

### Portfolio trackers and broker pages

| Tool | Primary figure and periods | Return method | Benchmark | Source |
|---|---|---|---|---|
| **Ghostfolio** (open source) | Performance for `Today`, `WTD`, `MTD`, `YTD`, `1Y`, `5Y`, `Max` | ROAI, "Return on Average Investment"; the code also ships MWR, ROI and TWR calculators | one benchmark on the chart (not verified) | [README](https://github.com/ghostfolio/ghostfolio); [calculator/](https://github.com/ghostfolio/ghostfolio/tree/main/apps/api/src/app/portfolio/calculator) has `mwr`, `roai`, `roi`, `twr` |
| **Portfolio Performance** (open source) | dashboard widgets; TTWROR and IRR side by side | TTWROR daily: `1 + r = (MVE + CFout) / (MVB + CFin)`, sub-periods compounded; IRR solved on dated flows. Deposits and withdrawals are external flows (neutralised in TTWROR); dividends and sale proceeds are internal; **fees count, taxes are excluded at security level** | user-chosen securities as benchmark | [time-weighted](https://help.portfolio-performance.info/en/concepts/performance/time-weighted/), [money-weighted](https://help.portfolio-performance.info/en/concepts/performance/money-weighted/) |
| **Sharesight** | total return split into capital gain, dividends, currency gain; "% p.a." only when average years invested ≥ 1 | Modified Dietz (money-weighted); cash accounts excluded from performance but included in value; "a 5% price gain on the first day of ownership annualises to 1,825%", so under a year it shows the holding-period return | index or fund | [return calculation](https://help.sharesight.com/performance_calculation_method/), [annualised](https://help.sharesight.com/absolute-and-annualised-return/), [components](https://help.sharesight.com/au/components-return/) |
| **Interactive Brokers PortfolioAnalyst** | `7D`, `MTD`, `1M`, `YTD`, `1Y`, custom; a **TWR / MWR toggle** | MWR via Modified Dietz (account flows end of day); TWR by geometric linking of sub-periods (deposits start of day, dividends end of day); "TWR is the preferred method of calculating returns by industry standards" | up to 3 benchmarks; widgets: allocation, Max Drawdown, Sortino, Sharpe, Calmar, Alpha, Beta, attribution | [white paper](https://www.interactivebrokers.com/images/common/Statements/MWR-TWR_white_paper.pdf), [dashboard guide](https://www.ibkrguides.com/portfolioanalyst/performanceandstatements/pa_viewingaccountperformance.htm) |
| **Morningstar Portfolio Manager** | total return and personal return; calendar-year and monthly views | personal return = IRR "on an individual scale"; total return assumes a lump sum at the period start | "select indexes" on the chart | [help](https://www.morningstar.com/help-center/portfolio/performance-charting); the article [How to use personal returns](https://www.morningstar.com/articles/204106/how-to-use-personal-returns) returned 404 today, quoted from the search summary |
| **Vanguard personal performance** | personal rate of return | IRR, "the interest rate that a bank would have to pay" to match the balance given the deposits; **as of the last day of the previous month, updated by the third business day**; "do not confuse ... with those posted for funds and indexes", which are time-weighted | — | [Vanguard](https://personal.vanguard.com/us/content/MyPortfolio/performance/LMperfSummaryInfoContent.jsp) (page needs JavaScript; text from the search summary) |
| **Fidelity performance page** | Personal Rate of Return; cumulative and annualized | money-weighted; "customers cannot elect the calculation methodology"; net of fees; "it may be appropriate to compare annualized returns of different periods, but not cumulative returns" | user-selected; "Why is it important to select a benchmark?" is the first FAQ | [Fidelity help](https://www.fidelity.com/webcontent/ap002390-mlo-content/19.09/help/learn_performancereporting.shtml) |
| **Portfolio Visualizer** | end balance, CAGR, IRR when there are cash flows; standard deviation, Sharpe, Sortino, max drawdown | monthly returns; "risk characteristics ... are calculated from monthly returns and annualized, and maximum drawdown is calculated from monthly portfolio balances"; total return, dividends reinvested by default; risk-free = 3-month T-bill (FRED); inflation = CPI-U | any ticker, or a blended series such as `0.6*SPY+0.4*AGG` | [FAQ](https://www.portfoliovisualizer.com/faq) |
| **Simba's backtesting spreadsheet** (Bogleheads) | growth chart and **telltale chart** (portfolio ÷ benchmark) | annual total returns "including dividends", expense-ratio adjustments in `Raw_Data`; benchmark 100 % cash gives nominal growth, 100 % inflation gives real growth | a benchmark portfolio, e.g. 60/40 | [wiki, 2022 capture](https://web.archive.org/web/20220128172554/https://www.bogleheads.org/wiki/Simba's_backtesting_spreadsheet) |

### The conventions, distilled

| Question | What the professionals do | Sources |
|---|---|---|
| Primary figure | portfolio value (or NAV) with the period return next to it; brokers put the *personal* (money-weighted) return first, terminals the time-weighted one | IBKR, Fidelity, Vanguard, Bloomberg PORT above |
| Period labels | a fixed set: `1D`/`Today`, `WTD`, `MTD`, `1M`, `3M`, `6M`, `YTD`, `1Y`, `3Y`, `5Y`, `10Y`, `Max`/`Since inception`; multi-year returns are labelled `(ann.)` | Ghostfolio, IBKR, [ffn labels](https://github.com/pmorissette/ffn/blob/master/ffn/core.py) `3Y (ann.)`, `Since Incep. (ann.)`; Bogleheads spreadsheet 1m/3m/6m/YTD/1y/3y/5y/10y |
| Sign and colour | green up, red down in the West; red up, green down in China, Japan, Taiwan (cultural: red is auspicious) — so colour alone is never the carrier, the sign is | Bloomberg above; [HN thread](https://news.ycombinator.com/item?id=20022959), [Benzinga](https://www.benzinga.com/general/education/21/10/23258001/did-you-know-you-dont-want-to-be-in-the-green-if-youre-trading-in-china-japan-or-taiwan) (secondary; not verified against an exchange style guide) |
| Delayed vs stale | delayed data is labelled by its delay ("15 minutes delayed", a `D` badge, a timestamp visibly behind the clock); the free feeds of Deutsche Börse and LSEG are 15 min behind by regulation (MiFIR Art. 13); stale is judged by quote age *within the session*, and a closed market is a third state, not "stale" | [Deutsche Börse](https://www.mds.deutsche-boerse.com/mds-en/real-time-data/Delayed-data), [LSEG DMD](https://dmd.lseg.com/) (not read), [EODHD](https://eodhd.com/financial-academy/fundamental-analysis-examples/real-time-market-data-reliability-stale-price-detection-rest-fallback-and-websocket-recovery), [andinet.de](https://www.andinet.de/en/finance/securities/delayed_market_data_explained.html) |
| Benchmark | one to three, chosen by the user, drawn from the same start as the portfolio; fund fact sheets use a **composite** index that mirrors the allocation (Vanguard Balanced: 60 % stocks / 40 % bonds) and a "Growth of $10,000" chart | IBKR (up to 3), [Vanguard Balanced Index fact sheet](https://workplace.vanguard.com/assets/corp/fund_communications/pdf_publish/us-products/fact-sheet/F0869.pdf), Portfolio Visualizer blends |
| Drawdown | max drawdown as a number plus its dates; a table of the worst episodes: start, valley, end, days | [quantstats `drawdown_details`](https://github.com/ranaroussi/quantstats/blob/main/quantstats/stats.py) columns `start, valley, end, days, max drawdown, 99% max drawdown`; Wealthfolio `peak_date, trough_date, recovery_date, drawdown_duration_days` |
| Contribution / attribution | per holding: weight × return = contribution; portfolio: allocation, selection, currency effects; Sharesight splits total return into capital, dividends, currency; Wealthfolio into contributions, distributions, income, realized, unrealized, FX effect, fees, taxes, residual | Bloomberg PORT, Sharesight components, [Wealthfolio `performance_model.rs`](https://github.com/afadil/wealthfolio/blob/main/crates/core/src/portfolio/performance/performance_model.rs) |
| Glance vs detail | glance: value, one period change, one line, market state; detail: the period grid, the components, the risk table, the holdings table with weights and gain/loss. The intraday view is a separate mode "relative to the prior day's close" | Bloomberg PORT intraday tab, TradingView watchlist row, Koyfin summary rows |
| Data freshness on the page | brokers state the as-of ("as of the last day of the previous month", "holdings as of the previous business day") | Vanguard, IBKR |

## 2. Open-source projects worth learning from

| Project | Stars, licence | What it computes | Worth borrowing |
|---|---|---|---|
| [ghostfolio/ghostfolio](https://github.com/ghostfolio/ghostfolio) | 9 298, AGPL-3.0 | ROAI shown; MWR, ROI, TWR calculators in `apps/api/src/app/portfolio/calculator/`; activities `BUY, SELL, DIVIDEND, FEE, INTEREST, LIABILITY`; multi-currency; "static analysis to identify potential risks" (X-ray); the FAQ's statement that dividends are not part of ROAI comes from a search summary, **not verified** (the FAQ needs JavaScript) | the period set `Today · WTD · MTD · YTD · 1Y · 5Y · Max`; the idea of a rules-based "X-ray" (concentration, currency, fees) | 
| [portfolio-performance/portfolio](https://github.com/portfolio-performance/portfolio) | 4 073, EPL-1.0 | TTWROR and IRR with the exact flow treatment above; volatility, drawdown widgets; trade calendars; PDF importers | the **daily TTWROR formula** and its rule for what is external (deposits) vs internal (dividends); fees in, taxes out at security level; showing both measures |
| [afadil/wealthfolio](https://github.com/afadil/wealthfolio) | 8 927, AGPL-3.0 | `twr`, `annualized_twr`, `irr` (XIRR), `annualized_irr`, `volatility`, `max_drawdown` with peak/trough/recovery dates, a nine-part attribution, a `PerformanceDataQuality` flag ([performance_model.rs](https://github.com/afadil/wealthfolio/blob/main/crates/core/src/portfolio/performance/performance_model.rs)) | the attribution split and the data-quality flag travelling with every result |
| [OpenBB-finance/OpenBB](https://github.com/OpenBB-finance/OpenBB) | 73 023, AGPL-3.0 per its LICENSE file (GitHub reports NOASSERTION) | a data platform with `econometrics` and `quantitative` extensions; no portfolio tracker in the current tree | nothing for this screen; too large a dependency for HA |
| [ranaroussi/yfinance](https://github.com/ranaroussi/yfinance) | 25 248, Apache-2.0 | `Ticker`, `download`, `Market`, WebSocket streaming, `Search`, `Screener`; README: "intended for personal use only" | already chosen in doc 18; its `WebSocket` class is the candidate if a live tick ever replaces the 60 s spark poll |
| [ranaroussi/quantstats](https://github.com/ranaroussi/quantstats) | 7 636, Apache-2.0 | the full tear-sheet vocabulary: Cumulative Return, CAGR, Sharpe, Sortino, Max Drawdown, Longest DD Days, Volatility (ann.), Calmar, Ulcer Index, `MTD 3M 6M YTD 1Y 3Y(ann.) 5Y(ann.) 10Y(ann.) All-time(ann.)`, Best/Worst Day/Month/Year, Beta/Alpha vs benchmark ([reports.py](https://github.com/ranaroussi/quantstats/blob/main/quantstats/reports.py)); `drawdown_details` | the metric names and the drawdown table; the monthly-returns heat map as a possible sixth page |
| [pmorissette/bt](https://github.com/pmorissette/bt) | 2 983, MIT | a tree of algos: `RunYearly/Quarterly/Monthly`, **`RunIfOutOfBounds(tolerance)`** (relative deviation `abs(w − target) / target > tolerance`, "quarterly or whenever any security's weight deviates by more than 20%" via `Or`), `WeighTarget`, `Rebalance`, `CapitalFlow`, `CorporateActions`, commission models ([algos.py](https://github.com/pmorissette/bt/blob/master/bt/algos.py)) | the threshold-rebalance predicate and the "calendar OR band" composition; a second reference for the golden match beside Excel |
| [pmorissette/ffn](https://github.com/pmorissette/ffn) | 2 680, MIT | `PerformanceStats`: Total Return, CAGR, Max Drawdown, Calmar, `MTD 3m 6m YTD 1Y 3Y (ann.) 5Y (ann.) 10Y (ann.) Since Incep. (ann.)`, Daily Sharpe/Sortino, Daily Vol (ann.), Best/Worst Day/Year, Avg Drawdown, Avg Drawdown Days, Win Year %, Win 12m % ([core.py](https://github.com/pmorissette/ffn/blob/master/ffn/core.py)) | small, pandas-only; the natural library for the HA app's stats if we do not want to hand-roll |
| [robertmartin8/PyPortfolioOpt](https://github.com/robertmartin8/PyPortfolioOpt) | 6 028, MIT | mean-variance, Black-Litterman, HRP optimisation | nothing: the owner's weights are given, not optimised |
| [sarvjeets/lakshmi](https://github.com/sarvjeets/lakshmi) | 148, MIT | Bogleheads-inspired CLI: allocation across accounts, what-if, "suggests which funds to allocate new money to ... to keep the actual asset allocation close to the desired", IRR, tax lots, rebalance / tax-loss analysis | the "where should new money go" suggestion as a portal read-out |
| [danbuchal/portfolio-tracker](https://github.com/danbuchal/portfolio-tracker) | 145, no licence file, last push 2026-09-07; a Google Sheet | asset-allocation dashboard, quotes "delayed up to 20 minutes", collapsible column groups, funds with more than one asset class | the collapsible groups idea for the portal's Advanced block |
| [feram18/led-stock-ticker](https://github.com/feram18/led-stock-ticker) | 100, GPL-3.0, last push 2025-06 | Raspberry Pi + hzeller; 32×16, 64×32, **128×64**; market-status dot left of the symbol, a one-day history chart or a logo, currency selection, `update_rate` 10 min, `rotation_rate` 10 s | the closest prior art for a 128×64 ticker page: symbol · status dot · price · day % · sparkline |
| [yahnyshc/stockTicker](https://github.com/yahnyshc/stockTicker) | 10, MIT | 64×32, Finnhub WebSocket, logos or a 64-column chart, PostgreSQL history | nothing beyond feram18 |
| [Tickertronix/Tickertronix-Open](https://github.com/Tickertronix/Tickertronix-Open) | 19, MIT | a Pi hub serving Matrix Portal S3 panels and a CYD; single-asset mode "dwell time (default 2.5s)", "4-color palette (black/white/green/red)" | the hub-and-thin-display split is exactly HA + panel |
| [chromatel/chromaticker](https://github.com/chromatel/chromaticker) | 1, no licence | 192×16 HUB75, yfinance, "optional portfolio value mode (shares × price)", a status dot for "market open/closed, pre-market status, data freshness", dimming and night schedules, web UI | the one status dot carrying open/closed/pre/fresh |
| [mrfaptastic/led-stock-ticker-proxy](https://github.com/mrfaptastic/led-stock-ticker-proxy) | 4, GPL-3.0, 2024 | a proxy for a Pi ticker, by the author of the HUB75 DMA library the panel uses | nothing to reuse; worth knowing he built one |
| [Meterbit/PIXLPAL-M1](https://github.com/Meterbit/PIXLPAL-M1) | 36, other | an ESP32-S3 128×64 desk companion with a crypto/news ticker | nothing; noted because it is the same panel class |

Fintic, an "all in one LED ticker" (two 64×32 P3 panels, Pi 3A+, stocks,
crypto, forex, news, weather) was posted on the [SparkFun forum, 2021](https://community.sparkfun.com/t/all-in-one-led-ticker-stocks-crypto-forex-news-weather-sports-custom-images-gifs-messages/42570);
its repository was not found on GitHub. TickrCast, a commercial ESP32-S3
HUB75 ticker with server-side rendering, is on Kickstarter ([CNX Software,
2026-09-03](https://www.cnx-software.com/2026/09/03/tickrcast-esp32-s3-hub75-led-ticker-display-with-server-side-rendering-and-ota/));
not open source, but its architecture (compose on a server, the ESP32 only
draws) is the same conclusion doc 18 reached.

Home Assistant: the HACS readers of real broker accounts are already listed
in doc 18; nothing new computes portfolio returns.

## 3. Reddit and the Bogleheads forum

What was read, thread by thread. Where a thread could not be read (429 or a
timeout) it is listed as such rather than paraphrased.

### Bogleheads.org forum

- [What Spreadsheet or Software Do You Use To Track](https://www.bogleheads.org/forum/viewtopic.php?t=433919)
  (2024-06, 42 posts; first page read): answers are "my own Excel", Tiller
  (criticised: "tracks balances but not transactions so you can't track
  basis"), the Retiree Portfolio Model spreadsheet; the recurring want is a
  single view across custodians.
- [A Free Google Sheet for Asset Allocation Tracking](https://www.bogleheads.org/forum/viewtopic.php?t=451043)
  (2025-03, 78 posts; first page read): the sheet's selling points are an
  allocation dashboard, quotes "delayed up to 20 minutes", table views,
  collapsible column groups, funds split over several asset classes; the
  first critique (Raspberry-503) is that it assumes every asset class is
  balanced in every account, i.e. no asset location.
- [A call to all Bogleheads: let's accurately calculate returns!](https://www.bogleheads.org/forum/viewtopic.php?t=186899)
  (2016; read from a [2019 capture](https://web.archive.org/web/20190202032300/https://www.bogleheads.org/forum/viewtopic.php?t=186899)):
  the opening post calls "point A to point B on a chart" a "horrible and
  wildly inaccurate" way to measure a portfolio with contributions; the
  wiki's author (longinvest) answers that the wiki spreadsheet gives both
  the time-weighted and the money-weighted figure and that he uses it "to
  verify that my ... three-fund portfolio ... is effectively tracking" its
  benchmark. Others: "What if you just plugged in your transactions and
  used the XIRR formula in Excel?"; reinvested dividends are the
  spreadsheet pain point.
- Not read: [portfolio tracker suggestions](https://www.bogleheads.org/forum/viewtopic.php?t=402237)
  (timeouts on every route).

### Reddit

Read through the `.rss` feeds on 2026-09-15, 10:26–10:47; the search
feed gives at most 25 hits per query, the thread feed the post and its
top-level comments.

**r/Bogleheads**

- [What do you use for portfolio tracking?](https://www.reddit.com/r/Bogleheads/comments/1ucl5aj/what_do_you_use_for_portfolio_tracking/)
  (2026-06, 30 comments read): the majority answer is a spreadsheet —
  Excel's "Stock" data type with Data → Refresh, or LibreOffice with manual
  entry "every 2-3 months" tracking "changes since last update, and changes
  YTD, as percentage of account balance ... and of overall portfolio" with
  a fund-type column for allocation. Tools named: Ghostfolio ("great if you
  like selfhosting"), Portfolio Performance (two brokers), Empower ("a lot
  better when it was Personal Capital"), Vanguard Portfolio Watch (kept up
  by hand for its allocation view), Fidelity ("a good big picture
  dollar-amount view. Not much in the way of central performance view"),
  Yahoo Finance. The spreadsheet pain point, asked twice: "How do you
  handle dividend reinvestment?" — quantities drift.
- [Not really liking Personal Capital/Empower anymore](https://www.reddit.com/r/Bogleheads/comments/1gltmij/not_really_liking_personal_capitalempower_anymore/)
  (2024-11, 22 comments read): the ask is "a single place ... that updates
  based on my monthly contributions". The dominant reply is DIY sheets,
  because aggregators break links and because of credential risk ("As
  someone who works in InfoSec in a financial firm, I highly recommend
  staying away from aggregators"). Monarch is criticised for dropping an
  account to 0 and back, which made "graphs and change over time data
  useless" — a data-quality lesson: a missing series must be marked, never
  zeroed.
- [Worth it to use a portfolio tracker?](https://www.reddit.com/r/Bogleheads/comments/1ek2f94/worth_it_to_use_a_portfolio_tracker/)
  (2024-08, 19 comments read): "I just want to see how much total
  gain/loss I have between my accounts ... a spreadsheet ... doesn't
  account for the price you paid". One home sheet described in detail:
  target allocations by category, every holding tagged to a category so
  two funds of one class balance together, "a line for cash to invest",
  and the sheet "shows me how much money to put into each category" — the
  contribution-based rebalancing of the Bogleheads wiki and of lakshmi.

**r/investing**

- [Looking for a (free) portfolio tracker](https://www.reddit.com/r/investing/comments/1nr2q3c/looking_for_a_free_portfolio_tracker/)
  (2025-09): the wish list, verbatim: "Track how much I've invested over
  time (e.g. a graph showing monthly contributions); See total return /
  profit & loss; Track the performance of individual stocks (growth,
  percentage change, etc.)"; "a visual dashboard that gives me both
  historical data and up-to-date performance". A later comment on a
  multi-currency tracker: the frustration was "no historical exchange
  rates" — which our ECB and Yahoo FX series cover.
- [External tools for better visualization / tracking / risk analysis](https://www.reddit.com/r/investing/comments/1qcqfr5/external_tools_for_better_visualization_tracking/)
  (2026-01): most replies removed by AutoModerator; nothing usable.
- Found, not fetched (budget): [Time weighted (TWROR) portfolio tracker
  recommendation?](https://www.reddit.com/r/investing/comments/194m0r/time_weighted_twror_portfolio_tracker/) (2013).

**r/portfolios, r/dataisbeautiful, r/homeassistant, r/raspberry_pi**

- The r/dataisbeautiful search shows the genre: "[OC] My Stock Portfolio
  Vs. S&P 500" (2022), "Portfolio value over time with different asset
  allocations" (2018), "All possible US stock market retirement portfolio
  returns from 1871-2015" (2017), "US 60/40 Portfolio Return v. Personal
  Income" (2022) — portfolio against one benchmark, and allocations
  compared over long windows.
- Two r/homeassistant searches ("stock ticker", "portfolio stocks")
  returned five threads between them, three on topic ("Ideas for smart
  home apps for a LED Ticker", 2023; "New integration - Biofects Portfolio
  Tracker", 2025-11; an eToro balance sensor, 2023): market data on HA is a
  niche.
- r/raspberry_pi has the ticker builds: Fintic ("My Desk Size LED Matrix
  Ticker", 2021), a 96×48 HUB75 multi-source display (2025-11), "First
  Project: Stock Ticker" (2017), a crypto ticker guide (2020).

- [[OC] My Stock Portfolio Vs. S&P 500](https://www.reddit.com/r/dataisbeautiful/comments/xcektu/oc_my_stock_portfolio_vs_sp_500/)
  (r/dataisbeautiful, 2022-09, 13 comments read): per-fund return against
  the S&P 500 over seven years, from "tax lots and cost basis" in Tableau.
  The useful comment is a different depiction: "each fund's growth since
  Jan. 1 in ratio to the S&P 500's growth since Jan. 1 ... gives me a much
  clearer sense of how each fund is doing" — the telltale chart again. The
  poster also corrected his own aggregate (a SUM where an AVG belonged):
  the aggregate of per-holding figures is where home dashboards go wrong.
- [Been looking for a portfolio tracker app/software and moving my spreadsheet](https://www.reddit.com/r/portfolios/comments/1r0p1hv/been_looking_for_a_portfolio_tracker_appsoftware/)
  (r/portfolios, 2026-02): after years in Excel, "the real issue hasn't
  been performance tracking. It's context" — the reason behind a trade is
  lost once it closes; another reply needs "accumulated dividends" tracked
  because the strategy sells half on a double. Notes per position and a
  dividend total are cheap to keep.
- [I want to build a dividend portfolio tracker and I'd appreciate some input](https://www.reddit.com/r/portfolios/comments/1tikpj3/i_want_to_build_a_dividend_portfolio_tracker_and/)
  (r/portfolios, 2026-05): the post lists what a spreadsheet user already
  tracks — "the dividend income it produces", "fundamentals, returns,
  allocation" — and asks which features are worth paying for. The feed
  returned **no replies**, so there are no answers to report.
- [Ideas for smart home apps for a LED Ticker](https://www.reddit.com/r/homeassistant/comments/17heeft/ideas_for_smart_home_apps_for_a_led_ticker/)
  (r/homeassistant, 2023-10): a commercial ticker maker asking for content
  beyond "sports and stocks"; the one reply asks whether it is integrated
  into HA at all. Nothing on layout.

- [My Desk Size LED Matrix Ticker (Stocks, Weather, News, GIFs and More)!](https://www.reddit.com/r/raspberry_pi/comments/p7fyrp/my_desk_size_led_matrix_ticker_stocks_weather/)
  (r/raspberry_pi, 2021-08, 20 comments read): the builder's own post
  describes the same project as the SparkFun Fintic post (a year's work,
  inspired by Times Square, "real time stock, crypto, forex prices, news
  headli[nes]"), on two 64×32 P3 panels, a Pi 3 A+ and an Adafruit bonnet.
  The comments are about parts sourcing and power ("14 amps?!"; the builder:
  "total amperage should be around 11A or 55W max"); nobody discusses what
  the stock screen should show.
- [Multiple Data Sources from Pi 3 Displayed to HUB75 96x48 LED Matrix](https://www.reddit.com/r/raspberry_pi/comments/1p4fvvp/multiple_data_sources_from_pi_3_displayed_to/)
  (r/raspberry_pi, 2025-11, 5 comments read): a GPS-synced clock that wants
  weather and "my company's stock ticker" added, "just informational"; the
  advice given is one fetch thread per source feeding a queue that the
  screen thread reads, with the fetchers asleep most of the time — the same
  split as HA computing and the panel drawing.
- [New integration - Biofects Portfolio Tracker](https://www.reddit.com/r/homeassistant/comments/1on00fm/new_integration_biofects_portfolio_tracker/)
  (r/homeassistant, 2025-11; the feed carried the post only, no replies):
  an HA integration to "track your stocks and crypto, enter your amounts and
  purchase prices, and see profit/loss charts on your dashboard", with news
  feeds and "scheduled updates to keep things fresh without overloading
  APIs" ([repository](https://github.com/biofects/Biofects-Portfolio-Tracker):
  1 star, MIT, last push 2025-11-14).
  Not in doc 18's HACS list; a lot-and-cost-basis tracker, not a backtest.

**What they want, and the mistakes they name.** Across the threads read:
one view across accounts; contributions shown separately from growth; total
gain/loss against what was paid, not just quantities × price; performance
of each holding; allocation against target with "where does new money go";
no credentials handed to a third party (a point in favour of a self-hosted
HA app). Mistakes: measuring a portfolio with contributions "from point A
to point B on a chart" (Bogleheads t=186899); quantities that drift when
dividends reinvest; an account that reads 0 for a day and poisons the
history; comparing cumulative returns across different periods (Fidelity's
FAQ); annualising short periods (Sharesight's 1,825 % example); long charts
in nominal terms only (Simba's real-growth mode).

### LED and ambient market displays people built

Prior art is in the table above (feram18, yahnyshc, Tickertronix,
chromaticker, Fintic). What they converge on for a small panel: one symbol
at a time or a scrolling row; the **day change in percent** with a sign;
a **status dot** for the market state; a one-day sparkline; refresh every
1–10 minutes; a web page for the symbol list. None of them shows a
portfolio return over a window, dividends, or a benchmark: the panel design
in doc 18 goes further than any of them.

## 4. Methodology: how returns should be computed and labelled

**Time-weighted vs money-weighted.** The GIPS standards (CFA Institute,
2020 edition) require time-weighted returns; money-weighted returns are
allowed only when "the firm has control over the external cash flows" and
the portfolio is closed-end, fixed-life, fixed-commitment or illiquid
([GIPS 2020 for Firms, 1.A.35](https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf)).
TWR must be computed at least monthly, with sub-period returns at large
cash flows, daily-weighted adjustment for the others, and geometric linking
(2.A.24); the Modified Dietz method is the named daily-weighted
approximation ([Guidance Statement on Calculation Methodology, 2011](https://www.gipsstandards.org/wp-content/uploads/2021/03/calculation_methodology_gs_2011.pdf)).
MWR must be "annualized since-inception" and use "daily external cash
flows" (2.A.29). The retail side inverts the emphasis: Vanguard, Fidelity
and Sharesight show the money-weighted figure first because it is "the
performance experienced by an investor" ([IBKR white paper](https://www.interactivebrokers.com/images/common/Statements/MWR-TWR_white_paper.pdf));
the Bogleheads wiki calls them **investor return** (MWR, "the interest rate
on a savings account, such that the same sequence (and timing) of
contributions and withdrawals would end up with the same final balance")
and **portfolio return** (TWR, "comparable return", "a single lump sum
invested in the portfolio") and shows a worked case where they differ,
10.0 % vs 12.69 % ([wiki, 2021 capture](https://web.archive.org/web/20210916223819/https://www.bogleheads.org/wiki/Calculating_personal_returns)).

For our ledger: with contributions at 0 (the default) the two coincide and
`chg` is a true TWR. With contributions on, `value_end / value_start − 1` is
neither; it overstates the return by the contributions. Section 6 makes
this the first improvement.

**Annualising.** "Returns for periods of less than one year must not be
annualized" (GIPS 2.A.12). Sharesight applies the same rule with a
concrete threshold: annualise only when average years invested ≥ 1
([Sharesight](https://help.sharesight.com/absolute-and-annualised-return/)).
Fidelity: compare annualised returns across periods, never cumulative ones
([Fidelity](https://www.fidelity.com/webcontent/ap002390-mlo-content/19.09/help/learn_performancereporting.shtml)).
GIPS also ties risk statistics to a periodicity: the three-year
annualised ex post standard deviation is computed from **monthly** returns
(4.A.1), and "the periodicity of the composite ... returns and the benchmark
returns must be the same" (2.A.18). Portfolio Visualizer follows this
(monthly returns, annualised) and computes max drawdown from **monthly**
balances ([PV FAQ](https://www.portfoliovisualizer.com/faq)) — our daily
`mdd` will be deeper than PV's for the same portfolio, which matters for
the golden match in doc 18: compare end values, not drawdowns, or
downsample to month ends first.

**Real vs nominal.** Portfolio Visualizer adjusts returns, contributions and
withdrawals by CPI-U ([PV FAQ](https://www.portfoliovisualizer.com/faq));
Simba's spreadsheet gets the real curve by dividing by an inflation series
used as the benchmark ([Simba wiki](https://web.archive.org/web/20220128172554/https://www.bogleheads.org/wiki/Simba's_backtesting_spreadsheet)).
For a EUR portfolio the series is Eurostat's HICP (**source not fetched**;
the ECB Data Portal that already serves the 1999–2003 FX rates carries it).

**Dividend reinvestment.** Total-return indices "reflect both movements in
stock prices and the reinvestment of dividend income" ([S&P DJI Index
Mathematics, March 2025](https://www.spglobal.com/spdji/en/documents/methodologies/methodology-index-math.pdf));
Portfolio Visualizer "assumes by default that all dividends and capital
gains distributions are reinvested" ([PV FAQ](https://www.portfoliovisualizer.com/faq)).
Our ledger reinvests only at the year-end sweep, which is a deliberate,
documented difference (doc 18): the `px` line shows the no-dividend case,
and a "reinvest on pay date" option would put us on PV's convention.

**Expense-ratio drag.** "The displayed performance is then calculated based
on the value of fund shares and is thus net of these fees" ([PV FAQ](https://www.portfoliovisualizer.com/faq)),
confirming doc 18's rule that the TER must not be subtracted twice. The
SEC's illustration of the drag: $100 000 at 4 % for 20 years with ongoing
fees of 0.25 %, 0.50 % or 1 %, and "not only is your investment balance
reduced by the fee, but you also lose any return you would have earned on
that fee" ([SEC Investor Bulletin](https://www.sec.gov/investor/alerts/ib_fees_expenses.pdf))
— which is why the `gross` counterfactual is `net × exp(TER × years)`, not
`net + TER × years`.

**Rebalancing: calendar vs threshold.** Vanguard's 2015 paper: "there is no
optimal frequency or threshold for rebalancing, since risk-adjusted returns
do not differ meaningfully"; the recommendation is "annual or semiannual
monitoring, with rebalancing at 5% thresholds", and "annual rebalancing is
likely to be preferred when taxes or substantial time/costs are involved".
Monthly monitoring with a 1 % threshold meant 423 rebalancing events over
1926–2014 against 19 for annual monitoring with a 10 % threshold; a never
rebalanced 50/50 drifted to about 81 % equity with 13.2 % volatility
against about 10 % ([Zilbering, Jaconetti, Kinniry, Vanguard Research,
November 2015](https://web.archive.org/web/20230606014619/https://www.vanguard.ca/documents/best-practices-for-portfolio-rebalancing.pdf);
read from a [mirror](https://foro.masdividendos.com/uploads/short-url/5jOqkMshktUetcUeS6EpKnsBLUM.pdf)).
Vanguard's 2024 paper for target-date funds proposes a **200/175** rule: a
200 bp threshold and a 175 bp destination, and shows that around March 2020
monthly rebalancing let the allocation drift 7 %, quarterly 10 %
([The rebalancing edge, Vanguard, December 2024](https://corporate.vanguard.com/content/dam/corp/research/pdf/the_rebalancing_edge_optimizing_target_date_fund_rebalancing_through_threshold_based_strategies.pdf)).
The Bogleheads wiki lists five triggers (calendar, absolute %, relative %,
dollar amount, with contributions) and Swedroe's **5/25 rule**: 5
percentage points absolute for allocations of 20 % or more, 25 % relative
for smaller ones; it also notes that a 50/50 portfolio needs a 4 % relative
move between stocks and bonds to shift 1 %, and that checking weekly while
trading rarely "could provide the best rebalancing bonus"
([Bogleheads wiki: Rebalancing](https://www.bogleheads.org/wiki/Rebalancing)).
Daryanani's study behind that note found 20 % relative bands and a look
interval of at most two weeks best, with equity never drifting more than
5 % from 60/40 ([Kitces on Daryanani 2008](https://www.kitces.com/blog/best-opportunistic-rebalancing-frequency-time-horizons-vs-tolerance-band-thresholds/)).
Portfolio Visualizer's defaults are the same 5 % absolute / 25 % relative
bands, annual rebalancing by default, and a drift chart when rebalancing is
off ([PV FAQ](https://www.portfoliovisualizer.com/faq)).

For our fourteen positions the 5/25 rule gives absolute bands only for VOO
(23.7 %); every other position is under 20 % and gets a relative band:
GLDM 16.5 % → ±4.1 points, ASHR 1.25 % → ±0.31 points.

**Benchmark for a multi-asset allocation.** GIPS: the benchmark "must
reflect the investment mandate, objective, or strategy" and "must not [be]
a price-only benchmark" (1.A.18) — `^GSPC` fails both tests for a
stock/bond/gold portfolio; `^SP500TR` fixes only the second. Fund houses
use composites: Vanguard Balanced Index is measured against a "Balanced
Composite Index" of 60 % US stocks and 40 % US bonds ([fact sheet](https://workplace.vanguard.com/assets/corp/fund_communications/pdf_publish/us-products/fact-sheet/F0869.pdf));
Portfolio Visualizer builds one from an expression such as `0.6*SPY+0.4*AGG`
([PV FAQ](https://www.portfoliovisualizer.com/faq)). For the owner's
weights the honest benchmark is a blend the app can compute from the same
Yahoo total-return-capable tickers it already holds (for instance
`^SP500TR`, a bond ETF's adjusted close, gold): "Benchmark" becomes a small
allocation table like the portfolio's, with a preset "same weights, no
rebalance" and a preset "60/40".

## 5. Settings inventory

Legend for "Seen in": PV Portfolio Visualizer · PP Portfolio Performance ·
GF Ghostfolio · WF Wealthfolio · SS Sharesight · IB IBKR PortfolioAnalyst ·
MS Morningstar · FI Fidelity · VG Vanguard · KF Koyfin · TV TradingView ·
BB Bloomberg · GIPS · BH Bogleheads wiki/forum · bt · qs quantstats ·
LED the LED-ticker repos · 18 = already in doc 18.

Verdicts: **Core** on the simple page; **Advanced** folded; **Skip** with
the reason. Defaults are the professional defaults where a source states
one, otherwise the value doc 18 already chose.

### Universe

| Setting | What it does | Pro default | Range | Seen in | Verdict |
|---|---|---|---|---|---|
| Indices list | the MARKETS page and the tape | SPX, NDX, CAC, DAX (18) | ≤ 8 symbols | TV, KF, LED | Core (18) |
| Tickers list | the TICKER page | the fourteen funds (18) | ≤ 8 on the panel | TV, KF, LED | Core (18) |
| Display name per symbol | a 3–4 letter mnemonic for 128 px | Yahoo `shortName` truncated | free text ≤ 8 | TV, LED | Core (18) |
| Tape exchanges | which sessions the top row shows | NYSE, NASDAQ, LSE, XETRA, EURONEXT, TOKYO (18) | any `exchange_calendars` code | LED status dot, TV extended hours | Core (18) |
| Proxy / backfill symbol | extend a young fund with its index or an older share class | none | one symbol per position | PV "Backfilling asset returns" | Advanced: fixes the 2010 VOO gap in the owner's backtest |

### Portfolio model

| Setting | What it does | Pro default | Range | Seen in | Verdict |
|---|---|---|---|---|---|
| Positions: symbol, target weight | the allocation | the owner's fourteen (18) | ≤ 16, sum = 100 % | PV, PP, GF, WF, SS | Core (18) |
| Entry date per position | when a position starts | inception | any date ≥ inception | 18, KF "purchase date" | Advanced (18) |
| Initial capital | the base | 10 000 (18); PV also 10 000 | > 0 | PV, MS "growth of 10,000", VG fact sheet | Core (18) |
| Inception date | the start of MAX | 2000-01-01 (18) | ≥ oldest data | PV start year, GIPS 2.A.27 "inception date" | Core (18) |
| Weights as amounts | enter money instead of % and normalise | percent | percent / amount | PV "Entering portfolio allocations" | Skip: one entry mode keeps the table light |
| Asset-class tag per position | groups holdings (equity, bond, gold, REIT) for an allocation read-out | none | equity, bond, real assets, cash | PV, IB, MS, lakshmi | Advanced: one tag makes a stock/bond/gold summary and the composite benchmark possible |

### Returns methodology

| Setting | What it does | Pro default | Range | Seen in | Verdict |
|---|---|---|---|---|---|
| Return measure | which figure is the big one | trackers: money-weighted; terminals: time-weighted | TWR / MWR (XIRR) | IB toggle, PP both, WF both, GIPS 1.A.35 | Advanced with a visible label on the page; default TWR because the backtest has no real cash flows |
| Show both | TWR and XIRR side by side | PP yes | on/off | PP, WF, BH | Advanced |
| Annualised for ≥ 1 y | CAGR/`(ann.)` on multi-year windows | annualise from 1 y | 1 y / 3 y threshold | GIPS 2.A.12, SS, FI | Core as a rule, not a setting: label `(ann.)`; never under 1 y |
| Real (inflation-adjusted) | divide by CPI | off | off / on, index choice | PV, Simba | Advanced |
| Dividend handling | reinvest on pay date / sweep to cash at year end / drop | PV reinvest; ours sweep (18) | three modes | PV, PP internal flow, GF | Advanced: the sweep stays default, "reinvest on pay date" for the PV convention |
| Price basis | close vs adjusted close for benchmarks | total return | close / adjclose | 18, S&P TR definition | Skip as a user setting: fixed by the council's rule |

### Rebalancing

| Setting | What it does | Pro default | Range | Seen in | Verdict |
|---|---|---|---|---|---|
| Mode | HOLD / REBAL | annual (PV) | hold / calendar / bands / both | 18, PV, VG, bt `Or` | Core (18) |
| Calendar frequency | when the sweep runs | annual (PV, VG 2015) | monthly / quarterly / semi-annual / annual; day of year | PV, VG, bt | Advanced (31 Dec stays default) |
| Threshold bands | rebalance when a weight leaves its band | 5 % absolute / 25 % relative (PV, BH 5/25) | 1–10 points; 10–50 % | PV, BH, VG 200/175, bt | Advanced |
| Check interval for bands | how often drift is tested | daily in backtests; VG "annual or semiannual monitoring"; Daryanani ≤ 2 weeks | daily / weekly / monthly | VG, Kitces | Advanced |
| Destination | rebalance to target or to the band edge | to target | target / edge (VG 175 bp) | VG 2024 | Skip: a fund-manager refinement |
| Rebalance with contributions only | new cash buys the underweight, no selling | — | on/off | BH wiki, lakshmi | Advanced: it is HOLD with directed cash; cheap to add |
| Show drift | current vs target | PV shows drift when rebalancing is off | on/off | PV, 18 HOLDINGS | Core (18, `TGT→NOW`) plus an out-of-band mark |

### Cash and contributions

| Setting | What it does | Pro default | Range | Seen in | Verdict |
|---|---|---|---|---|---|
| Contribution amount and period | periodic cash in | 0 (18); PV "cashflows" | monthly / quarterly / yearly; amount | PV, GF, WF | Core (18) |
| Inflation-index contributions | grow the contribution by CPI | PV option | on/off | PV | Advanced |
| Withdrawals | periodic cash out | none | amount / % of balance | PV | Skip: accumulation portfolio |
| Cash yield | interest on the cash row | 0 | 0–5 % or a cash proxy (`^CASHUS` in PV) | PV | Advanced |
| Cash excluded from performance | Sharesight excludes cash from % but keeps it in value | SS excludes | in / out | SS | Skip: our cash is part of the model by the owner's decision |

### Fees and taxes

| Setting | What it does | Pro default | Range | Seen in | Verdict |
|---|---|---|---|---|---|
| TER override per symbol | for funds Yahoo lacks | Yahoo `fundProfile` | 0–2 % | 18, PV, Simba | Advanced (18) |
| Show `TER DRAG ~` | the estimate line | on | on/off | 18 | Core (18) |
| Gross-of-fees counterfactual | dashed EST line | off | on/off | 18, GIPS gross/net | Advanced (18) |
| Advisor fee | % of assets, tiered, fixed | none | PV models | PV | Skip: no advisor |
| Transaction costs | commission per trade | none (18) | fixed / % | bt, GIPS 2.A.13 | Skip: the owner's decision; PV also ignores them |
| Taxes on dividends | withholding | none | 0–30 % | PP (taxes excluded at security level), GF | Skip in v1: US funds in an EU account is a tax question, not a chart |

### Currency

| Setting | What it does | Pro default | Range | Seen in | Verdict |
|---|---|---|---|---|---|
| Portfolio currency | the reporting currency | EUR (18) | EUR / USD | 18, SS "home currency", PP | Core (18) |
| Show currency effect | the FX part of the return | SS shows it as a component | on/off | SS, WF `fx_effect`, BB currency effect | Advanced: one footer number `FX +2.1%` |
| FX source | Yahoo `EURUSD=X` plus ECB 1999–2003 | fixed | — | 18 | Skip: not a user choice |

### Benchmarks

| Setting | What it does | Pro default | Range | Seen in | Verdict |
|---|---|---|---|---|---|
| Benchmark symbol | the dim line | first index (18) | any symbol | IB, MS, PP, GF | Core (18), but total-return |
| Up to three | more lines | IB 3 | 1–3 | IB | Skip on the panel (128 px); Advanced in HA's dashboard |
| Blended benchmark | weights over 2–3 series | Vanguard composite 60/40 | a small allocation table | PV, VG fact sheet, GIPS 1.A.18 | Advanced, with presets "same weights" and "60/40" |
| Telltale view | portfolio ÷ benchmark | Simba | on/off | Simba, Bogle | Advanced: one extra line mode on PORTFOLIO |

### Risk metrics

| Setting | What it does | Pro default | Range | Seen in | Verdict |
|---|---|---|---|---|---|
| Max drawdown | deepest fall | on | daily / month-end basis | PV monthly, qs daily, WF | Core (18); add dates |
| Drawdown table | worst episodes | qs 5 rows | 3–10 | qs `drawdown_details` | Advanced: HA dashboard only |
| Volatility (ann.) | standard deviation | qs, PV, GIPS 3 y monthly | daily / monthly basis | PV, qs, GIPS 4.A.1 | Advanced |
| Sharpe / Sortino / Calmar | risk-adjusted | PV, IB, qs | risk-free choice | PV (3-mo T-bill), IB, qs | Skip on the panel: three ratios nobody reads from 3 m; Advanced in HA |
| Beta / alpha vs benchmark | co-movement | IB, qs | — | IB, qs | Skip |
| Best / worst year | range of annual returns | qs, ffn | — | qs, ffn, VG fact sheet | Advanced: fits a YEARS page |
| Rolling returns | 1 y / 3 y rolling | PV | window | PV, Simba | Skip in v1 |

### Display and formatting

| Setting | What it does | Pro default | Range | Seen in | Verdict |
|---|---|---|---|---|---|
| Default window | the preset on boot | YTD or 1Y | YTD 1Y 3Y 5Y 10Y MAX (18) | GF, IB, ffn | Core (18) |
| Extra presets | `1M`, `3M`, `6M`, `WTD`, `MTD` | GF `WTD MTD`; IB `7D MTD 1M`; ffn `3m 6m` | on/off per preset | GF, IB, ffn, BH | Advanced |
| Colour scheme | green/red; blue/red (CVD); red-up (Asia) | green up | 3 schemes | BB PDFU COLORS, HN/Benzinga | Advanced |
| Sign always shown | `+`/`−` on every change | yes | fixed | 18, BB (colour is never alone) | Core as a rule |
| Lines on PORTFOLIO | value, no-dividend, benchmark, gross | value + benchmark | toggles | 18 | Core (18) |
| Big-number format | `12.3K` / `1.24M`, decimals | 18 rules | — | 18 | Skip as a setting: the rule set is fixed |
| Growth-of-10 000 base | index all lines to the same base | MS, VG | on/off | MS, VG, BH spreadsheet | Core as a rule: all lines start at `C` |
| Chart scale | linear / log | linear | linear / log | PV (log option) | Advanced: log for MAX windows |
| Carousel dwell | seconds per page | 20 s (18); Tickertronix 2.5 s per asset | 5–60 s | 18, LED | Core (18) |
| Night dimming | brightness schedule | — | schedule | chromaticker, panel already | Skip here: the panel's own setting |

### Alerts and thresholds

| Setting | What it does | Pro default | Range | Seen in | Verdict |
|---|---|---|---|---|---|
| Out-of-band mark | `!` on a holding outside its band | — | on/off | PV drift, BH 5/25 | Advanced (comes with bands) |
| Day-move alert | flag a symbol moving more than x % | — | 1–10 % | TV alerts | Skip: the panel is not a trading screen |
| Drawdown alert | flag when below −x % from peak | — | 5–30 % | — | Skip |
| HA notifications | push on the above | — | on/off | HA | Skip in v1; the sensors exist for automations |

### Data and refresh

| Setting | What it does | Pro default | Range | Seen in | Verdict |
|---|---|---|---|---|---|
| Live poll interval | during sessions | 60 s (18, measured) | 30–300 s | LED `update_rate` 10 min, HACS 6 h | Core (18) |
| Daily fetch time | history refresh | 07:00 local (18) | time | 18 | Advanced |
| Delay label | show `D`/`15M` when the feed is delayed | TV `D`; exchanges 15 min | auto | TV, Deutsche Börse, LSEG | Core as a rule |
| Stale threshold | age beyond which a quote is STALE | 20 min in session (18); 3 trading days for history (18) | minutes / days | EODHD, 18 | Advanced |
| Source label | where the figure came from (live, previous close, cache) | EODHD recommends | auto | EODHD, WF data quality | Advanced: shows in the portal's diagnostics |
| Provider | Yahoo today; a seam | Yahoo | — | 18 | Skip as a user setting |

**Count** (counted from the tables above): 69 settings inventoried —
22 Core (18 of them already in doc 18; the other 4 are labelling rules,
not switches: `(ann.)` only from 1 y, a sign on every change, every line
starting at `C`, the delay label), 28 Advanced, 19 Skip. The portal's plain blocks stay as doc 18 has them;
Advanced gains four folds — *Returns*, *Rebalancing*, *Benchmark*,
*Display* — each with its defaults pre-filled, so the page reads light
until opened.

## 6. Ten improvements, ranked

1. **Name the return, and add the second one.** Label the window figure
   `TWR` and, when contributions are on, compute it properly (daily
   geometric linking with contributions as external flows, PP's formula);
   show `XIRR (ann.)` since inception as the "your money" figure. Today's
   `chg` is right only with zero contributions. Sources: GIPS 1.A.35 and
   2.A.24/2.A.29; [PP](https://help.portfolio-performance.info/en/concepts/performance/time-weighted/);
   [IBKR](https://www.interactivebrokers.com/images/common/Statements/MWR-TWR_white_paper.pdf);
   [Bogleheads wiki](https://web.archive.org/web/20210916223819/https://www.bogleheads.org/wiki/Calculating_personal_returns).
2. **Total-return, mandate-matching benchmark.** Default `^SP500TR` (not
   `^GSPC`), and a blended benchmark preset built from the portfolio's own
   asset-class tags. Sources: GIPS 1.A.18; [Vanguard Balanced fact sheet](https://workplace.vanguard.com/assets/corp/fund_communications/pdf_publish/us-products/fact-sheet/F0869.pdf);
   [PV blends](https://www.portfoliovisualizer.com/faq).
3. **Freshness as three states, by quote age.** `LIVE` (fresh within the
   session), `DELAYED 15M` (the feed's lag, measured in doc 18 as ~15 min
   for European indices), `STALE` (no update for 20 min while the calendar
   says open), `CLOSE` with its date. A small `D` beside a delayed price,
   as TradingView does. Sources: [EODHD](https://eodhd.com/financial-academy/fundamental-analysis-examples/real-time-market-data-reliability-stale-price-detection-rest-fallback-and-websocket-recovery);
   [Deutsche Börse](https://www.mds.deutsche-boerse.com/mds-en/real-time-data/Delayed-data);
   [TradingView](https://www.tradingview.com/support/solutions/43000698958-alerts-based-on-real-time-and-non-real-time-symbols/).
4. **Never annualise under a year; label `(ann.)` above it.** `cagr` today
   appears only from 3 y; the rule should be: 1 y and longer get both the
   cumulative and the `(ann.)` figure, shorter windows only the cumulative.
   Sources: GIPS 2.A.12; [Sharesight](https://help.sharesight.com/absolute-and-annualised-return/);
   [Fidelity](https://www.fidelity.com/webcontent/ap002390-mlo-content/19.09/help/learn_performancereporting.shtml).
5. **Threshold bands beside the calendar sweep, with a drift mark.** A
   `REBAL` sub-mode "bands 5/25, checked monthly", and on HOLDINGS a `!`
   when a position is outside its band. Sources: [Vanguard 2015](https://web.archive.org/web/20230606014619/https://www.vanguard.ca/documents/best-practices-for-portfolio-rebalancing.pdf);
   [Vanguard 2024](https://corporate.vanguard.com/content/dam/corp/research/pdf/the_rebalancing_edge_optimizing_target_date_fund_rebalancing_through_threshold_based_strategies.pdf);
   [Bogleheads wiki](https://www.bogleheads.org/wiki/Rebalancing);
   [bt `RunIfOutOfBounds`](https://github.com/pmorissette/bt/blob/master/bt/algos.py).
6. **Drawdown with dates.** `MDD −23% 22-01→22-10, REC 24-02` in the
   footer or on click; the HA dashboard gets the five-row table. Sources:
   [quantstats](https://github.com/ranaroussi/quantstats/blob/main/quantstats/stats.py);
   [Wealthfolio](https://github.com/afadil/wealthfolio/blob/main/crates/core/src/portfolio/performance/performance_model.rs).
   Note for the golden match: PV's drawdown is from month ends.
7. **Contribution per holding and an FX line.** HOLDINGS shows each
   position's contribution to the window return (weight × return), sorted,
   so the top and bottom contributors read first; PORTFOLIO's footer gains
   `FX` for a EUR portfolio of USD funds. Sources: [Bloomberg PORT](https://data.bloomberglp.com/professional/sites/4/Portfolio_and_Risk_Analytics_Brochure4.pdf);
   [Sharesight components](https://help.sharesight.com/au/components-return/);
   Wealthfolio attribution.
8. **Growth-of-10 000 discipline and a telltale option.** All lines on
   PORTFOLIO start at `C` (they nearly do; make it a checked rule), and an
   Advanced line mode draws portfolio ÷ benchmark, flat when they match.
   Sources: [Morningstar](https://www.morningstar.com/help-center/portfolio/performance-charting);
   [Vanguard fact sheet](https://workplace.vanguard.com/assets/corp/fund_communications/pdf_publish/us-products/fact-sheet/F0869.pdf);
   [Simba](https://web.archive.org/web/20220128172554/https://www.bogleheads.org/wiki/Simba's_backtesting_spreadsheet).
9. **Real-terms toggle.** `REAL` in the heading when on; HICP for EUR.
   Sources: [PV FAQ](https://www.portfoliovisualizer.com/faq); Simba.
   The HICP series itself is not yet fetched.
10. **Colour schemes, colour never alone.** A Display setting with
    green/red, blue/red (Bloomberg's CVD scheme) and red-up; thin lines
    and dark shades on black are what CVD users misread, which argues for
    the bright value line and a dim *grey*, not dim red or green, for the
    secondary lines. Source: [Bloomberg UX](https://www.bloomberg.com/company/stories/designing-the-terminal-for-color-accessibility/).

Honourable mentions, cheap once the above exist: `1M` and `MTD` presets
(Ghostfolio, IBKR); a YEARS page with calendar-year bars (Morningstar,
quantstats, every fund fact sheet); a data-quality field in `status`
per payload (Wealthfolio); per-holding annualised return as Koyfin shows it.

## Sources that could not be reached

- bogleheads.org: every direct fetch returns 403; Wayback captures of
  2024–2026 are stored as 403 too. Read instead: `Rebalancing` (through a
  third-party fetcher), `Calculating personal returns` (2021 capture),
  `Simba's backtesting spreadsheet` (2022 capture), forum t=433919 and
  t=451043 (first pages, third-party fetcher), t=186899 (2019 capture).
  Not read: `Expense ratios`, forum t=402237, the 2020 blog series "The
  elusive rebalancing bonus".
- portfoliovisualizer.com resolves to 0.0.0.0 on this Mac; the FAQ was read
  through a third-party fetcher. The backtest form itself was not read.
- testfol.io/help: 403 and a JavaScript shell; not verified.
- ghostfol.io/en/faq: a JavaScript application; only the README and the
  source were read.
- Morningstar "How to use personal returns": 404 today; the help-center
  page was read.
- Vanguard's personal-performance page and Morningstar's "Total vs
  Personal Return" page need JavaScript; quoted from search summaries.
- LSEG Workspace, Refinitiv Eikon portfolio views: not verified.
- Exchange colour conventions in Asia: secondary sources only.
- Eurostat HICP series: not fetched.
- Reddit: every thread requested was read in the end (some after a 429 and
  a 90 s retry). Not fetched: the r/LED search "stock ticker matrix" and the
  r/Bogleheads search "track returns spreadsheet" (429 in the first sweep,
  not retried), and the r/investing thread [Time weighted (TWROR) portfolio
  tracker recommendation?](https://www.reddit.com/r/investing/comments/194m0r/time_weighted_twror_portfolio_tracker/)
  (left out to stay inside the fetch budget). Reddit's search feed returns
  at most 25 hits, so the subreddit sweeps are samples, not censuses.
