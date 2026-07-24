"""Tests for the scheduler service."""
import pytest
from app.services.scheduler_service import build_daily_plan, build_gantt


def _task(id_="T1", description="Inspect engine", manhours=8.0, risk_score=3.0, task_key="inspect_engine"):
    return {
        "id": id_,
        "description": description,
        "task_key": task_key,
        "ata_chapter": "72",
        "manhours": manhours,
        "risk_score": risk_score,
        "priority": "MEDIUM",
        "resources": {
            "skills": ["B1"],
            "tools": ["Borescope"],
            "materials": ["Seals"],
        },
        "historical_avg_manhours": manhours,
        "historical_occurrences": 10,
    }


class TestBuildDailyPlan:
    def test_returns_dict(self):
        plan = build_daily_plan([_task()])
        assert isinstance(plan, dict)

    def test_single_task_assigned_to_day1(self):
        plan = build_daily_plan([_task(manhours=4.0)])
        assert "Day 1" in plan
        assert len(plan["Day 1"]) == 1

    def test_task_splits_across_days(self):
        # 48 manhours with capacity 24 h/day => spans 2 days
        plan = build_daily_plan([_task(manhours=48.0)], team_capacity_hours=24)
        assert "Day 1" in plan
        assert "Day 2" in plan

    def test_higher_risk_scheduled_first(self):
        high_risk = _task(id_="T1", risk_score=8.0, manhours=4.0)
        low_risk = _task(id_="T2", risk_score=2.0, manhours=4.0)
        plan = build_daily_plan([low_risk, high_risk], team_capacity_hours=24)
        first_task_id = plan["Day 1"][0]["task_id"]
        assert first_task_id == "T1"

    def test_plan_items_have_required_fields(self):
        plan = build_daily_plan([_task()])
        item = list(plan.values())[0][0]
        assert "task_id" in item
        assert "description" in item
        assert "allocated_hours" in item
        assert "risk_score" in item
        assert "skills" in item

    def test_total_hours_preserved(self):
        """Total allocated hours should equal total task manhours."""
        tasks = [_task("T1", manhours=10.0), _task("T2", manhours=6.0)]
        plan = build_daily_plan(tasks, team_capacity_hours=24)
        total = sum(
            item["allocated_hours"]
            for items in plan.values()
            for item in items
        )
        assert abs(total - 16.0) < 0.01

    def test_empty_task_list(self):
        plan = build_daily_plan([])
        assert plan == {}


class TestBuildGantt:
    def test_returns_list(self):
        plan = build_daily_plan([_task()])
        gantt = build_gantt(plan)
        assert isinstance(gantt, list)

    def test_gantt_entry_fields(self):
        plan = build_daily_plan([_task()])
        gantt = build_gantt(plan)
        entry = gantt[0]
        assert "id" in entry
        assert "name" in entry
        assert "start_day" in entry
        assert "end_day" in entry
        assert "hours" in entry
        assert "risk_score" in entry

    def test_end_day_greater_than_start_day(self):
        plan = build_daily_plan([_task(manhours=8.0)])
        gantt = build_gantt(plan)
        for entry in gantt:
            assert entry["end_day"] >= entry["start_day"] + 1

    def test_name_truncated_at_80(self):
        long_desc = "Inspect " + "x" * 200
        task = _task(description=long_desc[:240])
        plan = build_daily_plan([task])
        gantt = build_gantt(plan)
        assert len(gantt[0]["name"]) <= 80

    def test_empty_plan_returns_empty_gantt(self):
        gantt = build_gantt({})
        assert gantt == []
