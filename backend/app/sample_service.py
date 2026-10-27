"""Order, Payment and Notification sample services used by the Compose E2E path."""
import os, time
from datetime import datetime, timedelta
from uuid import uuid4
import httpx
from fastapi import FastAPI, Header, HTTPException

NAME=os.getenv('SAMPLE_SERVICE','order-service')
INGESTION_URL=os.getenv('INGESTION_URL','http://ingestion:8000/api/v1/telemetry')
PAYMENT_URL=os.getenv('PAYMENT_URL','http://payment-service:8000')
NOTIFICATION_URL=os.getenv('NOTIFICATION_URL','http://notification-service:8000')
app=FastAPI(title=NAME)

async def emit(trace_id,span_id,parent,operation,start,status='OK',error=None):
    end=datetime.utcnow(); payload={'event_id':uuid4().hex,'trace_id':trace_id,'span_id':span_id,'parent_span_id':parent,'service_name':NAME,'operation_name':operation,'start_time':start.isoformat(),'end_time':end.isoformat(),'status':status,'error_message':error}
    metric={'event_id':uuid4().hex,'service_name':NAME,'metric_name':'request_latency_ms','metric_value':(end-start).total_seconds()*1000,'recorded_at':end.isoformat()}
    async with httpx.AsyncClient(timeout=3) as client:
        await client.post(f'{INGESTION_URL}/traces',json=payload);await client.post(f'{INGESTION_URL}/metrics',json=metric)
        if error: await client.post(f'{INGESTION_URL}/logs',json={'event_id':uuid4().hex,'service_name':NAME,'message':error,'severity':'ERROR','timestamp':end.isoformat(),'trace_id':trace_id,'span_id':span_id})

@app.get('/health')
def health():return {'status':'healthy','service':NAME}

@app.post('/api/v1/orders')
async def order(scenario:str='normal'):
    if NAME!='order-service':raise HTTPException(404,'Not an order service')
    trace_id,span_id,start=uuid4().hex,uuid4().hex,datetime.utcnow()
    try:
        async with httpx.AsyncClient(timeout=4) as client: result=await client.post(f'{PAYMENT_URL}/internal/payment',params={'scenario':scenario},headers={'x-trace-id':trace_id,'x-parent-span-id':span_id})
        if result.status_code>=400: raise HTTPException(result.status_code,result.text)
        await emit(trace_id,span_id,None,'create_order',start);return {'trace_id':trace_id,'status':'created'}
    except Exception as exc:
        await emit(trace_id,span_id,None,'create_order',start,'ERROR',str(exc));raise

@app.post('/internal/payment')
async def payment(scenario:str='normal',x_trace_id:str=Header(...),x_parent_span_id:str=Header(...)):
    if NAME!='payment-service':raise HTTPException(404,'Not a payment service')
    span_id,start=uuid4().hex,datetime.utcnow()
    if scenario in {'payment_failure','invalid_downstream','intermittent_unavailable'}:
        await emit(x_trace_id,span_id,x_parent_span_id,'charge',start,'ERROR','payment provider unavailable');raise HTTPException(502,'payment provider unavailable')
    if scenario=='slow_payment': time.sleep(1.2)
    try:
        async with httpx.AsyncClient(timeout=4) as client: result=await client.post(f'{NOTIFICATION_URL}/internal/notification',params={'scenario':scenario},headers={'x-trace-id':x_trace_id,'x-parent-span-id':span_id})
        if result.status_code>=400: raise HTTPException(result.status_code,result.text)
        await emit(x_trace_id,span_id,x_parent_span_id,'charge',start);return {'status':'paid'}
    except Exception as exc:
        await emit(x_trace_id,span_id,x_parent_span_id,'charge',start,'ERROR',str(exc));raise

@app.post('/internal/notification')
async def notification(scenario:str='normal',x_trace_id:str=Header(...),x_parent_span_id:str=Header(...)):
    if NAME!='notification-service':raise HTTPException(404,'Not a notification service')
    span_id,start=uuid4().hex,datetime.utcnow()
    if scenario=='notification_timeout': time.sleep(1.2);await emit(x_trace_id,span_id,x_parent_span_id,'send_receipt',start,'ERROR','notification timeout');raise HTTPException(504,'notification timeout')
    await emit(x_trace_id,span_id,x_parent_span_id,'send_receipt',start);return {'status':'sent'}
