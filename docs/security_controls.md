# Security Controls

This document defines practical security controls for a production-style IoT monitoring deployment.

## API Security

- Require authentication for dashboard and API access.
- Use role-based permissions for facility managers, technicians, and admins.
- Add audit logs for device reset, threshold changes, and incident status changes.
- Disable public write endpoints in production unless protected.

## MQTT Security

- Require MQTT username/password or client certificates.
- Use topic-level access controls so devices can publish only to their own topics.
- Validate that payload `device_id` matches the MQTT topic device segment.
- Reject stale timestamps and malformed payloads.

## Secret Management

- Keep Telegram bot token and chat ID in environment variables.
- Never commit `.env`.
- Rotate notification credentials if leaked.
- Use separate credentials for development and production.

## Data Protection

- Store only operational data needed for monitoring.
- Define retention rules for sensor logs and alert history.
- Avoid storing personally identifiable information unless required.
- Back up MongoDB and test restore procedures.

## Deployment Checklist

- HTTPS enabled.
- CORS locked to trusted dashboard origins.
- MongoDB not exposed publicly.
- MQTT broker not exposed without authentication.
- Docker images rebuilt from pinned dependencies.
- Health checks monitored for backend, broker, and database.
