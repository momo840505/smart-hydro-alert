# Smart Hydro Alert

Smart Hydro Alert is an IoT water monitoring and leak alert prototype built for Group 4.

The system receives `0/1` sensor values from an ESP32 or simulator through MQTT, stores readings in MongoDB, applies backend decision logic, sends optional user notifications, and displays the current system state through a React dashboard.

The current prototype supports:

- real-time water flow monitoring
- human presence detection
- FC-37 / water-contact sensor detection
- abnormal water usage warning
- forgotten tap alert
- local leak detection
- critical leak / overflow detection
- LED output state
- buzzer output state
- optional Telegram user notification
- dashboard simulation without physical hardware

---

## Current Condition States

| Status | Meaning |
|---|---|
| `NORMAL` | No water flow and no local water contact |
| `NORMAL_FLOW` | Water is flowing while a human is present |
| `WARNING` | Water is flowing with no human present, but the duration is still below the alert threshold |
| `ALERT` | Water is flowing with no human present for too long |
| `LEAK` | FC-37 / water sensor detects local water contact while no water flow is detected |
| `CRITICAL` | Water flow and local water contact are both detected |

---

## Demo Time Logic

For the demo, the backend uses a scaled time rule:

```text
1 real second = 10 system seconds
30 real seconds = 300 system seconds
```

This means the 300-second abnormal-flow threshold can be demonstrated in about 30 seconds.

This rule applies to both:

```text
dashboard / backend simulation
real ESP32 sensor payloads
```

As long as the backend keeps receiving:

```text
water_flow = 1
human_present = 0
water_detected = 0
```

the backend will automatically calculate the running duration. After about 30 real seconds, the status changes from:

```text
WARNING → ALERT
```

---

## Project Structure

```text
IoT-group4/
├── app/
│   ├── api/
│   │   ├── alerts.py                 # Alert history API
│   │   ├── devices.py                # Device live, history, simulate, reset APIs
│   │   └── websocket.py              # WebSocket route for live device updates
│   │
│   ├── core/
│   │   └── config.py                 # App settings from environment variables
│   │
│   ├── database/
│   │   ├── collections.py            # MongoDB collection names
│   │   └── mongodb.py                # MongoDB / Beanie setup
│   │
│   ├── models/
│   │   ├── alert.py                  # Alert document model
│   │   ├── device.py                 # Device document model
│   │   ├── sensor.py                 # Sensor history document model
│   │   └── payloads.py               # MQTT/API payload schemas and status logic
│   │
│   ├── mqtt/
│   │   ├── client.py                 # MQTT subscriber client
│   │   ├── handlers.py               # MQTT message validation and routing
│   │   └── topics.py                 # MQTT topic parsing helpers
│   │
│   ├── services/
│   │   ├── alert_service.py          # ALERT / CRITICAL creation and duplicate prevention
│   │   ├── device_service.py         # Device state, backend timer, reset logic
│   │   ├── notification_service.py   # Telegram notification support
│   │   ├── sensor_service.py         # Sensor history storage
│   │   └── websocket_manager.py      # WebSocket connection manager
│   │
│   └── main.py                       # FastAPI app entry point
│
├── frontend-react/
│   ├── src/
│   │   ├── App.jsx                   # Main React dashboard
│   │   ├── App.css                   # Dashboard styles
│   │   ├── index.css                 # Global styles
│   │   └── main.jsx                  # React entry point
│   ├── package.json
│   └── vite.config.js
│
├── frontend/                         # Legacy static frontend
│   └── index.html
│
├── simulator/
│   ├── __main__.py                   # CLI simulator entry
│   ├── config.py
│   ├── publisher.py
│   └── scenarios.py
│
├── docker/
│   └── mosquitto.conf                # MQTT broker config
│
├── tests/
│   ├── test_alert_logic.py
│   ├── test_payloads.py
│   └── test_topics.py
│
├── README.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── environment.yml
├── pyproject.toml
├── .env.example
├── .gitignore
└── .dockerignore
```

---

## Sensor Payload Format

The backend uses `0/1` values for sensor data.

This is the format used by the code and dashboard.

