"""Tests for the enrichment service."""
import pytest
from app.services.enrichment_service import enrich_tasks


def _base_task(task_key="inspect_engine", manhours=3.0):
    return {
        "id": "T1",
        "description": "Inspect engine fan blades",
        "task_key": task_key,
        "ata_chapter": "",
        "manhours": manhours,
        "priority": "MEDIUM",
        "dependencies": [],
        "resources": {"skills": ["Technician"], "tools": [], "materials": []},
    }


class TestEnrichTasks:
    def test_enriched_task_has_historical_fields(self):
        tasks = enrich_tasks([_base_task()])
        task = tasks[0]
        assert "historical_avg_manhours" in task
        assert "historical_risk_factor" in task
        assert "historical_occurrences" in task

    def test_manhours_blended_with_historical(self):
        raw = _base_task(manhours=3.0)
        tasks = enrich_tasks([raw])
        # Blended = 0.6 * historical + 0.4 * heuristic
        # Blended should differ from raw heuristic
        assert tasks[0]["manhours"] != 3.0 or tasks[0]["historical_avg_manhours"] == 3.0

    def test_resources_upgraded_from_historical(self):
        raw = _base_task(task_key="inspect_engine")
        tasks = enrich_tasks([raw])
        skills = tasks[0]["resources"]["skills"]
        assert "B1" in skills or "Engine Specialist" in skills

    def test_unknown_task_key_still_has_fields(self):
        raw = _base_task(task_key="")
        tasks = enrich_tasks([raw])
        assert tasks[0]["historical_avg_manhours"] is None

    def test_ata_chapter_populated_from_historical(self):
        raw = _base_task(task_key="inspect_engine")
        raw["ata_chapter"] = ""
        tasks = enrich_tasks([raw])
        assert tasks[0]["ata_chapter"] == "72"

    def test_returns_same_number_of_tasks(self):
        raw_tasks = [_base_task("inspect_engine"), _base_task("replace_avionics")]
        enriched = enrich_tasks(raw_tasks)
        assert len(enriched) == 2

    def test_original_list_not_mutated(self):
        raw = _base_task()
        original_manhours = raw["manhours"]
        enrich_tasks([raw])
        # raw should be unchanged since enrich_tasks does dict(task) copy
        assert raw["manhours"] == original_manhours
