"""Disclosure loader — Claude-owned helper passes now; IO bodies are Codex's."""

from __future__ import annotations

from datetime import date

from pipeline.disclosure_loader import count_kr_chars, fetch_dart_mdna, load_ir_decks


def test_count_kr_chars_counts_only_hangul():
    assert count_kr_chars("HBM 수요 강세 2026") == 4   # 수,요,강,세
    assert count_kr_chars("ascii only 123") == 0


def test_load_ir_decks_returns_documents(tmp_path):
    docs = load_ir_decks(
        [{"filename": "missing.pdf", "event_label": "2024Q1",
          "period_label": "2024Q1", "doc_date": "2024-04-25"}],
        tmp_path,
    )
    # A missing deck is warned + dropped, not crashed (no silent total failure).
    assert isinstance(docs, list)


def test_fetch_dart_mdna_nonempty():
    doc = fetch_dart_mdna("20240814003052", "2024Q2", date(2024, 8, 14))
    assert doc.source == "dart_mdna"
    assert doc.char_count_kr > 0
