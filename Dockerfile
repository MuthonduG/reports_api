FROM python:3.10-slim

ENV PYTHONBUFFERED 1

WORKDIR /app

COPY requirements.txt .

COPY django.sh /app/django.sh

RUN pip install -r requirements.txt

RUN chmod +x /app/django.sh

COPY . .

EXPOSE 8000

ENTRYPOINT [ "/app/django.sh" ]
