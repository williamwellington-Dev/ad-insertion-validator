"""Phase 1-3: VAST parsing, wrapper resolution and validation.

Your code goes here. See BRIEF.md for each task and its expected output.
"""
import xml.etree.ElementTree as ET
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
VAST_NS = {"v": "http://www.iab.com/VAST"}


def parse_duration(text):
    """'00:00:30.000' -> 30.0 seconds. Return None if the format is invalid."""
    parts = text.split(":")
    if len(parts) != 3:
        return None
    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
    except ValueError:
        return None
    return hours * 3600 + minutes * 60 + seconds


def parse_inline(filename):
    root = ET.parse(DATA / filename).getroot()
    title = root.find("v:Ad/v:InLine/v:AdTitle", VAST_NS).text.strip()
    duration = parse_duration(root.find(".//v:Duration", VAST_NS).text.strip())

    impressions = []
    for imp in root.findall(".//v:Impression", VAST_NS):
        impressions.append(imp.text.strip())

    tracking = []
    for t in root.findall(".//v:Tracking", VAST_NS):
        tracking.append((t.get("event"), t.text.strip()))

    media = []
    for m in root.findall(".//v:MediaFile", VAST_NS):
        media.append((m.get("width"), m.get("height"), m.text.strip()))

    return {
        "title": title,
        "duration": duration,
        "impressions": impressions,
        "tracking": tracking,
        "media": media,
    }

def resolve(filename, max_depth=5):
    """Task 2: follow Wrapper -> VASTAdTagURI until an InLine, a no-fill, a loop or max depth."""
    raise NotImplementedError


def validate(filename):
    """Task 3: return a list of issue strings (empty list = clean)."""
    raise NotImplementedError


if __name__ == "__main__":
    print(parse_inline("vast_inline.xml"))