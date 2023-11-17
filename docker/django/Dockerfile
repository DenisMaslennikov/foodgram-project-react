FROM python:3.10
WORKDIR /code
ENV PYTHONDONTWRITEBYTECODE=1\
    PYTHONUNBUFFERED=1
RUN pip install --upgrade pip
COPY ../../backend/requirements.txt .
RUN pip install -r requirements.txt
COPY ../../backend/. .

