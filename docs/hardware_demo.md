# Hardware Demonstration Guide

This guide explains how to present Smart Hydro Alert as a credible IoT portfolio project.

## Demo Evidence To Capture

Add the following assets to `docs/images/`:

- ESP32 prototype photo;
- sensor wiring photo;
- dashboard screenshot;
- serial monitor screenshot showing MQTT payloads;
- short demo GIF or video thumbnail;
- Telegram notification screenshot with sensitive chat identifiers removed.

## Recommended Demo Flow

1. Start MongoDB, Mosquitto, and the FastAPI backend with Docker Compose.
2. Start the React dashboard.
3. Reset the selected device to a normal state.
4. Trigger the six scenarios:
   - `NORMAL`
   - `NORMAL_FLOW`
   - `WARNING`
   - `ALERT`
   - `LEAK`
   - `CRITICAL`
5. Show how dashboard state, risk level, expected LED output, buzzer output, event history, and alert history change.
6. If hardware is connected, show the ESP32 publishing the same payload structure used by the simulator.

## What To Say In Interviews

Use this positioning:

> Smart Hydro Alert is a real-time IoT monitoring prototype that connects sensor events, MQTT messaging, backend validation, persistent event storage, alert-state logic, WebSocket updates, and a React dashboard. The simulator mirrors the physical payload schema so the software workflow can be tested without hardware.

## Hardware Components

- ESP32 microcontroller
- YF-S201 water-flow sensor
- LD2410C presence sensor
- FC-37 water-contact sensor
- OLED display
- LEDs
- buzzer

## Limitations To Be Transparent About

- It is a prototype, not a certified safety system.
- Flow measurements require calibration.
- Presence detection is configured for short-range classroom testing.
- Alert thresholds should be tuned for each installation site.
- Long-term reliability requires field testing across multiple devices and facilities.
