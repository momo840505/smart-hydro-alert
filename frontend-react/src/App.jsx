import { useCallback, useEffect, useState } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000";
const DEFAULT_DEVICE_ID = "device01";
const ALERT_THRESHOLD = 300;

const SCENARIOS = [
    {
        key: "NORMAL",
        emoji: "🌿",
        title: "Normal",
        subtitle: "No flow + no leak",
        payload: {
            water_flow: 0,
            human_present: 0,
            water_detected: 0,
            alert: 0,
            status: "NORMAL",
            running_duration_sec: 0,
            flow_rate_lpm: 0,
        },
    },
    {
        key: "NORMAL_FLOW",
        emoji: "🚰",
        title: "Normal Flow",
        subtitle: "Flow + human present",
        payload: {
            water_flow: 1,
            human_present: 1,
            water_detected: 0,
            alert: 0,
            status: "NORMAL_FLOW",
            running_duration_sec: 0,
            flow_rate_lpm: 0.4,
        },
    },
    {
        key: "WARNING",
        emoji: "🌤️",
        title: "Warning",
        subtitle: "Flow + no human + short duration",
        payload: {
            water_flow: 1,
            human_present: 0,
            water_detected: 0,
            alert: 0,
            status: "WARNING",
            running_duration_sec: 120,
            flow_rate_lpm: 0.4,
        },
    },
    {
        key: "ALERT",
        emoji: "🚨",
        title: "Alert",
        subtitle: "Flow + no human + long duration",
        payload: {
            water_flow: 1,
            human_present: 0,
            water_detected: 0,
            alert: 1,
            status: "ALERT",
            running_duration_sec: 310,
            flow_rate_lpm: 0.4,
        },
    },
    {
        key: "LEAK",
        emoji: "💧",
        title: "Leak",
        subtitle: "FC-37 detects water only",
        payload: {
            water_flow: 0,
            human_present: 0,
            water_detected: 1,
            alert: 0,
            status: "LEAK",
            running_duration_sec: 0,
            flow_rate_lpm: 0,
        },
    },
    {
        key: "CRITICAL",
        emoji: "🔥",
        title: "Critical",
        subtitle: "Flow + FC-37 detects water",
        payload: {
            water_flow: 1,
            human_present: 0,
            water_detected: 1,
            alert: 1,
            status: "CRITICAL",
            running_duration_sec: 330,
            flow_rate_lpm: 0.4,
        },
    },
];

const LOGIC_RULES = [
    {
        status: "NORMAL",
        condition: "No flow + no leak",
        meaning: "System idle / normal",
        led: "Green",
        buzzer: "Off",
        notify: "No",
    },
    {
        status: "NORMAL_FLOW",
        condition: "Flow + human present",
        meaning: "Normal water usage",
        led: "Blue",
        buzzer: "Off",
        notify: "No",
    },
    {
        status: "WARNING",
        condition: "Flow + no human + short duration",
        meaning: "Suspicious abnormal usage",
        led: "Yellow",
        buzzer: "Off",
        notify: "No",
    },
    {
        status: "ALERT",
        condition: "Flow + no human + long duration",
        meaning: "Forgotten tap / abnormal flow",
        led: "Red",
        buzzer: "Intermittent",
        notify: "Yes",
    },
    {
        status: "LEAK",
        condition: "FC-37 detects water only",
        meaning: "Possible local leak / overflow",
        led: "White",
        buzzer: "Slow beep",
        notify: "No",
    },
    {
        status: "CRITICAL",
        condition: "Flow + FC-37 detects water",
        meaning: "Severe leak / overflow condition",
        led: "Red flashing",
        buzzer: "Continuous",
        notify: "Yes",
    },
];

function toBool(value) {
    return value === 1 || value === true || value === "1" || value === "true";
}

function to01(value) {
    return toBool(value) ? 1 : 0;
}

function compactHistory(items) {
    const ordered = [...items].reverse();
    const compact = [];

    for (const item of ordered) {
        const last = compact[compact.length - 1];

        if (!last || last.status !== item.status) {
            compact.push(item);
        }
    }

    return compact.reverse();
}

function formatTime(value) {
    if (!value) return "—";

    const date = typeof value === "number" ? new Date(value * 1000) : new Date(value);

    return date.toLocaleTimeString("en-AU", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
    });
}

