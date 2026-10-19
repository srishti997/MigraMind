from datetime import date, timedelta
from app.main import SessionLocal, Episode, Contact, Profile
with SessionLocal() as s:
    if not s.query(Episode).first():
        for days, severity, duration, trigger in [(2,4,90,'Screen time'),(6,7,180,'Poor sleep'),(11,5,120,'Stress'),(16,3,60,'Unknown')]:
            s.add(Episode(date=(date.today()-timedelta(days=days)).isoformat(),severity=severity,duration=duration,trigger=trigger,notes='Synthetic demo episode. Replace with your own observations.'))
        s.add(Contact(name='Jamie Morgan (demo)',relationship='Partner',phone='+12025550142'))
        s.add(Profile(id=1,name='Alex',support='Please keep the room quiet and dim. Ask before calling or visiting.',avoid='Bright lights, strong fragrances, and loud sounds.'))
        s.commit()
