FROM python:3.11

COPY /server /server
#WORKDIR /server

RUN pip3 install ./server
#RUN pip install --upgrade pydantic
#RUN pip install --upgrade sqlmodel
CMD ["python3", "-m", "uvicorn", "server.rdtsserver.main:rdts_app", "--host", "0.0.0.0"]
