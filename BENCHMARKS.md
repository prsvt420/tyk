# Benchmarks

Local load measurements for the short link creation and redirect endpoints.
The application, PostgreSQL and Locust run on the same computer.

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
  excluded, and caches are not reset between runs.

RPS is the arithmetic mean of three final HTML `total_rps` values.
The RPS range shows the lowest and highest repeat. Latency columns show
the range of Locust's approximate p50, p95 and p99 values across repeats,
in milliseconds. These are not percentiles of pooled requests.

Creation figures use POST `/api/v1/short-links`; redirect figures use
GET `/r/{short_code}` and exclude setup POSTs. Mixed figures use aggregate
traffic, including setup. Equal user counts in mixed traffic do not
guarantee an equal POST/GET request ratio. RPS includes failed requests;
failures are reported alongside throughput.

## Running Measurements

Run Locust from the repository root against the running application.
Replace every placeholder in this command template before running it:

```text
uv run locust -f tests/load/locustfile.py --host http://127.0.0.1:8000 --headless -u <users> -r <users> -t 60s --html tests/load/results/<version>/<scenario>/<run>/locust_report.html --csv tests/load/results/<version>/<scenario>/<run>/locust <user-classes>
```

Use the application version for `<version>` (for example, `v0.1.0`)
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

## v0.1.0

Collected on 2026-10-24 using an AMD Ryzen 7 7700 8-Core Processor,
31.06 GiB of OS-visible physical RAM and Windows 11 (build 26200).
Python 3.13.11, Locust 2.47.0 and Uvicorn 0.48.0 were installed.
FastAPI 0.136.3, SQLAlchemy 2.0.51 and asyncpg 0.31.0 were also installed.
The database server was PostgreSQL 18.

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

## Comparing Future Versions

Keep the scenario, user levels, duration, timeout, reset procedure,
logging settings, output method and host conditions consistent.
Run each scenario three times at every user level.
