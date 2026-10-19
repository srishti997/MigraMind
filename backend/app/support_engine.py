"""Explainable action ordering; no medical classification, messaging, or model score."""
from collections import Counter
ACTIONS=('call_contact','prepare_sms','support_card')
LABELS={'call_contact':'Call contact','prepare_sms':'Prepare SMS','support_card':'Open my support card'}
MIN_FEEDBACK=3

def recommend(preferences,contacts,feedback,*,fixed=False):
    preferred=preferences.get('preferred_actions') or []
    method={'call':'call_contact','sms':'prepare_sms'}.get(preferences.get('communication_method'))
    pins=list(dict.fromkeys(preferred+([method] if method else [])))
    counts=Counter(row['action_id'] for row in feedback)
    positive=Counter(row['action_id'] for row in feedback if row['helpful'])
    adaptive=bool(preferences.get('use_feedback')) and preferences.get('ranking_mode')!='fixed' and not fixed
    scores={action:(positive[action]+1)/(counts[action]+2) if adaptive and counts[action]>=MIN_FEEDBACK else .5 for action in ACTIONS}
    available={action:bool(contacts) or action=='support_card' for action in ACTIONS}
    def key(action):
        return (not available[action],0 if action in pins else 1,pins.index(action) if action in pins else 0,-scores[action] if action not in pins else 0,ACTIONS.index(action))
    ordered=sorted(ACTIONS,key=key)
    result=[]
    for action in ordered:
        if not available[action]:explanation='Save a trusted contact to use this action. No call or message will start automatically.'
        elif action in preferred:explanation=f'Your explicitly prioritized action (position {preferred.index(action)+1}).'
        elif action==method:explanation='Matches your saved communication method.'
        elif adaptive and counts[action]>=MIN_FEEDBACK:explanation=f'Your feedback marked this helpful {positive[action]} of {counts[action]} times; smoothed ratings order unpinned actions.'
        else:explanation='Stable default order; feedback ordering is off or fewer than 3 ratings are available for this action.'
        result.append({'id':action,'label':LABELS[action],'available':available[action],'explanation':explanation,
            'feedback_count':counts[action] if adaptive else 0})
    preferred_contact=preferences.get('preferred_contact_id')
    selected=next((row['id'] for row in contacts if row['id']==preferred_contact),contacts[0]['id'] if contacts else None)
    return {'algorithm_version':'explicit-feedback-v1','policy':'configured_fixed' if fixed or preferences.get('ranking_mode')=='fixed' else 'preference_first_adaptive',
        'feedback_ranking_enabled':adaptive,'contact_id':selected,'contact_selection':'explicit_preference' if selected is not None and selected==preferred_contact else 'first_saved_fallback' if selected is not None else 'none',
        'actions':result,'recommended_action':next((a['id'] for a in result if a['available']),None),
        'limitations':'Explicit choices always win. Feedback is optional, self-reported and context-dependent; rankings do not establish medical benefit or delivery.'}
