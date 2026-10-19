"""Versioned local research input contract; no real data or generated clinical examples."""
from datetime import datetime, timezone
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, Field, AwareDatetime, ConfigDict, field_validator, model_validator

class Provenance(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source_kind: Literal['unknown','synthetic','real_longitudinal'] = 'unknown'
    participant_key: str = Field(default='', max_length=200)
    source_description: str = Field(default='', max_length=2000)
    consent_confirmed: bool = False
    point_in_time_verified: bool = False

class Snapshot(BaseModel):
    schema_version: int = 3
    exported_at: AwareDatetime
    episodes: list[dict]
    wellness: list[dict] = Field(default_factory=list)
    early_symptoms: list[dict] = Field(default_factory=list)
    attack_sessions: list[dict] = Field(default_factory=list)
    @field_validator('schema_version')
    @classmethod
    def version(cls,v):
        if v!=3: raise ValueError('Only MigraMind export schema 3 is supported')
        return v
    @model_validator(mode='after')
    def unique_ids(self):
        for collection in [self.episodes,self.wellness,self.early_symptoms,self.attack_sessions]:
            ids=[str(row.get('id')) for row in collection]
            if len(ids)!=len(set(ids)):raise ValueError('Snapshot contains duplicate record IDs')
        return self

class Coverage(BaseModel):
    model_config = ConfigDict(extra='forbid')
    start_at: AwareDatetime
    end_at: AwareDatetime
    confirmed_at: AwareDatetime
    complete: bool
    @model_validator(mode='after')
    def order(self):
        if self.end_at<=self.start_at or self.confirmed_at<self.end_at:
            raise ValueError('Coverage must be confirmed after its observation interval ends')
        return self

class Bundle(BaseModel):
    model_config = ConfigDict(extra='forbid')
    research_schema_version: Literal[1] = 1
    provenance: Provenance = Field(default_factory=Provenance)
    snapshots: list[Snapshot] = Field(default_factory=list)
    coverage: list[Coverage] = Field(default_factory=list)
    @model_validator(mode='after')
    def ordered(self):
        times=[s.exported_at for s in self.snapshots]
        if times!=sorted(times) or len(times)!=len(set(times)):
            raise ValueError('Snapshots require unique increasing availability times')
        return self

def aware(value):
    if isinstance(value,str):value=datetime.fromisoformat(value.replace('Z','+00:00'))
    if not isinstance(value,datetime) or value.utcoffset() is None:
        raise ValueError('A timezone-aware timestamp is required')
    return value.astimezone(timezone.utc)

def zone(value):
    try:return ZoneInfo(value)
    except (ZoneInfoNotFoundError,ValueError,TypeError):raise ValueError('Invalid IANA timezone')
