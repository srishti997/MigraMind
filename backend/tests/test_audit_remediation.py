"""Synthetic regressions for the independently reproduced final-audit defects."""
from dataclasses import replace
from datetime import timedelta

import pytest
from test_auth import clients, register
from test_research import fake_rows
from research.dataset import chronological_split, HORIZON


def split(rows, grid):
    return chronological_split(rows, grid_start=grid[0].prediction_at, grid_end=grid[-1].horizon_end)


def test_legacy_future_exclusion_cannot_move_earlier_partitions():
    rows=fake_rows(240)
    original=split(rows,rows)
    changed=split(rows[:-1],rows)
    assert original['train']==changed['train']
    assert original['validation']==changed['validation']
    # Empty validation/test partitions cannot remove their fixed purge boundary.
    earlier=split([r for r in rows if r.prediction_at<rows[144].prediction_at],rows)
    assert original['train']==earlier['train']
    assert earlier['validation']==earlier['test']==[]
    assert len(original['train'])==142
    boundary=rows[144].prediction_at
    assert all(r.horizon_end<boundary and r.label_available_at<boundary for r in original['train'])


def test_legacy_later_coverage_cannot_veto_an_earlier_label():
    from test_research import fixture_bundle, stamp
    from research.contract import Coverage
    from research.dataset import build_dataset
    bundle=fixture_bundle();start=stamp('2026-01-03T12:00Z')
    original=build_dataset(bundle,start,start+HORIZON,'UTC')
    # This longer coverage sorts before the old evidence but was confirmed later.
    bundle.coverage.append(Coverage(start_at=start-HORIZON,end_at=start+HORIZON,
        confirmed_at=start+30*HORIZON,complete=True))
    assert build_dataset(bundle,start,start+HORIZON,'UTC')==original
    bundle.coverage=bundle.coverage[-1:]
    assert build_dataset(bundle,start,start+HORIZON,'UTC')[0]==[]


def test_legacy_holdout_values_and_late_labels_cannot_change_training_fit():
    pytest.importorskip('sklearn')
    import numpy as np
    from research.models import make_logistic, matrix
    from research.evaluation import choose_threshold
    rows=fake_rows(240);parts=split(rows,rows)
    test_start=rows[192].prediction_at
    changed=[replace(r,target=1-r.target,features={k:10. for k in r.features},
        label_available_at=r.label_available_at+30*HORIZON) if r.prediction_at>=test_start else r for r in rows]
    other=split(changed,rows)
    assert parts['train']==other['train'] and parts['validation']==other['validation']
    fits=[]
    for data in (parts,other):
        model=make_logistic().fit(matrix(data['train']),[r.target for r in data['train']])
        validation=model.predict_proba(matrix(data['validation']))[:,1]
        fits.append((model.named_steps['model'].coef_,validation,
            choose_threshold([r.target for r in data['validation']],validation)))
    np.testing.assert_array_equal(fits[0][0],fits[1][0])
    np.testing.assert_array_equal(fits[0][1],fits[1][1])
    assert fits[0][2]==fits[1][2]
    # Invalid off-grid values cannot bypass the declared schedule.
    with pytest.raises(ValueError):split([replace(rows[0],prediction_at=rows[0].prediction_at+timedelta(hours=1))],rows)


def test_episode_create_and_update_share_strict_policy_and_preserve_history(clients):
    from app.main import Episode
    a,_,factory=clients; user=register(a)
    valid={'started_at':'2026-01-02T10:00:00Z','ended_at':'2026-01-02T11:00:00Z','timezone_name':'UTC','severity':0}
    row=a.post('/api/episodes',json=valid).json()
    assert row['duration']==60
    invalid=[{'ended_at':valid['started_at']},{'ended_at':'2026-01-02T09:00:00Z'},
        {'started_at':'2099-01-02T10:00:00Z','ended_at':None},{'ended_at':'2099-01-02T11:00:00Z'},
        {'date':'2026-01-03'},{'duration':45},{'severity':True},{'duration':1.5},
        {'medications':[{'name':'Synthetic','taken_at':'2099-01-02T10:00:00Z'}]}]
    for changes in invalid:
        assert a.post('/api/episodes',json={**valid,**changes}).status_code==422
        assert a.put(f"/api/episodes/{row['id']}",json={**valid,**changes}).status_code==422
        assert a.get('/api/episodes').json()==[row]
    assert a.post('/api/episodes',json={'date':'2099-01-02'}).status_code==422
    # Sub-minute positive intervals may round to zero; unknown duration stays null.
    assert a.post('/api/episodes',json={**valid,'ended_at':'2026-01-02T10:00:10Z'}).json()['duration']==0
    assert a.post('/api/episodes',json={**valid,'ended_at':None}).json()['duration'] is None
    with factory() as s:
        historic=Episode(owner_id=user['id'],date='2026-01-03',started_at='2026-01-03T10:00:00+00:00',
            ended_at='2026-01-03T10:00:00+00:00',timezone_name='UTC',severity=None,duration=0,trigger='Unknown',notes='Synthetic historical invalid interval')
        s.add(historic);s.commit();historic_id=historic.id
    before=a.get('/api/episodes').json()
    old=next(r for r in before if r['id']==historic_id)
    assert a.put(f'/api/episodes/{historic_id}',json={k:v for k,v in old.items() if k not in ('id','owner_id')}).status_code==422
    assert a.get('/api/episodes').json()==before


def test_phone_validation_rejects_unsafe_syntax_without_national_assumptions(clients):
    a,_,_=clients;register(a)
    valid=['112','1','020 1234-5678','+91 (20) 1234-5678','001-202-555-0100']
    for phone in valid:
        assert a.post('/api/contacts',json={'name':'Synthetic','relationship':'Test','phone':phone}).status_code==201
    row=a.get('/api/contacts').json()[0]
    for phone in ['---','()','   ','+','++123','12+3','tel:112','*123#','123;456','123?body=x','(123','123)','((12))','()12','123\n456','１２３']:
        payload={'name':'Synthetic','relationship':'Test','phone':phone}
        assert a.post('/api/contacts',json=payload).status_code==422
        assert a.put(f"/api/contacts/{row['id']}",json=payload).status_code==422
    assert a.get('/api/contacts').json()[0]==row
