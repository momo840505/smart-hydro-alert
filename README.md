# Smart Hydro Alert

Smart Hydro Alert is an IoT water monitoring and leak alert prototype built for Group 4.

The system receives `0/1` sensor values from an ESP32 or simulator through MQTT, stores readings in MongoDB, applies backend decision logic, sends optional user notifications, and displays the current system state through a React dashboard.

The current prototype supports:

- real-time water flow monitoring
- human presence detection
- FC-37 / water-contact sensor detection
- abnormal water usage warning
- forgotten tap alert
- local water contact detection
- critical leak / overflow detection
- LED output state
- buzzer output state
- optional user notification
- dashboard simulation without physical hardware
- measured water waste estimate for report and demo purposes
- leak contact time tracking for FC-37-only leak cases

---

## Project Use Case

The target scenario is a vacant room after checkout, such as a hotel room or Airbnb room.

After a guest leaves, the room may remain empty for a period of time. During this time, water-related issues may not be noticed immediately.

Possible situations include:

- a tap left running
- a sink overflow
- local water contact near the basin
- a small leak near a pipe or sink area
- water flow while no person is present
- water contact detected after checkout while the room is empty

The system is designed to detect these situations early and show the risk level through the dashboard, LEDs, buzzer, and notification status.

---

## Current Condition States

| Status | Meaning |
|---|---|
| `NORMAL` | No water flow and no local water contact |
| `NORMAL_FLOW` | Water is flowing while a human is present |
| `WARNING` | Water is flowing with no human present, but the duration is still below the alert threshold |
| `ALERT` | Water is flowing with no human present for too long |
| `LEAK` | FC-37 / water sensor detects local water contact while no measurable water flow is detected |
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

## Classroom Demo Plan

During the presentation, the system will be demonstrated using dashboard simulation.

This is because the real tap and sensor setup is located in a bathroom or practical testing area, so it is not realistic to bring the teacher there during the presentation.

The demo plan is:

1. Use the React dashboard and backend simulation to demonstrate the full system logic.
2. Show status transitions on the dashboard.
3. Show changing flow-rate values in the simulation.
4. Show measured water waste from YF-S201 flow readings.
5. Show FC-37 leak contact time.
6. Show Device History and Alert History.
7. Provide an additional recorded video of the real hardware tap test as supporting evidence.

The simulated flow rate is designed to vary between:

```text
0.10 L/min → 0.20 L/min → 0.30 L/min → 0.40 L/min
```

This matches the prototype hardware test where the YF-S201 started detecting water flow at around `0.10 L/min` and reached around `0.40 L/min` at maximum tap flow.

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
| `water_flow` | No measurable water flow | Water flow detected |
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

## Flow Rate and Water Estimate Design

The YF-S201 flow sensor provides pulse-based water flow information.

The common calculation is:

```text
Flow rate (L/min) = pulse frequency / 7.5
```

For this prototype, the flow rate is used only as an estimate for reporting and dashboard display. It is not used as the main alert trigger.

The prototype tap test showed:

```text
YF-S201 starts detecting flow at around 0.10 L/min
Maximum measured tap flow is around 0.40 L/min
```

Therefore, the main alert logic does not use a fixed flow-rate threshold such as `0.50 L/min`. A fixed `0.50 L/min` threshold may not trigger reliably in this prototype.

The main alert logic uses:

```text
water_flow
human_present
water_detected
duration
```

---

## Estimated Water Waste

The dashboard shows measured water waste only when YF-S201 detects measurable flow.

Formula:

```text
Measured water waste (L) = flow_rate_lpm × duration_seconds / 60
```

Example:

```text
flow_rate_lpm = 0.40 L/min
duration = 300 sec = 5 min

Measured water waste = 0.40 × 5 = 2.00 L
```

The dashboard separates:

| Dashboard value | Meaning |
|---|---|
| `Flow rate` | Current YF-S201 estimated flow rate |
| `Live measured waste` | Current event water waste estimate using live flow rate and running duration |
| `Total measured waste` | Accumulated measured waste from `WARNING`, `ALERT`, and `CRITICAL` events |
| `Leak contact time` | How long FC-37 has detected water contact when YF-S201 does not detect measurable flow |

---

## Why LEAK is not counted as litres

When the status is:

```text
LEAK
water_flow = 0
water_detected = 1
```

the FC-37 sensor has detected water contact, but the YF-S201 flow sensor has not detected measurable flow.

This can mean:

- a few water drops are on the FC-37 sensor
- the same water drop remains on the sensor
- local water is already present near the sink
- there is a very small leak below the YF-S201 detection range
- the leak is not passing through the YF-S201 sensor

Because FC-37 can detect water contact but cannot measure flow rate, the system does not claim an exact litre value for `LEAK`.

Instead, the dashboard records:

```text
Leak contact time
```

This is more realistic than pretending that FC-37 can measure water volume.

If `water_flow=1` and `water_detected=1`, the status becomes:

```text
CRITICAL
```

