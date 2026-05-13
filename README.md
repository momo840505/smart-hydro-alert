# Smart Hydro Alert

FastAPI backend for an IoT smart water monitoring system. Subscribes to MQTT messages
from ESP32 devices, stores readings in MongoDB, detects abnormal water-usage events
(water flowing ≥ 5 min with no human present), and pushes real-time updates to a
React dashboard via WebSocket.


---

## Project Structure

```text
5.backend/
├── app/
│   ├── api/                          # REST + WebSocket routers
│   │   ├── alerts.py                 # GET /api/alerts
│   │   ├── devices.py                # POST /register, GET /live, GET /history
│   │   └── websocket.py              # /ws/devices/{device_id}
│   │
│   ├── core/
│   │   └── config.py                 # Settings (pydantic-settings, reads .env)
│   │
│   ├── database/
│   │   ├── collections.py            # MongoDB collection name constants
│   │   └── mongodb.py                # Motor client + Beanie init / teardown
│   │
│   ├── models/
│   │   ├── alert.py                  # Beanie Document — alerts collection
│   │   ├── device.py                 # Beanie Document — devices collection
│   │   ├── sensor.py                 # Beanie Document — sensor_logs collection
│   │   └── payloads.py               # Pydantic models for MQTT/API payloads
│   │
│   ├── mqtt/
│   │   ├── client.py                 # aiomqtt subscriber w/ reconnect loop
│   │   ├── handlers.py               # Validate → route messages to services
│   │   └── topics.py                 # Topic parsing helpers
│   │
│   ├── services/
│   │   ├── alert_service.py          # Alert rule + duplicate prevention
│   │   ├── device_service.py         # Device register / touch / status
│   │   ├── notification_service.py   # Telegram Bot notifications
│   │   ├── sensor_service.py         # Sensor log storage + history queries
│   │   └── websocket_manager.py      # WS connection registry + broadcast
│   │
│   └── main.py                       # FastAPI app + lifespan (DB, MQTT)
│
├── simulator/                        # Mock ESP32 — publishes MQTT for end-to-end testing
│   ├── __main__.py                   # CLI: python -m simulator <scenario>
│   ├── config.py                     # Reads MQTT_* env vars from .env
│   ├── publisher.py                  # aiomqtt connect + publish helpers
│   └── scenarios.py                  # leak / normal / intermittent / multi
│
├── frontend/                         # Minimal dashboard (static HTML/CSS/JS)
│   └── index.html                    # Live device status + alerts table
│
├── tests/
│   ├── test_alert_logic.py           # Alert rule unit tests
│   ├── test_payloads.py              # Pydantic schema tests
│   └── test_topics.py                # MQTT topic parsing tests
│
├── docker/
│   └── mosquitto.conf                # MQTT broker config (anonymous, port 1883)
│
├── README.md                         # This file
├── Dockerfile                        # Backend + simulator image
├── docker-compose.yml                # Mongo + Mosquitto + Backend + Simulator
├── .dockerignore
├── .env.example                      # Env var template (copy to .env)
├── .gitignore
├── environment.yml                   # Conda env spec
├── pyproject.toml                    # ruff + black + pytest config
└── requirements.txt                  # pip dependencies
```

---

## Prerequisites

Pick **one** of two paths:

- **Docker path (recommended for testing)** — only Docker Desktop required. Everything else runs in containers via the provided `docker-compose.yml`.
- **Local path (no Docker)** — install MongoDB and Mosquitto natively, run the backend in a local conda env.

| Tool | Docker path | Local path |
|---|---|---|
| Docker Desktop | required | -- |
| Anaconda / Miniconda | -- | required |
| Python 3.11 | -- | via conda |
| MongoDB 5.0+ | container | local install or Atlas |
| Mosquitto 2.0+ | container | local install |

---

## Quickstart with Docker (recommended)

This starts MongoDB, Mosquitto, and the backend all in one command. The simulator
runs on demand via `docker compose run`.

### 1. Build and start the services

```bash
docker compose up --build
```

Or, to run in the background:

```bash
docker compose up -d --build
```

On startup you should see:

- `smartwater-mongo` ready and accepting connections on `localhost:27017`
- `smartwater-mosquitto` listening on `localhost:1883`
- `smartwater-backend` log: `mongo connected`, `mqtt connected`, `Uvicorn running on http://0.0.0.0:8000`
- `smartwater-frontend` serving the dashboard on `localhost:3000`

Open in your browser:

- **Dashboard:** http://localhost:3000 — live device status + alerts table
- **API docs (Swagger):** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health

### 2. Run a simulator scenario (in a separate terminal)

The `simulator` service is gated behind the `tools` profile so it doesn't auto-start.
Invoke it as a one-shot:

```bash
# leak: should fire one alert at tick 300
docker compose --profile tools run --rm simulator leak --device-id device01 --duration 310 --tick 0.1

# normal: no alert expected
docker compose --profile tools run --rm simulator normal --device-id device02 --duration 60 --tick 0.1

# multi-device: device 0 leaks, others normal
docker compose --profile tools run --rm simulator multi --count 4 --duration 320 --tick 0.1
```

