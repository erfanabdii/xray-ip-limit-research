# Attribution and included license texts

This research builds on Xray-core, 3x-ui, prior routing-rule integration work and
existing native/core integrations. It does not claim to invent account-scoped
IP limiting. See [sources and discussion history](docs/SOURCES.md).

The patches are intended for review in their respective upstream projects:

| Material | Upstream base | Included upstream license text |
| --- | --- | --- |
| Xray native modifications/tests and Lua research tools | XTLS/Xray-core `701af60772cda123492f86e383e1fdba066614a9` | [Mozilla Public License 2.0](licenses/Xray-core-MPL-2.0.txt) |
| Panel integration and diagnostics | MHSanaei/3x-ui `608ef4e4010bf83e2e78328e08f77efc051ad4d7` | [GNU General Public License 3.0](licenses/3x-ui-GPL-3.0.txt) |

Original upstream notices remain applicable to their material; the upstream
license texts are copied verbatim. This package does not relicense both upstream
codebases under one blanket license or assert a contributor agreement on behalf
of their maintainers. The research documents/data have no additional blanket
license assigned in this preparation stage.

The selected export changes fixture account labels consistently and generalizes
one deployment-specific test comment. Those are publication edits to copies,
not fixes to the prototype's known behavior. Original implementation and evidence
files remain unchanged locally. Compiled artifacts, dependencies, production
settings and private host-specific runners are not distributed here.
