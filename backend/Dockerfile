# ---- Base stage ----
FROM python:3.11-slim AS base

WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ---- Dependencies stage ----
FROM base AS deps

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Development stage ----
FROM deps AS dev

COPY . .

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"]

# ---- Production stage ----
FROM deps AS prod

# Create non-root user
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser

COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

USER appuser

EXPOSE 8003

ENTRYPOINT ["./entrypoint.sh"]
