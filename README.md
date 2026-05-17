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
- optional user notification
- dashboard simulation without physical hardware
- estimated water waste for report and demo purposes

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
│   │   ├── alerts.py
│   │   ├── devices.py
│   │   └── websocket.py
│   ├── core/
│   │   └── config.py
│   ├── database/
│   │   ├── collections.py
│   │   └── mongodb.py
│   ├── models/
│   │   ├── alert.py
│   │   ├── device.py
│   │   ├── sensor.py
│   │   └── payloads.py
│   ├── mqtt/
│   │   ├── client.py
│   │   ├── handlers.py
│   │   └── topics.py
│   ├── services/
│   │   ├── alert_service.py
│   │   ├── device_service.py
│   │   ├── notification_service.py
│   │   ├── sensor_service.py
│   │   └── websocket_manager.py
│   └── main.py
│
├── frontend-react/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── frontend/
│   └── index.html
│
├── simulator/
│   ├── __main__.py
│   ├── config.py
│   ├── publisher.py
│   └── scenarios.py
│
├── docker/
│   └── mosquitto.conf
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
  "flow_rate_lpm": 0.4
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

## Flow Rate and Estimated Water Waste

The YF-S201 flow sensor provides pulse-based water flow information.

The common calculation is:

```text
Flow rate (L/min) = pulse frequency / 7.5
```

For this prototype, the flow rate is used only as an estimate for reporting and dashboard display. It is not used as the main alert trigger.

The dashboard estimates water waste using:

```text
Estimated water waste (L) = flow rate (L/min) × duration (min)
```

Since the backend stores duration in seconds, the calculation is:

```text
Estimated water waste (L) = flow_rate_lpm × running_duration_sec / 60
```

Example:

```text
flow_rate_lpm = 0.40 L/min
running_duration_sec = 300 sec = 5 min

Estimated water waste = 0.40 × 5 = 2.00 L
```

Important:

```text
The estimated water waste value is for demo and report purposes.
The main alert logic does not use a fixed flow-rate threshold.
The main alert logic uses water_flow, human_present, water_detected, and duration.
```

This design was chosen because the prototype YF-S201 tap test measured around `0.40 L/min`. Therefore, using a fixed threshold such as `0.50 L/min` may not trigger reliably in the prototype.

---

## Device History and Alert History

The dashboard uses human-readable history instead of raw backend values.

Device History shows recent sensor events, for example:

```text
Room returned to normal
Normal water usage detected
Unattended water flow detected
Forgotten tap detected
Local water contact detected
Critical leak condition detected
```

Alert History shows generated alert events, for example:

```text
Forgotten tap alert → Notification sent
Critical leak alert → Buzzer and notification activated
```

Raw `0/1` backend values are still available in the technical backend values section.

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

| Tool | Purpose |
|---|---|
| Docker Desktop | Runs MongoDB, Mosquitto, and backend |
| Node.js + npm | Runs the React/Vite dashboard locally |
| Git | Version control |

---

## Quickstart for Demo

The recommended demo setup uses Docker for the backend services and Vite for the React dashboard.

### 1. Start backend services

Open PowerShell from the project root:

```powershell
cd C:\Users\momo8\Documents\GitHub\personal-clone\IoT-group4
docker compose up -d --build mongo mosquitto backend
```

