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
# see app/core/security.py and src/App.jsx's ADMIN_API_KEY constant). Render's
# Blueprint spec (render.yaml) has no way to pass a build-time argument into a
# `runtime: docker` service (confirmed against Render's docs -- there is no
# buildArgs/dockerBuildArgs field), only runtime env vars, so a default has to
# live here for the zero-config Render deploy to work at all.
#
# IMPORTANT -- this value is NOT a secret and must never be treated as one:
# it ships inside the built frontend's public JS bundle regardless of where it
# comes from, so anyone can read it out of the deployed site's devtools whether
# or not it's also in this file. Its only job is to stop the write endpoints
# from being wide open to literally anyone with curl; it is not meant to
# withstand a motivated reader, and a real access-control story (per-user
# login, RBAC) is listed as a limitation in the README/production risk
# assessment. Do not reuse this value anywhere it *would* need to be secret
# (e.g. do not also make it a real user password) -- generate a fresh one with
# the command in .env.example if you rotate it, and update the ADMIN_API_KEY
# env var on the Render service to the same new value at the same time.
ARG VITE_ADMIN_API_KEY=dHljEUAQ1kMe0K_WdZxCWACn-Dyykepu3i7dWIut6BY
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
