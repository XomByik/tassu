FROM python:3.11-slim

# Inštalácia PostgreSQL klienta pre psql príkaz
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Inštalácia Python závislostí
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["bash"]
