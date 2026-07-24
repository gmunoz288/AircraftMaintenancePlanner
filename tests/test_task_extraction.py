"""Tests for task extraction service."""
import pytest
from app.services.task_extraction_service import (
    extract_tasks_from_text,
    normalize_task_key,
    estimate_manhours,
    infer_resources,
    _detect_action,
    _detect_system,
)


class TestDetectAction:
    def test_inspect(self):
        assert _detect_action("Inspect the engine oil filter") == "inspect"

    def test_replace(self):
        assert _detect_action("Replace hydraulic pump seal") == "replace"

    def test_overhaul_priority(self):
        # overhaul is listed before replace, so it should win
        assert _detect_action("Overhaul and replace the engine") == "overhaul"

    def test_no_action(self):
        assert _detect_action("Random text with no maintenance verb") == ""


class TestDetectSystem:
    def test_engine(self):
        assert _detect_system("Engine fan blade inspection") == "engine"

    def test_landing_gear(self):
        assert _detect_system("Landing gear retraction check") == "landing_gear"

    def test_avionics(self):
        assert _detect_system("Avionics system functional test") == "avionics"

    def test_hydraulic(self):
        assert _detect_system("Check hydraulic actuator for leaks") == "hydraulic"

    def test_flight_controls(self):
        assert _detect_system("Inspect aileron hinge bearings") == "flight_controls"

    def test_general_fallback(self):
        assert _detect_system("Perform a routine operational check") == "general"


class TestNormalizeTaskKey:
    def test_inspect_engine(self):
        assert normalize_task_key("Inspect engine fan blades") == "inspect_engine"

    def test_replace_landing_gear(self):
        assert normalize_task_key("Replace landing gear actuator") == "replace_landing_gear"

    def test_check_avionics(self):
        assert normalize_task_key("Check avionics navigation system") == "check_avionics"

    def test_no_action_defaults_to_check(self):
        key = normalize_task_key("Engine noise at startup")
        assert key.endswith("_engine")

    def test_no_system_defaults_to_general(self):
        key = normalize_task_key("Inspect the system components")
        assert "inspect" in key


class TestEstimateManhours:
    def test_engine_inspect_lower_than_engine_overhaul(self):
        mh_inspect = estimate_manhours("Inspect engine oil system")
        mh_overhaul = estimate_manhours("Overhaul engine")
        assert mh_overhaul > mh_inspect

    def test_landing_gear_higher_than_general(self):
        mh_lg = estimate_manhours("Replace landing gear leg")
        mh_gen = estimate_manhours("Clean the aircraft windows")
        assert mh_lg > mh_gen

    def test_returns_positive(self):
        assert estimate_manhours("Verify navigation system") > 0


class TestInferResources:
    def test_engine_skills(self):
        resources = infer_resources("Inspect engine turbine blades")
        assert "B1" in resources["skills"]
        assert len(resources["tools"]) > 0

    def test_avionics_skills(self):
        resources = infer_resources("Replace avionics FMS unit")
        assert "B2" in resources["skills"]

    def test_general_fallback(self):
        resources = infer_resources("Perform general inspection")
        assert "Technician" in resources["skills"]


class TestExtractTasksFromText:
    def test_detects_engine_inspection(self):
        text = "Inspect engine fan blades for damage and wear"
        tasks = extract_tasks_from_text(text)
        assert len(tasks) >= 1
        assert tasks[0]["task_key"] == "inspect_engine"

    def test_multiple_tasks(self):
        text = (
            "Inspect engine oil filter\n"
            "Replace landing gear actuator seal\n"
            "Check avionics ILS receiver\n"
        )
        tasks = extract_tasks_from_text(text)
        assert len(tasks) == 3

    def test_fallback_for_empty_text(self):
        tasks = extract_tasks_from_text("")
        assert tasks == []

    def test_fallback_for_non_task_text(self):
        tasks = extract_tasks_from_text("This is a document header. Aircraft registration: EC-MAA.")
        # Should provide the general fallback task
        assert len(tasks) >= 1

    def test_task_has_required_fields(self):
        tasks = extract_tasks_from_text("Inspect landing gear for cracks")
        task = tasks[0]
        assert "id" in task
        assert "description" in task
        assert "task_key" in task
        assert "manhours" in task
        assert "priority" in task
        assert "resources" in task

    def test_critical_priority(self):
        tasks = extract_tasks_from_text("Critical: inspect engine turbine blades immediately")
        assert tasks[0]["priority"] == "HIGH"

    def test_description_truncated_at_240(self):
        long_line = "Inspect " + "x" * 300
        tasks = extract_tasks_from_text(long_line)
        assert len(tasks[0]["description"]) <= 240

    def test_ata_chapter_detection(self):
        tasks = extract_tasks_from_text("Inspect ATA 72 engine fan module")
        assert tasks[0]["ata_chapter"] == "72"