While the simulator runs, the backend container's log will show every received message and the alert when it fires.

### 3. Verify the pipeline

From your host machine (host ports are mapped through):

```bash
# List alerts
curl http://localhost:8000/api/alerts

# Live device state
curl http://localhost:8000/api/devices/device01/live

# Recent sensor history
curl "http://localhost:8000/api/devices/device01/history?limit=5"
```

Or open http://localhost:8000/docs and try the endpoints in Swagger UI.

### 4. Stop / clean up

```bash
# Stop the stack (keeps data volumes)
docker compose down

# Stop AND delete Mongo + Mosquitto data
docker compose down -v
```

### Useful Docker commands

```bash
# Tail backend logs
docker compose logs -f backend

# Tail Mosquitto logs (see every published message broker-side)
docker compose logs -f mosquitto

# Open a shell inside the backend container
docker compose exec backend bash

# Open a Mongo shell
docker compose exec mongo mongosh smart_water
```

> **Hot reload:** the compose file bind-mounts `./app` and `./simulator` into the
> backend container, and uvicorn runs with `--reload`, so code edits take effect
> without a rebuild. Rebuild only when `requirements.txt` changes:
> `docker compose up -d --build backend`.

---

## Getting Started (local path, without Docker)

### 1. Create the local conda env (one-time)

The `.conda/` directory at the project root is a **prefix env** — isolated to this project.

```bash
conda create --prefix ./.conda python=3.11 pip -y
./.conda/python.exe -m pip install -r requirements.txt
```

Or, using the provided `environment.yml`:

```bash
conda env create --prefix ./.conda -f environment.yml
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Then edit `.env` and set at minimum:

- `MONGO_URI` — MongoDB connection string
- `MQTT_HOST` / `MQTT_PORT` — Mosquitto broker
- `JWT_SECRET` — replace with a long random string
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` — optional, leave empty to disable notifications

### 3. Start the dependencies

You need **MongoDB** and **Mosquitto** running locally before the backend starts.

Quick option — Docker:

```bash
docker run -d --name mongo -p 27017:27017 mongo:7
docker run -d --name mosquitto -p 1883:1883 eclipse-mosquitto:2 \
  mosquitto -c /mosquitto-no-auth.conf
```

### 4. Activate the env

```bash
conda activate ./.conda
```

Or skip activation and call the binaries by path:

- Windows: `.\.conda\Scripts\uvicorn.exe ...`
- macOS / Linux: `./.conda/bin/uvicorn ...`

### 5. Run the backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On startup, the backend will:

1. Connect to MongoDB and initialise Beanie ODM
2. Start the MQTT subscriber as a background task
3. Subscribe to `home/+/+/sensor`, `home/+/+/alert`, `home/+/+/status`
4. Serve REST + WebSocket endpoints on port `8000`

Once running:

- API docs (Swagger): http://localhost:8000/docs
- API docs (ReDoc): http://localhost:8000/redoc
- Health check: http://localhost:8000/health

---

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET`  | `/health` | Liveness probe |
| `POST` | `/api/devices/register` | Register a new ESP32 device |
| `GET`  | `/api/devices/{device_id}/live` | Latest live state |
| `GET`  | `/api/devices/{device_id}/history` | Sensor log history (filter by `start_time`, `end_time`, `limit`) |
| `GET`  | `/api/alerts` | Alert history (filter by `device_id`, `start_time`, `end_time`, `limit`) |
| `WS`   | `/ws/devices/{device_id}` | Live `sensor_update` / `alert_created` / `device_status` events |

---

## Testing the Pipeline End-to-End

The `simulator/` package mocks an ESP32 publishing MQTT — use it to exercise the
full backend pipeline without any hardware.

### Prerequisites

The backend, MongoDB, and Mosquitto must be running. The simulator uses the same
`MQTT_HOST` / `MQTT_PORT` / `MQTT_USERNAME` / `MQTT_PASSWORD` from `.env` as the
backend.

### Available scenarios

| Scenario | What it does | Expected backend outcome |
|---|---|---|
| `leak` | Water flowing, no human, duration counter incrementing | Alert fires at `running_duration_sec == 300` |
| `normal` | Random water/human, mostly human present | No alert |
| `intermittent` | Water cycles on/off, human always present | No alert |
| `multi` | Multiple devices concurrently (device 0 = leak, rest = normal) | One alert (from device 0) |

### Run a scenario

```bash
# Fastest end-to-end alert test: tick every 100ms, simulate 310 "seconds" in ~31s real time
python -m simulator leak --device-id device01 --location bathroom --duration 310 --tick 0.1

# Normal usage
python -m simulator normal --device-id device02 --duration 60

# Cycling water with human present
python -m simulator intermittent --device-id device03 --duration 60

