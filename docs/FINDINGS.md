# Findings and design review

Prepared on 2026-10-16 from recorded experiments and pinned source snapshots.
Claim IDs refer to [CLAIMS.json](CLAIMS.json).

## The identity and enforcement problem

The target is a cap on distinct active source IPs for an authenticated account,
not a count of physical devices. Two devices behind one NAT may share one slot;
one device using multiple egresses may consume multiple slots. An IP limiter
cannot reconstruct identity lost through shared or rotating intermediary exits.

In the topology investigated, Xray can attribute a trusted forwarded IP to a
session while the origin firewall sees a CDN or local proxy as the packet source.
Recording or requesting a ban for the attributed IP does not establish that an
origin firewall rule matches its packets. An IP-only ban can also affect another
account sharing that IP. Replacing iptables with nftables alone does not change
that identity mismatch. This explanation is based on source/topology review;
the loopback benchmarks did not replay the live CDN/firewall path. [F01, F02]

```text
network packet source:  CDN / local proxy -> origin firewall
authenticated session: account + attributed source IP -> Xray dispatcher
```

The analysis assumes trustworthy source-IP attribution through the intended
proxy path. It does not audit the deployment's header trust boundary.

## Options that were considered

| Option | What it can offer | Evidence and remaining boundary |
| --- | --- | --- |
| Existing panel/Fail2Ban | Detect excess IPs, request firewall bans | Application IP and packet source can differ behind a CDN; IP-only scope |
| Controller managing official routing rules | Block attributed source IPs; rules can also match account | Existing prior work; no equivalent local benchmark of this bridge. Account scoping, concurrent edits and existing-flow behavior require verification |
| Cloudflare-edge ban | Act before traffic reaches the origin | No prototype/benchmark here; an IP ban alone does not identify the Xray account |
| HTTP filter before Xray | Potential request admission layer | Concept only; account authentication and stream lifecycle need a design |
| Native Go admission | Atomic account+IP admission tied to core lifecycle | Implemented and tested on one core; custom build and lifecycle/panel gaps remain |
| Pure Lua global table | Local script bookkeeping | Diagnostic tests demonstrate separate VM globals; no shared atomic cap |
| Official Lua + controller | Keep official Xray binary, share admission across two fixture cores | Working bounded prototype; higher measured CPU and conservative restart recovery |
| V2bX-style embedded core | Precedent for custom dispatcher integration | Backend/core integration, not a plugin attached to an official running binary |
| Subscription HWID cap | Restrict subscription registration/download in compatible clients | Does not itself cap simultaneous use of copied tunnel credentials |

A routing bridge must represent each intended account/IP relationship correctly.
One rule containing multiple users and multiple sources would match combinations
of those fields, not an arbitrary list of paired identities. No claim is made
that a config update, by itself, atomically reserves capacity or terminates every
already-routed stream. The existing issue author's end-to-end result remains
their reported result; we did not reproduce that bridge. [F22, F23]

## Native Go prototype

The core base is Xray `v26.10.10`, commit
`701af60772cda123492f86e383e1fdba066614a9`; the panel base is
`608ef4e4010bf83e2e78328e08f77efc051ad4d7`. The prototype changes are additional
working-tree changes, not features already present in those upstream commits.

Admission runs after account identity is available and before routing in both
`Dispatch` and `DispatchLink`. A policy snapshot maps exact account labels to
caps. Checking the cap and adding an IP reference happen under the same
per-account `OnlineMap` lock. An already admitted IP adds a reference; a new IP
at the cap is refused. A context marker prevents nested dispatch from counting
the same reservation twice. `context.AfterFunc` removes the reference when the
owning context ends; the final reference releases the distinct-IP slot. [F02, F05]

The policy file is read outside the connection decision path and kept as an
immutable in-memory snapshot, watched every two seconds. The panel publisher
runs from the existing IP-check job, reads the selected accounts' existing
`limit_ip`/enable records and writes changed policy bytes atomically. A disabled
or nonpositive-limit record produces no positive native cap; account enablement
is still handled by the panel/core's normal authentication configuration.
This prototype adds no check for each byte of user traffic.

