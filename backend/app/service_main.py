"""Role-specific FastAPI applications used by Docker Compose."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import initialize_database
from .routes import telemetry, query, demo, system, services, reports

initialize_database()
kind=os.getenv('SERVICE_KIND','query')
app=FastAPI(title=f'Distributed Observability {kind.title()} Service',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
if kind=='ingestion': app.include_router(telemetry.router); app.include_router(demo.router)
if kind=='query':
    app.include_router(query.router); app.include_router(system.router); app.include_router(services.router); app.include_router(reports.router)
@app.get('/health')
def health(): return {'status':'healthy','service':kind}
@app.get('/ready')
def ready(): return {'status':'ready','service':kind}