In this case, the system can estimate measured water waste using the YF-S201 flow rate.

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
- live measured water waste
- total measured water waste
- leak contact time
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
Live Measured Waste: 0.00 L
Total Measured Waste: 0.00 L
Leak Contact Time: 0s
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
Live Measured Waste: calculated from flow rate and duration
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
Live Measured Waste: calculated from flow rate and duration
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
Leak Contact Time: increases while water contact remains detected
Measured water waste in litres is not calculated because YF-S201 does not detect measurable flow
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
Total Measured Waste: keeps accumulated measured water waste
```

---

## Dynamic Demo Test with PowerShell

The dashboard buttons are useful for quick testing.

For a more realistic demo, send repeated sensor values through the backend simulation API.

Open a third PowerShell terminal from the project root.

### Why simulation is used in the classroom demo

The physical tap and YF-S201 flow sensor test is located in a bathroom or practical testing area. It is not realistic to bring the teacher to the bathroom during the presentation.

Therefore, the classroom demo uses backend simulation to show the full dashboard behaviour.

A separate real hardware video should be recorded to show:

- actual tap water through YF-S201
- FC-37 water contact detection
- LD2410C human presence detection
- OLED display
- LEDs
- buzzer
- Serial Monitor payload
- dashboard response

The simulation uses the same `0/1` payload structure as the ESP32 hardware.

### Flow-rate range used in simulation

In the real prototype test:

```text
YF-S201 starts detecting water flow at around 0.10 L/min
Maximum measured tap flow is around 0.40 L/min
```

Therefore, the simulation varies flow rate between:

```text
0.10 L/min → 0.20 L/min → 0.30 L/min → 0.40 L/min
```

This makes the demo more realistic than using a fixed value for every sensor message.

### Helper functions

Run this first:

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

function Reset-Normal {
    Invoke-RestMethod `
        -Method Post `
        -Uri "$base/api/devices/$device/reset?clear_logs=0"
}

function Get-DemoFlowRate {
    param([int]$Step)

    $rates = @(0.10, 0.20, 0.30, 0.40, 0.30, 0.20)

    return $rates[($Step - 1) % $rates.Count]
}
```

---

### Scenario 1: Normal room condition

This shows the room is empty and safe.

Expected result:

```text
NORMAL
Green LED
Buzzer off
No notification
Measured water waste = 0.00 L
Leak contact time = 0s
```

```powershell
Clear-Demo

for ($i = 1; $i -le 5; $i++) {
    Send-Sensor 0 0 0 0
    Start-Sleep -Seconds 1
}
```

---

### Scenario 2: Normal water usage

This shows water is flowing while a person is present.

Expected result:

```text
NORMAL → NORMAL_FLOW → NORMAL
Blue LED during normal water usage
No alert
No notification
```

```powershell
Clear-Demo

for ($i = 1; $i -le 3; $i++) {
    Send-Sensor 0 0 0 0
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 8; $i++) {
    $rate = Get-DemoFlowRate $i
    Send-Sensor 1 1 0 $rate
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 3; $i++) {
    Send-Sensor 0 0 0 0
    Start-Sleep -Seconds 1
}
```

---

### Scenario 3: Forgotten tap / unattended water flow

This shows water flowing while no person is present.

Expected result:

```text
NORMAL → WARNING → ALERT
Yellow LED during WARNING
Red LED during ALERT
Intermittent buzzer during ALERT
Notification sent
Live measured waste increases
Total measured waste increases
```

```powershell
Clear-Demo

for ($i = 1; $i -le 3; $i++) {
    Send-Sensor 0 0 0 0
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 35; $i++) {
    $rate = Get-DemoFlowRate $i
    Send-Sensor 1 0 0 $rate
    Start-Sleep -Seconds 1
}
```

---

### Scenario 4: Local water contact / possible low-flow leak

This shows FC-37 detecting water while YF-S201 does not detect measurable flow.

Expected result:

```text
NORMAL → LEAK
White LED
Slow beep
No remote notification
Leak contact time increases
Measured water waste in litres does not increase
```

This is because FC-37 can detect water contact but cannot measure flow rate or water volume.

```powershell
Clear-Demo

for ($i = 1; $i -le 3; $i++) {
    Send-Sensor 0 0 0 0
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 15; $i++) {
    Send-Sensor 0 0 1 0
    Start-Sleep -Seconds 1
}
```

---

### Scenario 5: Local leak becomes critical

This shows water contact first, then measurable flow appears.

Expected result:

```text
NORMAL → LEAK → CRITICAL
White LED during LEAK
Red flashing LED during CRITICAL
Continuous buzzer during CRITICAL
Notification sent
Leak contact time records the FC-37-only period
Total measured waste increases once YF-S201 detects measurable flow
```

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

for ($i = 1; $i -le 12; $i++) {
    $rate = Get-DemoFlowRate $i
    Send-Sensor 1 0 1 $rate
    Start-Sleep -Seconds 1
}
```

---

### Scenario 6: Full demo path

This is the best scenario for the presentation.

Expected result:

```text
NORMAL → NORMAL_FLOW → WARNING → ALERT → CRITICAL
Green → Blue → Yellow → Red → Red flashing
```

```powershell
Clear-Demo

for ($i = 1; $i -le 3; $i++) {
    Send-Sensor 0 0 0 0
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 6; $i++) {
    $rate = Get-DemoFlowRate $i
    Send-Sensor 1 1 0 $rate
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 35; $i++) {
    $rate = Get-DemoFlowRate $i
    Send-Sensor 1 0 0 $rate
    Start-Sleep -Seconds 1
}

for ($i = 1; $i -le 10; $i++) {
    $rate = Get-DemoFlowRate $i
    Send-Sensor 1 0 1 $rate
    Start-Sleep -Seconds 1
}
```

The full demo path should show:

```text
Current status changes
Flow rate changes
Live measured waste changes
Total measured waste accumulates
Leak contact time only changes during FC-37-only LEAK periods
Device History updates with human-readable events
Alert History records ALERT and CRITICAL events
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

## Real Hardware Test Evidence

For the final presentation, the dashboard simulation is used for live demonstration.

The real hardware test should be recorded separately as a video.

The video should show:

- ESP32 powered on
- sensor wiring
- OLED display
- YF-S201 connected to tap water
- FC-37 water detection
- LD2410C human presence detection
- Serial Monitor MQTT payload
- dashboard receiving the sensor values
- LED and buzzer output

This supports the claim that the simulation uses the same data format and decision logic as the real hardware prototype.

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
```