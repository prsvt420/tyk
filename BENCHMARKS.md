# Benchmarks

Local load measurements for the short link creation and redirect endpoints.
The application, PostgreSQL and Locust run on the same computer, together
with Redis when caching is enabled.

## Methodology

- Three scenarios: creation, redirects and mixed traffic.
- Three 60-second repeats for each user level: `1`, `10`, `50` and `100`.
  The first mixed level uses two users, one of each class.
- One application worker, no reload, `LOG_LEVEL=INFO` and ordinary
  terminal output.
- Unrelated heavy workloads avoided.
- The short links table starts empty before every run. The reset
  transaction is committed before Locust starts.
- Spawn rate equals the user count. There is no artificial task wait
  and the HTTP client read timeout is five seconds.
- Run time includes ramp-up and setup requests. No warm-up interval is
  excluded. Cache settings and resets are recorded for each version.

RPS is the arithmetic mean of three final HTML `total_rps` values.
The RPS range shows the lowest and highest repeat. Latency columns show
the range of Locust's approximate p50, p95 and p99 values across repeats,
in milliseconds. These are not percentiles of pooled requests.

Creation figures use POST `/api/v1/short-links`; redirect figures use
GET `/r/{short_code}` and exclude setup POSTs. Mixed figures use aggregate
traffic, including setup. Equal user counts in mixed traffic do not
guarantee an equal POST/GET request ratio. RPS includes failed requests;
failures are reported alongside throughput.

Each redirect user creates its own short link during setup and repeatedly
requests that link without following the redirect. With Redis enabled,
this workload reuses a small set of keys that warms within each run.

## Running Measurements

Run Locust from the repository root against the running application.
Replace every placeholder in this command template before running it:

```text
uv run locust -f tests/load/locustfile.py --host http://127.0.0.1:8000 --headless -u <users> -r <users> -t 60s --html tests/load/results/<version>/<scenario>/<run>/locust_report.html --csv tests/load/results/<version>/<scenario>/<run>/locust <user-classes>
```

Use the application version for `<version>` (for example, `v0.2.0`)
and a different `<run>` directory for every repeat (for example,
`run-01`). Select the scenario and user classes below:

| `<scenario>` | `<user-classes>`                            |
|--------------|---------------------------------------------|
| create       | `CreateShortLinkUser`                       |
| redirect     | `RedirectShortLinkUser`                     |
| mixed        | `CreateShortLinkUser RedirectShortLinkUser` |

Run each scenario three times at each `<users>` level: `1`, `10`, `50`
and `100`. For mixed traffic, use `2`, `10`, `50` and `100` total users.
This produces 12 runs per scenario and 36 runs in the complete series.

## Raw Reports

Reports are stored under
`tests/load/results/<version>/<scenario>/<run>/`.
Each run contains five files:

- `locust_report.html`
- `locust_stats.csv`
- `locust_stats_history.csv`
- `locust_failures.csv`
- `locust_exceptions.csv`

CSV files contain periodic snapshots and can differ slightly from the
final HTML report. All summaries below use the final HTML statistics.

## v0.1.0

Collected on 2026-10-24 using an AMD Ryzen 7 7700 8-Core Processor,
31.06 GiB of OS-visible physical RAM and Windows 11 (build 26200).
Python 3.13.11, Locust 2.47.0 and Uvicorn 0.48.0 were installed.
FastAPI 0.136.3, SQLAlchemy 2.0.51 and asyncpg 0.31.0 were also installed.
The database server was PostgreSQL 18.

Redis caching was not used in this version. Short link lookups went
directly to PostgreSQL.

