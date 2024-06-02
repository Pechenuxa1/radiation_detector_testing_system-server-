FROM python:3.11

COPY /server /server
#WORKDIR /server
ENV PYTHONPATH "${PYTHONPATH}:/server"
RUN pip3 install ./server
RUN pip install --upgrade pydantic
RUN pip install --upgrade sqlmodel
RUN pip install --upgrade "passlib[bcrypt]"
RUN pip install --upgrade "python-jose[cryptography]"
CMD ["python3", "-m", "uvicorn", "server.rdtsserver.main:main_app", "--host", "0.0.0.0"]


#ENV PYTHONPATH "${PYTHONPATH}:/server"
#CMD ["sh", "server/rdtsserver/scripts/start.sh"]
#CMD ["sh", "-c", "python3 -m uvicorn server.rdtsserver.main:main_app --host 0.0.0.0 && python3 server/rdtsserver/scripts/create_roles.py && python3 server/rdtsserver/scripts/create_admin.py"]
#CMD ["python3", "server/rdtsserver/scripts/create_roles.py"]
#CMD ["python3", "server/rdtsserver/scripts/create_admin.py"]