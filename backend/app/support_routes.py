from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from fastapi import Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from .support_engine import recommend
Action=Literal['call_contact','prepare_sms','support_card']
class PreferencesIn(BaseModel):
    model_config=ConfigDict(extra='forbid')
    preferred_contact_id: int|None=Field(default=None,gt=0)
    communication_method: Literal['none','call','sms']='none'
    preferred_actions: list[Action]=Field(default_factory=list,max_length=3)
    large_text: bool=False
    reduce_motion: bool=False
    simplified_view: bool=False
    use_feedback: bool=False
    ranking_mode: Literal['adaptive','fixed']='adaptive'
    @model_validator(mode='after')
    def unique(self):
        if len(set(self.preferred_actions))!=len(self.preferred_actions):raise ValueError('Support actions must be unique')
        return self
class FeedbackIn(BaseModel):
    model_config=ConfigDict(extra='forbid')
    session_id: int=Field(gt=0)
    action_id: Action
    helpful: bool=Field(strict=True)

def register_support(app,db,Contact,AttackSession,Preferences,Feedback):
    def prefs(s):
        row=s.get(Preferences,1)
        if not row:
            row=Preferences(id=1,**PreferencesIn().model_dump());s.add(row)
            try:s.commit()
            except IntegrityError:s.rollback();row=s.get(Preferences,1)
            s.refresh(row)
        return row
    @app.get('/api/support/preferences')
    def get_preferences(s=Depends(db)):return prefs(s)
    @app.put('/api/support/preferences')
    def save_preferences(data:PreferencesIn,s=Depends(db)):
        if data.preferred_contact_id is not None and not s.get(Contact,data.preferred_contact_id):raise HTTPException(422,'Choose an existing trusted contact')
        row=prefs(s)
        for k,v in data.model_dump().items():setattr(row,k,v)
        s.commit();s.refresh(row);return row
    @app.post('/api/support/preferences/reset')
    def reset_preferences(s=Depends(db)):
        row=prefs(s)
        for k,v in PreferencesIn().model_dump().items():setattr(row,k,v)
        s.commit();s.refresh(row);return row
    @app.get('/api/support/recommendations')
    def recommendations(policy:Literal['saved','fixed']=Query(default='saved'),s=Depends(db)):
        p=prefs(s)
        values={field:getattr(p,field) for field in PreferencesIn.model_fields}
        contacts=[{'id':c.id} for c in s.query(Contact).order_by(Contact.id).all()]
        feedback=[{'action_id':f.action_id,'helpful':f.helpful} for f in s.query(Feedback).all()]
        return recommend(values,contacts,feedback,fixed=policy=='fixed')
    @app.get('/api/support/feedback')
    def list_feedback(s=Depends(db)):return s.query(Feedback).order_by(Feedback.id.desc()).all()
    @app.post('/api/support/feedback',status_code=201)
    def add_feedback(data:FeedbackIn,s=Depends(db)):
        if s.query(AttackSession).filter_by(active_slot=1).first():raise HTTPException(409,'Feedback is available only after the active session ends')
        session=s.get(AttackSession,data.session_id)
        if not session:raise HTTPException(404,'Attack session not found')
        if session.ended_at is None:raise HTTPException(409,'End the session before adding feedback')
        row=Feedback(**data.model_dump(),created_at=datetime.now(timezone.utc).isoformat());s.add(row)
        try:s.commit()
        except IntegrityError:s.rollback();raise HTTPException(409,'This session and action already have feedback. Delete it before submitting a replacement.')
        s.refresh(row);return row
    @app.delete('/api/support/feedback/{id}',status_code=204)
    def delete_feedback(id:int,s=Depends(db)):
        row=s.get(Feedback,id)
        if not row:raise HTTPException(404,'Feedback not found')
        s.delete(row);s.commit()
