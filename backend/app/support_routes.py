from .auth import owned, owned_row
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

def register_support(app,db,Contact,AttackSession,Preferences,Feedback,require_user):
    def prefs(s,user):
        row=owned(s,Preferences,user).first()
        if not row:
            row=Preferences(owner_id=user.id,**PreferencesIn().model_dump());s.add(row)
            try:s.commit()
            except IntegrityError:s.rollback();row=owned(s,Preferences,user).first()
            s.refresh(row)
        return row
    @app.get('/api/support/preferences')
    def get_preferences(s=Depends(db),user=Depends(require_user)):return prefs(s,user)
    @app.put('/api/support/preferences')
    def save_preferences(data:PreferencesIn,s=Depends(db),user=Depends(require_user)):
        if data.preferred_contact_id is not None and not owned(s,Contact,user).filter_by(id=data.preferred_contact_id).first():raise HTTPException(422,'Choose an existing trusted contact')
        row=prefs(s,user)
        for k,v in data.model_dump().items():setattr(row,k,v)
        s.commit();s.refresh(row);return row
    @app.post('/api/support/preferences/reset')
    def reset_preferences(s=Depends(db),user=Depends(require_user)):
        row=prefs(s,user)
        for k,v in PreferencesIn().model_dump().items():setattr(row,k,v)
        s.commit();s.refresh(row);return row
    @app.get('/api/support/recommendations')
    def recommendations(policy:Literal['saved','fixed']=Query(default='saved'),s=Depends(db),user=Depends(require_user)):
        p=prefs(s,user)
        values={field:getattr(p,field) for field in PreferencesIn.model_fields}
        contacts=[{'id':c.id} for c in owned(s,Contact,user).order_by(Contact.id).all()]
        feedback=[{'action_id':f.action_id,'helpful':f.helpful} for f in owned(s,Feedback,user).all()]
        return recommend(values,contacts,feedback,fixed=policy=='fixed')
    @app.get('/api/support/feedback')
    def list_feedback(s=Depends(db),user=Depends(require_user)):return owned(s,Feedback,user).order_by(Feedback.id.desc()).all()
    @app.post('/api/support/feedback',status_code=201)
    def add_feedback(data:FeedbackIn,s=Depends(db),user=Depends(require_user)):
        if owned(s,AttackSession,user).filter_by(active_slot=1).first():raise HTTPException(409,'Feedback is available only after the active session ends')
        session=owned_row(s,AttackSession,data.session_id,user)
        if not session:raise HTTPException(404,'Attack session not found')
        if session.ended_at is None:raise HTTPException(409,'End the session before adding feedback')
        row=Feedback(owner_id=user.id,**data.model_dump(),created_at=datetime.now(timezone.utc).isoformat());s.add(row)
        try:s.commit()
        except IntegrityError:s.rollback();raise HTTPException(409,'This session and action already have feedback. Delete it before submitting a replacement.')
        s.refresh(row);return row
    @app.delete('/api/support/feedback/{id}',status_code=204)
    def delete_feedback(id:int,s=Depends(db),user=Depends(require_user)):
        row=owned_row(s,Feedback,id,user)
        if not row:raise HTTPException(404,'Feedback not found')
        s.delete(row);s.commit()
