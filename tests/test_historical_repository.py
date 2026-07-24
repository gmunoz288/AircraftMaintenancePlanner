"""Tests for the historical repository layer."""
import pytest
from app.repositories.historical_repository import find_by_task_key, get_all_records


class TestGetAllRecords:
    def test_returns_non_empty_list(self):
        records = get_all_records()
        assert len(records) > 0

    def test_records_have_required_fields(self):
        records = get_all_records()
        for rec in records:
            assert rec.task_key
            assert rec.avg_manhours > 0
            assert 0.0 <= rec.risk_factor <= 1.0
            assert rec.occurrences > 0


class TestFindByTaskKey:
    def test_exact_match_engine_inspect(self):
        rec = find_by_task_key("inspect_engine")
        assert rec is not None
        assert rec.task_key == "inspect_engine"
        assert rec.avg_manhours > 0

    def test_exact_match_landing_gear(self):
        rec = find_by_task_key("inspect_landing_gear")
        assert rec is not None
        assert "landing" in rec.task_key or rec.ata_chapter == "32"

    def test_exact_match_avionics(self):
        rec = find_by_task_key("replace_avionics")
        assert rec is not None

    def test_generic_fallback_for_unknown_key(self):
        rec = find_by_task_key("inspect_unknown_system_xyz")
        # Should fall back to inspect_general or check_general
        assert rec is not None

    def test_empty_key_returns_fallback(self):
        rec = find_by_task_key("")
        assert rec is not None

    def test_general_action_fallback(self):
        rec = find_by_task_key("clean_engine")
        assert rec is not None

    def test_returns_none_gracefully(self):
        # An extremely unusual key should still return something (fallback)
        rec = find_by_task_key("zzzz_qqqq")
        # May be None if no fallback applies, or a fallback record — either is acceptable
        # The function must not raise
        assert rec is None or hasattr(rec, "task_key")

    def test_resources_not_empty(self):
        rec = find_by_task_key("inspect_engine")
        assert len(rec.required_skills) > 0
        assert len(rec.required_tools) > 0
