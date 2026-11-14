# UI41 — Q-Link refresh common to every tab + exact approved radar/ADN maths

Baseline: UI40 PR #46 at commit \`80759018bed6bff638e7cdc82bc63ce8b6a1a8ee\` (UI39 PR #45 already included). Work in isolated branch; no master merge.

## Functional bug repaired (C++)
When \`parameterChanged(index==qLinkTarget(slot))\` was invoked by direct touchscreen/Data Wheel edit, REminiSCENT called \`set(qLinkProxy_[slot], value)\` **without** the \`notifyHostParameterChanged()\` required by pinned official SDK. That updates an atomic but does not refresh host-rendered pointer and value. UI41 emits the notification only if the proxy changes. Reverse path (Q-Link -> real parameter) was already using notification and stays intact. The change is limited to this branch.

## Original graphics maths ported without simplification
\`src/ui41_approved_visual_math.hpp\` translates the author's exact \`radarGraphic(V)\` and \`moleculeGraphic(V)\` numeric equations from the approved \`REminiSCENT_UI_LAB_10_INTEGRATION.html\`, including:
- RESONANCE: BODY positions bass and peak; DECAY controls ring opacity and echo persistence; EXCITE moves mid-body and changes peak strength; MIX affects the bass/mid opacity and strength.
- GRANULAR: SIZE changes the two node radii; DENSITY changes node count and angular frequency; POSITION shifts x; MIX changes the sine envelope amplitude. Extra grains tied to density. 11–29 nodes.
- No audio, parameters, 254 WAV, bank indexes or visual artefacts modified.

**Important:** This is geometry/host-sync code ready for the next MPC native graphics renderer stage; it is not yet an on-hardware radar or DNA animation. We have deliberately not replaced exact multivariable behaviour with a 1-parameter filmstrip or unapproved low-resolution 4D lookup. The SDK scripted UI can bind filmstrips to one handle, so the final multivariate compositing strategy must be validated without changing the author's design.

## Verification and limits
- Native pure-C++ test: \`tests/test_ui41_approved_visual_math.cpp\` checks all four independent graphical control dimensions and exact helix symmetry.
- Native host test: \`tests/test_ui41_qlink_host_callback.cpp\` loads the whole plugin as a VST2 \`.so\` and checks \`audioMasterAutomate\` notifications for all four Q-Links on RESONANCE/FILTER/GRANULAR.
- ARM32+64 build covered by existing pull_request workflow when source changes.
- Audio engine untouched. UI40 three-zone bar generator untouched. Q-Link callback fix still requires physical MPC validation.
- **NO MERGE / NO INTERMEDIATE INSTALLER**. Eclipse source visually identified but not integrated; prior ghost/reconstruction test rejected.
