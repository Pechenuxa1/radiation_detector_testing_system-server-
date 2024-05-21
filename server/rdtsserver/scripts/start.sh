#!/bin/bash

python3 -m uvicorn server.rdtsserver.main:main_app --host 0.0.0.0

python3 server/rdtsserver/scripts/create_roles.py

python3 server/rdtsserver/scripts/create_admin.py