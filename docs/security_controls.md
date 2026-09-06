# Security Notes

## Current Controls

The current project includes a few basic security checks:

* write endpoints use an `X-API-Key` outside local development
* CORS uses an explicit list of allowed origins
* MQTT payloads are validated with Pydantic
* MQTT topic device IDs are checked against payload device IDs
* stale timestamps are rejected
* oversized MQTT messages are rejected
* Telegram credentials are loaded from environment variables
* `.env` files are ignored by Git

## Demo Limitation

The hosted dashboard currently uses a shared key that is included in the frontend build.

This is useful for the demo, but it is not the same as real user authentication.

Anyone who can inspect the frontend bundle should not be treated as unable to discover that value.

## MQTT

The local Mosquitto setup currently does not use authentication or TLS.

For a real deployment I would add:

* device credentials
* TLS
* topic-level permissions
* separate credentials for each device

## Application Access

A larger system would also need:

* user login
* role-based permissions
* audit logs
* session handling

## Data

A real deployment should also define:

* database access rules
* backup procedures
* retention periods
* secret storage
* HTTPS configuration
