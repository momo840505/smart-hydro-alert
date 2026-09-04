# Multi-stage build so a single Docker web service can serve both the API and the
# built React dashboard on the same origin -- same pattern as career-copilot-agent's
# Dockerfile. Stage 1 builds the frontend to static files; stage 2 is the Python
# runtime, with nothing else needed to deploy.

# ---- Stage 1: build the React frontend ----
FROM node:22-slim AS frontend-build
WORKDIR /build/frontend-react
COPY frontend-react/package.json frontend-react/package-lock.json* ./
RUN npm install
COPY frontend-react/ ./
# VITE_API_BASE="" makes every fetch() in App.jsx use a relative path, so it hits
# whatever origin the built page is served from instead of localhost:8000 -- see
# src/App.jsx's API_BASE constant.
ENV VITE_API_BASE=""

# Shared admin key for the dashboard's simulate/reset buttons (X-API-Key header --
# see app/core/security.py and src/App.jsx's ADMIN_API_KEY constant for the full
# reasoning: single-operator demo, deters casual abuse, not meant to withstand
# someone reading the public bundle). Render's Blueprint spec (render.yaml) has no
# way to pass a build-time argument into a `runtime: docker` service, only runtime
# env vars -- so this can't come from Render's ADMIN_API_KEY env var the way the
# backend's copy of it does. Baked in here as a build ARG with a default instead:
# works out of the box on Render, and can still be overridden locally with
# `docker build --build-arg VITE_ADMIN_API_KEY=...`. To rotate it, change the
# default below AND the ADMIN_API_KEY env var on the Render service to the same
# new value.
ARG VITE_ADMIN_API_KEY=ROTATED-KEY-REDACTED-see-current-Dockerfile-for-the-real-one
ENV VITE_ADMIN_API_KEY=$VITE_ADMIN_API_KEY

RUN npm run build

# ---- Stage 2: Python backend, serving the built frontend ----
FROM python:3.11-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
COPY simulator/ ./simulator/

# Built frontend from stage 1. app/main.py mounts this directory as static files (via
# FRONTEND_DIST_DIR) once it exists -- unset in local dev / docker-compose, where the
# separate nginx "frontend" service (or `npm run dev`) serves the dashboard instead.
COPY --from=frontend-build /build/frontend-react/dist ./frontend_dist
ENV FRONTEND_DIST_DIR=/app/frontend_dist

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
