FROM python:3.11

COPY . .
RUN pip3 install .
CMD ["python3", "-m", "uvicorn", "rdtsserver.main:rdts_app", "--host", "0.0.0.0"]
