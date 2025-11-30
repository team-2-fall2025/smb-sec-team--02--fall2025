// src/pages/Dashboard.tsx
import { useEffect, useState } from "react";
import { format, subDays } from "date-fns";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from "recharts";

export function Dashboard() {
    // @ts-ignore
    const URL = import.meta.env.VITE_API_URL;

    const [stats, setStats] = useState({ assets: 0, intel_events: 0, risk_items: 0 });
    const [health, setHealth] = useState<string | null>(null);
    const [version, setVersion] = useState({ version: "unknown" });
    const [topAssets, setTopAssets] = useState<any[]>([]);
    const [detections24h, setDetections24h] = useState(0);
    const [detectionsTrend, setDetectionsTrend] = useState<any[]>([]);
    const [topHighSevDetections, setTopHighSevDetections] = useState<any[]>([]);
    
    // NEW: CSF Coverage state
    const [csfCoverage, setCsfCoverage] = useState({
        Identify: 0,
        Protect: 0,
        Detect: 0,
        Respond: 0,
        Recover: 0,
        Govern: 0
    });

    useEffect(() => {
        // Existing fetches...
        fetch(`${URL}/api/stats`).then(r => r.json()).then(setStats);
        fetch(`${URL}/health`).then(r => r.json()).then(d => setHealth(d.status));
        fetch(`${URL}/version`).then(r => r.json()).then(setVersion);

        fetch(`${URL}/api/assets/top-risky`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ limit: 5 }) })
            .then(r => r.json()).then(d => setTopAssets(d.data || []));

        const oneDayAgo = subDays(new Date(), 1).toISOString();
        fetch(`${URL}/api/detect/lastDay?last_seen_gte=${oneDayAgo}`).then(r => r.json()).then(setDetections24h);
        fetch(`${URL}/api/detect/trend?days=7`).then(r => r.json()).then(d => {
            const trend = (d.data || d).map((x: any) => ({ day: format(new Date(x.date), "MMM dd"), count: x.count }));
            setDetectionsTrend(trend);
        });
        fetch(`${URL}/api/detect/high-sev?min_severity=3&limit=5`).then(r => r.json()).then(d => setTopHighSevDetections(d.data || d));

        // NEW: Fetch CSF Coverage
        fetch(`${URL}/api/protect/coverage`)
            .then(r => r.json())
            .then(data => {
                setCsfCoverage({
                    Identify: Math.round((data["CSF.Identify"] || 0) * 100),
                    Protect: Math.round((data["CSF.Protect"] || 0) * 100),
                    Detect: Math.round((data["CSF.Detect"] || 0) * 100),
                    Respond: Math.round((data["CSF.Respond"] || 0) * 100),
                    Recover: Math.round((data["CSF.Recover"] || 0) * 100),
                    Govern: Math.round((data["CSF.Govern"] || 0) * 100),
                });
            })
            .catch(() => console.error("Failed to load CSF coverage"));
    }, [URL]);

    // Bar chart data for CSF functions
    const coverageData = [
        { function: "Identify", coverage: csfCoverage.Identify },
        { function: "Protect", coverage: csfCoverage.Protect },
        { function: "Detect", coverage: csfCoverage.Detect },
        { function: "Respond", coverage: csfCoverage.Respond },
        { function: "Recover", coverage: csfCoverage.Recover },
        { function: "Govern", coverage: csfCoverage.Govern },
    ];

    const colors = ["#6c757d", "#007bff", "#28a745", "#fd7e14", "#dc3545", "#6f42c1"];

    return (
        <div className="container-fluid">
            <h1 className="mb-4">Security Dashboard</h1>

            <div className="mb-4">
                <p>Health: <span className={health === "ok" ? "text-success" : "text-danger"}>{health}</span></p>
                <p>Version: {version.version}</p>
            </div>

            <div className="row g-3">
                {/* Existing Cards */}
                <div className="col-md-3">
                    <div className="card shadow-sm h-100">
                        <div className="card-body text-center">
                            <h5 className="card-title">Assets</h5>
                            <p className="display-6">{stats.assets}</p>
                        </div>
                    </div>
                </div>
                <div className="col-md-3">
                    <div className="card shadow-sm h-100">
                        <div className="card-body text-center">
                            <h5 className="card-title">Intel Events</h5>
                            <p className="display-6">{stats.intel_events}</p>
                        </div>
                    </div>
                </div>
                <div className="col-md-3">
                    <div className="card shadow-sm h-100">
                        <div className="card-body text-center">
                            <h5 className="card-title">Risk Items</h5>
                            <p className="display-6">{stats.risk_items}</p>
                        </div>
                    </div>
                </div>
                <div className="col-md-3">
                    <div className="card shadow-sm h-100">
                        <div className="card-body">
                            <h5 className="card-title">Detections (24h)</h5>
                            <p className="display-6 text-center">{detections24h}</p>
                            <div style={{ height: 80 }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={detectionsTrend}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="day" tick={{ fontSize: 10 }} />
                                        <YAxis tick={{ fontSize: 10 }} />
                                        <Tooltip />
                                        <Line type="monotone" dataKey="count" stroke="#dc3545" strokeWidth={2} dot={false} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>
                </div>

                {/* NEW: CSF Coverage Widget */}
                <div className="col-md-6">
                    <div className="card shadow-sm h-100">
                        <div className="card-body">
                            <h5 className="card-title">
                                CSF Coverage 
                                <span className="float-end text-success fw-bold">{csfCoverage.Protect}% Protect</span>
                            </h5>
                            <div style={{ height: 200 }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={coverageData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="function" tick={{ fontSize: 11 }} />
                                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                                        <Tooltip formatter={(value: number) => `${value}%`} />
                                        <Bar dataKey="coverage" radius={[8, 8, 0, 0]}>
                                            {coverageData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={colors[index]} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                            <small className="text-muted d-block text-center mt-2">
                                Based on implemented and in-progress controls
                            </small>
                        </div>
                    </div>
                </div>

                {/* Top Risky Assets */}
                <div className="col-md-6">
                    <div className="card shadow-sm">
                        <div className="card-body">
                            <h5 className="card-title">Top 5 Risky Assets</h5>
                            {topAssets.length === 0 ? (
                                <p className="text-muted">No data</p>
                            ) : (
                                <table className="table table-sm table-hover">
                                    <thead>
                                        <tr>
                                            <th>Asset</th>
                                            <th className="text-end">Score</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {topAssets.map((asset) => (
                                            <tr key={asset._id}>
                                                <td>{asset.name}</td>
                                                <td className="text-end text-danger fw-bold">
                                                    {asset.risk?.score || 0}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </div>
                </div>

                {/* Top High-Severity Detections */}
                <div className="col-md-6">
                    <div className="card shadow-sm">
                        <div className="card-body">
                            <h5 className="card-title">Top 5 High-Severity Detections</h5>
                            {topHighSevDetections.length === 0 ? (
                                <p className="text-muted">No high-severity detections</p>
                            ) : (
                                <table className="table table-sm table-hover">
                                    <thead>
                                        <tr>
                                            <th>Indicator</th>
                                            <th>Severity</th>
                                            <th>Last Seen</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {topHighSevDetections.map((det) => (
                                            <tr key={det._id}>
                                                <td><code className="small">{det.indicator}</code></td>
                                                <td>
                                                    <span className={`badge bg-${det.severity >= 5 ? 'danger' : 'warning'}`}>
                                                        {det.severity}
                                                    </span>
                                                </td>
                                                <td className="small">
                                                    {format(new Date(det.last_seen), "MMM dd, HH:mm")}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}