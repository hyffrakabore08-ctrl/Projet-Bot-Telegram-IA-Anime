FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory for persistent SQLite storage
RUN mkdir -p /data

EXPOSE 7860

CMD ["python", "app/main.py"]