Recorded unit/race tests covered competing IPs for one slot, many references to
one IP, account isolation, cancellation and bounded churn. A 16-account,
32-held-flow fixture refused 16 third IPs in each of three native-on runs, for
48 expected refusals; allowed data and later slot reuse passed. The 16,384-cycle
churn test was an in-process reservation test, not 16,384 Internet connections
or a multi-day memory-leak test. [F05, F06]

## Capacity release and panel controls

Closing a client-side socket is not necessarily the end of its server-side
logical flow. In the Windows VLESS/XHTTP fixture, the client and server's default
one-second `downlinkOnly` periods explained a roughly two-second release chain.
Setting one side to zero gave roughly one second; setting one side to two gave
roughly three seconds. Changing `connIdle` alone did not remove the two-second
delay. Both-zero release was below observer resolution, not proof of zero lifetime.
The default is also present in the pinned source's `SessionDefault`. [F10]

The timer protects half-close behavior: a response delayed by 0.4 seconds
survived with the one-second client setting and was lost with zero. Globally
zeroing it would sacrifice valid behavior. Silent mobile-network loss and CDN
idle behavior were not quantified by that local test.

The panel's IP Log is saved history, not the authoritative native reservation
table. Refresh reloads the display. Clear All clears local saved history; it
does not disconnect streams or release native slots, and later sync can refill
the display. Rejected native admissions may never enter the active map. [F03, F26]

The roughly ten-second node-sync cadence is separate from the 120-second
classification window for some database-only synchronized observations.
A controlled database fixture counted a 30-second-old observation and excluded
a 121-second-old one. The stipulated old timestamp was consistent with an
admission timestamp, not a per-byte heartbeat. This did not demonstrate that a
particular live remote flow had been misclassified. [F04]

## Official Lua prototype

The pinned core compiles Lua programs once and reuses isolated VMs from a pool.
Top-level lookup preparation avoids rebuilding invariant tables for each call.
The pool retains up to 16 idle states; this is not a ceiling on active states.
VM globals are not a shared atomic store, and the inspected routing context has
no final-flow-close callback. `routing.script` takes over normal rule selection;
an error or nil result does not promise continuation through ordinary rules.
[F11, F12, F16]

The full prototype used a supported DNS query binding to carry a private
loopback decision message to a Go controller. This is an experiment-specific
transport, not a public DNS service or official IP-limiter API. Caching, stale
answers and fallback were disabled; decision replies had zero TTL, the resolver
timeout was 200 ms, and both an explicit block return and a first-outbound
blackhole handled failures. One request was made for each new logical flow,
not each byte. [F13]

The controller maintained persistent StatsService connections and polled every
100 ms. Complete multi-core snapshots, pruning and admissions were serialized
with one mutex. Only granted pairs consumed capacity. An owner disappeared only
after its absence from a complete successful snapshot of all scoped nodes;
LastSeen age alone did not release it. Snapshot errors retained owners and
denied new admissions. [F14, F15]

Fifteen functional checks passed on two cores on one host, including a shared IP,
account isolation, competing new IPs, last-node release, cap changes and controller
stop/restart. Paused statistics were an internal fault injection, not a physical
gRPC link partition. Restart recovery blocked new scoped admissions until all
scoped flows were gone, while existing flows continued. This conservative
availability loss is not durable ownership recovery. Native Go did not acquire
two-node coordination from these Lua tests.

The first functional run passed 14 checks and failed the final socket audit due
to a wildcard UDP listener. It was retained as a failure. Constraining the fixture
outbound's `sendThrough` to loopback allowed the revised run to pass all 15 checks;
no production configuration was changed. [F24]

## Global coordination proposal

