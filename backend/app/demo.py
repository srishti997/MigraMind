"""Explicit operator-only fresh-demo provisioning; no import/reset/delete function."""
import argparse
import getpass
import os
from datetime import datetime, timezone
from sqlalchemy import func, select
from .deployment import DEMO_EMAIL, FIXTURE_VERSION


def provision(session, password, settings):
    if not settings.synthetic_demo:
        raise ValueError('Provisioning requires dedicated synthetic demonstration settings')
    if not 12 <= len(password) <= 128:
        raise ValueError('Use a private demo password of 12 to 128 characters')
    from .main import Base, User, Profile, SupportPreferences, Episode, DailyCheckin, CheckinRevision, DemoDeployment
    from .auth import hasher
    # Every application table must be empty. Never bless/copy/clear existing records.
    for table in Base.metadata.sorted_tables:
        if session.scalar(select(func.count()).select_from(table)):
            raise ValueError('Refusing to provision a nonempty database; use a fresh dedicated target')
    stamp = datetime.now(timezone.utc).isoformat()
    user = User(email=DEMO_EMAIL, display_name='Synthetic demonstration', password_hash=hasher.hash(password), created_at=stamp)
    session.add(user)
    session.flush()
    session.add_all([Profile(owner_id=user.id, name='Synthetic demonstration'),
        SupportPreferences(owner_id=user.id),
        Episode(owner_id=user.id, date='2026-01-02', severity=3, duration=60,
            started_at='2026-01-02T10:00:00+00:00', ended_at='2026-01-02T11:00:00+00:00',
            timezone_name='UTC', trigger='Unknown', notes='SYNTHETIC demonstration fixture; not a clinical observation.')])
    for day, status in [('2026-01-01', 'no_migraine'), ('2026-01-02', 'migraine'), ('2026-01-03', 'unknown')]:
        values = {'date':day, 'timezone_name':'UTC', 'status':status, 'event_at':day+'T12:00:00+00:00', 'observed_at':day+'T12:00:00+00:00',
            'status_recorded_at':stamp, 'sleep_hours':None, 'sleep_quality':None, 'stress':None,
            'hydration_ml':None, 'routine_changes':None, 'early_symptoms':None}
        row = DailyCheckin(owner_id=user.id, date=day, timezone_name='UTC', created_at=stamp,
            revision=1, values=values)
        session.add(row)
        session.flush()
        session.add(CheckinRevision(owner_id=user.id, checkin_id=row.id, revision=1,
            action='creation', recorded_at=stamp, values=values))
    session.add(DemoDeployment(id=1, fixture_version=FIXTURE_VERSION, created_at=stamp))
    session.commit()


def main():
    parser = argparse.ArgumentParser(description='Initialize only an empty, migrated synthetic demo target')
    parser.add_argument('action', choices=['provision'])
    parser.parse_args()
    from .main import security, SessionLocal
    if not security.synthetic_demo:
        raise SystemExit('Provisioning requires synthetic demonstration mode')
    password = os.getenv('DEMO_PASSWORD') or getpass.getpass('Private synthetic-demo password: ')
    try:
        with SessionLocal() as session:
            provision(session, password, security)
    except Exception:
        raise SystemExit('Demo provisioning failed; verify settings, migration and empty dedicated target. No reset performed.') from None
    print('Synthetic demonstration initialized. No real observations were imported.')


if __name__ == '__main__':
    main()
