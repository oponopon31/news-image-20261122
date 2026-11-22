# The World in One Day — Sunday 22 November 2026

One image summing up the world's news of Sunday 22 November 2026.

35 stories, all dated Sunday 22 November 2026: 3 illustrated leads,
10 featured stories and 22 more in the ALSO list, with a numbered
blocky world map, a DATE CHECK box listing the big 20–21 November
stories left out on purpose, and every story carrying its source.

Fresh rebuild, written from scratch in this session from the fixed
render (layout/map reference) and the story transcription — the
previous `main.py` was not read or copied. Pure Python standard
library only (hand-drawn 5×7 bitmap font, procedural scenes and map,
hand-rolled PNG encoder), no network, no randomness.

Run `python3 main.py` to render `entry.png` (1024×1024, 44,250 bytes,
byte-identical on every run — verified two consecutive runs produce
the same SHA-256).

Notes:
- Story #5's feature body is condensed to fit its three-line slot
  ("186 Shahed drones, 161 downed; strikes at 18 sites."); all facts
  and the source are kept.
- Stories #18 and #22 carry source "(AP)": the transcription flagged
  a second source token in the render as unreadable, so nothing was
  invented for it.
