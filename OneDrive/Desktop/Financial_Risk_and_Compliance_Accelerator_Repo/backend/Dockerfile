# ===============================
# STAGE 1 — Build dependencies
# ===============================
FROM python:3.10-slim AS builder

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install minimal system dependencies (compatible with Debian 13 "Trixie")
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ libopenblas-dev liblapack-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    -t /app/packages


# ===============================
# STAGE 2 — Runtime image
# ===============================
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/packages/bin:$PATH"

WORKDIR /app

# Copy installed dependencies
COPY --from=builder /app/packages /usr/local/lib/python3.10/site-packages

# Copy source files and models
COPY credit_deploy.py credit_main.py aml_main.py fraud_main.py ./
COPY derived_feature_names.json ./
COPY train_feature_names.json ./        
COPY models/ /app/models/
COPY data/ /data/

EXPOSE 5000

CMD ["python", "credit_deploy.py"]