function formatDateTime(value) {
    if (!value) return "—";

    const date = typeof value === "number" ? new Date(value * 1000) : new Date(value);

    return date.toLocaleString("en-AU", {
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
    });
}

function deriveStatus(waterFlow, humanPresent, waterDetected, duration, backendStatus) {
    if (backendStatus) return backendStatus;
    if (waterFlow && waterDetected) return "CRITICAL";
    if (!waterFlow && waterDetected) return "LEAK";
    if (waterFlow && !humanPresent && duration >= ALERT_THRESHOLD) return "ALERT";
    if (waterFlow && !humanPresent) return "WARNING";
    if (waterFlow && humanPresent) return "NORMAL_FLOW";
    return "NORMAL";
}

function getStatusMeta(status) {
    const map = {
        NORMAL: {
            label: "NORMAL",
            className: "normal",
            emoji: "🌿",
            title: "Everything looks good",
            message: "No water flow and no water contact are detected. The room is idle and safe.",
            led: "Green",
            ledClass: "led-green",
            buzzer: "Off",
            notify: "No",
            color: "#22c55e",
        },
        NORMAL_FLOW: {
            label: "NORMAL_FLOW",
            className: "normal-flow",
            emoji: "🚰",
            title: "Normal water usage",
            message: "Water is flowing while a person is present, so this is treated as normal use.",
            led: "Blue",
            ledClass: "led-blue",
            buzzer: "Off",
            notify: "No",
            color: "#0ea5e9",
        },
        WARNING: {
            label: "WARNING",
            className: "warning",
            emoji: "🌤️",
            title: "Unattended water flow",
            message: "Water is flowing while no person is detected. The system is monitoring the duration.",
            led: "Yellow",
            ledClass: "led-yellow",
            buzzer: "Off",
            notify: "No",
            color: "#f59e0b",
        },
        ALERT: {
            label: "ALERT",
            className: "alert",
            emoji: "🚨",
            title: "Forgotten tap risk",
            message: "Water has been running without human presence for too long. User notification is required.",
            led: "Red",
            ledClass: "led-red",
            buzzer: "Intermittent",
            notify: "Yes",
            color: "#f43f5e",
        },
        LEAK: {
            label: "LEAK",
            className: "leak",
            emoji: "💧",
            title: "Local water contact detected",
            message: "The FC-37 sensor detected water contact while no flow is detected.",
            led: "White",
            ledClass: "led-white",
            buzzer: "Slow beep",
            notify: "No",
            color: "#38bdf8",
        },
        CRITICAL: {
            label: "CRITICAL",
            className: "critical",
            emoji: "🔥",
            title: "Critical leak or overflow risk",
            message: "Water flow and local water contact are both detected. This is the highest risk state.",
            led: "Red flashing",
            ledClass: "led-red flashing",
            buzzer: "Continuous",
            notify: "Yes",
            color: "#ef4444",
        },
    };

    return (
        map[status] ?? {
            label: "WAITING",
            className: "waiting",
            emoji: "⏳",
            title: "Waiting for data",
            message: "Send a demo scenario or connect the ESP32 to start monitoring.",
            led: "—",
            ledClass: "led-off",
            buzzer: "—",
            notify: "—",
            color: "#94a3b8",
        }
    );
}

function getEventMessage(item) {
    const status = item.status;

    if (status === "NORMAL") {
        return {
            event: "Room returned to normal",
            summary: "No water flow or water contact detected",
            action: "Monitoring continued",
        };
    }

    if (status === "NORMAL_FLOW") {
        return {
            event: "Normal water usage detected",
            summary: "Water is flowing while a person is present",
            action: "No action required",
        };
    }

    if (status === "WARNING") {
        return {
            event: "Unattended water flow detected",
            summary: "Water is flowing while no person is detected",
            action: "Monitoring duration",
        };
    }

    if (status === "ALERT") {
        return {
            event: "Forgotten tap detected",
            summary: "Unattended water flow exceeded the time threshold",
            action: "Buzzer activated and notification sent",
        };
    }

    if (status === "LEAK") {
        return {
            event: "Local water contact detected",
            summary: "The FC-37 water sensor detected water near the monitored area",
            action: "Slow beep activated",
        };
    }

    if (status === "CRITICAL") {
        return {
            event: "Critical leak condition detected",
            summary: "Water flow and local water contact are both detected",
            action: "Continuous buzzer and notification sent",
        };
    }

    return {
        event: "Unknown device event",
        summary: "Sensor values require checking",
        action: "Review technical backend values",
    };
}

