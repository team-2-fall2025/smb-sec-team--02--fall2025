import { useEffect, useState } from "react";
import { Asset } from "../models/Asset";

export function Dashboard() {
  
  // @ts-ignore
  const URL = import.meta.env.VITE_API_URL;
  const [stats, setStats] = useState({ assets: 0, intel_events: 0, risk_items: 0 });
  const [health, setHealth] = useState();
  const [version, setVersion] = useState({ version: "unknown" });
  const [topAssets, setTopAssets] = useState<any[]>([]);

  useEffect(() => {
    fetch(`${URL}/api/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch((err) => console.error("Stats fetch error:", err));

    fetch(`${URL}/health`)
      .then((r) => r.json())
      .then((data) => setHealth(data.status))
      .catch((err) => console.error("Health fetch error:", err));

    fetch(`${URL}/version`)
      .then((r) => r.json())
      .then(setVersion)
      .catch((err) => console.error("Version fetch error:", err));
    const fetchTopAssets = async () => {
      try {
        const res = await fetch(`${URL}/api/assets/top-risky`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ limit: 5 }),
        });

        if (!res.ok) {
          throw new Error(`Failed to fetch top assets: ${res.status}`);
        }

        const data = await res.json();
        debugger;
        setTopAssets(data.data); // data.data contains the list of assets
      } catch (err) {
        console.error(err);
      }
    };

    fetchTopAssets();
}, []);


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

    <div className="row">
      <div className="col-md-4 mb-3">
        <div className="card shadow-sm">
          <div className="card-body">
            <h5 className="card-title">Assets</h5>
            <p className="display-6">{stats.assets}</p>
          </div>
        </div>
      </div>
      <div className="col-md-4 mb-3">
        <div className="card shadow-sm">
          <div className="card-body">
            <h5 className="card-title">Intel Events</h5>
            <p className="display-6">{stats.intel_events}</p>
          </div>
        </div>
      </div>
      <div className="col-md-4 mb-3">
        <div className="card shadow-sm">
          <div className="card-body">
            <h5 className="card-title">Risk Items</h5>
            <p className="display-6">{stats.risk_items}</p>
          </div>
        </div>
      </div>
      <div className="col-md-4 mb-3">
        <div className="card shadow-sm">
          <div className="card-body">
            <h5 className="card-title">Top 5 Risky Assets</h5>
            <p className="display-6">{stats.risk_items}</p>
          </div>
        </div>
      </div>
      {/* Top 5 Risky Assets */}
      <div className="card bg-gray-100 p-4 rounded shadow col-span-1 md:col-span-1">
        <h2 className="text-lg font-semibold mb-2">Top 5 Risky Assets</h2>
        {topAssets.length === 0 ? (
          <p className="text-muted">No data</p>
        ) : (
          <ul className="list-group list-group-flush">
            {topAssets.map((asset) => (
              <li key={asset._id} className="list-group-item d-flex justify-content-between align-items-center">
                {asset.name}
                <span className="badge bg-danger">{asset.risk.score}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  </div>
);
}