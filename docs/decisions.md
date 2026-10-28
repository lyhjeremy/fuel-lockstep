# Decisions

D1. Hong Kong window starts 2020-04-30, the first version in the data.gov.hk historical archive of the Consumer Council file. Nothing earlier is available at daily resolution.

D2. The archive's price column is labeled "Retail Price" until 2020-10-30 and "Pump Price" from 2020-10-31. The level shows no break at the switch (Standard went from 17.39 to 17.29, the same cut every brand made that week), so the two are treated as one series of posted pump prices.

D3. Premium feed faults. Some snapshots report one brand's premium price equal to its own standard price, and the next snapshot restores the surcharge. A brand can also price both grades the same for weeks at a time (PetroChina did in November 2020, as the Council's own page shows), so only a match that lasts exactly one snapshot, with a surcharge on both sides of it, is dropped. Standard is the headline grade in every screen; premium and diesel are secondary.

D4. A day's price is the last snapshot taken that day, carried forward to days with no new snapshot. The archive stores a version only when the file changes, and snapshots are taken around 09:00 to 11:00 HKT. A price change that takes effect overnight therefore shows up on the day it was harvested, and one-day lags between brands are within the resolution of the data.

D5. Hong Kong's cost benchmark is the C&SD monthly import unit value of unleaded petrol (table 915-91104), HK$ per litre. For weekly pass-through, the US Gulf Coast conventional gasoline spot price is converted to HK$ per litre. Hong Kong sells only 98 RON, so the Gulf Coast series (regular grade) is a proxy for world gasoline price movements, not Hong Kong's import cost; the monthly C&SD series checks it.

D6. Los Angeles: EIA weekly retail (regular, all formulations, Monday survey) against the mean LA reformulated RBOB spot price over the seven days before the survey.

D7. Chart colors are the Ledger base accents: oxide for retail prices and cost rises, pine for costs and cost falls, gray for everything else. The pair fails the dataviz validator's lightness and chroma checks because the house palette is deliberately muted, and its protan separation (7.6) is in the 6 to 8 band that needs a second cue. So any chart using both accents labels both series directly and draws the pine series dashed.

D8. Pass-through specification: four weekly lags of cost changes (split into rises and falls), one lag of the retail change, and an error-correction term, for every market. Hong Kong's long-run relation includes a linear time trend because its margin over cost drifts upward through the whole sample. Perth's price is the Tuesday median, the trough of its weekly cycle; a weekly mean of a cycling price mixes peak and trough days and made the fitted response unstable. results/passthrough_robustness.csv reruns every market with 6 and 8 lags and Perth at the weekly mean and the Wednesday peak.

D9. Walk-in discounts come from Internet Archive captures of the Consumer Council's Oil Price Watch page (Chinese and English home pages, one capture per day at most, 119 days from November 2020 to July 2026). Capture dates are UTC. As a check, the pump prices on those pages match the open-data archive's Standard price for the same brand and date on 97.5% of rows.

D10. The net margin is the mean across the five brands of the price after the walk-in discount, minus duty and that month's import unit value. Card and loyalty discounts are not observed, so the true average transaction price is lower than this net price by an unknown amount.
