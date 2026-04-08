from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.mongo import close_mongo_connection, connect_to_mongo
from app.services.seed_service import ensure_indexes, seed_initial_data

settings = get_settings()
setup_logging(settings.debug)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    await ensure_indexes()
    await seed_initial_data()
    yield
    await close_mongo_connection()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version='1.0.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def _health_payload():
    return {'status': 'ok', 'service': settings.app_name}


@app.api_route('/', methods=['GET', 'HEAD'])
@app.api_route('/health', methods=['GET', 'HEAD'])
async def health(request: Request):
    if request.method == 'HEAD':
        return Response(status_code=200, headers={'Cache-Control': 'no-store'})
    return JSONResponse(_health_payload(), headers={'Cache-Control': 'no-store'})


app.include_router(api_router)
