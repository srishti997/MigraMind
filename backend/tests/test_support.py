"""Synthetic fixtures only; descriptive comparisons are not real-user outcomes."""
import pytest
from app.support_engine import recommend
from research.support_evaluation import evaluate_trials,Trial

def test_nonemergency_feedback_does_not_override_explicit_choices():
    feedback=[{'action_id':'prepare_sms','helpful':True}]*8+[{'action_id':'call_contact','helpful':False}]*8
    prefs={'use_feedback':True,'preferred_actions':['call_contact'],'communication_method':'sms'}
    ranked=recommend(prefs,[{'id':1}],feedback)
    assert [r['id'] for r in ranked['actions']]==['call_contact','prepare_sms','support_card']
    assert 'explicitly' in ranked['actions'][0]['explanation']
    assert all('emergency' not in row['id'] for row in ranked['actions'])

def test_smoothed_evidence_ranks_unpinned_actions_and_default_ties_stable():
    p={'use_feedback':True}
    feedback=[{'action_id':'call_contact','helpful':False}]*3
    assert recommend(p,[{'id':1}],feedback)['recommended_action']=='prepare_sms'
    assert recommend(p,[{'id':1}],feedback,fixed=True)['recommended_action']=='call_contact'
    assert recommend(p,[{'id':1}],[])['recommended_action']=='call_contact'

def test_evaluation_separates_simulation_from_real_and_handles_unknowns():
    fixtures=[{'source':'simulated_test','policy':'adaptive','completed':True,'interactions':2,'chosen_action':'prepare_sms','explicit_first_choice':'prepare_sms','order_before':['call_contact','prepare_sms'],'order_after':['prepare_sms','call_contact']},
        {'source':'real_user_study','policy':'fixed','completed':None,'interactions':None}]
    report=evaluate_trials(fixtures);groups=report['results_by_source']
    synthetic=groups['simulated_test']['adaptive'];real=groups['real_user_study']['fixed']
    assert synthetic['completion_rate']==1 and synthetic['mean_interactions']==2
    assert synthetic['preference_alignment']==1 and synthetic['top_recommendation_change_rate']==1
    assert real['completion_rate'] is None and real['mean_interactions'] is None
    assert real['completion_observations']==0 and real['trials']==1
    assert evaluate_trials([])['results_by_source']['real_user_study']['adaptive']['completion_rate'] is None
    with pytest.raises(ValueError):Trial(source='simulated_test',policy='adaptive',interactions=-1)
    with pytest.raises(ValueError):Trial(source='simulated_test',policy='adaptive',chosen_action='emergency_call')
