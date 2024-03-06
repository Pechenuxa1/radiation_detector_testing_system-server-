from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Security, HTTPException, status
import os
from dotenv import load_dotenv

from server.rdtsserver.db.tables import RDTSDatabase
from server.rdtsserver.dependencies import engine, get_session
from server.rdtsserver.routers import assemblies, crystals, crystalstates, testsuites, testsuiteresults
from server.rdtsserver.utils.security import get_api_key


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    RDTSDatabase.metadata.create_all(engine)
    yield


rdts_app = FastAPI(title="RDTS Server", version="1.0.1", lifespan=lifespan)
rdts_app.include_router(assemblies.router,
                        prefix="/assemblies",
                        tags=["assemblies"],
                        dependencies=[Depends(get_session)])
rdts_app.include_router(crystals.router,
                        prefix="/crystals",
                        tags=["crystals"],
                        dependencies=[Depends(get_session)])
rdts_app.include_router(crystalstates.router,
                        prefix="/crystalstates",
                        tags=["crystalstates"],
                        dependencies=[Depends(get_session)])
rdts_app.include_router(testsuites.router,
                        prefix="/testsuites",
                        tags=["testsuites"],
                        dependencies=[Depends(get_session)])
rdts_app.include_router(testsuiteresults.router,
                        prefix="/testsuiteresults",
                        tags=["testsuiteresults"],
                        dependencies=[Depends(get_session)])


@rdts_app.get("/health")
def health() -> str:
    return "Server is running!"


load_dotenv('server/rdtsserver/config.env')


@rdts_app.get("/private")
def private(api_key: str = Security(get_api_key)):
    return f"API Key: {api_key}"
