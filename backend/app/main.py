from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import initialize_database
from .routes import telemetry,query,demo,system,services,reports
initialize_database()
app=FastAPI(title='Distributed Observability Platform',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
app.include_router(telemetry.router); app.include_router(query.router)
app.include_router(demo.router)
app.include_router(system.router); app.include_router(services.router); app.include_router(reports.router)
@app.get('/health')
def health(): return {'status':'healthy'}
@app.get('/ready')
def ready(): return {'status':'ready'}
