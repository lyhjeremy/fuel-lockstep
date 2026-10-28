# Fuel Lockstep: spec

Project 37. Started 2026-10-28.

## Question

Hong Kong's five petrol brands post the same pump price for each grade almost all the time. Prices across nearby stations in the US vary by a dollar a gallon or more. Is Hong Kong's alignment what you would expect from common costs and a small, transparent market, or does it show patterns that cost movements cannot explain? What does a market with many independent stations look like when you run the same screens?

## Decisions (Jeremy, 2026-10-28)

1. Same question as the old essay, answered with time-series data. Run the timing, variance and event-study screens instead of only proposing them.
2. US side: EIA weekly retail prices (Los Angeles, California, US) plus EIA wholesale and spot prices for pass-through. Station-level dispersion comes from Western Australia's FuelWatch (every Perth station, daily).
3. Output: a GitHub repo with code, a Ledger write-up site linked from lyhjeremy.com, and a LaTeX paper in consulting style (executive summary up front, numbered exhibits, case citations).
4. The project stands alone. Do not mention any earlier essay.
5. HK window: all available history.
6. I decide everything and push to main as Jeremy with no AI trailer.

## Data

| Source | What | Span |
|---|---|---|
| data.gov.hk historical archive of `oilprice_en.csv` (Consumer Council) | posted pump price by brand and grade, one version per change | 2020-04-30 to now |
| Consumer Council price trend database | price after walk-in discount less duty, monthly import price | last 2 years |
| Census and Statistics Department | monthly import prices of motor spirit | as far back as published |
| EIA | weekly retail gasoline (LA, CA, US), NY Harbor / LA spot RBOB-CARBOB, Brent | 2000 to now |
| FuelWatch WA | daily station prices, Perth metro ULP | 2001 to now |
| FX | HKD/USD (pegged; check only) | |

Note: Hong Kong's posted-price history starts in April 2020 because the archive does. That still covers the 2022 price shock.

## Screens

1. Timing: the share of brands that change price on the same day; the lag between the first and the last mover; who leads.
2. Variance: dispersion across brands of posted prices over time, compared with the volatility of input costs.
3. Pass-through and asymmetry: how fast and how much retail prices respond to cost increases versus decreases (rockets and feathers).
4. Event studies: retail response around large cost shocks.
5. Discounts: spread of net prices across brands, where the data allows.
6. WA comparison: the same dispersion and timing measures across Perth stations.

## Rules

Ledger design, designcheck must pass, no em dashes, numbers come only from the repo's data, sources cited.
