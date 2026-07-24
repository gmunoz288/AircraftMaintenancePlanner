from typing import List, Optional
from pydantic import BaseModel, Field


class Resources(BaseModel):
    skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    materials: List[str] = Field(default_factory=list)


class Task(BaseModel):
    id: str
    description: str
    task_key: str = ""
    ata_chapter: str = ""
    manhours: float = 2.0
    priority: str = "MEDIUM"
    dependencies: List[str] = Field(default_factory=list)
    resources: Resources = Field(default_factory=Resources)
    risk_score: float = 0.0
    # Historical enrichment fields
    historical_avg_manhours: Optional[float] = None
    historical_risk_factor: Optional[float] = None
    historical_occurrences: int = 0


class HistoricalRecord(BaseModel):
    task_key: str
    description: str
    ata_chapter: str = ""
    aircraft_type: str = ""
    avg_manhours: float
    min_manhours: float
    max_manhours: float
    risk_factor: float = 1.0
    required_skills: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    required_materials: List[str] = Field(default_factory=list)
    incident_rate: float = 0.0
    occurrences: int = 1
