from fastapi import FastAPI, Depends
from server.rdtsserver.dependencies import get_session

from server.rdtsserver.routers import assemblies, crystals, crystalstates, testsuites, testsuiteresults, auth

app_1_0_2 = FastAPI(version="1.0.2")
app_1_0_2.include_router(assemblies.router,
                   prefix="/assemblies",
                   tags=["assemblies"],
                   dependencies=[Depends(get_session)])
app_1_0_2.include_router(crystals.router,
                   prefix="/crystals",
                   tags=["crystals"],
                   dependencies=[Depends(get_session)])
app_1_0_2.include_router(crystalstates.router,
                   prefix="/crystalstates",
                   tags=["crystalstates"],
                   dependencies=[Depends(get_session)])
app_1_0_2.include_router(testsuites.router,
                   prefix="/testsuites",
                   tags=["testsuites"],
                   dependencies=[Depends(get_session)])
app_1_0_2.include_router(testsuiteresults.router,
                   prefix="/testsuiteresults",
                   tags=["testsuiteresults"],
                   dependencies=[Depends(get_session)])
app_1_0_2.include_router(auth.router,
                   prefix="/auth",
                   tags=["auth"],
                   dependencies=[Depends(get_session)])