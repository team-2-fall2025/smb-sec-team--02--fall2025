import { useEffect, useState, version } from "react";


export function Dashboard() {
  const URL = import.meta.env.VITE_API_BASE;
  const [stats, setStats] = useState({ assets: 0, intel_events: 0, risk_items: 0 });
  const [health, setHealth] = useState();
  const [version, setVersion] = useState({version: "unknown"});

    useEffect(() => {
      // Fetch stats
      fetch(`${URL}/api/stats`)
        .then((r) => r.json())
        .then((data) => setStats(data))
        .catch((err) => console.error("Stats fetch error:", err));

      // Fetch health
      fetch(`${URL}/health`)
        .then((r) => r.json())
        .then((data) => setHealth(data.status))
        .catch((err) => console.error("Health fetch error:", err));

      // Fetch version
      fetch(`${URL}/version`)
        .then((r) => r.json())
        .then((data) => setVersion(data))
        .catch((err) => console.error("Version fetch error:", err));
    }, []);

    return (
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Security Dashboard</h1>
        <div className="mb-4">
          <p>Health: <span className={health === "ok" ? "text-green-500" : "text-red-500"}>{health}</span></p>
          <p>Version: {version.version}</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="card bg-gray-100 p-4 rounded shadow">
            <h2 className="text-lg font-semibold">Assets</h2>
            <p className="text-2xl">{stats.assets}</p>
          </div>
          <div className="card bg-gray-100 p-4 rounded shadow">
            <h2 className="text-lg font-semibold">Latest Intel Events</h2>
            <p className="text-2xl">{stats.intel_events}</p>
          </div>
          <div className="card bg-gray-100 p-4 rounded shadow">
            <h2 className="text-lg font-semibold">Risk Items</h2>
            <p className="text-2xl">{stats.risk_items}</p>
          </div>
        </div>
      </div>
    );
}