# Ad Insertion Validator

A Python tool that checks a video ad pipeline end to end:

- **VAST**: parses ad responses, follows wrapper chains, and flags spec problems
- **VMAP**: reads the ad-break schedule for a piece of content
- **SCTE-35**: decodes ad-break cue markers from an HLS stream manifest
- **Reconciliation**: compares planned ad breaks with what the stream actually delivered

## Run it

```bash
pip install -r requirements.txt
python src/vast.py
```

## What I learned

_(Write this section yourself once it's built: what VAST, VMAP and SCTE-35 do, how CSAI and SSAI differ, and how this compares to radio log reconciliation.)_

## Note on authorship

The sample data in `data/` and the task brief were AI-generated. All code in `src/` is my own.