function getAlertMessage(item) {
    const status = item.status ?? item.alert_type;

    if (status === "ALERT") {
        return {
            alert: "Forgotten tap alert",
            detail: "Unattended water flow reached the alert threshold",
            action: item.notified ? "Notification sent" : "Alert recorded",
        };
    }

    if (status === "CRITICAL") {
        return {
            alert: "Critical leak alert",
            detail: "Water flow and local water contact were detected together",
            action: item.notified ? "Buzzer and notification activated" : "Critical alert recorded",
        };
    }

    return {
        alert: "System alert",
        detail: "An alert event was generated",
        action: item.notified ? "Notification sent" : "Alert recorded",
    };
}

function shouldEstimateWaste(status) {
    return status === "WARNING" || status === "ALERT" || status === "CRITICAL";
}

function calculateEstimatedWasteLitres(status, flowRateLpm, durationSec) {
    const safeFlowRate = Number(flowRateLpm || 0);
    const safeDuration = Number(durationSec || 0);

    if (!shouldEstimateWaste(status) || safeFlowRate <= 0 || safeDuration <= 0) {
        return 0;
    }

    return safeFlowRate * (safeDuration / 60);
}

function SensorCard({ emoji, title, value, raw, detail, active }) {
    return (
        <article className={`sensor-card ${active ? "active" : ""}`}>
            <div className="sensor-icon">{emoji}</div>
            <div>
                <p>{title}</p>
                <h3>{value}</h3>
                <span>{detail}</span>
            </div>
            <code>{raw}</code>
        </article>
    );
}

function OutputCard({ title, value, children }) {
    return (
        <article className="output-card">
            <p>{title}</p>
            <h3>{value}</h3>
            {children}
        </article>
    );
}

function EstimateCard({ title, value, detail }) {
    return (
        <article className="estimate-card">
            <p>{title}</p>
            <h3>{value}</h3>
            <span>{detail}</span>
        </article>
    );
}

