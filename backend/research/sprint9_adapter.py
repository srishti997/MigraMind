"""Explicit read-only projection. Never reads an application database by itself."""
from .revision_contract import RevisionBundle, ResearchSource


def project_account(session, account_id, account_key, provenance, captured_at):
    """Administrator-supplied session/identity; not a public authorization endpoint.

    Journals must be exported within a consistent DB read transaction by the caller.
    No clinical values or identities are logged. No app rows are altered.
    """
    source = ResearchSource.model_validate(provenance)
    if source.source_kind == 'consented' and (not source.consent_reference or not source.provenance_verified):
        raise ValueError('Reviewed research consent and provenance are required before projection')
    from app.main import CheckinRevision, User
    if not isinstance(account_id, int) or isinstance(account_id, bool) or account_id <= 0:
        raise ValueError('Explicit positive account scope required')
    if session.get(User, account_id) is None: raise ValueError('Account unavailable')
    fields = ('date', 'timezone_name', 'status', 'event_at', 'observed_at', 'status_recorded_at',
        'sleep_hours', 'sleep_quality', 'stress', 'hydration_ml')
    rows = session.query(CheckinRevision).filter_by(owner_id=account_id).order_by(CheckinRevision.id).all()
    projected = [{'account_key':account_key, 'record_id':str(row.checkin_id),
        'revision':row.revision, 'action':row.action, 'recorded_at':row.recorded_at,
        'values':{key:row.values[key] for key in fields} if row.values else None} for row in rows]
    # App status reports are NOT an independently adjudicated outcome journal.
    metadata = source.model_dump()
    metadata['outcome_history_complete'] = False
    return RevisionBundle(account_key=account_key, captured_at=captured_at, provenance=metadata,
        daily_revisions=projected, outcome_revisions=[])