| Field | 0 means | 1 means |
|---|---|---|
| `water_flow` | No water flow | Water flow detected |
| `human_present` | No human detected | Human detected |
| `water_detected` | FC-37 / water sensor is dry | Water contact detected |
| `alert` | No user alert required | User alert required |

Example payload:

```json
{
  "water_flow": 1,
  "human_present": 0,
  "water_detected": 1,
  "alert": 1,
  "status": "CRITICAL"
}
```

For real MQTT messages from ESP32, the full payload should also include `device_id` and `timestamp`.

Example MQTT payload:

```json
{
  "device_id": "device01",
  "timestamp": 1778926532,
  "water_flow": 1,
  "human_present": 0,
  "water_detected": 1,
  "alert": 1,
  "status": "CRITICAL",
  "running_duration_sec": 0,
  "flow_rate_lpm": 6.1
}
```

---

## Decision Logic

| Status | Sensor condition | LED output | Buzzer output | Notify user |
|---|---|---|---|---|
| `NORMAL` | `water_flow=0`, `water_detected=0` | Green | Off | No |
| `NORMAL_FLOW` | `water_flow=1`, `human_present=1`, `water_detected=0` | Blue | Off | No |
| `WARNING` | `water_flow=1`, `human_present=0`, duration below threshold | Yellow | Off | No |
| `ALERT` | `water_flow=1`, `human_present=0`, duration reaches threshold | Red | Intermittent | Yes |
| `LEAK` | `water_flow=0`, `water_detected=1` | White | Slow beep | No |
| `CRITICAL` | `water_flow=1`, `water_detected=1` | Red flashing | Continuous | Yes |

The backend creates remote user notifications only for:

```text
ALERT
CRITICAL
```

---

## MQTT Topics

The backend subscribes to these MQTT topic patterns:

```text
home/+/+/sensor
home/+/+/alert
home/+/+/status
```

Example sensor topic:

```text
home/bathroom/device01/sensor
```

Example status topic:

```text
home/bathroom/device01/status
```

Example alert topic:

```text
home/bathroom/device01/alert
```

---

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Backend health check |
| `POST` | `/api/devices/register` | Register or update a device |
| `GET` | `/api/devices` | List all devices |
| `GET` | `/api/devices/{device_id}/live` | Get latest live state for one device |
| `GET` | `/api/devices/{device_id}/history` | Get sensor history |
| `POST` | `/api/devices/{device_id}/simulate` | Send simulated `0/1` sensor values into the backend |
| `POST` | `/api/devices/{device_id}/reset?clear_logs=0` | Reset device state to normal |
| `POST` | `/api/devices/{device_id}/reset?clear_logs=1` | Reset device state and clear demo logs |
| `GET` | `/api/alerts` | Get alert history |
| `WS` | `/ws/devices/{device_id}` | Live WebSocket events |

---

## Prerequisites

Recommended setup:

| Tool | Purpose |
|---|---|
| Docker Desktop | Runs MongoDB, Mosquitto, backend, and optional frontend container |
| Node.js + npm | Runs the React/Vite dashboard locally |
| Git | Version control |

---

## Quickstart with Docker Backend + React Dev Server

This is the recommended setup for development and demo.

### 1. Start backend services

From the project root:

```powershell
cd C:\Users\momo8\Documents\GitHub\personal-clone\IoT-group4
docker compose up -d --build mongo mosquitto backend
```

Check running containers:

```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected containers:

```text
smartwater-mongo
smartwater-mosquitto
smartwater-backend
```

Backend URLs:

```text
Backend API: http://localhost:8000
Swagger docs: http://localhost:8000/docs
Health check: http://localhost:8000/health
```

### 2. Start React dashboard

Open a second PowerShell terminal:

```powershell
cd C:\Users\momo8\Documents\GitHub\personal-clone\IoT-group4\frontend-react
npm install
npm run dev
```

Then open the URL shown by Vite.

Usually:

```text
http://localhost:5173/
```

If port 5173 is already in use, Vite may show another port, for example:

```text
http://localhost:5174/
```

Use the port shown in the terminal.

---

## Docker Frontend Option

The `docker-compose.yml` can also serve the React build through Nginx on port `3000`.

Build the React frontend first:

```powershell
cd frontend-react
npm install
npm run build
cd ..
```

Then start the frontend container:

```powershell
docker compose up -d --build frontend
```

Open:

```text
http://localhost:3000/
```

For active development, use the Vite dev server on `5173` or `5174`.

For Docker demo serving, use `3000`.

---

## React Dashboard Features

The React dashboard shows:

- backend online/offline state
- selected device ID
- current system status
- flow sensor value
- human presence value
- FC-37 / water sensor value
- running duration
- LED output
- buzzer output
- notify user status
- simulation scenario buttons
- reset normal button
- clear demo button
- compact device history
- alert history
- technical backend values

Dashboard status colours:

| Status | Dashboard colour / visual |
|---|---|
| `NORMAL` | Green |
| `NORMAL_FLOW` | Blue |
| `WARNING` | Yellow |
| `ALERT` | Red |
| `LEAK` | White / light blue |
| `CRITICAL` | Red flashing |

---

## Dashboard Demo Buttons

The dashboard includes built-in scenario buttons.

| Button | Expected result |
|---|---|
| `Normal` | Green normal state |
| `Normal Flow` | Blue normal water usage |
| `Warning` | Yellow suspicious water usage |
| `Alert` | Red forgotten tap risk |
| `Leak` | White local water detection |
| `Critical` | Red flashing critical risk |
| `Reset Normal` | Return to normal state |
| `Clear Demo` | Reset state and clear demo logs |

Use `Reset Normal` before a simple demo.

Use `Clear Demo` before recording or presenting a clean full demo.

---

## PowerShell Dynamic Demo Tests

These tests send repeated backend simulation payloads. They are useful when no physical sensors are connected.

Open a new PowerShell terminal from the project root.

### Helper functions

```powershell
$base = "http://localhost:8000"
$device = "device01"

function Send-Sensor {
    param(
        [int]$Flow,
        [int]$Human,
        [int]$Water,
        [double]$Rate = 0
    )

    $body = @{
        water_flow = $Flow
        human_present = $Human
        water_detected = $Water
        alert = 0
        running_duration_sec = 0
        flow_rate_lpm = $Rate
    } | ConvertTo-Json -Compress

    Invoke-RestMethod `
        -Method Post `
        -Uri "$base/api/devices/$device/simulate" `
        -ContentType "application/json" `
        -Body $body
}

function Reset-Normal {
    Invoke-RestMethod `
        -Method Post `
        -Uri "$base/api/devices/$device/reset?clear_logs=0"
}

function Clear-Demo {
    Invoke-RestMethod `
        -Method Post `
        -Uri "$base/api/devices/$device/reset?clear_logs=1"
}
```

---

### A. Normal usage path: green → blue → green

```powershell
Clear-Demo

for ($i = 1; $i -le 3; $i++) {
    Send-Sensor 0 0 0 0
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 8; $i++) {
    Send-Sensor 1 1 0 3.2
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 3; $i++) {
    Send-Sensor 0 0 0 0
    Start-Sleep -Seconds 1
}
```

Expected dashboard result:

```text
NORMAL → NORMAL_FLOW → NORMAL
```

---

### B. Forgotten tap path: green → yellow → red

```powershell
Clear-Demo

for ($i = 1; $i -le 3; $i++) {
    Send-Sensor 0 0 0 0
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 35; $i++) {
    Send-Sensor 1 0 0 4.5
    Start-Sleep -Seconds 1
}
```

Expected dashboard result:

```text
NORMAL → WARNING → ALERT
```

The backend applies:

```text
1 real second = 10 system seconds
```

So after around 30 real seconds, the system reaches 300 system seconds and changes to `ALERT`.

---

### C. Local leak path: green → white → green

```powershell
Clear-Demo

for ($i = 1; $i -le 3; $i++) {
    Send-Sensor 0 0 0 0
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 10; $i++) {
    Send-Sensor 0 0 1 0
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 3; $i++) {
    Send-Sensor 0 0 0 0
    Start-Sleep -Seconds 1
}
```

Expected dashboard result:

```text
NORMAL → LEAK → NORMAL
```

---

### D. Local leak becomes critical: green → white → red flashing

```powershell
Clear-Demo

