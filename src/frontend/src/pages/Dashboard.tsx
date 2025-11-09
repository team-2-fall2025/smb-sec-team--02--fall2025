import { useEffect, useState } from "react";
import { format, subDays } from "date-fns";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

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

    useEffect(() => {
        // 1. Stats
        fetch(`${URL}/api/stats`)
            .then((r) => r.json())
            .then(setStats)
            .catch((err) => console.error("Stats error:", err));

        // 2. Health
        fetch(`${URL}/health`)
            .then((r) => r.json())
            .then((data) => setHealth(data.status))
            .catch((err) => console.error("Health error:", err));

        // 3. Version
        fetch(`${URL}/version`)
            .then((r) => r.json())
            .then(setVersion)
            .catch((err) => console.error("Version error:", err));

        // 4. Top 5 Risky Assets
        fetch(`${URL}/api/assets/top-risky`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ limit: 5 }),
        })
            .then((r) => r.json())
            .then((data) => setTopAssets(data.data || []))
            .catch((err) => console.error("Top assets error:", err));

        // 5. Detections (24h)
        const oneDayAgo = subDays(new Date(), 1).toISOString();
        fetch(`${URL}/api/detect/lastDay?last_seen_gte=${oneDayAgo}`)
            .then((r) => r.json())
            .then((data) => setDetections24h(data || 0))
            .catch((err) => console.error("24h detections error:", err));

        // 6. Detections Trend (7 days)
        fetch(`${URL}/api/detect/trend?days=7`)
            .then((r) => r.json())
            .then((data) => {
                const trend = (data.data || data).map((d: any) => ({
                    day: format(new Date(d.date), "MMM dd"),
                    count: d.count,
                }));
                setDetectionsTrend(trend);
            })
            .catch((err) => console.error("Trend error:", err));

        // 7. Top 5 High-Severity Detections
        fetch(`${URL}/api/detect/high-sev?min_severity=3&limit=5`)
            .then((r) => r.json())
            .then((data) => setTopHighSevDetections(data.data || data))
            .catch((err) => console.error("High-sev error:", err));
    }, [URL]);

    return (
        <div className="container-fluid">
            <h1 className="mb-4">Security Dashboard</h1>

            <div className="mb-4">
                <p>
                    Health:{" "}
                    <span className={health === "ok" ? "text-success" : "text-danger"}>
                        {health}
                    </span>
                </p>
                <p>Version: {version.version}</p>
            </div>

            <div className="row g-3">
                {/* 1. Assets */}
                <div className="col-md-3">
                    <div className="card shadow-sm h-100">
                        <div className="card-body text-center">
                            <h5 className="card-title">Assets</h5>
                            <p className="display-6">{stats.assets}</p>
                        </div>
                    </div>
                </div>

                {/* 2. Intel Events */}
                <div className="col-md-3">
                    <div className="card shadow-sm h-100">
                        <div className="card-body text-center">
                            <h5 className="card-title">Intel Events</h5>
                            <p className="display-6">{stats.intel_events}</p>
                        </div>
                    </div>
                </div>

                {/* 3. Risk Items */}
                <div className="col-md-3">
                    <div className="card shadow-sm h-100">
                        <div className="card-body text-center">
                            <h5 className="card-title">Risk Items</h5>
                            <p className="display-6">{stats.risk_items}</p>
                        </div>
                    </div>
                </div>

                {/* 4. Detections (24h) + Trendline */}
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

                {/* 5. Top 5 Risky Assets */}
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

                {/* 6. Top 5 High-Severity Detections */}
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
                                                <td>
                                                    <code className="small">{det.indicator}</code>
                                                </td>
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