| Scenario | Users | Mean RPS |     RPS range | p50 (ms) | p95 (ms) | p99 (ms) | Failed / requests |
|----------|------:|---------:|--------------:|---------:|---------:|---------:|------------------:|
| create   |     1 |   562.19 | 548.92–570.54 |        2 |        2 |        2 |       0 / 100,691 |
| create   |    10 |   674.57 | 672.46–676.94 |       13 |    18–23 |       49 |       0 / 120,872 |
| create   |    50 |   785.74 | 782.94–787.61 |    56–57 |   94–100 |  130–150 |       0 / 140,792 |
| create   |   100 |   762.97 | 744.74–775.85 |    58–59 |  190–480 | 650–3400 |     365 / 136,718 |
| redirect |     1 |   763.57 | 760.88–766.31 |        1 |        1 |        2 |       0 / 136,662 |
| redirect |    10 |   885.38 | 869.79–895.27 |    10–11 |       12 |    46–48 |       0 / 158,637 |
| redirect |    50 |   980.74 | 969.43–994.60 |    28–30 |  100–190 |  220–320 |       0 / 175,744 |
| redirect |   100 |   959.06 | 952.59–963.28 |    28–29 |  480–720 | 770–1000 |       0 / 171,866 |
| mixed    |     2 |   764.06 | 752.83–772.08 |        2 |        4 |      4–5 |       0 / 136,907 |
| mixed    |    10 |   686.15 | 650.73–706.76 |    11–12 |    44–46 |    53–58 |       0 / 122,859 |
| mixed    |    50 |   754.36 | 752.77–756.14 |       55 |      150 |  250–260 |       0 / 135,163 |
| mixed    |   100 |   711.33 | 705.43–715.95 |    60–61 |  560–580 |     1100 |       0 / 127,464 |

The 36 runs contain 1,664,858 requests, including
726 setup POSTs. All setup requests succeeded. There were
365 failed requests, all in `create/run-10`:
365 of 44,484 requests failed (0.82%). The other 35 runs had zero failures.
The failing run is included in the summary.

At 100 users, mean throughput was lower than at 50 users in every
scenario, while p95 and p99 increased. Increasing concurrency therefore
did not improve throughput at that tested level in this configuration.

## v0.2.0

Collected on 2026-10-27 on the same computer and operating system as
`v0.1.0`. The application ran locally with one worker, no reload and
`LOG_LEVEL=INFO`, using ordinary terminal output.
Python 3.13.11, Locust 2.47.0, Uvicorn 0.48.0, FastAPI 0.136.3,
SQLAlchemy 2.0.51 and asyncpg 0.31.0 were installed.
The database server was PostgreSQL 18. Redis caching used
redis-py 8.1.0 and hiredis 3.5.0.

Before every run, the short links table was truncated and the transaction
committed, and Redis keys matching `short_link:*` were deleted.
The cache warmed during the measured run. Cache settings were:

| Setting                         | Value |
|---------------------------------|------:|
| `CACHE_SHORT_LINK_TTL_SECONDS`  | 86400 |
| `CACHE_CONNECT_TIMEOUT_SECONDS` |   0.5 |
| `CACHE_SOCKET_TIMEOUT_SECONDS`  |   0.2 |

| Scenario | Users | Mean RPS |       RPS range | p50 (ms) | p95 (ms) | p99 (ms) | Failed / requests |
|----------|------:|---------:|----------------:|---------:|---------:|---------:|------------------:|
| create   |     1 |   541.94 |   530.21–554.66 |        2 |        2 |      2–3 |        0 / 96,915 |
| create   |    10 |   650.85 |   643.92–654.76 |    13–14 |    23–25 |    51–53 |       0 / 116,600 |
| create   |    50 |   761.76 |   751.62–767.98 |       58 |   96–110 |  150–180 |       1 / 136,463 |
| create   |   100 |   753.40 |   749.29–760.52 |    59–60 |  480–490 | 750–1200 |     118 / 134,989 |
| redirect |     1 |   824.42 |   821.83–826.76 |        1 |        1 |        2 |       0 / 147,622 |
| redirect |    10 |  1391.01 | 1388.94–1394.33 |        7 |        8 |     9–10 |       0 / 249,189 |
| redirect |    50 |  1561.84 | 1556.64–1569.50 |       31 |    35–36 |       40 |       0 / 279,808 |
| redirect |   100 |  1495.49 | 1490.15–1499.55 |       65 |    76–77 |    93–99 |       0 / 267,976 |
| mixed    |     2 |   891.30 |   883.30–899.94 |        2 |        3 |      3–4 |       0 / 159,694 |
| mixed    |    10 |  1004.37 | 1003.62–1005.45 |        9 |       14 |    15–16 |       0 / 179,922 |
| mixed    |    50 |  1047.31 | 1043.10–1050.28 |       39 |    68–69 |    77–80 |       0 / 187,642 |
| mixed    |   100 |  1045.72 | 1044.27–1046.93 |       77 |  140–150 |  170–180 |       0 / 187,369 |

