FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

COPY Bot_memorizer.py .

CMD ["/bin/bash", "-c", "python bot.py"]
