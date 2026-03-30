"""Tests for jafat.runner."""

import json

import pytest

from jafat.runner import parse_ndjson


def _lines(*items):
    """Convert objects to a list of JSON-encoded strings (simulating a stream)."""
    return [json.dumps(item) + "\n" for item in items]


def test_parse_ndjson_yields_objects():
    stream = _lines({"type": "assistant"}, {"type": "result"})
    events = list(parse_ndjson(stream))
    assert len(events) == 2
    assert events[0]["type"] == "assistant"
    assert events[1]["type"] == "result"


def test_parse_ndjson_skips_blank_lines():
    stream = ["\n", "  \n", json.dumps({"type": "system"}) + "\n"]
    events = list(parse_ndjson(stream))
    assert len(events) == 1


def test_parse_ndjson_skips_bad_json():
    stream = ["not-json\n", json.dumps({"type": "ok"}) + "\n"]
    events = list(parse_ndjson(stream))
    assert len(events) == 1
    assert events[0]["type"] == "ok"
