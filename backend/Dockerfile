# ── IAmina Backend — Production Dockerfile ───────────────────────────────────
# Build:  docker build -t iamina-backend .
# Run:    docker run --env-file ../.env -p 8000:8000 iamina-backend
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: dependency install (layer-cached) ───────────────────────────────
FROM python:3.12-slim AS deps

WORKDIR /app

# System deps required by psycopg2-binary, Pillow, and firebase-admin
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime image ───────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Security: run as non-root
RUN addgroup --system iamina && adduser --system --ingroup iamina iamina

WORKDIR /app

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application source
COPY --chown=iamina:iamina . .

# Runtime system libs (psycopg2 needs libpq at runtime, not gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

USER iamina

# Collect static files (Django admin + any future assets).
# SECRET_KEY is required for settings to import; this throwaway value is scoped to
# this single build step only (not an ENV — never persisted into the image).
RUN SECRET_KEY=build-only-not-used-at-runtime python manage.py collectstatic --noinput

EXPOSE 8000

# Gunicorn: 2×CPU + 1 workers, gthread for async-friendly Django
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--worker-class", "gthread", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "amina.wsgi:application"]
