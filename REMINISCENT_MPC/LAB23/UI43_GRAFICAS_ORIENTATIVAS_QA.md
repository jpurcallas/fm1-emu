# UI43 — RESONANCE + GRANULAR as parametric previews

**Base UI42** PR #48 head \`7516790b1a51b74a6fb8b0a9fb2ed6052e2089a7\`.

The author's clarification (14-Nov-2026) is explicit: like ADSR, **RADAR and DNA are visual descriptions of the user's chosen settings**, NOT audio meters, oscilloscopes, musical animation or physical simulations. They move/settle when the real knobs, touch widgets or Data Wheel change values; this is *not* audio-driven animation.

## Implemented in active TUI.json
- RESONANCE (tab page 5): four transparent, native 16-frame FilmStrip knobs reading the existing **Parameter 38, 39, 40, 41** (BODY/DECAY/EXCITE/MIX).
- GRANULAR (tab page 8): four transparent, native 16-frame FilmStrip knobs reading **Parameter 44, 45, 46, 47** (SIZE/DENSITY/POSITION/MIX).
- Each screen's original static baked-on graph is cleaned **only inside the original chart area**, then the four independently parameter-controlled transparent layers are composited by MPC's existing skin renderer.
- Existing touch controls, Q-Link banks, geometry outside the two charts, 11 tabs, UI42 bars and audio remain **unchanged**.
- New graphics reference the correct orange/gold/teal approved LAB10 colour family, the original radar ring and two-strand DNA composition. The art's main photo comes from the original LAB10 HTML bundled reference; do not replace with a new photo.

**No new host parameters**. Reuse the Q-Link/host notification fix already verified in UI41. No custom DRM, raw touch input, reflection of PCM audio, or SDK fork.

## Source and assets
- \`tools/ui43_generate_representative_graphics.py\`: reproduces two new static page backgrounds and eight RGBA 16-frame strips. Requires only Python/Pillow, original **private** LAB10 background files \`lab10_mpc_05.png\` and \`lab10_mpc_08.png\`, original \`REminiSCENT_UI_LAB_10_INTEGRATION.html\`, and the pre-UI43 TUI.
- Pixel assets **stay private**, like all earlier skin PNGs, and must be included by the final assembler. No original images overwritten.
- \`tests/test_ui43_representative_graphics.py\` reconstructs the pre-UI43 TUI from active UI43, regenerates the exact active TUI, and checks 8 bindings, 128 frames, differing extremes, alpha, dimensions, 11 tabs, and preservation of other components. CI uses synthetic art; this proves structure, not final pixel-quality or physical MPC rendering.
- Local original-art preview and asset checks were performed with approved source images; see PR notes.

## Verification gates not yet crossed
- Compare composed charts on the actual MPC display; ensure 4 transparent filmstrips are composited by the firmware in correct paint order, do not steal focus, and refresh when host parameters change.
- Include all 10 new private PNGs when assembling final skin. UI42 already has its own 24 private assets. This branch must NOT change BLEND or provide a replacement for the approved blue eclipse: that is a different chat's independent UI44 work.
- Final validation and installer only when all features integrated. **NO MERGE / NO INTERMEDIATE INSTALLER.**