A strict shared cap needs one atomic admission authority, a stable account key,
node-specific references, idempotent operations and generation-aware ownership.
An expired lease or missing heartbeat does not prove that an old flow stopped.
Reassigning its slot while it still transfers can exceed the cap. The earlier
lease-reassignment proposal was therefore restricted: require confirmed closure
or valid fencing, or retain uncertain ownership with an availability cost.
Nine offline model tests and counterexamples informed this conclusion; they are
not an operational distributed coordinator. [F20, F21]

Neither real WAN/mTLS/partition tests nor durable failover of the native design
have been completed. Two independent native installations each enforcing cap N
do not implement a global cap N.

Historical postcheck summaries recorded unchanged production invariants and
cleanup of owned lab processes. Raw host fingerprints and private guard logs
are omitted. This is a historical audit summary, not a fresh attestation of a
live server's state. [F25]

## Open issues and proposed direction

| ID | Observed gap | Proposed resolution, not implemented |
| --- | --- | --- |
| B01 | Missing first valid policy can leave native unlimited while panel legacy handling is suppressed | Publish initial policy, explicit pending/ready handoff and retained last-good state; define startup failure policy |
| B02 | Panel drops empty CSV tokens; core rejects a trailing comma | One parsing contract and matching test vectors |
| B03 | Replacing custom core with stock removes enforcement without an ownership handshake | Process-bound capability/readiness check and controlled ownership transfer around updates |
| B04 | Native coordination is single-node; Lua restart recovery loses availability | Agree on authority, durable/generation-aware ownership and partition semantics before implementation |
| B05 | Existing settings are partly integrated; Clear/Refresh are not session controls | Explicit active/rejected-state API and account+IP disconnect semantics; reconcile allowlist/ban-duration behavior |
| B06 | Coverage is bounded | Test UDP/XUDP, prolonged mux/churn, restarts, overload and sustained multi-account workloads |
| B07 | Lua replaces normal rule selection | Translate and verify real routing behavior and failure handling before use |
| B08 | Source IP may rotate or be shared | State the IP-identity boundary; endpoint choice is not permanent device identity |

B01 combines separately reproduced component behavior; a combined simultaneous
startup failure was not tested end to end. B03 is inferred from replacement and
ownership code paths; a real production upgrade was not performed. The passing
gap-reproduction tests preserve these flaws rather than assert desirable behavior.
[F17, F18, F19, F26, F27]

Native Go is the lower-CPU candidate in the matched full-solution comparison.
Keeping the official core binary is the Lua prototype's main architectural
advantage, not a demonstrated total-CPU advantage. Maintainer discussion should
first settle the policy boundary and whether a small generic admission/lifecycle
interface is preferable to embedding panel-specific policy in the core.

## Edge probes and other projects

The older three completed direct-HTTPS scans each attempted 21 addresses in two
modes, five times per mode. Address-level results were 3 multi-egress / 10 single /
8 unknown, then the same counts, then 3 / 9 / 9. All 105 ECH attempts in the third
run failed ECH setup. A completed attempt count is not successful validation of
both modes. [F28]

The final expanded run attempted 65 addresses in 650 samples. Across successful
replies, 52 addresses had one observed egress and 13 had none; no address had
multiple observed egresses. The prior 18-sample run was incomplete. The reports
do not independently record the network label or VPN/TUN state; those came from
user reports. These traces neither prove filtering/BGP attribution nor validate
an entire VLESS connection. Coverage of the separately described 69-address input
was not established. Endpoints and egress IPs have been omitted. [F29, F30]

Other-panel findings are limited snapshot research, not installed-system
comparisons. The inspected alireza0/x-ui path used nftables keyed by IP and port;
session closing in s-ui did not itself establish an automatic concurrent-IP cap.
Subscription HWID and tunnel admission remain different mechanisms. V2bX and
Sir-MmD are prior integration/native work; this package does not claim first
invention. Specific original-V2bX diagnostic failures must not be generalized to
newer forks, some of which register XHTTP and both dispatch paths. See
[sources and attribution](SOURCES.md). [F22, F23]
