# Move Bench

[Use Move Bench](https://coolcode.ca/movebench/) to compare job offers, housing, recurring expenses and one-time moving costs. Your financial inputs stay on your device. No account or API key is needed.

<!-- coolcode:guide -->
Enter actual pay and expenses for your current and proposed places. Move Bench separates the gross-pay change from the expense change, calculates an equivalent gross salary and shows moving-cost recovery. All salary comparisons are before income tax and payroll deductions; provincial household averages appear only as dated context and never fill your budget automatically. Vancouver/Halifax place presets preserve your financial entries, and a research checklist links to product prices, groceries, housing, wages and regulated Atlantic fuel limits with their geographic and date limitations.
<!-- /coolcode:guide -->

## What it does

- Arbitrary place/scenario names, with Vancouver, Langley and Halifax starting suggestions.
- Place-pair buttons set city labels and reference provinces without changing any pay, expense or moving assumptions.
- Five evidence links explain geographic coverage, source periods and unit matching, plus a page-visit research checklist.
- Annual salary or hourly rate, paid hours and paid weeks. Zero or missing working hours cannot silently produce a meaningful hourly offer.
- Configurable monthly expense categories, one-time moving cost and a 1–600 month comparison horizon.
- Gross-pay change, expense change, equivalent annual gross salary and a simple moving-cost recovery period.
- Optional commuting-time comparison: gross pay per work-and-commute hour.
- Explicit local save/load/delete, JSON import/export, CSV and print.
- Historical Statistics Canada provincial household-spending context, separately labelled and never used as a city price estimate.

The **Try an illustrative example** button loads hypothetical Vancouver/Halifax figures with a visible label. These figures are not market data, current rents or salary guidance. A blank worksheet assumes no prices; a required field must explicitly contain zero when it does not apply.

## Calculation meanings

Annual hourly pay = hourly rate × paid hours per week × paid weeks per year. Annual salary is used directly. Monthly pay = annual gross pay / 12.

Monthly difference before deductions = (proposed monthly gross pay − current monthly gross pay) − (proposed listed expenses − current listed expenses).

Equivalent gross salary = current annual gross salary + 12 × the monthly expense difference, floored at zero. The version including moving costs spreads those costs across the chosen horizon. Moving-cost recovery is shown only when the monthly difference is positive; it is rounded up to a whole month.

**This is not take-home pay or disposable income.** Tax, payroll deductions, benefits, employment likelihood, inflation, investment returns and property appreciation are not estimated. Costs and pay stay constant over the scenario horizon. Province changes can materially affect taxes. Large refundable deposits may affect immediate cash requirements without being a permanent expense; the explanatory UI distinguishes this.

## Sources and privacy

The source for separate regional context is [Statistics Canada table 11-10-0222-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1110022201), Survey of Household Spending, under the [Statistics Canada Open Licence](https://www.statcan.gc.ca/en/reference/licence). Initial downloads contain reference years through **2023**. Provincial household averages include all household types and non-spenders; they are not current local rents or complete cost-of-living indices. The snapshot retains quality flags, vectors, actual reference years, source links, check date and download hash. CoolCode is not endorsed by Statistics Canada.

No scenario values or imported files are sent to a server. Explicit storage uses `coolcode:movebench:scenario` in this browser. Delete saved removes that record; Start blank clears the active worksheet. Reloading loses unsaved input. Exports contain your personal financial data. The site retrieves its own public files and uses the shared aggregate-open counter, which excludes inputs.

## Expand or customize

`web/config.json` controls suggested place names/regions, `place_pairs`, public `research` links, the `research_checklist`, monthly expense categories and the **explicitly illustrative** example. Only place/region fields from presets are applied; even a mistaken financial field in a preset cannot overwrite visitor numbers. Research links open without scenario query parameters; checklist ticks are temporary and not part of saves or exports. Visitors may enter any place name. Add a non-overlapping expense category with a unique `id`, `label` and optional `hint`; forms, totals and exports derive from this array. For example, add `pets` and then provide values in any example scenario. Existing imported scenarios missing a required new category must be completed rather than silently assuming zero.

`references.json` selects exact official table columns and contextual spending categories. Do not interpret provincial averages as local prices or auto-fill the worksheet from them. To change reference coverage, edit that file, run the refresh, review data and tests, then publish. Adding a place label alone needs no source refresh. The snapshot retains actual captured years, with the newest published year displayed for each selected region.

## Build, refresh and deploy

Python 3.12+ and Node 24+; no app dependencies or secrets.

```sh
python3 scripts/refresh.py
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -v
python3 scripts/build.py
```

Build is offline. Refresh downloads and validates the official CSV ZIP, and atomically replaces `web/data/benchmarks.json` only after schema, dimension, unit and coverage validation. Failed source checks preserve the previous snapshot. If the public context file cannot be loaded in a browser, the private calculator still works.

**Browser tool · Check and publish** (`.github/workflows/pages.yml`) refreshes on main pushes, manual dispatch, and monthly at **14:47 UTC on the 20th**. PRs test the committed snapshot without fetching/deploying. Failed collection blocks publication, retaining the previous Pages deployment. Successful refresh data is included in the Pages artifact; it is not automatically committed. Every subsequent main publication rechecks the source rather than replacing fresh public data with an old seed.

Set Pages source to **GitHub Actions**. CI smoke tests the actual example, arbitrary place labels, invalid inputs, persistence and mobile layout at a repository subpath.

Watchdog integration contract:

- repository: `jsdyer/movebench`
- workflow: `pages.yml`; manual dispatch has no required inputs
- collection step: `Refresh validated Statistics Canada spending data`
- freshness URL: `https://coolcode.ca/movebench/data/status.json`
- freshness field: `checked_at`; suggested maximum age **40 days**

The separate inactivity guard allowlists `pages.yml` and itself. Regenerate after workflow changes:

```sh
python3 scripts/add_schedule_guard.py --repository jsdyer/movebench .github/workflows/pages.yml
```

The central homepage, audit, Worker registry, watchdog targets and sitemap use the [CoolCode lifecycle](https://github.com/jsdyer/jsdyer.github.io/blob/main/docs/tool-lifecycle.md). This app does not need a live API gateway or a new secret.

## Research links and geographic limits

The source cards were checked against each tool's documented coverage on 2026-11-26. [Price Atlas](https://coolcode.ca/priceatlas/) and [Pantry Prices](https://coolcode.ca/pantryprices/) provide provincial product/package averages, not city shop quotes. [Housing Pulse](https://coolcode.ca/housing-pulse/) has separately labelled CMA and province series; the card directs users to match dwelling type, quarter and asking/paid-rent population. [Wage Window](https://coolcode.ca/wagewindow/) uses Job Bank occupations and economic regions such as Halifax and Lower Mainland, whose boundaries do not become city limits. [Fuel Window](https://coolcode.ca/fuelwindow/) covers Nova Scotia and PEI regulated limits; it supplies no BC station price. Cards intentionally link to each tool's selector rather than inventing unsupported URL filters or hard-coding prices that age. Users read the actual reference/effective date in the destination and enter their own quotes. These links do not add another collector or schedule.
