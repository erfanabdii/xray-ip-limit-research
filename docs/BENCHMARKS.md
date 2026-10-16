# Recorded measurements and their limits

These are historical bounded fixtures. Preparing the publication package ran
only offline calculations, an isolated state-model check and file/patch checks,
not another VPS benchmark.
The exported [measurement JSON files](../measurements/) omit session identifiers,
endpoints, host identity and private raw logs.

## Comparisons that should stay separate

| Pass | Workload and repeats | CPU accounting |
| --- | --- | --- |
| 2 | One account; 40 × 64 KiB echoes plus a 4 MiB transfer limited to 1 MiB/s; three samples/mode | Server process lifetime, including startup and surrounding work |
| 3 | 16 accounts, up to 32 held flows; matched allowed phases total roughly eight seconds and 1 MiB each direction; three samples/mode | Precise process CPU for the two allowed phases; lifetime also recorded separately |
| 5 | 8 accounts, 16 held flows, 48 allowed connection starts and 128 held echoes totaling 1 MiB each direction; one-second active idle; three rotated rounds | Sum of five matched allowed phases, server plus controller where present |

Pass 2 used the installed build's matched `-gcflags=all=-l=4` settings and Go
1.27.2/dependency versions for the comparison. An earlier comparison with
unmatched build flags was excluded from overhead attribution. “Candidate off”
is the candidate build without opt-in; “candidate on” enables the native gate.

## Pass 2: server lifetime

| Mode | Mean CPU, ms |
| --- | ---: |
| Stock | 145.770667 |
| Candidate off | 147.573333 |
| Candidate on | 150.375333 |

On versus stock: **+3.158843%**. On versus candidate off: **+1.898717%**.
One candidate-on throttling event was recorded. The ratio describes this
process-lifetime workload, not the cost per account or per admitted connection.

## Pass 3: matched allowed phases

| Mode | Mean phase CPU, ms | Mean lifetime CPU, ms |
| --- | ---: | ---: |
| Stock | 86.965433 | 119.636667 |
| Candidate off | 94.819205 | 123.894667 |
| Candidate on | 101.712097 | 133.794333 |

Phase on versus stock: **+16.956925%**; versus off: **+7.269510%**. The off build
also differs from stock, so the whole stock/on gap cannot be assigned to active
admission alone. Throttling and three samples limit fine-grained conclusions.
Lifetime and phase ratios have different denominators and must not be mixed.

In the separate functional run, native-on refused 16 third IPs in each of three
runs, 48 total. Stock and candidate-off refused none in the corresponding phase.
Allowed-data and release checks passed. This is a one-core account-isolation test.

## Pass 5: complete solutions, equal allowed work

| Mode | Mean CPU, ms | Sample CPU range, ms | Maximum sum of process VmHWM, MiB |
| --- | ---: | ---: | ---: |
| Stock | 97.780385 | 93.397238–100.841138 | 39.519531 |
| Simple Lua | 97.927491 | 95.563371–101.138771 | 39.894531 |
| Native Go | 103.116571 | 100.923654–106.127567 | 40.386719 |
| Lua + controller | 159.284357 | 157.167379–163.323884 | 58.390625 |

The matched phases are first-IP admission, second-IP admission, held transfer,
short connections and active idle. The table includes core plus controller CPU,
not the traffic generator or echo target, and excludes startup, extra-IP
refusals and cleanup. The full Lua solution used **54.470184%** more CPU time than
native, an absolute difference of **56.167786 ms** for the matched work. Native
was **5.457317%** above stock in this pass. Simple Lua was **0.150445%** above stock;
that small sample difference is not a demonstrated general effect.

Each enforcing sample also checked eight extra-IP refusals outside these CPU
phases: 24 per enforcing mode across three rounds. Denials matter operationally,
but mixing their unequal work into the allowed-throughput comparison would change
the question being measured. High-rate abuse/overload was not established here.

RAM is the sum of each solution process's high-water RSS (`VmHWM`). Shared pages
are included, and process peaks need not occur simultaneously. It is neither
unique physical memory nor a steady-state leak measurement.

The lab had a 20%-of-one-core CPU quota and a 192 MiB memory limit. Throttling
occurred in every mode; whole-lab throttled time includes startup and other
processes and must not be attributed to the limiter alone. The cgroup memory
peak was 79,097,856 bytes, with zero recorded max/OOM/OOM-kill events. These
controls protected the host; they also prevent treating latency samples as
production p95/p99 or saturation-throughput results.

## Release and functional evidence

[release-timing.json](../measurements/release-timing.json) records nine observer
cases. Defaults gave approximately 2.0 s; one zero override about 1.0 s; one
two-second override about 3.0 s. Both-zero was below observer resolution. A
0.4-second delayed response survived client `downlinkOnly=1` and failed at zero.
This is an intervention on local flow lifetime, not a silent mobile-loss test.

[functional.json](../measurements/functional.json) preserves both the initial
Lua functional failure and the revised 15/15 result. Two-core behavior used one
host, including genuine controller process stop/restart and an internally paused
stats path. No geographically distributed partition, durable ownership recovery
or production panel/core combination is established by that result.

## Conclusions supported by these data

The complete native implementation was cheaper than the complete Lua/controller
prototype in the matched pass-5 fixture. The experiment does not establish zero
native overhead or lower total production CPU than panel+Fail2Ban. The differing
native ratios in passes 2, 3 and 5 are workload/accounting-dependent observations,
not a constant to multiply by the number of users.

A short native reservation-churn test and a local Lua pool microbenchmark answer
different questions. The former did not show retained growth after GC in that
bounded run; the latter favored top-level invariant preparation (about 759 versus
2562 ns/op). Neither substitutes for sustained full-solution performance and
lifecycle testing. The full original benchmark runner is not part of this package;
the included calculator reproduces tables from the selected saved metrics only.
