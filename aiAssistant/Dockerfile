FROM python:3.11

WORKDIR /aiAssistant

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y postgresql-client

COPY . .

ENV PYTHONPATH="/"