function App() {
    const [health, setHealth] = useState(false);
    const [devices, setDevices] = useState([]);
    const [selectedDevice, setSelectedDevice] = useState(DEFAULT_DEVICE_ID);
    const [live, setLive] = useState(null);
    const [history, setHistory] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [lastCheck, setLastCheck] = useState(null);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [scenarioBusy, setScenarioBusy] = useState("");
    const [showRaw, setShowRaw] = useState(false);

    const loadDashboard = useCallback(
        async ({ showLoading = false } = {}) => {
            if (showLoading) {
                setLoading(true);
            }

            setError("");

            try {
                const healthRes = await fetch(`${API_BASE}/health`);
                setHealth(healthRes.ok);

                const devicesRes = await fetch(`${API_BASE}/api/devices`);
                const devicesData = devicesRes.ok ? await devicesRes.json() : [];
                setDevices(devicesData);

                const currentDevice =
                    selectedDevice || devicesData?.[0]?.device_id || DEFAULT_DEVICE_ID;

                if (!selectedDevice) {
                    setSelectedDevice(currentDevice);
                }

                const [liveRes, historyRes, alertRes] = await Promise.all([
                    fetch(`${API_BASE}/api/devices/${currentDevice}/live`),
                    fetch(`${API_BASE}/api/devices/${currentDevice}/history?limit=80`),
                    fetch(`${API_BASE}/api/alerts?device_id=${currentDevice}&limit=10`),
                ]);

                if (liveRes.ok) {
                    setLive(await liveRes.json());
                }

                if (historyRes.ok) {
                    setHistory(await historyRes.json());
                }

                if (alertRes.ok) {
                    setAlerts(await alertRes.json());
                }

                setLastCheck(new Date());
            } catch (err) {
                setHealth(false);
                setError("Cannot connect to backend. Please check Docker backend is running.");
                console.error(err);
            } finally {
                if (showLoading) {
                    setLoading(false);
                }
            }
        },
        [selectedDevice],
    );

    useEffect(() => {
        const firstLoadTimer = window.setTimeout(() => {
            void loadDashboard();
        }, 0);

        const intervalTimer = window.setInterval(() => {
            void loadDashboard();
        }, 2500);

        return () => {
            window.clearTimeout(firstLoadTimer);
            window.clearInterval(intervalTimer);
        };
    }, [loadDashboard]);

    const latest = live ?? history?.[0] ?? {};

    const waterFlow = toBool(latest.water_flow);
    const humanPresent = toBool(latest.human_present);
    const waterDetected = toBool(latest.water_detected);
    const alert = toBool(latest.alert);
    const duration = Number(latest.running_duration_sec ?? 0);
    const flowRate = Number(latest.flow_rate_lpm ?? 0);

    const status = deriveStatus(
        waterFlow,
        humanPresent,
        waterDetected,
        duration,
        latest.status,
    );

    const meta = getStatusMeta(status);
    const currentRule = LOGIC_RULES.find((rule) => rule.status === status);
    const displayHistory = compactHistory(history).slice(0, 5);

    const estimatedWaste = calculateEstimatedWasteLitres(status, flowRate, duration);
    const durationMinutes = duration / 60;

    async function runScenario(scenario) {
        setScenarioBusy(scenario.key);
        setError("");

        try {
            const response = await fetch(`${API_BASE}/api/devices/${selectedDevice}/simulate`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(scenario.payload),
            });

            if (!response.ok) {
                throw new Error(`Simulation failed: ${response.status}`);
            }

            await loadDashboard();
        } catch (err) {
            setError("Simulation failed. Please check backend is running.");
            console.error(err);
        } finally {
            setScenarioBusy("");
        }
    }

    async function resetToNormal({ clearLogs = false } = {}) {
        setScenarioBusy(clearLogs ? "CLEAR" : "RESET");
        setError("");

        try {
            const response = await fetch(
                `${API_BASE}/api/devices/${selectedDevice}/reset?clear_logs=${clearLogs ? 1 : 0}`,
                {
                    method: "POST",
                },
            );

            if (!response.ok) {
                throw new Error(`Reset failed: ${response.status}`);
            }

            if (clearLogs) {
                setHistory([]);
                setAlerts([]);
            }

            await loadDashboard();
        } catch (err) {
            setError("Reset failed. Please check backend is running.");
            console.error(err);
        } finally {
            setScenarioBusy("");
        }
    }

    return (
        <main className="dashboard-shell">
            <div className="sunny-background">
                <div className="blob blob-a" />
                <div className="blob blob-b" />
                <div className="blob blob-c" />
            </div>

            <section className="hero">
                <div>
                    <p className="mini-label">Group 4 IoT Prototype</p>
                    <h1>Smart Hydro Alert</h1>
                    <p className="hero-subtitle">
                        Real-time water usage, local leak detection, user notification, LED output,
                        and buzzer response in one dashboard.
                    </p>
                </div>

                <div className="hero-actions">
                    <div className={`health-pill ${health ? "online" : "offline"}`}>
                        <span />
                        {health ? "Backend Online" : "Backend Offline"}
                    </div>

                    <select
                        value={selectedDevice}
                        onChange={(event) => setSelectedDevice(event.target.value)}
                    >
                        {devices.length === 0 ? (
                            <option value={DEFAULT_DEVICE_ID}>{DEFAULT_DEVICE_ID}</option>
                        ) : (
                            devices.map((device) => (
                                <option key={device.device_id} value={device.device_id}>
                                    {device.device_id}
                                </option>
                            ))
                        )}
                    </select>

                    <button
                        type="button"
                        onClick={() => loadDashboard({ showLoading: true })}
                        disabled={loading}
                    >
                        {loading ? "Refreshing..." : "Refresh"}
                    </button>
                </div>
            </section>

            {error ? <div className="error-banner">{error}</div> : null}

            <section className={`status-showcase ${meta.className}`}>
                <div className="status-main">
                    <div className="big-emoji">{meta.emoji}</div>

                    <div>
                        <span className="status-chip" style={{ backgroundColor: meta.color }}>
                            {meta.label}
                        </span>
                        <h2>{meta.title}</h2>
                        <p>{meta.message}</p>
                    </div>
                </div>

                <div className="status-side">
                    <div>
                        <span>Last device message</span>
                        <strong>{formatTime(latest.last_seen ?? latest.timestamp)}</strong>
                    </div>
                    <div>
                        <span>Dashboard check</span>
                        <strong>{formatTime(lastCheck)}</strong>
                    </div>
                    <div>
                        <span>Current rule</span>
                        <strong>{currentRule?.condition ?? "Waiting"}</strong>
                    </div>
                </div>
            </section>

            <section className="grid four">
                <SensorCard
                    emoji="🚰"
                    title="Flow Sensor"
                    value={waterFlow ? "Flowing" : "No flow"}
                    raw={`water_flow=${to01(waterFlow)}`}
                    detail={`${flowRate.toFixed(2)} L/min`}
                    active={waterFlow}
                />

                <SensorCard
                    emoji="🧍"
                    title="Human Presence"
                    value={humanPresent ? "Present" : "Not detected"}
                    raw={`human_present=${to01(humanPresent)}`}
                    detail="LD2410C presence input"
                    active={humanPresent}
                />

                <SensorCard
                    emoji="💧"
                    title="FC-37 Water Sensor"
                    value={waterDetected ? "Water detected" : "Dry"}
                    raw={`water_detected=${to01(waterDetected)}`}
                    detail="Local leak / overflow input"
                    active={waterDetected}
                />

                <SensorCard
                    emoji="⏱️"
                    title="Running Duration"
                    value={`${duration}s`}
                    raw={`alert=${to01(alert)}`}
                    detail={`Alert threshold: ${ALERT_THRESHOLD}s`}
                    active={duration >= ALERT_THRESHOLD}
                />
            </section>

            <section className="grid three">
                <OutputCard title="LED Output" value={meta.led}>
                    <div className={`led-dot ${meta.ledClass}`} />
                </OutputCard>

                <OutputCard title="Buzzer Output" value={meta.buzzer}>
                    <span className="small-note">Local physical warning</span>
                </OutputCard>

                <OutputCard title="Notify User" value={meta.notify}>
                    <span className="small-note">
                        Remote message only for ALERT and CRITICAL
                    </span>
                </OutputCard>
            </section>

            <section className="panel estimate-panel">
                <div className="panel-header">
                    <div>
                        <p className="mini-label">Water Usage Estimate</p>
                        <h2>Estimated Water Waste</h2>
                    </div>
                    <p>
                        This value is for demo and report purposes. The alert decision still uses
                        0/1 sensor states and duration, not a fixed flow-rate threshold.
                    </p>
                </div>

                <div className="estimate-grid">
                    <EstimateCard
                        title="Flow rate"
                        value={`${flowRate.toFixed(2)} L/min`}
                        detail="Estimated from YF-S201 pulse frequency"
                    />

                    <EstimateCard
                        title="System duration"
                        value={`${duration}s`}
                        detail={`${durationMinutes.toFixed(2)} min used in the estimate`}
                    />

                    <EstimateCard
                        title="Estimated water waste"
                        value={`${estimatedWaste.toFixed(2)} L`}
                        detail="Flow rate × system duration"
                    />
                </div>

                <div className="estimate-note">
                    <strong>Formula:</strong> Water wasted = flow rate × duration / 60. The YF-S201
                    flow rate is used as an estimate only. The main alert logic is still based on
                    water flow state, human presence, water detection, and duration.
                </div>
            </section>

            <section className="panel">
                <div className="panel-header">
                    <div>
                        <p className="mini-label">No Hardware Demo Mode</p>
                        <h2>Simulation Control</h2>
                    </div>
                    <p>
                        Use Reset before each full demo path. Backend uses 1 real second = 10 system
                        seconds for continuous abnormal water flow.
                    </p>
                </div>

                <div className="scenario-grid">
                    <button
                        type="button"
                        className="scenario-button scenario-normal"
                        onClick={() => resetToNormal({ clearLogs: false })}
                        disabled={Boolean(scenarioBusy)}
                    >
                        <span>↩️</span>
                        <strong>Reset Normal</strong>
                        <small>Return to no flow + no leak</small>
                        {scenarioBusy === "RESET" ? <em>Resetting...</em> : null}
                    </button>

                    <button
                        type="button"
                        className="scenario-button scenario-normal"
                        onClick={() => resetToNormal({ clearLogs: true })}
                        disabled={Boolean(scenarioBusy)}
                    >
                        <span>🧹</span>
                        <strong>Clear Demo</strong>
                        <small>Reset normal and clear logs</small>
                        {scenarioBusy === "CLEAR" ? <em>Clearing...</em> : null}
                    </button>

                    {SCENARIOS.map((scenario) => (
                        <button
                            key={scenario.key}
                            type="button"
                            className={`scenario-button scenario-${scenario.key.toLowerCase()}`}
                            onClick={() => runScenario(scenario)}
                            disabled={Boolean(scenarioBusy)}
                        >
                            <span>{scenario.emoji}</span>
                            <strong>{scenario.title}</strong>
                            <small>{scenario.subtitle}</small>
                            {scenarioBusy === scenario.key ? <em>Sending...</em> : null}
                        </button>
                    ))}
                </div>
            </section>

            <section className="panel">
                <div className="panel-header">
                    <div>
                        <p className="mini-label">Decision Logic</p>
                        <h2>Condition Rules</h2>
                    </div>
                    <p>The highlighted row is the rule currently triggered by the latest 0/1 payload.</p>
                </div>

                <div className="logic-table">
                    <div className="logic-row table-head">
                        <span>Condition</span>
                        <span>Meaning</span>
                        <span>Status</span>
                        <span>LED</span>
                        <span>Buzzer</span>
                        <span>Notify</span>
                    </div>

                    {LOGIC_RULES.map((rule) => (
                        <div
                            key={rule.status}
                            className={`logic-row ${rule.status === status ? "active" : ""}`}
                        >
                            <span>{rule.condition}</span>
                            <span>{rule.meaning}</span>
                            <span className="logic-status">{rule.status}</span>
                            <span>{rule.led}</span>
                            <span>{rule.buzzer}</span>
                            <span>{rule.notify}</span>
                        </div>
                    ))}
                </div>
            </section>

            <section className="bottom-grid">
                <div className="panel">
                    <div className="panel-header compact">
                        <div>
                            <p className="mini-label">Recent Sensor Events</p>
                            <h2>Device History</h2>
                        </div>
                    </div>

                    <div className="event-list">
                        {displayHistory.length === 0 ? (
                            <p className="empty">No sensor history yet. Press a demo button first.</p>
                        ) : (
                            displayHistory.map((item, index) => {
                                const message = getEventMessage(item);

                                return (
                                    <div
                                        key={`${item.timestamp}-${item.status}-${index}`}
                                        className="event-item readable-event"
                                    >
                                        <div className="event-main">
                                            <strong>{message.event}</strong>
                                            <span>{formatDateTime(item.timestamp)}</span>
                                            <p>{message.summary}</p>
                                        </div>
                                        <code>{message.action}</code>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>

                <div className="panel">
                    <div className="panel-header compact">
                        <div>
                            <p className="mini-label">Notification Log</p>
                            <h2>Alert History</h2>
                        </div>
                    </div>

                    <div className="event-list">
                        {alerts.length === 0 ? (
                            <p className="empty">
                                No ALERT or CRITICAL notification has been created yet.
                            </p>
                        ) : (
                            alerts.map((item, index) => {
                                const message = getAlertMessage(item);

                                return (
                                    <div key={`${item.timestamp}-${index}`} className="event-item alert-item">
                                        <div className="event-main">
                                            <strong>{message.alert}</strong>
                                            <span>{formatDateTime(item.timestamp)}</span>
                                            <p>{message.detail}</p>
                                        </div>
                                        <code>{message.action}</code>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>
            </section>

            <section className="panel raw-panel">
                <button
                    type="button"
                    className="raw-toggle"
                    onClick={() => setShowRaw((value) => !value)}
                >
                    {showRaw ? "Hide technical backend values" : "Show technical backend values"}
                </button>

                {showRaw ? (
                    <pre>
                        {JSON.stringify(
                            {
                                selectedDevice,
                                latest,
                                derived_status: status,
                                led: meta.led,
                                buzzer: meta.buzzer,
                                notify_user: meta.notify,
                                flow_rate_lpm: flowRate,
                                system_duration_sec: duration,
                                estimated_water_waste_litres: Number(estimatedWaste.toFixed(2)),
                                formula:
                                    "estimated_water_waste = flow_rate_lpm * (running_duration_sec / 60)",
                                time_scale_rule: "1 real second = 10 system seconds",
                            },
                            null,
                            2,
                        )}
                    </pre>
                ) : null}
            </section>
        </main>
    );
}

export default App;