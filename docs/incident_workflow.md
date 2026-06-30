# Incident Workflow

Smart Hydro Alert currently detects water-waste and leak-risk states. A production deployment should also track incident handling from detection to resolution.

## Incident States

| State | Meaning |
|---|---|
| `DETECTED` | Backend created an alert from sensor or ESP32 alert topic. |
| `NOTIFIED` | Telegram or another notification channel was attempted. |
| `ACKNOWLEDGED` | A technician or facility manager confirmed the alert. |
| `INVESTIGATING` | Someone is checking the sink, tap, floor, or sensor. |
| `RESOLVED` | The issue is fixed or the alert was confirmed as a false positive. |
| `CLOSED` | Final notes and resolution category are recorded. |

## Recommended Data Fields

- `incident_id`
- `device_id`
- `location`
- `status`
- `risk_level`
- `condition_status`
- `detected_at`
- `acknowledged_at`
- `resolved_at`
- `assigned_to`
- `resolution_category`
- `resolution_notes`

## Workflow

```text
Sensor event
  -> alert created
  -> notification sent
  -> technician acknowledges
  -> inspection starts
  -> incident resolved
  -> historical analytics updated
```

## Dashboard Upgrade

Add an incident panel with:

- active incident count;
- unacknowledged high-risk alerts;
- mean acknowledgement time;
- mean resolution time;
- incident history by device and location;
- false-positive review notes.

## Portfolio Value

This extension demonstrates that the project can evolve from a live sensor dashboard into an operational monitoring workflow.