The 36 runs contain 2,144,672 requests, including 726 setup POSTs.
All setup requests succeeded. There were 119 failed requests, all in
the creation scenario:

| Run             | Users | Failed / requests |
|-----------------|------:|------------------:|
| `create/run-08` |    50 |        1 / 45,732 |
| `create/run-10` |   100 |       45 / 45,422 |
| `create/run-11` |   100 |        5 / 44,817 |
| `create/run-12` |   100 |       68 / 44,750 |

The other 32 runs had zero failures. All runs are included in the
summary. No Locust exceptions were recorded.

At 100 users, mean throughput was lower than at 50 users in every
scenario. Redirect throughput peaked at 1561.84 RPS with 50 users;
increasing concurrency to 100 users raised redirect p95 from 35–36 ms
to 76–77 ms.

## v0.1.0 to v0.2.0

The table compares the mean RPS of three repeats at each user level.
Percentage changes are calculated from the unrounded means.

| Scenario | Users | v0.1.0 RPS | v0.2.0 RPS |  Change |
|----------|------:|-----------:|-----------:|--------:|
| create   |     1 |     562.19 |     541.94 |  −3.60% |
| create   |    10 |     674.57 |     650.85 |  −3.52% |
| create   |    50 |     785.74 |     761.76 |  −3.05% |
| create   |   100 |     762.97 |     753.40 |  −1.26% |
| redirect |     1 |     763.57 |     824.42 |  +7.97% |
| redirect |    10 |     885.38 |    1391.01 | +57.11% |
| redirect |    50 |     980.74 |    1561.84 | +59.25% |
| redirect |   100 |     959.06 |    1495.49 | +55.93% |
| mixed    |     2 |     764.06 |     891.30 | +16.65% |
| mixed    |    10 |     686.15 |    1004.37 | +46.38% |
| mixed    |    50 |     754.36 |    1047.31 | +38.84% |
| mixed    |   100 |     711.33 |    1045.72 | +47.01% |

Redirect throughput increased at every tested user level. At 100 users,
p95 decreased from 480–720 ms to 76–77 ms and p99 from 770–1000 ms to
93–99 ms, while p50 increased from 28–29 ms to 65 ms.

Creation throughput decreased by 1.26–3.60% across the tested levels.
Creation failures were recorded in both versions: 365 in `v0.1.0` and
119 in `v0.2.0`.

Mixed throughput increased by 16.65–47.01%. Its request composition also
changed: at 100 users, GET requests accounted for 30.68% of measured
POST/GET traffic in `v0.1.0` and 64.10% in `v0.2.0`, excluding setup
requests. Interpret this aggregate result together with the separate
creation and redirect scenarios.

These figures compare local release configurations. Redis was enabled
in `v0.2.0`; its cache was reset before each run and warmed during the
measurement. The series does not isolate Redis from other release
changes or establish production capacity.

## Comparing Future Versions

Keep the scenario, user levels, duration, timeout, reset procedure,
logging settings, output method and host conditions consistent.
Run each scenario three times at every user level.