# Multiple devices at once
python -m simulator multi --count 4 --duration 320 --tick 0.1
```

> **Note on `--tick`**: it's the wall-clock interval between sensor messages. The
> `running_duration_sec` field still increments by 1 per tick, so a small tick
> compresses the simulation. With `--tick 0.1`, the 300-second alert threshold is
> reached in 30 seconds of real time.

### What to look for

When `leak` runs against a live backend:

1. Backend log shows `sensor → ...` lines as it ingests each message.
2. At tick #300, backend log shows `alert created: device=device01 duration=300s strength=LOW`.
3. MongoDB: `sensor_logs` has 300+ documents, `alerts` has 1 document, `devices.device01.active_alert_at` is non-null.
4. WebSocket clients on `/ws/devices/device01` receive a stream of `sensor_update` events plus one `alert_created` event.
5. If Telegram is configured: a message arrives in your chat.

### Watching the backend reactions

In a third terminal, tail the alerts collection or hit the API:

```bash
# Open API docs and try GET /api/alerts
http://localhost:8000/docs

# Or via curl
curl http://localhost:8000/api/alerts | jq

# Or subscribe to WebSocket (using websocat or similar)
websocat ws://localhost:8000/ws/devices/device01
```

### Manual one-off publish (without the simulator)

If you just want to fire a single message:

```bash
mosquitto_pub -h localhost -t home/bathroom/device01/sensor -m '{
  "device_id": "device01",
  "timestamp": 1778926532,
  "water_flow": true,
  "human_present": false,
  "running_duration_sec": 301
}'
```

---

## Development Commands

Run from the project root with the conda env active.

```bash
# Run tests
pytest -q

# Lint
ruff check app tests

# Auto-fix lint
ruff check --fix app tests

# Format
black app tests
```

---

## Notes

- All timestamps in MQTT payloads and database documents are **Unix epoch seconds (UTC)** as integers — see [`schemas.md`](schemas.md).
- The duplicate-alert prevention uses `Device.active_alert_at` in MongoDB, so it survives backend restarts.
- The MQTT subscriber reconnects with exponential backoff (1s → 30s cap).
- For multi-instance deployments, the in-memory `WebSocketManager` would need a pub/sub backend (e.g. Redis); single-instance is fine for development.

## React Frontend Dashboard

This project includes a Vite + React dashboard for the Smart Water Monitoring and Alert System.

The dashboard visualises live IoT data from the backend and shows whether the system has detected abnormal water usage. It is designed for the Group 4 demo and connects the ESP32/MQTT/backend pipeline to a clear web interface.

### Dashboard Features

The React dashboard displays:

- backend connection status
- selected device ID
- live water flow status
- live human presence status
- current running duration
- latest flow rate
- active alert status
- abnormal water usage alert history
- system logic summary
- demo scenario explanation
- IoT architecture flow

The dashboard also refreshes automatically every few seconds and includes a manual **Sync Dashboard** button.

### Frontend Location

The React frontend is located in:

```text
frontend-react/
```

Main frontend files:

```text
frontend-react/src/App.jsx
frontend-react/src/App.css
```

### Backend API Used by the Dashboard

The dashboard connects to the FastAPI backend using these endpoints:

```text
GET /health
GET /api/devices/{device_id}/live
GET /api/devices/{device_id}/history?limit=1
GET /api/alerts?device_id={device_id}
```

For the current demo, the default device is:

```text
device01
```

### Run the Backend Services

From the project root:

```powershell
docker compose up -d
```

Check running containers:

```powershell
docker compose ps
```

The main services should include:

```text
smartwater-mosquitto
smartwater-mongo
smartwater-backend
```

### Run the React Frontend

From the project root:

```powershell
cd frontend-react
npm install
npm run dev
```

Then open the dashboard in the browser:

```text
http://localhost:5173
```

### Run Demo Simulator Scenarios

From the project root, run simulator commands in a separate terminal.

#### Leak / abnormal water usage scenario

```powershell
docker compose --profile tools run --rm simulator leak --device-id device01 --duration 310 --tick 0.1
```

This simulates water running while no human is detected. Once the running duration reaches 300 seconds, the backend records a `WATER_RUNNING_NO_HUMAN` alert.

Expected dashboard result:

```text
Water Flow: YES
Human Present: NO
Running Duration: 300s or above
Active Alert: YES
Alert History: new WATER_RUNNING_NO_HUMAN event
```

#### Normal usage scenario

```powershell
docker compose --profile tools run --rm simulator normal --device-id device01 --duration 60 --tick 0.1
```

This is used to test normal system behaviour where the alert condition should not be triggered.

#### Intermittent usage scenario

```powershell
docker compose --profile tools run --rm simulator intermittent --device-id device01 --duration 120 --tick 0.1
```

This is used to test changing sensor readings and confirm that short or interrupted usage does not create the same continuous abnormal usage alert.

### Alert Rule

The current alert rule is:

```text
water_flow = true
human_present = false
running_duration_sec >= 300
```

When this condition is met, the backend records an abnormal water usage alert.

Current alert type:

```text
WATER_RUNNING_NO_HUMAN
```

### Notes for Demo

The dashboard is connected to the backend API, not directly to MQTT. The data flow is:

```text
ESP32 / Simulator → MQTT Broker → FastAPI Backend → MongoDB → React Dashboard
```

The frontend is mainly responsible for displaying live status and alert history clearly. Alert creation and severity logic are handled by the backend.