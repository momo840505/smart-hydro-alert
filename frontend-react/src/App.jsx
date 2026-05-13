import { useCallback, useEffect, useState } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000";

function App() {
    const [deviceId, setDeviceId] = useState("device01");
    const [health, setHealth] = useState(false);
    const [latest, setLatest] = useState(null);
    const [history, setHistory] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [syncing, setSyncing] = useState(false);
    const [lastUpdated, setLastUpdated] = useState("Never");

    const syncDashboard = useCallback(async (showLoading = true) => {
        try {
            if (showLoading) {
                setSyncing(true);
            }

            const [healthRes, liveRes, historyRes, alertRes] = await Promise.all([
                fetch(`${API_BASE}/health`),
                fetch(`${API_BASE}/api/devices/${deviceId}/live`),
                fetch(`${API_BASE}/api/devices/${deviceId}/history?limit=1`),
                fetch(`${API_BASE}/api/alerts?device_id=${deviceId}`),
            ]);

            setHealth(healthRes.ok);

            const liveData = liveRes.ok ? await liveRes.json() : null;
            setLatest(liveData);

            const historyData = historyRes.ok ? await historyRes.json() : [];
            setHistory(historyData);

            const alertData = alertRes.ok ? await alertRes.json() : [];
            setAlerts(alertData);

            setLastUpdated(new Date().toLocaleTimeString());
        } catch (error) {
            console.error(error);
            setHealth(false);
        } finally {
            if (showLoading) {
                setSyncing(false);
            }
        }
    }, [deviceId]);

    useEffect(() => {
        const firstLoad = setTimeout(() => {
            syncDashboard(false);
        }, 0);

        const timer = setInterval(() => {
            syncDashboard(false);
        }, 3000);

        return () => {
            clearTimeout(firstLoad);
            clearInterval(timer);
        };
    }, [syncDashboard]);

    const waterFlow = latest?.water_flow ?? false;
    const humanPresent = latest?.human_present ?? false;
    const runningDuration = latest?.running_duration_sec ?? 0;
    const flowRate = history?.[0]?.flow_rate_lpm ?? 0;
    const activeAlert = latest?.has_active_alert ?? false;
    const deviceStatus = latest?.status ?? "UNKNOWN";
    const lastSeen = latest?.last_seen
        ? new Date(latest.last_seen * 1000).toLocaleTimeString()
        : "—";

    return (
        <main className="page">
            <section className="hero">
                <div className="hero-text">
                    <p className="tag">💧 Group 4 IoT Prototype</p>
                    <h1>Smart Water Monitoring and Alert System</h1>
                    <p className="subtitle">
                        A live React dashboard for abnormal water usage and water waste detection.
                    </p>
                </div>

                <div className={health ? "connection online" : "connection offline"}>
                    <span></span>
                    {health ? "ONLINE" : "DISCONNECTED"}
                </div>
            </section>

            <section className="summary">
                <div className="summary-card">
                    <span className="summary-icon water">🚰</span>
                    <div>
                        <p>Water Flow</p>
                        <h2>{waterFlow ? "YES" : "NO"}</h2>
                    </div>
                </div>

                <div className="summary-card">
                    <span className="summary-icon human">🚶</span>
                    <div>
                        <p>Human Present</p>
                        <h2>{humanPresent ? "YES" : "NO"}</h2>
                    </div>
                </div>

                <div className="summary-card">
                    <span className="summary-icon timer">⏱️</span>
                    <div>
                        <p>Running Duration</p>
                        <h2>{runningDuration}s</h2>
                    </div>
                </div>

                <div className="summary-card">
                    <span className="summary-icon flow">🌊</span>
                    <div>
                        <p>Flow Rate</p>
                        <h2>{Number(flowRate).toFixed(1)} L/min</h2>
                    </div>
                </div>

                <div className={activeAlert ? "summary-card danger-card" : "summary-card"}>
                    <span className="summary-icon alert">🚨</span>
                    <div>
                        <p>Active Alert</p>
                        <h2>{activeAlert ? "YES" : "NO"}</h2>
                    </div>
                </div>
            </section>

            <section className="control-panel">
                <div>
                    <p className="section-label">Device Control</p>
                    <h2>Live Dashboard Sync</h2>
                    <p className="small-text">
                        Device status: <strong>{deviceStatus}</strong> · Last seen: <strong>{lastSeen}</strong>
                    </p>
                </div>

                <div className="control-actions">
                    <select value={deviceId} onChange={(e) => setDeviceId(e.target.value)}>
                        <option value="device01">device01</option>
                    </select>

                    <button onClick={() => syncDashboard(true)} disabled={syncing}>
                        {syncing ? "🔄 Syncing..." : "🔄 Sync Dashboard"}
                    </button>
                </div>

                <p className="updated">Last updated: {lastUpdated}</p>
            </section>

            <section className="two-column">
                <div className="panel">
                    <p className="section-label">Project Overview</p>
                    <h2>Abnormal Water Usage Logic</h2>
                    <p>
                        The ESP32 sends sensor readings to the MQTT broker. The backend checks
                        whether water is running while no human is detected. If this situation
                        continues for 300 seconds, the system records an abnormal water usage alert.
                    </p>

                    <div className="logic-box">
                        <div className={waterFlow ? "logic-active" : ""}>
                            🚰 Water Flow = {waterFlow ? "YES" : "NO"}
                        </div>
                        <div className={!humanPresent ? "logic-active" : ""}>
                            🚶 Human Present = {humanPresent ? "YES" : "NO"}
                        </div>
                        <div className={runningDuration >= 300 ? "logic-active" : ""}>
                            ⏱️ Duration = {runningDuration}s
                        </div>
                        <div className={activeAlert ? "alert-step" : ""}>
                            🚨 {activeAlert ? "Alert Created" : "No Active Alert"}
                        </div>
                    </div>
                </div>

                <div className="panel">
                    <p className="section-label">Demo Scenario</p>
                    <h2>How the System Works</h2>

                    <div className="timeline">
                        <div>
                            <span>1</span>
                            <p>🔌 ESP32 reads sensors</p>
                        </div>
                        <div>
                            <span>2</span>
                            <p>📡 MQTT sends live data</p>
                        </div>
                        <div>
                            <span>3</span>
                            <p>🖥️ Backend checks logic</p>
                        </div>
                        <div>
                            <span>4</span>
                            <p>📊 Dashboard updates automatically</p>
                        </div>
                    </div>
                </div>
            </section>

            <section className="panel">
                <p className="section-label">System Architecture</p>
                <h2>IoT Data Flow</h2>

                <div className="architecture">
                    <div>🔌<strong>ESP32</strong></div>
                    <span>→</span>
                    <div>📡<strong>MQTT Broker</strong></div>
                    <span>→</span>
                    <div>🖥️<strong>FastAPI</strong></div>
                    <span>→</span>
                    <div>🗄️<strong>MongoDB</strong></div>
                    <span>→</span>
                    <div>📊<strong>React Dashboard</strong></div>
                </div>
            </section>

            <section className="panel">
                <p className="section-label">Alert History</p>
                <h2>Recorded Abnormal Water Usage Events</h2>

                {alerts.length === 0 ? (
                    <div className="empty">
                        ✅ No abnormal water usage has been detected yet.
                    </div>
                ) : (
                    <div className="table-wrap">
                        <table>
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Device</th>
                                    <th>Type</th>
                                    <th>Severity</th>
                                    <th>Duration</th>
                                    <th>Notified</th>
                                </tr>
                            </thead>
                            <tbody>
                                {alerts.map((a, index) => (
                                    <tr key={index}>
                                        <td>
                                            {a.timestamp
                                                ? new Date(a.timestamp * 1000).toLocaleString()
                                                : "—"}
                                        </td>
                                        <td>{a.device_id}</td>
                                        <td>{a.alert_type}</td>
                                        <td>
                                            <span className="badge">{a.strength}</span>
                                        </td>
                                        <td>{a.duration_sec}s</td>
                                        <td>{a.notified ? "Yes" : "No"}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>
        </main>
    );
}

export default App;