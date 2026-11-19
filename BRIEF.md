# Ad Insertion Validator: Build Brief

**Goal:** a GitHub project you wrote yourself that lets you honestly list VAST, VMAP, SCTE-35 and CSAI/SSAI on your resume, and talk through them in an NBCU interview.

**Rules for yourself:** you write all the code in `src/`. Ask me for hints or a review, not answers. Commit after each task. Don't move on until your output matches the "Check" for that task.

**Setup**
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

---

## The scenario

You're the integration analyst for a 40-minute streamed show. The ad server sends VAST responses, a VMAP schedules the breaks, and the stream carries SCTE-35 cues where breaks actually happened. Ad Ops has a spreadsheet of planned breaks. Your job is to prove what's right and find what's broken.

| File | What it is |
|---|---|
| `vast_inline.xml` | A clean 30-second ad (InLine) |
| `vast_wrapper_1.xml` → `vast_wrapper_2.xml` → `vast_inline.xml` | A wrapper chain: SSP → DSP → the real ad |
| `vast_broken.xml` | An ad with spec problems |
| `vast_nofill.xml` | No ad available (no-fill), which is normal, not an error |
| `vast_loop_a.xml` ↔ `vast_loop_b.xml` | Two wrappers pointing at each other forever |
| `vmap.xml` | Ad-break schedule: pre-roll, three mid-rolls, post-roll |
| `stream.m3u8` | HLS manifest (6-second segments) with SCTE-35 cue markers |
| `planned_breaks.csv` | What Ad Ops expected to air |

---

## Phase 1: Read an ad (VAST InLine)

**Concept.** VAST is the XML an ad server returns to a player. An `<InLine>` ad contains everything: title, `<Impression>` URL(s) (called when the ad starts showing), `<Linear><Duration>`, `<TrackingEvents>` (start, firstQuartile, midpoint, thirdQuartile, complete) and `<MediaFiles>` (the actual video renditions).

**Task 1.** Write `parse_duration()` and `parse_inline()` in `src/vast.py`. Return: title, duration in seconds, impression URLs, tracking events as (event, url) pairs, and media files with width/height/url.

**Hint.** VAST 4 uses a namespace, so `root.find("Ad")` returns `None`. Use `root.find("v:Ad", VAST_NS)`. URLs are inside CDATA, but `.text` handles that. Call `.strip()` on it.

**Check** (on `vast_inline.xml`):
- title: `Northshore Coffee - Morning Roast 30s`
- duration: `30.0`
- 1 impression, 5 tracking events, 2 media files (1920x1080 and 1280x720)

---

## Phase 2: Follow the wrapper chain

**Concept.** Programmatic ads pass through middlemen. Each middleman returns a `<Wrapper>` with its own tracking and a `<VASTAdTagURI>` pointing to the next response. The player must follow the chain to the InLine ad and fire **every** layer's impressions and tracking. That's why wrapper chains matter for measurement and reconciliation. In this project the URIs are local file names instead of real HTTP calls.

**Task 2.** Write `resolve()`. Return a status (`OK`, `NO_FILL`, `LOOP`, `TOO_DEEP`), the chain of files visited, the wrapper depth, and **all** impressions and tracking events merged from every layer.

**Hint.** Keep a `seen` set of files you've visited. If the next URI is already in it, that's a loop. A VAST with no `<Ad>` element is a no-fill.

**Check:**
| Input | Status | Chain / depth | Merged counts |
|---|---|---|---|
| `vast_wrapper_1.xml` | OK | wrapper_1 → wrapper_2 → inline, depth 2 | 3 impressions, 8 tracking events, 2 media files |
| `vast_nofill.xml` | NO_FILL | — | — |
| `vast_loop_a.xml` | LOOP | loop_a → loop_b → loop_a | — |

---

## Phase 3: Validate against the spec

**Task 3.** Write `validate()` and run it on `vast_broken.xml`. Rules:
1. An InLine ad must have `AdSystem`, `AdTitle` and at least one `Impression`
2. `Duration` must be `HH:MM:SS` or `HH:MM:SS.mmm`
3. A Linear creative must have at least one `MediaFile`
4. Tracking URLs must be `https://`

**Check:** exactly 4 issues:
- missing Impression
- bad Duration (`15 seconds`)
- no MediaFile
- non-https tracking URL on the `start` event

