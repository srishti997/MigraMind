"""Offline contract v2: one account, genuine availability times, no identity/free text."""
from collections import defaultdict
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, field_validator, model_validator
from .contract import aware, zone


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class ResearchSource(Strict):
    source_kind: Literal['synthetic', 'consented']
    source_reference: str = Field(min_length=1, max_length=200)
    consent_reference: str | None = Field(default=None, max_length=200)
    provenance_verified: bool = False
    outcome_history_complete: bool = False

    @field_validator('source_reference', 'consent_reference')
    @classmethod
    def reference(cls, value):
        if value is not None and not value.strip(): raise ValueError('A nonblank reference is required')
        return value.strip() if value is not None else None


class DailyValues(Strict):
    date: date
    timezone_name: str = Field(max_length=100)
    status: Literal['migraine', 'no_migraine', 'unknown']
    event_at: AwareDatetime
    observed_at: AwareDatetime
    status_recorded_at: AwareDatetime
    sleep_hours: float | None = Field(default=None, ge=0, le=24, allow_inf_nan=False)
    sleep_quality: int | None = Field(default=None, ge=0, le=10)
    stress: int | None = Field(default=None, ge=0, le=10)
    hydration_ml: int | None = Field(default=None, ge=0, le=20000)

    @field_validator('event_at', 'observed_at', 'status_recorded_at')
    @classmethod
    def utc(cls, value): return aware(value)

    @model_validator(mode='after')
    def chronology(self):
        if not self.event_at <= self.observed_at <= self.status_recorded_at:
            raise ValueError('Invalid observation chronology')
        if self.event_at.astimezone(zone(self.timezone_name)).date() != self.date:
            raise ValueError('Event does not match its source-local date')
        return self


class OutcomeValues(Strict):
    # Supplied by a reviewed external adjudication journal, NEVER inferred from diary absence.
    kind: Literal['onset', 'no_episode_interval', 'unknown_interval', 'observation_interval']
    start_at: AwareDatetime
    end_at: AwareDatetime | None = None
    verified: bool = False
    verification_reference: str | None = Field(default=None, min_length=1, max_length=200)
    independently_verified: bool = False
    complete: bool = False

    @field_validator("verification_reference")
    @classmethod
    def evidence_reference(cls, value):
        if value is not None and not value.strip(): raise ValueError("Blank evidence reference")
        return value.strip() if value is not None else None

    @field_validator('start_at', 'end_at')
    @classmethod
    def utc(cls, value): return aware(value) if value is not None else None

    @model_validator(mode='after')
    def chronology(self):
        if self.kind != 'onset' and self.end_at is None:
            raise ValueError('Coverage requires an explicit end')
        if self.end_at is not None and self.end_at <= self.start_at:
            raise ValueError('Outcome interval must increase')
        return self


class Revision(Strict):
    account_key: str = Field(min_length=1, max_length=100)
    record_id: str = Field(min_length=1, max_length=100)
    revision: int = Field(ge=1)
    action: Literal['creation', 'correction', 'deletion']
    recorded_at: AwareDatetime

    @field_validator('recorded_at')
    @classmethod
    def utc(cls, value): return aware(value)


class DailyRevision(Revision):
    values: DailyValues | None


class OutcomeRevision(Revision):
    values: OutcomeValues | None


def groups(revisions):
    result = defaultdict(list)
    for row in revisions: result[row.record_id].append(row)
    return {key:sorted(value, key=lambda r:r.revision) for key,value in sorted(result.items())}


class RevisionBundle(Strict):
    research_schema_version: Literal[2] = 2
    account_key: str = Field(min_length=1, max_length=100)
    captured_at: AwareDatetime
    provenance: ResearchSource
    daily_revisions: list[DailyRevision] = Field(default_factory=list)
    outcome_revisions: list[OutcomeRevision] = Field(default_factory=list)

    @field_validator('captured_at')
    @classmethod
    def utc(cls, value): return aware(value)

    @model_validator(mode='after')
    def journal_integrity(self):
        dates = set()
        for collection in (self.daily_revisions, self.outcome_revisions):
            for chain in groups(collection).values():
                identity = None
                previous = None
                for index,row in enumerate(chain, 1):
                    if row.account_key != self.account_key:
                        raise ValueError('Mixed or unclaimed account records are forbidden')
                    if row.revision != index or row.recorded_at > self.captured_at:
                        raise ValueError('Incomplete or future revision chain')
                    if previous and (row.recorded_at < previous.recorded_at or previous.action == 'deletion'):
                        raise ValueError('Invalid revision order or resurrection')
                    if (index == 1 and row.action != 'creation') or (index > 1 and row.action == 'creation'):
                        raise ValueError('Invalid creation action')
                    if (row.action == 'deletion') != (row.values is None):
                        raise ValueError('Only deletions have null values')
                    if isinstance(row, DailyRevision) and row.values:
                        value = row.values
                        if value.status_recorded_at != row.recorded_at:
                            raise ValueError('Server confirmation must match revision availability')
                        key = (value.date, value.timezone_name)
                        if identity is not None and key != identity:
                            raise ValueError('Daily date/timezone cannot change within a record')
                        identity = key
                    if isinstance(row, OutcomeRevision) and row.values:
                        value = row.values
                        if value.start_at > row.recorded_at or (value.end_at and value.end_at > row.recorded_at):
                            raise ValueError('Outcomes cannot be confirmed before they occur or finish')
                        if identity is not None and identity != value.kind:
                            raise ValueError('Outcome kind cannot change within a record')
                        identity = value.kind
                    previous = row
                if isinstance(chain[0], DailyRevision):
                    day = identity[0]
                    if day in dates: raise ValueError('Duplicate daily dates')
                    dates.add(day)
        return self