for ($i = 1; $i -le 3; $i++) {
    Send-Sensor 0 0 0 0
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 8; $i++) {
    Send-Sensor 0 0 1 0
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 10; $i++) {
    Send-Sensor 1 0 1 6.1
    Start-Sleep -Seconds 1
}
```

Expected dashboard result:

```text
NORMAL → LEAK → CRITICAL
```

---

### E. Full demo path: green → blue → yellow → red → red flashing

```powershell
Clear-Demo

for ($i = 1; $i -le 3; $i++) {
    Send-Sensor 0 0 0 0
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 6; $i++) {
    Send-Sensor 1 1 0 3.2
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 35; $i++) {
    Send-Sensor 1 0 0 4.5
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 10; $i++) {
    Send-Sensor 1 0 1 6.1
    Start-Sleep -Seconds 1
}
```

Expected dashboard result:

```text
NORMAL → NORMAL_FLOW → WARNING → ALERT → CRITICAL
```

---

## MQTT Simulator

The `simulator/` package mocks an ESP32 publishing MQTT messages.

Run simulator commands from the project root.

```powershell
docker compose --profile tools run --rm simulator leak --device-id device01 --duration 310 --tick 0.1
```

The `--tick` value controls the wall-clock interval between messages.

For older simulator scenarios:

```text
--tick 0.1
```

means one simulated second is sent every 0.1 real seconds.

The newer backend demo logic also supports:

```text
1 real second = 10 system seconds
```

for continuous abnormal flow when real or simulated sensor messages arrive repeatedly.

---

## Manual MQTT Publish

You can manually publish a sensor message through Mosquitto.

Example `NORMAL_FLOW` payload:

```powershell
$payload = @{
    device_id = "device01"
    timestamp = [int][double]::Parse((Get-Date -UFormat %s))
    water_flow = 1
    human_present = 1
    water_detected = 0
    alert = 0
    status = "NORMAL_FLOW"
    running_duration_sec = 0
    flow_rate_lpm = 3.2
} | ConvertTo-Json -Compress

docker exec smartwater-mosquitto mosquitto_pub `
    -h localhost `
    -t home/bathroom/device01/sensor `
    -m $payload
```

Example `CRITICAL` payload:

```powershell
$payload = @{
    device_id = "device01"
    timestamp = [int][double]::Parse((Get-Date -UFormat %s))
    water_flow = 1
    human_present = 0
    water_detected = 1
    alert = 1
    status = "CRITICAL"
    running_duration_sec = 0
    flow_rate_lpm = 6.1
} | ConvertTo-Json -Compress

docker exec smartwater-mosquitto mosquitto_pub `
    -h localhost `
    -t home/bathroom/device01/sensor `
    -m $payload
```

---

## Telegram Notification

The backend can send Telegram notifications for:

```text
ALERT
CRITICAL
```

Do not hard-code Telegram credentials in `docker-compose.yml`.

Use environment variables instead.

Create a `.env` file from `.env.example`:

```powershell
copy .env.example .env
```

Then set:

```text
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Leave them empty if Telegram notification is not needed.

Important:

```text
Do not commit .env to GitHub.
```

---

## Useful Docker Commands

```powershell
docker compose ps
```

```powershell
docker compose logs -f backend
```

```powershell
docker compose logs -f mosquitto
```

```powershell
docker compose restart backend
```

```powershell
docker compose down
```

```powershell
docker compose down -v
```

Open Mongo shell:

```powershell
docker exec -it smartwater-mongo mongosh smart_water
```

Clear demo data manually:

```powershell
docker exec -it smartwater-mongo mongosh smart_water --eval "db.sensor_logs.deleteMany({}); db.alerts.deleteMany({}); db.devices.deleteMany({});"
```

---

## Development Commands

Run tests:

```powershell
pytest -q
```

Run lint:

```powershell
ruff check app tests
```

Format code:

```powershell
black app tests
```

Build React dashboard:

```powershell
cd frontend-react
npm run build
cd ..
```

---

## Data Flow

The system data flow is:

```text
ESP32 / Simulator
        ↓
MQTT Broker
        ↓
FastAPI Backend
        ↓
MongoDB
        ↓
React Dashboard
        ↓
LED / Buzzer / User Notification Display
```

The frontend does not decide the real alert state.  
The backend handles sensor validation, status classification, duration timing, alert creation, and notification logic.

The dashboard displays the backend state clearly for demo and monitoring.