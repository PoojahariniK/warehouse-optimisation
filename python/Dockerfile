FROM python:3.12

RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt && pip show pandas

COPY src/ ./src/
COPY datasets/ /app/datasets/

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.optimization_engine.main"]