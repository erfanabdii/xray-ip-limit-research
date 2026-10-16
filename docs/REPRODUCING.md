# Reproduction boundaries

There are three distinct checks: recalculating saved measurements, applying and
testing selected patches against pinned source, and rerunning the entire original
network/benchmark experiment. This package supports the first two. It omits the
private host-specific benchmark wrapper and production guards, so it is not a
turnkey replay of the third.

## Offline calculation

From this package directory, with Python 3:

```sh
python scripts/summarize.py
```

The script reads only the exported JSON files. It starts no proxy, opens no
socket and requires no account or endpoint. Its means, ranges and ratios should
match [BENCHMARKS.md](BENCHMARKS.md), subject to displayed rounding.

The nine-test coordination model is also completely offline:

```sh
python scripts/coordination_model.py
```

It includes counterexamples to expiry-only reclamation and uncoordinated leaders.
A passing test demonstrates the modeled counterexample, not a deployed solution.
Only its output harness and synthetic node labels were adapted for this package.

## Patch bases and separation

| Patch | Repository and pinned base | Scope |
| --- | --- | --- |
| `xray-native.patch` | XTLS/Xray-core, `701af60772cda123492f86e383e1fdba066614a9` | Gate, OnlineMap reservation, dispatcher hooks, tests and microbenchmarks |
| `panel-integration.patch` | MHSanaei/3x-ui, `608ef4e4010bf83e2e78328e08f77efc051ad4d7` | Policy publisher, selected-account legacy suppression and diagnostic tests |
| `xray-lua-research.patch` | Same Xray base | Official-Lua diagnostics, pool tests and loopback-only fixture controller |

Native and Lua patches are alternatives for inspecting the two paths. The Lua
controller/tests do not require the native feature. The panel patch contains no
frontend changes and does not make IP Log Clear/Refresh into session controls.

Use fresh disposable development checkouts. Checkout the exact base before
applying the appropriate patch. For example, with the native patch copied into
the parent directory of a fresh Xray checkout:

```sh
git switch -c codex/ip-admission-review 701af60772cda123492f86e383e1fdba066614a9
git apply --check ../xray-native.patch
git apply ../xray-native.patch
go test -count=1 ./common/nativeiplimit ./app/stats
```

Optional race checking, with the toolchain/C compiler required by Go's race
detector:

```sh
go test -race -count=1 ./common/nativeiplimit ./app/stats
```

For the Lua patch in a separate checkout of the same base:

```sh
git apply --check ../xray-lua-research.patch
git apply ../xray-lua-research.patch
go test -count=1 ./app/router -run '^TestDiagnosticLua'
go test -count=1 ./common/lua -run '^TestValidationPass5'
go test -count=1 ./cmd/validation5-controller
```

For the panel patch in a fresh checkout of the pinned panel base:

```sh
git apply --check ../panel-integration.patch
git apply ../panel-integration.patch
go test -count=1 ./internal/web/job -run 'Test(PublishNativeIPLimit|WriteNativeIPLimit|ProcessObservedManagedNative|NativePolicyWriteFailure|ValidationLegacyRemote|ValidationPanelScope)'
```

The panel package's test helpers use temporary fixture databases. Do not point a
development checkout at a production database or inherit native-limiter opt-in
environment settings from a running service. Follow the dependencies, build and
test requirements of each pinned repository; this package does not ship modules,
toolchains, binaries or runtime geo assets.

## How to read a passing diagnostic test

`TestValidationMissingInitialPolicyHasNoNativeLimit` passes when it reproduces
the open cold-start gap. The panel/core trailing-comma tests pass when they
demonstrate their conflicting behavior. The Lua separate-VM test passes when it
demonstrates that a naive Lua global cannot implement the shared cap. Such results
are evidence for the report, not successful remediation of the flaws.

Unit tests are not the full historical 16-account traffic fixture or a WAN test.
Before a future upstream PR, rebase the chosen design, fix the documented gaps,
add failing contract tests for the desired behavior and run the upstream project's
required checks. The current 3x-ui contribution guide requests focused changes
against main and the relevant full build/test checks; this package is a design
review candidate, not a substitute for that CI. See [sources](SOURCES.md).

The Lua example files show the decision-message format with synthetic fixture
identities and loopback addresses. They are fragments, not a complete inbound,
resolver, routing or deployment configuration. The controller deliberately accepts
only fixture identities/documentation IPs and loopback endpoints.
