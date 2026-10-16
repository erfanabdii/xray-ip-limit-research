# Sources, attribution and discussion history

Links in the source section are pinned to reviewed commits where available.
Issue/PR status below was refreshed through the GitHub connector on 2026-10-16.
The documentation and current contribution guide were also read on that date;
those pages can change. Historical comments are not promises of acceptance.

## Reviewed prototype bases

- [XTLS/Xray-core base commit](https://github.com/XTLS/Xray-core/commit/701af60772cda123492f86e383e1fdba066614a9), corresponding to the reviewed `v26.10.10` source.
- [MHSanaei/3x-ui base commit](https://github.com/MHSanaei/3x-ui/commit/608ef4e4010bf83e2e78328e08f77efc051ad4d7), reviewed source version 3.10.2.

The native limiter and publisher in this package are additional review patches.
The linked base commits do not already contain them.

Relevant base-source paths:

| Topic | Source |
| --- | --- |
| Lua VM reuse, idle cap and active-growth TODO | [common/lua/pool.go](https://github.com/XTLS/Xray-core/blob/701af60772cda123492f86e383e1fdba066614a9/common/lua/pool.go) |
| Script compilation/execution | [app/router/script.go](https://github.com/XTLS/Xray-core/blob/701af60772cda123492f86e383e1fdba066614a9/app/router/script.go) |
| Script takes over route selection | [app/router/router.go](https://github.com/XTLS/Xray-core/blob/701af60772cda123492f86e383e1fdba066614a9/app/router/router.go) |
| Default one-second half-close timeout | [features/policy/policy.go](https://github.com/XTLS/Xray-core/blob/701af60772cda123492f86e383e1fdba066614a9/features/policy/policy.go) |
| Policy-default inheritance | [app/policy/config.go](https://github.com/XTLS/Xray-core/blob/701af60772cda123492f86e383e1fdba066614a9/app/policy/config.go) |
| Panel online-IP processing/classification | [check_client_ip_job.go](https://github.com/MHSanaei/3x-ui/blob/608ef4e4010bf83e2e78328e08f77efc051ad4d7/internal/web/job/check_client_ip_job.go) |
| Original Fail2Ban/firewall action setup | [x-ui.sh](https://github.com/MHSanaei/3x-ui/blob/608ef4e4010bf83e2e78328e08f77efc051ad4d7/x-ui.sh) |
| Saved IP history and Clear operation | [inbound_client_ips.go](https://github.com/MHSanaei/3x-ui/blob/608ef4e4010bf83e2e78328e08f77efc051ad4d7/internal/web/service/inbound_client_ips.go) |
| UI Refresh/Clear handlers | [ClientInfoModal.tsx](https://github.com/MHSanaei/3x-ui/blob/608ef4e4010bf83e2e78328e08f77efc051ad4d7/frontend/src/pages/clients/ClientInfoModal.tsx) |
| Node sync cadence | [node_traffic_sync_job.go](https://github.com/MHSanaei/3x-ui/blob/608ef4e4010bf83e2e78328e08f77efc051ad4d7/internal/web/job/node_traffic_sync_job.go) |

Official routing documentation explains ordered matching, combined field
conditions and script takeover: [Routing configuration](https://xtls.github.io/config/routing.html)
and [Lua routing guide](https://xtls.github.io/development/lua/guide/routing.html).
The lifecycle/sharing claims here additionally rely on the pinned code and the
included diagnostic tests, not on a generic claim that Lua is fast or slow.

## Existing 3x-ui feature request

[Issue #6573](https://github.com/MHSanaei/3x-ui/issues/6573) was opened by **mjbe71**
on **2026-09-16**. At the 2026-10-16 check it was open with zero comments.
It reports the CDN/client-IP versus origin-firewall mismatch and a working
IP-based blackhole-routing bridge across a main panel and four remote nodes.
The author emphasizes top rule priority and links their implementation example.
Those deployment results are the author's report, not our benchmark.

This research credits that work. It investigates stricter account+IP admission,
flow release and coordination in addition to routing-rule ban enforcement. It
does not claim that the issue's bridge was merged or that these prototypes
supersede it without an equivalent comparison.

## Earlier Xray IP-restriction proposal

[PR #2277](https://github.com/XTLS/Xray-core/pull/2277), **amir-devman**, was opened
on **2023-06-30** and closed, unmerged, on **2024-08-06**. The refreshed record
retains that closed/unmerged state.

Several different concerns appear in its history:

- **yuhan6665**, 2023-07-04, questioned putting authorization/business policy in
  the core. [Comment](https://github.com/XTLS/Xray-core/pull/2277#issuecomment-1619353992)
- **RPRX**, 2023-07-04, expressed reluctance toward service-specific limits while
  leaving room to consider an already implemented PR. This is a paraphrase of
  that historical comment, not a current acceptance criterion.
  [Comment](https://github.com/XTLS/Xray-core/pull/2277#issuecomment-1619397762)
- **mmmray**, 2024-07-29, suggested external components using an API and raised
  performance-critical-path and multi-node concerns.
  [Comment](https://github.com/XTLS/Xray-core/pull/2277#issuecomment-2254770107)
- **yuhan6665**, 2024-08-06, closed it in favor of proposal #3637.
  [Closing comment](https://github.com/XTLS/Xray-core/pull/2277#issuecomment-2270258893)

This is not one blanket explanation for why the present panel has no identical
feature. The maintained policy boundary needs fresh maintainer discussion; a
public research package or passing local tests do not establish acceptance.

## Related implementations and snapshot boundaries

The local comparison reviewed selected paths rather than installing and
benchmarking every panel. For unpinned comparisons below, treat the observation
as the 2026-10-15 research note, not the guaranteed current state of all branches.

| Project | Reviewed scope / relevance | Limitation |
| --- | --- | --- |
| alireza0/x-ui | [nftables path](https://github.com/alireza0/x-ui/blob/main/iplimit/nft_linux.go) and [online store](https://github.com/alireza0/x-ui/blob/main/web/service/online_store.go) used IP+port enforcement in the selected research | Moving links; no live deployment benchmark or universal panel ranking |
| alireza0/s-ui | [stats](https://github.com/alireza0/s-ui/blob/main/service/stats.go), [session/user path](https://github.com/alireza0/s-ui/blob/main/core/inbound_users.go) | Session-close capability alone did not prove an automatic concurrent-IP cap in the inspected paths |
| PasarGuard | [subscription operation](https://github.com/PasarGuard/panel/blob/main/app/operation/subscription.py) | The examined HWID subscription behavior is not tunnel-IP admission |
| Remnawave | [HWID device-limit documentation](https://docs.rw/features/hwid-device-limit/) | Subscription/device registration boundary, not a claim about every deployment or copied tunnel credential |
| Original V2bX | [limiter/conn.go at 20cd508...](https://github.com/InazumaV/V2bX/blob/20cd5086215cbceea3bc5691109b73395f26518d/limiter/conn.go) | Old embedded-core snapshot; specific diagnostic failures must not be generalized to all forks |
| Newer V2bX fork | [wyx2685 inbound path at 71277de...](https://github.com/wyx2685/V2bX/blob/71277de69efbbc86c23ad8ae02b68efd174e5756/core/xray/inbound.go) | Demonstrates why a blanket “V2bX lacks XHTTP” claim is wrong; not an installed compatibility test |
| Sir-MmD native example | [iplimit.go at bacaa472...](https://github.com/Sir-MmD/Xray-core/blob/bacaa47268398bbeeddc9c3c88e1ee143101da21/common/speedlimit/iplimit.go) and [tests](https://github.com/Sir-MmD/Xray-core/blob/bacaa47268398bbeeddc9c3c88e1ee143101da21/common/speedlimit/iplimit_test.go) | Prior native work; its small test suite is not the full benchmark/race/production coverage of every fork |

The original-V2bX snapshot diagnostics reproduced a wrong decrement key,
future-shifted time comparison and non-atomic count/add admission. Those specific
tests are not exported here; these are scoped prior research findings, not newly
reproduced defects in current versions. V2bX is a server backend/core integration,
distinct from the V2Box client application.

Marzban external account-disabling examples and selected Hiddify paths were also
surveyed. Fetch/coverage limits prevent a stronger comparative claim, so they
are not ranked as complete alternatives here. No first-invention claim is made.

## Contribution workflow

The [current 3x-ui contribution guide](https://github.com/MHSanaei/3x-ui/blob/main/CONTRIBUTING.md),
read on 2026-10-16, requests focused main-branch PRs and relevant build/test checks.
Future implementation PRs should follow its then-current requirements. The
review patches in this package have not passed through upstream CI or design
approval. Posting, creating a repository or opening a PR is a separate step.
