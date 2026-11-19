"""Phase 1-3: VAST parsing, wrapper resolution and validation.

Your code goes here. See BRIEF.md for each task and its expected output.
"""
import xml.etree.ElementTree as ET
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
VAST_NS = {"v": "http://www.iab.com/VAST"}


def parse_duration(text):
    """'00:00:30.000' -> 30.0 seconds. Return None if the format is invalid."""
    raise NotImplementedError


def parse_inline(filename):
    """Task 1: return a dict summarizing an InLine VAST ad."""
    raise NotImplementedError


def resolve(filename, max_depth=5):
    """Task 2: follow Wrapper -> VASTAdTagURI until an InLine, a no-fill, a loop or max depth."""
    raise NotImplementedError


def validate(filename):
    """Task 3: return a list of issue strings (empty list = clean)."""
    raise NotImplementedError


if __name__ == "__main__":
    root = ET.parse(DATA / "vast_inline.xml").getroot()
    print(root.tag)
    title = root.find("v:Ad/v:InLine/v:AdTitle", VAST_NS)
    print(title.text)
    duration = root.find(".//v:Duration", VAST_NS)
    print(duration.text.strip())
    for imp in root.findall(".//v:Impression", VAST_NS):
        print(imp.text.strip())