**Interview angle:** this is the "validation checklists / acceptance criteria / certification" part of the job description.

---

## Phase 4: Read the break schedule (VMAP)

**Concept.** VMAP tells the player *where* breaks go and which VAST to request for each. `timeOffset` is `start`, `end`, or a timestamp.

**Task 4.** Write `parse_vmap()`. For each break: break_id, timeOffset, offset in seconds (keep `start`/`end` as-is), ad tag. Then call your `resolve()` on each ad tag.

**Hint.** Same namespace issue, different namespace. It's in `VMAP_NS`.

**Check:**
| break_id | offset | ad tag | resolve status |
|---|---|---|---|
| preroll | start | vast_inline.xml | OK |
| midroll-1 | 600.0 | vast_wrapper_1.xml | OK |
| midroll-2 | 1200.0 | vast_broken.xml | OK (but fails validation) |
| midroll-3 | 1800.0 | vast_nofill.xml | NO_FILL |
| postroll | end | vast_loop_a.xml | LOOP |

---

## Phase 5: Decode SCTE-35 from the stream

**Concept.** In live and linear streams, ad breaks are marked with SCTE-35 cues: "break starts at this PTS, lasts X seconds." They're the TV equivalent of the log triggers that fire spots in radio automation. In HLS they show up as tags in the manifest. Here, `#EXT-OATCLS-SCTE35:` carries the base64 cue, `#EXT-X-CUE-OUT` opens the break and `#EXT-X-CUE-IN` closes it. In **SSAI**, the stitcher reads these cues and swaps ads into those segments on the server side.

**Task 5.** Write `extract_breaks()`. Walk the manifest line by line, keeping a running clock (add each `#EXTINF` duration). When you hit a cue, decode it. When you hit `CUE-IN`, close the break. Return: splice_event_id, pts_time, break_duration, playlist start and playlist end.

**Hint.**
```python
cue = Cue(b64_string)
cue.decode()
cue.command.splice_event_id, cue.command.pts_time, cue.command.break_duration
```
Try `cue.show()` once to see everything inside a cue.

**Check:** 4 breaks, total stream length 2400.0 s
| event | pts | duration | playlist start → end |
|---|---|---|---|
| 101 | 600.0 | 60.0 | 600 → 660 |
| 102 | 1200.0 | 90.0 | 1200 → 1290 |
| 103 | 1800.0 | 30.0 | 1800 → 1830 |
| 104 | 2100.0 | 30.0 | 2100 → 2130 |

**Interview angle:** in real streams, PTS doesn't equal playlist time (it starts at an arbitrary value and wraps around about every 26.5 hours). Here they match to keep things simple. Be ready to say so.

---

## Phase 6: Reconcile planned vs delivered

**Task 6.** Write `reconcile()`. Match each planned break to a delivered break whose start is within ±2 s. Label each one:
- `MATCHED`: start and duration both within tolerance
- `DURATION_MISMATCH`: start matches, duration doesn't
- `MISSING`: planned, never delivered
- `UNPLANNED`: delivered, never planned

**Check:**
| break | result |
|---|---|
| midroll-1 | MATCHED |
| midroll-2 | MATCHED |
| midroll-2b | MISSING |
| midroll-3 | DURATION_MISMATCH (planned 60, delivered 30) |
| event 104 @ 2100 s | UNPLANNED |

This is your Radio Airplay Reconciler idea applied to ad breaks. That's the story to tell in the interview.

---

## Phase 7: Ship it

1. A `main.py` (or a Streamlit page) that runs everything and prints or shows one report
2. Write the "What I learned" section of the README in your own words
3. Push it to GitHub as a public repo: `ad-insertion-validator`

**Optional stretch (CSAI, seen with your own eyes):** open Google's IMA SDK sample video player in a browser with DevTools → Network open, play a sample pre-roll, and watch the impression and quartile tracking calls fire. One paragraph about it in the README.

---

## When it's done: resume lines

- **Skills:** Ad Tech: VAST/VMAP parsing, SCTE-35 cue decoding, CSAI/SSAI workflows (project-based)
- **Project:** Ad Insertion Validator (Python, XML, threefive): Parses VAST/VMAP responses and follows wrapper chains, validates ads against IAB spec rules, decodes SCTE-35 markers from HLS manifests, and reconciles planned versus delivered ad breaks.
