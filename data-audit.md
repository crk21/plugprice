# PlugPrice – AFDC DC Fast Data Audit (pulled 2026-10-22, IST)
Source: https://developer.nlr.gov/api/alt-fuel-stations/v1.json?fuel_type=ELEC&ev_charging_level=dc_fast&status=all&access=public&limit=all (DEMO_KEY). developer.nrel.gov did not respond (no connection). Raw: data/afdc_dcfast_raw.json (71 MB). Script: analyze.py. Full output: data/analysis_output.txt.

## 1. Totals
- 16,505 stations (all US), 81,430 DC fast ports.
- Status: E 15,843 (79,130 ports) | T 562 (1,358 ports) | P 100 (942 ports).

## 2. ev_pricing fill
- Overall 1,457 / 16,505 = **8.8%** (E only: 8.9%).
- Top 15 networks (stations / fill% / numeric-price%): ChargePoint 4,598 / 0.0 / 0.0; Tesla 3,294 / 9.4 / 9.4; EVgo 1,215 / 0 / 0; Electrify America 1,194 / 0 / 0; EV Connect 813 / 0.9 / 0.9; Blink 702 / 4.0 / 0.0; RED_E 609 / 0 / 0; Non-Networked 545 / 68.1 / 18.7; FORD_CHARGE 354 / 0 / 0; EVCS 223 / 0 / 0; IONNA 202 / 0 / 0; FCN 172 / 0 / 0; RIVIAN_ADVENTURE 162 / 0 / 0; VIALYNK 142 / 0 / 0; EVGATEWAY 119 / 0 / 0.

## 3. Usable vs vague
- Of 1,457 filled: 965 (66.2%) contain a number ($x, ¢, x/kWh or /min); 492 are vague. That's **~5.8% of all stations with a usable price**.
- Most common vague strings: "Free" (409), "Please download 7Charge app for current pricing." (43), "Dynamic EV pricing rates" (31).
- Samples: "$0.40 per kWh + $2 connection" · "$0.72 per kWh" · "$0.30 per kWh; $0.45 per kWh from 4pm-9pm" · "$0.46 Peak / $0.29 Off-Peak per kWh" · "$0.39 per kWh" · "$0.61 per kWh + tax; app discounts and time of use rates available" · "Free for Level 2; $0.40 per kWh for DC fast charging" · "$.45 per kWh" · "$0.48 per kWh" (Tesla) · "Free; $2 for 30 mins or $23 per day parking fee" · "Free for Level 2 charging; fee for DC fast charging" · "L2: Free" · "Free" · "Dynamic EV pricing rate" · "Please download 7Charge app for current pricing."
- Caveat: the regex is a heuristic. Strings like "Free; $2… parking fee" count as numeric even though the number is a parking fee, not a charging price.

## 4. Top 10 states (stations / fill% / numeric%)
CA 2,938 / 9.7 / 6.8 · FL 957 / 20.7 / 16.0 · TX 950 / 9.9 / 8.0 · NY 821 / 7.2 / 5.5 · IL 653 / 6.9 / 4.7 · MI 596 / 4.9 / 3.2 · GA 568 / 7.9 / 4.4 · WA 557 / 5.4 / 3.8 · MA 546 / 3.3 / 2.9 · CO 513 / 6.8 / 3.3

## 5. Reliability fields (E stations)
- status_code (E/T/P), date_last_confirmed (15,803/15,843 present), updated_at (100%), open_date (100%), expected_date (P stations only).
- Freshness: median date_last_confirmed = 2026-10-21. 11,382 were confirmed in the last 30 days, 11,593 in ≤90 days, 499 more than a year ago, and 40 have no date. updated_at median is 2026-10-21.
- Limits: there's no per-port uptime, no outage reason and no history. "T" is a coarse station-level flag (562 stations). To track reliability over time, we'd need to snapshot this daily and diff it ourselves, then add user check-ins.

## 6. Network price pages (HTTP check only, not scraped)
- Electrify America: https://www.electrifyamerica.com/pricing/ (200). Prices are listed by state and plan.
- EVgo: https://www.evgo.com/pricing/ (returned 429, rate-limited/bot-blocked). It publishes plan and regional pricing.
- Tesla: https://www.tesla.com/support/charging/supercharging (403 to curl). Per-site prices are mostly in the app/map. AFDC already has $/kWh for 309 Tesla sites.
- ChargePoint: each site host sets its own price, shown only in the app/map. There's no central price page (the guessed URL returned 404).
- IONNA: /pricing returned 404. Pricing seems to be app-based. Not verified; check manually.

## Verdict: hybrid, leaning reliability-first
AFDC is good for station coverage and fresh status data: 96% of stations are E and most were confirmed within the last 30 days. It's very poor for prices: only 5.8% of stations have a usable number, and the big networks (ChargePoint, EVgo, EA, IONNA) have 0%. Launch with a complete station map plus reliability, built from daily AFDC status diffs. Add prices network by network from public pages (start with EA, then EVgo) and from user-submitted prices. A price-first launch would be empty for about 94% of stations.
