# Account-scoped IP admission in Xray: research and review patches

[راهنمای فارسی و ترتیب مطالعه](README.fa.md)

This package investigates a concurrent source-IP cap for each authenticated
account when a reverse proxy or CDN separates the reported client IP from the
packet source seen by the origin firewall. It contains prototype patches,
selected recorded measurements and reproducible offline calculations.

**Research prototype, not a deployment release.** The native implementation is
single-node. Cold-start ownership, parser consistency, binary replacement and
panel controls remain unresolved. No production account was activated for these
experiments, and preparing this package did not change an active service.

The native Go prototype made an atomic admission decision inside Xray using its
per-account online-IP map. A second prototype used official Lua routing, a local
Go controller and StatsService snapshots; it coordinated two cores on one host.
That does not establish native coordination between geographically separate nodes.

In the same bounded pass-5 workload, three samples per mode gave:

| Mode | Mean CPU time for matched allowed phases | Maximum sum of process HWM |
| --- | ---: | ---: |
| Stock routing | 97.780 ms | 39.520 MiB |
| Stock + simple Lua, no limiter | 97.927 ms | 39.895 MiB |
| Native Go | 103.117 ms | 40.387 MiB |
| Stock + Lua + controller | 159.284 ms | 58.391 MiB |

CPU includes server plus controller where present, excludes client/target and
startup/denial/cleanup phases, and was measured under a CPU quota. The complete
Lua solution used about 54.47% more CPU time than native Go **in this workload**.
These are not percentage points of VPS utilization or a per-user surcharge.
See [methodology and other passes](docs/BENCHMARKS.md).

## Contents

- [Findings, alternatives and unresolved design decisions](docs/FINDINGS.md)
- [Evidence and benchmark boundaries](docs/BENCHMARKS.md)
- [Recalculate tables and inspect/test patches](docs/REPRODUCING.md)
- [Thirty scoped claims and their evidence](docs/CLAIMS.json)
- [Sources, previous work and discussion history](docs/SOURCES.md)
- [Draft comment for the existing upstream issue](docs/MAINTAINER-DRAFT.md)
- [Licensing and attribution](NOTICE.md)

The patches are separated into native core changes, a panel publisher, and Lua
research tools. They preserve known flaws for review. Synthetic account labels
replace the original test label; production configs, endpoints, credentials,
databases, binaries and private remote runners are absent.

To recalculate the saved CPU tables with Python 3, without running a proxy:

```sh
python scripts/summarize.py
```

That calculation is not a replay of the end-to-end benchmarks. The selected
patches provide unit/diagnostic reproduction; the full private benchmark wrapper
is not shipped. No claim of zero overhead, complete transport coverage, long-term
leak freedom or upstream acceptance is made.
