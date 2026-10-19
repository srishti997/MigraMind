from datetime import datetime, timezone, date
from fastapi import Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from .tracking_schemas import WellnessIn, EarlySymptomIn, utc, valid_zone
from .analytics import summarize

def register_tracking(app, db, Episode, Wellness, EarlySymptom, Contact, Profile, AttackSession, SupportPreferences, SupportFeedback):
    def get_row(s, model, id):
        row=s.get(model,id)
        if not row: raise HTTPException(404,'Record not found')
        return row
    def wellness_values(data):
        values=data.model_dump(); values['date']=data.date.isoformat(); return values
    def commit(s,row):
        try: s.commit()
        except IntegrityError:
            s.rollback(); raise HTTPException(409,'A wellness check-in already exists for this date. Edit that entry instead.')
        s.refresh(row); return row
    @app.get('/api/wellness')
    def list_wellness(s=Depends(db)): return s.query(Wellness).order_by(Wellness.date.desc()).all()
    @app.post('/api/wellness',status_code=201)
    def add_wellness(data: WellnessIn,s=Depends(db)):
        row=Wellness(**wellness_values(data),recorded_at=datetime.now(timezone.utc).isoformat());s.add(row);return commit(s,row)
    @app.put('/api/wellness/{id}')
    def edit_wellness(id:int,data:WellnessIn,s=Depends(db)):
        row=get_row(s,Wellness,id)
        for k,v in wellness_values(data).items():setattr(row,k,v)
        return commit(s,row)
    @app.delete('/api/wellness/{id}',status_code=204)
    def delete_wellness(id:int,s=Depends(db)):
        s.delete(get_row(s,Wellness,id));s.commit()
    @app.get('/api/early-symptoms')
    def list_early(s=Depends(db)):return s.query(EarlySymptom).order_by(EarlySymptom.onset_at.desc()).all()
    @app.post('/api/early-symptoms',status_code=201)
    def add_early(data:EarlySymptomIn,s=Depends(db)):
        values=data.model_dump();values['onset_at']=utc(data.onset_at)
        row=EarlySymptom(**values,recorded_at=datetime.now(timezone.utc).isoformat());s.add(row);s.commit();s.refresh(row);return row
    @app.put('/api/early-symptoms/{id}')
    def edit_early(id:int,data:EarlySymptomIn,s=Depends(db)):
        row=get_row(s,EarlySymptom,id);values=data.model_dump();values['onset_at']=utc(data.onset_at)
        for k,v in values.items():setattr(row,k,v)
        s.commit();s.refresh(row);return row
    @app.delete('/api/early-symptoms/{id}',status_code=204)
    def delete_early(id:int,s=Depends(db)):
        s.delete(get_row(s,EarlySymptom,id));s.commit()
    @app.get('/api/insights')
    def insights(timezone_name:str=Query(default='Asia/Kolkata',max_length=100),as_of:date|None=None,s=Depends(db)):
        try: valid_zone(timezone_name)
        except ValueError:raise HTTPException(422,'Invalid reporting timezone')
        from zoneinfo import ZoneInfo
        today=as_of or datetime.now(ZoneInfo(timezone_name)).date()
        return summarize(s.query(Episode).all(),s.query(Wellness).all(),today,timezone_name)
    @app.get('/api/export')
    def export(s=Depends(db)):
        def records(model):return [{col.name:getattr(row,col.name) for col in model.__table__.columns if col.name!='active_slot'} for row in s.query(model).order_by(model.id).all()]
        data={'schema_version':3,'exported_at':datetime.now(timezone.utc).isoformat(),
            'scope':'Single-user local prototype. Missing values are unknown. UTC timestamps with original IANA timezones where recorded; legacy dates have no inferred timezone.',
            'episodes':records(Episode),'wellness':records(Wellness),'early_symptoms':records(EarlySymptom),
            'attack_sessions':records(AttackSession),'contacts':records(Contact),'profiles':records(Profile),
            'support_preferences':records(SupportPreferences),'support_feedback':records(SupportFeedback)}
        return JSONResponse(data,headers={'Content-Disposition':'attachment; filename="migramind-records.json"','Cache-Control':'no-store'})
