from .auth import owned, owned_row
from datetime import datetime, timezone, date
from fastapi import Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from .tracking_schemas import WellnessIn, EarlySymptomIn, utc, valid_zone
from .analytics import summarize

def register_tracking(app, db, Episode, Wellness, EarlySymptom, Contact, Profile, AttackSession, SupportPreferences, SupportFeedback, require_user, SharingConsent):
    def get_row(s, model, id, user):
        row=owned_row(s,model,id,user)
        if not row: raise HTTPException(404,'Record not found')
        return row
    def wellness_values(data,existing=None):
        from zoneinfo import ZoneInfo
        from datetime import timedelta,time
        values=data.model_dump(); values['date']=data.date.isoformat()
        if 'episode_observation' not in data.model_fields_set and existing:
            values.pop('episode_observation')
            # Preserve an existing confirmation only if its date/zone are unchanged.
            if existing.date!=values['date'] or existing.timezone_name!=values['timezone_name']:
                values.update(episode_observation=None,observation_recorded_at=None)
        else:
            observation=data.episode_observation
            if observation:
                day_end=datetime.combine(data.date+timedelta(days=1),time.min,ZoneInfo(data.timezone_name))
                if day_end>datetime.now(timezone.utc):
                    raise HTTPException(422,'Whole-day observations require a completed local date. Leave it unknown for today.')
            values['observation_recorded_at']=datetime.now(timezone.utc).isoformat() if observation else None
        return values
    def commit(s,row):
        try: s.commit()
        except IntegrityError:
            s.rollback(); raise HTTPException(409,'A wellness check-in already exists for this date. Edit that entry instead.')
        s.refresh(row); return row
    @app.get('/api/wellness')
    def list_wellness(s=Depends(db),user=Depends(require_user)): return owned(s,Wellness,user).order_by(Wellness.date.desc()).all()
    @app.post('/api/wellness',status_code=201)
    def add_wellness(data: WellnessIn,s=Depends(db),user=Depends(require_user)):
        row=Wellness(owner_id=user.id,**wellness_values(data),recorded_at=datetime.now(timezone.utc).isoformat());s.add(row);return commit(s,row)
    @app.put('/api/wellness/{id}')
    def edit_wellness(id:int,data:WellnessIn,s=Depends(db),user=Depends(require_user)):
        row=get_row(s,Wellness,id,user)
        for k,v in wellness_values(data,row).items():setattr(row,k,v)
        return commit(s,row)
    @app.delete('/api/wellness/{id}',status_code=204)
    def delete_wellness(id:int,s=Depends(db),user=Depends(require_user)):
        s.delete(get_row(s,Wellness,id,user));s.commit()
    @app.get('/api/early-symptoms')
    def list_early(s=Depends(db),user=Depends(require_user)):return owned(s,EarlySymptom,user).order_by(EarlySymptom.onset_at.desc()).all()
    @app.post('/api/early-symptoms',status_code=201)
    def add_early(data:EarlySymptomIn,s=Depends(db),user=Depends(require_user)):
        values=data.model_dump();values['onset_at']=utc(data.onset_at)
        row=EarlySymptom(owner_id=user.id,**values,recorded_at=datetime.now(timezone.utc).isoformat());s.add(row);s.commit();s.refresh(row);return row
    @app.put('/api/early-symptoms/{id}')
    def edit_early(id:int,data:EarlySymptomIn,s=Depends(db),user=Depends(require_user)):
        row=get_row(s,EarlySymptom,id,user);values=data.model_dump();values['onset_at']=utc(data.onset_at)
        for k,v in values.items():setattr(row,k,v)
        s.commit();s.refresh(row);return row
    @app.delete('/api/early-symptoms/{id}',status_code=204)
    def delete_early(id:int,s=Depends(db),user=Depends(require_user)):
        s.delete(get_row(s,EarlySymptom,id,user));s.commit()
    @app.get('/api/insights')
    def insights(timezone_name:str=Query(default='Asia/Kolkata',max_length=100),as_of:date|None=None,s=Depends(db),user=Depends(require_user)):
        try: valid_zone(timezone_name)
        except ValueError:raise HTTPException(422,'Invalid reporting timezone')
        from zoneinfo import ZoneInfo
        today=as_of or datetime.now(ZoneInfo(timezone_name)).date()
        return summarize(owned(s,Episode,user).all(),owned(s,Wellness,user).all(),today,timezone_name)
    @app.get('/api/pattern-insights')
    def pattern_insights(timezone_name:str=Query(default='Asia/Kolkata',max_length=100),days:int=Query(default=30,ge=7,le=90),s=Depends(db),user=Depends(require_user)):
        try:valid_zone(timezone_name)
        except ValueError:raise HTTPException(422,'Invalid reporting timezone')
        from .pattern_insights import describe
        return describe(owned(s,Episode,user).all(),owned(s,Wellness,user).all(),
            owned(s,EarlySymptom,user).all(),timezone_name,days,datetime.now(timezone.utc))

    @app.get('/api/export')
    def export(s=Depends(db),user=Depends(require_user)):
        def records(model):return [{col.name:getattr(row,col.name) for col in model.__table__.columns if col.name not in ('active_slot','owner_id')} for row in owned(s,model,user).order_by(model.id).all()]
        data={'schema_version':4,'exported_at':datetime.now(timezone.utc).isoformat(),
            'account':{'email':user.email,'display_name':user.display_name,'created_at':user.created_at},'sharing_consents':records(SharingConsent),
            'scope':'Current account only. Unclaimed legacy records excluded. Missing values are unknown. UTC timestamps with original IANA timezones where recorded; legacy dates have no inferred timezone.',
            'episodes':records(Episode),'wellness':records(Wellness),'early_symptoms':records(EarlySymptom),
            'attack_sessions':records(AttackSession),'contacts':records(Contact),'profiles':records(Profile),
            'support_preferences':records(SupportPreferences),'support_feedback':records(SupportFeedback)}
        return JSONResponse(data,headers={'Content-Disposition':'attachment; filename="migramind-records.json"','Cache-Control':'no-store'})
