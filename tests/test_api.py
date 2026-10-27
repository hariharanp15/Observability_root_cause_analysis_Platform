from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_sample_failure_is_queryable_end_to_end():
    created = client.post('/api/v1/demo/orders?scenario=payment_failure')
    assert created.status_code == 200
    trace_id = created.json()['data']['trace_id']
    assert len(client.get(f'/api/v1/traces/{trace_id}/spans').json()['data']) == 4
    assert client.get(f'/api/v1/traces/{trace_id}/logs').json()['data'][0]['severity'] == 'ERROR'
    report = client.post(f'/api/v1/diagnostics/analyze/{trace_id}')
    assert report.status_code == 200
    assert report.json()['data']['affected_service'] == 'payment-service'
    assert client.get('/api/v1/dependencies').json()['data']

def test_validation_filters_and_alert_status():
    assert client.get('/api/v1/logs?start_time=2026-10-24T00:00:00&end_time=2026-10-23T00:00:00').status_code == 422
    assert client.get('/api/v1/traces/missing-trace').status_code == 404
    assert client.patch('/api/v1/alerts/999999?status=BROKEN').status_code == 422
    assert client.get('/api/v1/overview').status_code == 200

def test_system_service_and_evidence_routes():
    generated = client.post('/api/v1/demo/orders?scenario=payment_failure').json()['data']['trace_id']
    assert client.get('/api/v1/system/status').status_code == 200
    assert client.get('/api/v1/system/statistics').status_code == 200
    assert client.get('/api/v1/services').status_code == 200
    assert client.get('/api/v1/services/payment-service').status_code == 200
    evidence = client.get(f'/api/v1/reports/traces/{generated}/evidence')
    assert evidence.status_code == 200
    assert len(evidence.json()['data']['spans']) == 4