Check that the backend services are running:

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
Swagger API docs: http://localhost:8000/docs
Health check: http://localhost:8000/health
```

### 2. Start React dashboard

Open a second PowerShell terminal:

```powershell
cd C:\Users\momo8\Documents\GitHub\personal-clone\IoT-group4\frontend-react
npm install
npm run dev
```

Open the dashboard:

```text
http://localhost:5173/
```

This project uses port `5173` for the React dashboard.

If port `5173` is already in use, close the previous Vite terminal or stop the process using that port before running the dashboard again.

---

## Dashboard Features

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
- estimated water waste
- simulation scenario buttons
- reset normal button
- clear demo button
- human-readable device history
- human-readable alert history
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

## Dashboard Testing Steps

### Step 1: Open the dashboard

Open:

```text
http://localhost:5173/
```

Check that the dashboard shows:

```text
Backend Online
```

### Step 2: Clear previous demo data

Click:

```text
Clear Demo
```

Expected result:

```text
The device state returns to normal.
Old device history and alert history are cleared.
```

### Step 3: Test normal room condition

Click:

```text
Normal
```

Expected result:

```text
Status: NORMAL
LED: Green
Buzzer: Off
Notify User: No
Estimated Water Waste: 0.00 L
```

### Step 4: Test normal water usage

Click:

```text
Normal Flow
```

Expected result:

```text
Status: NORMAL_FLOW
LED: Blue
Buzzer: Off
Notify User: No
Device History: Normal water usage detected
```

### Step 5: Test unattended water flow

Click:

```text
Warning
```

Expected result:

```text
Status: WARNING
LED: Yellow
Buzzer: Off
Notify User: No
Device History: Unattended water flow detected
Estimated Water Waste: calculated from flow rate and duration
```

### Step 6: Test forgotten tap alert

Click:

```text
Alert
```

Expected result:

```text
Status: ALERT
LED: Red
Buzzer: Intermittent
Notify User: Yes
Device History: Forgotten tap detected
Alert History: Forgotten tap alert
```

### Step 7: Test local water contact

Click:

```text
Leak
```

Expected result:

```text
Status: LEAK
LED: White
Buzzer: Slow beep
Notify User: No
Device History: Local water contact detected
```

### Step 8: Test critical leak / overflow

Click:

```text
Critical
```

Expected result:

```text
Status: CRITICAL
LED: Red flashing
Buzzer: Continuous
Notify User: Yes
Device History: Critical leak condition detected
Alert History: Critical leak alert
```

---

## Dynamic Demo Test with PowerShell

The dashboard buttons are useful for quick testing.  
For a more realistic demo, send repeated sensor values through the backend simulation API.

Open a third PowerShell terminal from the project root.

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

function Clear-Demo {
    Invoke-RestMethod `
        -Method Post `
        -Uri "$base/api/devices/$device/reset?clear_logs=1"
}
```

### Full demo path

This demonstrates:

```text
NORMAL → NORMAL_FLOW → WARNING → ALERT → CRITICAL
```

```powershell
Clear-Demo

for ($i = 1; $i -le 3; $i++) {
    Send-Sensor 0 0 0 0
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 6; $i++) {
    Send-Sensor 1 1 0 0.4
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 35; $i++) {
    Send-Sensor 1 0 0 0.4
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 10; $i++) {
    Send-Sensor 1 0 1 0.4
    Start-Sleep -Seconds 1
}
```

Expected result:

```text
Green → Blue → Yellow → Red → Red flashing
```

The system uses:

```text
1 real second = 10 system seconds
```

So around 30 real seconds of unattended flow becomes 300 system seconds and triggers `ALERT`.

---

## Other Dynamic Test Scenarios

### Normal usage path

```powershell
Clear-Demo

for ($i = 1; $i -le 3; $i++) {
    Send-Sensor 0 0 0 0
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 8; $i++) {
    Send-Sensor 1 1 0 0.4
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 3; $i++) {
    Send-Sensor 0 0 0 0
    Start-Sleep -Seconds 1
}
```

Expected:

```text
NORMAL → NORMAL_FLOW → NORMAL
```

### Forgotten tap path

```powershell
Clear-Demo

for ($i = 1; $i -le 3; $i++) {
    Send-Sensor 0 0 0 0
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 35; $i++) {
    Send-Sensor 1 0 0 0.4
    Start-Sleep -Seconds 1
}
```

Expected:

```text
NORMAL → WARNING → ALERT
```

### Local leak path

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

Expected:

```text
NORMAL → LEAK → NORMAL
```

### Local leak becomes critical

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
    Send-Sensor 1 0 1 0.4
    Start-Sleep -Seconds 1
}
```

Expected:

```text
NORMAL → LEAK → CRITICAL
```

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
    flow_rate_lpm = 0.4
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
    flow_rate_lpm = 0.4
} | ConvertTo-Json -Compress

docker exec smartwater-mosquitto mosquitto_pub `
    -h localhost `
    -t home/bathroom/device01/sensor `
    -m $payload
```

---

## Notification

The backend can send notifications for:

```text
ALERT
CRITICAL
```

Do not hard-code notification credentials in `docker-compose.yml`.

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

Leave them empty if notification is not needed.

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

Run React dashboard:

```powershell
cd frontend-react
npm install
npm run dev
```

Open:

```text
http://localhost:5173/
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