from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from dotenv import load_dotenv

from server.rdtsserver.db.tables import RDTSDatabase
from server.rdtsserver.dependencies import engine, get_session
from server.rdtsserver.routers import assemblies, crystals, crystalstates, testsuites, testsuiteresults
from server.rdtsserver.versions.v1.v1_0_1 import app_1_0_1
#from server.rdtsserver.versions.v1.v1_0_2 import app_1_0_2


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    RDTSDatabase.metadata.create_all(engine)
    yield

main_app = FastAPI(title="RDTS Server", lifespan=lifespan)
'''
main_app = FastAPI(title="RDTS Server", version="1.0.1", lifespan=lifespan)
main_app.include_router(assemblies.router,
                        prefix="/assemblies",
                        tags=["assemblies"],
                        dependencies=[Depends(get_session)])
main_app.include_router(crystals.router,
                        prefix="/crystals",
                        tags=["crystals"],
                        dependencies=[Depends(get_session)])
main_app.include_router(crystalstates.router,
                        prefix="/crystalstates",
                        tags=["crystalstates"],
                        dependencies=[Depends(get_session)])
main_app.include_router(testsuites.router,
                        prefix="/testsuites",
                        tags=["testsuites"],
                        dependencies=[Depends(get_session)])
main_app.include_router(testsuiteresults.router,
                        prefix="/testsuiteresults",
                        tags=["testsuiteresults"],
                        dependencies=[Depends(get_session)])
'''
ACTUAL_API_VERSION = "/v1.0.2"

main_app.mount("/v1.0.1", app_1_0_1)
#main_app.mount("/v1.0.2", app_1_0_2)


@main_app.get("/actual_api")
def actual_api():
    return {"version": f"Actual server version is {ACTUAL_API_VERSION}"}


@main_app.get("/health")
def health() -> str:
    return "Server is running!"


load_dotenv('server/rdtsserver/config.env')
