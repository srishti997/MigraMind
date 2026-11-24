"""In-process synthetic core journeys; no external service or existing database."""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import Base, app, auth, db
from test_auth import ORIGIN, PASSWORD, clients, login, register


def test_synthetic_core_journey_and_owner_isolation(clients):
    first, other, _ = clients
    register(first, 'journey-one@example.test')
    register(other, 'journey-two@example.test')
    duplicate = other.post('/api/auth/register', json={
        'email':'journey-one@example.test','password':PASSWORD,'display_name':'Synthetic duplicate'})
    assert duplicate.status_code == 400

    payload = {'date':'2025-01-02','severity':4,'duration':60,'notes':'Synthetic entry'}
    created = first.post('/api/episodes', json=payload)
    assert created.status_code == 201
    identifier = created.json()['id']
    assert [row['id'] for row in first.get('/api/episodes').json()] == [identifier]
    assert other.get('/api/episodes').json() == []
    assert other.put(f'/api/episodes/{identifier}',json=payload).status_code == 404
    assert other.delete(f'/api/episodes/{identifier}').status_code == 404

    assert first.post('/api/episodes',json={**payload,'severity':11}).status_code == 422
    assert len(first.get('/api/episodes').json()) == 1
    edited=first.put(f'/api/episodes/{identifier}',json={**payload,'severity':7})
    assert edited.status_code == 200 and edited.json()['severity'] == 7
    summary=first.get('/api/insights?timezone_name=UTC&as_of=2025-01-02').json()
    assert (summary['episode_count'],summary['headache_days'],summary['average_severity']) == (1,1,7)
    assert first.delete(f'/api/episodes/{identifier}').status_code == 204
    assert first.get('/api/episodes').json() == []

    previous=first.cookies.get('migramind_session')
    token=first.headers['X-CSRF-Token']
    assert first.post('/api/auth/logout').status_code == 204
    other.cookies.clear();other.cookies.set('migramind_session',previous)
    assert other.get('/api/episodes',headers={'X-CSRF-Token':token}).status_code == 401
    assert login(first,'journey-one@example.test','Synthetic-incorrect').status_code == 401
    assert login(first,'journey-one@example.test').status_code == 200


def test_synthetic_file_database_reopens_without_process_restart(tmp_path):
    path=tmp_path/'synthetic-core-reopen.sqlite'
    assert not path.exists()
    url='sqlite:///'+path.as_posix()
    engine=create_engine(url,connect_args={'check_same_thread':False})
    Base.metadata.create_all(engine)
    def override():
        with sessionmaker(bind=engine)() as session: yield session
    app.dependency_overrides[db]=override
    auth.limiter.clear()
    try:
        with TestClient(app,headers={'Origin':ORIGIN}) as client:
            client.headers['X-CSRF-Token']=client.get('/api/auth/session').json()['csrf_token']
            register(client,'reopen@example.test')
            assert client.post('/api/episodes',json={'date':'2025-01-02','severity':3,'notes':'Synthetic persisted'}).status_code == 201
        engine.dispose()
        engine=create_engine(url,connect_args={'check_same_thread':False})
        with TestClient(app,headers={'Origin':ORIGIN}) as client:
            assert login(client,'reopen@example.test').status_code == 200
            rows=client.get('/api/episodes').json()
            assert len(rows)==1 and rows[0]['notes']=='Synthetic persisted'
    finally:
        app.dependency_overrides.clear()
        auth.limiter.clear()
        engine.dispose()
