"""Tests for the risk scoring service."""
import pytest
from app.services.risk_service import score_task_risk
from app.config import MAX_RISK_SCORE


def _task(description="inspect engine", manhours=4.0, priority="MEDIUM", hist_rf=None):
    t = {
        "description": description,
        "manhours": manhours,
        "priority": priority,
    }
    if hist_rf is not None:
        t["historical_risk_factor"] = hist_rf
    return t


class TestScoreTaskRisk:
    def test_returns_float(self):
        assert isinstance(score_task_risk(_task()), float)

    def test_minimum_score_is_one(self):
        assert score_task_risk(_task("clean windows", 1.0)) >= 1.0

    def test_maximum_score_capped(self):
        assert score_task_risk(_task("critical overhaul engine", 80.0, "HIGH")) <= MAX_RISK_SCORE

    def test_engine_scores_higher_than_general(self):
        engine_score = score_task_risk(_task("inspect engine fan blades"))
        general_score = score_task_risk(_task("clean aircraft cabin"))
        assert engine_score > general_score

    def test_overhaul_scores_higher_than_inspect(self):
        overhaul = score_task_risk(_task("overhaul engine", 40.0))
        inspect = score_task_risk(_task("inspect engine", 4.0))
        assert overhaul > inspect

    def test_critical_priority_increases_score(self):
        normal = score_task_risk(_task("inspect avionics", priority="MEDIUM"))
        critical = score_task_risk(_task("inspect avionics", priority="HIGH"))
        assert critical > normal

    def test_high_historical_risk_factor_increases_score(self):
        low_rf = score_task_risk(_task("inspect hydraulic", hist_rf=0.2))
        high_rf = score_task_risk(_task("inspect hydraulic", hist_rf=0.9))
        assert high_rf > low_rf

    def test_large_manhours_increases_score(self):
        small = score_task_risk(_task("inspect engine", manhours=2.0))
        large = score_task_risk(_task("inspect engine", manhours=50.0))
        assert large > small

    def test_score_rounded_to_two_decimals(self):
        score = score_task_risk(_task("inspect engine"))
        assert score == round(score, 2)
