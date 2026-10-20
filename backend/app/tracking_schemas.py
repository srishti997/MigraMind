from datetime import date as Date, datetime, timezone
from typing import Annotated
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, Field, AwareDatetime, field_validator, model_validator, ConfigDict

ShortText = Annotated[str, Field(min_length=1, max_length=100)]
def valid_zone(value):
    try: ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError): raise ValueError('Use a valid IANA timezone')
    return value
class Medication(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=200)
    taken_at: AwareDatetime
class EpisodeIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    date: Date | None = None
    severity: int | None = Field(default=None, ge=0, le=10)
    duration: int | None = Field(default=None, ge=0, le=525600)
    trigger: str = Field(default='Unknown', max_length=100)
    notes: str = Field(default='', max_length=3000)
    started_at: AwareDatetime | None = None
    ended_at: AwareDatetime | None = None
    timezone_name: str | None = Field(default=None, max_length=100)
    pain_location: str = Field(default='', max_length=200)
    symptoms: list[ShortText] = Field(default_factory=list, max_length=30)
    functional_impact: str = Field(default='', max_length=100)
    medications: list[Medication] = Field(default_factory=list, max_length=30)
    attack_session_id: int | None = Field(default=None, gt=0)
    @field_validator('timezone_name')
    @classmethod
    def zone(cls,v): return valid_zone(v) if v else v
    @model_validator(mode='after')
    def chronology(self):
        if self.started_at:
            if not self.timezone_name: raise ValueError('Timezone is required for timed entries')
            if self.ended_at and self.ended_at < self.started_at: raise ValueError('End must not precede start')
        elif not self.date or self.ended_at:
            raise ValueError('Provide a start timestamp or a legacy date; end requires start')
        return self

def utc(value): return value.astimezone(timezone.utc).isoformat() if value else None

def episode_values(data):
    values=data.model_dump(exclude={'date','started_at','ended_at','medications'})
    values['date'] = data.started_at.astimezone(ZoneInfo(data.timezone_name)).date().isoformat() if data.started_at else data.date.isoformat()
    values['started_at']=utc(data.started_at); values['ended_at']=utc(data.ended_at)
    if data.started_at and data.ended_at:
        values['duration']=round((data.ended_at-data.started_at).total_seconds()/60)
    values['medications']=[{'name':m.name,'taken_at':utc(m.taken_at)} for m in data.medications]
    return values
class WellnessIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    date: Date
    timezone_name: str = Field(max_length=100)
    sleep_hours: float | None = Field(default=None, ge=0, le=24, allow_inf_nan=False)
    sleep_quality: int | None = Field(default=None, ge=0, le=10)
    stress: int | None = Field(default=None, ge=0, le=10)
    hydration_ml: int | None = Field(default=None, ge=0, le=20000)
    missed_meals: bool | None = None
    screen_hours: float | None = Field(default=None, ge=0, le=24, allow_inf_nan=False)
    menstrual_notes: str | None = Field(default=None, max_length=1000)
    episode_observation: Literal['episode','no_episode'] | None = None
    _zone=field_validator('timezone_name')(valid_zone)
class EarlySymptomIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    symptom: str = Field(min_length=1, max_length=200)
    onset_at: AwareDatetime
    timezone_name: str = Field(max_length=100)
    notes: str = Field(default='', max_length=3000)
    _zone=field_validator('timezone_name')(valid_zone)
