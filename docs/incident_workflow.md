# Incident Workflow

The current backend stores alerts but does not implement a complete incident-management workflow.

This document records one possible extension for the project.

## Possible States

| State           | Meaning                                          |
| --------------- | ------------------------------------------------ |
| `DETECTED`      | An alert is created                              |
| `NOTIFIED`      | A notification is sent                           |
| `ACKNOWLEDGED`  | Someone confirms the alert                       |
| `INVESTIGATING` | The problem is being checked                     |
| `RESOLVED`      | The issue is fixed or marked as a false positive |
| `CLOSED`        | Final notes are recorded                         |

## Possible Fields

* `incident_id`
* `device_id`
* `location`
* `risk_level`
* `detected_at`
* `acknowledged_at`
* `resolved_at`
* `assigned_to`
* `resolution_category`
* `resolution_notes`

## Example Flow

```text
sensor event
    ↓
alert created
    ↓
notification
    ↓
acknowledgement
    ↓
investigation
    ↓
resolution
```

A future dashboard could also show:

* active incidents
* unacknowledged alerts
* acknowledgement time
* resolution time
* incident history
