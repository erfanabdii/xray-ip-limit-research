# Draft comment for 3x-ui issue #6573

Local draft only. It has not been posted. Target:
https://github.com/MHSanaei/3x-ui/issues/6573

---

Thanks for documenting the CDN/source-IP enforcement mismatch. I investigated
an account-scoped alternative and prepared research patches plus anonymized
measurements for design feedback.

The native prototype reserves a distinct IP atomically in the authenticated
account's existing online map before routing, and releases its reference when
the owning flow context ends. The panel prototype reads the existing IP cap for
selected accounts. It is single-node and not ready for deployment: initial-policy
readiness, parser consistency, core-update ownership and panel session controls
remain open.

I also tested official Lua routing with a local Go controller and StatsService
snapshots. It shared a cap across two cores on one host, but conservative restart
recovery blocks new scoped admissions until existing scoped flows are gone.
This is not a distributed production implementation.

For an equal allowed workload of 8 accounts/16 held flows, three samples per
mode averaged 97.780 ms CPU for stock, 103.117 ms for native and 159.284 ms for
Lua plus controller. Those totals include the server/controller, exclude
startup/refusal/cleanup and were measured under a CPU quota; they are not a
general overhead guarantee. The routing-rule bridge in this issue was not
benchmarked against them.

Before proposing a mergeable patch, would you prefer a routing-action integration
in the panel, or coordination with Xray maintainers on a small generic
admission/lifecycle interface? What panel contract should govern ownership,
session visibility/disconnect and behavior during updates or unavailable nodes?

The local review package contains pinned-base patches, recorded metrics,
limitations and prior-work attribution. Research package:
https://github.com/erfanabdii/xray-ip-limit-research

This file remains an unposted draft; publication of the research package
does not post this comment or open an upstream PR.
