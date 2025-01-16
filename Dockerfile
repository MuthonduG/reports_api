FROM python:3.10-slim

ENV PYTHONBUFFERED 1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy Django start script
COPY django.sh /app/django.sh
RUN chmod +x /app/django.sh

# Copy application code
COPY . .

EXPOSE 8000

# Start the Django server
ENTRYPOINT [ "/app/django.sh" ]
