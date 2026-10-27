"""Thin API gateway: validates route ownership, forwards requests, and returns bounded upstream failures."""
import os
import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware

INGESTION_URL=os.getenv('INGESTION_URL','http://ingestion:8000')
QUERY_URL=os.getenv('QUERY_URL','http://query:8000')
ORDER_URL=os.getenv('ORDER_URL','http://order-service:8000')
app=FastAPI(title='Observability API Gateway',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
@app.get('/health')
def health(): return {'status':'healthy','service':'api-gateway'}
@app.api_route('/api/v1/{path:path}',methods=['GET','POST','PATCH'])
async def route(path:str,request:Request):
    upstream=INGESTION_URL if path.startswith(('telemetry/','demo/')) else ORDER_URL if path.startswith('orders') else QUERY_URL
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            result=await client.request(request.method,f'{upstream}/api/v1/{path}',params=request.query_params,content=await request.body(),headers={'content-type':request.headers.get('content-type','application/json'),'x-correlation-id':request.headers.get('x-correlation-id','')})
        return Response(content=result.content,status_code=result.status_code,media_type=result.headers.get('content-type'))
    except httpx.TimeoutException: raise HTTPException(504,{'code':'UPSTREAM_TIMEOUT','service':upstream})
    except httpx.HTTPError: raise HTTPException(503,{'code':'UPSTREAM_UNAVAILABLE','service':upstream})
