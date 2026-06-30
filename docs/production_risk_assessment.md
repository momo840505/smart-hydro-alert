# Production Risk Assessment

Smart Hydro Alert is a portfolio and academic prototype. This document explains the additional work required before a production deployment.

## Sensor Reliability

Risks:

- water-flow sensors may drift without calibration;
- FC-37 water-contact readings may be affected by splashes or cleaning;
- presence detection can be sensitive to placement and environment;
- hardware failures may create missing or stale readings.

Mitigations:

- calibration workflow per device;
- sensor heartbeat messages;
- stale-data detection;
- redundant readings for high-risk zones;
- maintenance logs for sensor replacement.

## False Positives and False Negatives

Risks:

- single-sensor triggers may create noisy alerts;
- short cleaning events may resemble leaks;
- low-flow leaks may not be detected by the flow sensor.

Mitigations:

- combined-sensor validation;
- configurable thresholds per facility;
- alert acknowledgement and feedback;
- historical event review;
- anomaly detection after enough labelled data is collected.

## Security

Risks:

- unauthenticated dashboards expose facility state;
- MQTT topics can be spoofed if the broker is open;
- Telegram tokens must not be committed;
- public deployments require network hardening.

Mitigations:

- API authentication;
- role-based access control;
- MQTT username/password or certificates;
- secret management;
- HTTPS-only deployments;
- audit logs for alert acknowledgement and configuration changes.

## Data Operations

Risks:

- MongoDB can grow without retention rules;
- event history may need privacy review depending on location;
- outages can create missing records.

Mitigations:

- retention policy;
- backup and restore testing;
- monitoring for backend, broker, and database health;
- queueing or retry strategy for temporary database outages.

## Product Extensions

Production-ready extensions include:

- multi-building and multi-device management;
- alert acknowledgement workflow;
- technician assignment;
- mobile-first dashboard;
- threshold configuration UI;
- sensor calibration tools;
- automatic shut-off valve integration;
- long-term water-waste analytics.
