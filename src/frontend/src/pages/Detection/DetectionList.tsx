import { useState, useMemo, useEffect } from "react";
import { Button, Table, Form, Row, Col } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { format } from "date-fns";
import { Detection } from "../../models/Detection";

// -------------------------------------------------------------------
// 1. Detection type (matches backend Pydantic model)
// -------------------------------------------------------------------
// -------------------------------------------------------------------
// 2. Detections List Component (client-side filtering only)
// -------------------------------------------------------------------
export function DetectionList() {
  const navigate = useNavigate();
  // @ts-ignore
  const URL = import.meta.env.VITE_API_URL;

  // -----------------------------------------------------------------
  // State
  // -----------------------------------------------------------------
  const [detections, setDetections] = useState<Detection[]>([]);
  const [searchIndicator, setSearchIndicator] = useState("");
  const [filterSeverity, setFilterSeverity] = useState("");
  const [filterSource, setFilterSource] = useState("");
  const [filterAsset, setFilterAsset] = useState("");
  const [filterTTP, setFilterTTP] = useState("");
  const [sortByLastSeen, setSortByLastSeen] = useState<"asc" | "desc" | "">("");

  // -----------------------------------------------------------------
  // Fetch ALL detections once (no query params)
  // -----------------------------------------------------------------
  useEffect(() => {
    fetch(`${URL}/api/detect/detections`)
      .then((r) => r.json())
      .then((res) => setDetections(res.data || res))
      .catch((err) => console.error("Detections fetch error:", err));
  }, [URL]);

  // -----------------------------------------------------------------
  // Client-side filtering & sorting (useMemo = like Assets)
  // -----------------------------------------------------------------
  const filteredDetections = useMemo(() => {
    let filtered = [...detections];

    // Search by indicator (partial, case-insensitive)
    if (searchIndicator) {
      filtered = filtered.filter((d) =>
        d.indicator.toLowerCase().includes(searchIndicator.toLowerCase())
      );
    }

    // Filter by severity (exact)
    if (filterSeverity) {
      filtered = filtered.filter((d) => d.severity === Number(filterSeverity));
    }

    // Filter by source (partial)
    if (filterSource) {
      filtered = filtered.filter((d) =>
        d.source.toLowerCase().includes(filterSource.toLowerCase())
      );
    }

    // Filter by asset_id (partial)
    if (filterAsset) {
      filtered = filtered.filter((d) =>
        d.asset_id.toLowerCase().includes(filterAsset.toLowerCase())
      );
    }

    // Filter by TTP (any match in array)
    if (filterTTP) {
      filtered = filtered.filter((d) =>
        d.ttp.some((t) => t.toLowerCase().includes(filterTTP.toLowerCase()))
      );
    }

    // Sort by last_seen
    if (sortByLastSeen === "asc") {
      filtered.sort(
        (a, b) => new Date(a.last_seen).getTime() - new Date(b.last_seen).getTime()
      );
    } else if (sortByLastSeen === "desc") {
      filtered.sort(
        (a, b) => new Date(b.last_seen).getTime() - new Date(a.last_seen).getTime()
      );
    }

    return filtered;
  }, [
    detections,
    searchIndicator,
    filterSeverity,
    filterSource,
    filterAsset,
    filterTTP,
    sortByLastSeen,
  ]);

  // -----------------------------------------------------------------
  // Unique values for dropdowns
  // -----------------------------------------------------------------
  const sources = Array.from(new Set(detections.map((d) => d.source)));
  const ttps = Array.from(new Set(detections.flatMap((d) => d.ttp))).sort();

  // -----------------------------------------------------------------
  // Severity badge color
  // -----------------------------------------------------------------
  const getSeverityBadge = (sev: number) => {
    const map: Record<number, string> = {
      1: "secondary",
      2: "info",
      3: "primary",
      4: "warning",
      5: "danger",
    };
    return map[sev] || "secondary";
  };

  // -----------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------
  return (
    <div className="container mt-4">
      <h3 className="mb-3 fw-bold text-primary">Detections</h3>

      {/* ------------------------------------------------------------- */}
      {/* Filters (exact copy of Assets layout) */}
      {/* ------------------------------------------------------------- */}
      <Row className="mb-3 g-2">
        <Col md={2}>
          <Form.Control
            placeholder="Search Indicator"
            value={searchIndicator}
            onChange={(e) => setSearchIndicator(e.target.value)}
          />
        </Col>

        <Col md={2}>
          <Form.Select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
          >
            <option value="">All Severities</option>
            {[1, 2, 3, 4, 5].map((s) => (
              <option key={s} value={s}>
                {s} - {s === 5 ? "Critical" : s === 4 ? "High" : s === 3 ? "Medium" : s === 2 ? "Low" : "Info"}
              </option>
            ))}
          </Form.Select>
        </Col>

        <Col md={2}>
          <Form.Control
            placeholder="Filter Source"
            value={filterSource}
            onChange={(e) => setFilterSource(e.target.value)}
          />
        </Col>

        <Col md={2}>
          <Form.Control
            placeholder="Filter Asset"
            value={filterAsset}
            onChange={(e) => setFilterAsset(e.target.value)}
          />
        </Col>

        <Col md={2}>
          <Form.Select
            value={filterTTP}
            onChange={(e) => setFilterTTP(e.target.value)}
          >
            <option value="">All TTPs</option>
            {ttps.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </Form.Select>
        </Col>

        <Col md={2}>
          <Form.Select
            value={sortByLastSeen}
            onChange={(e) =>
              setSortByLastSeen(e.target.value as "asc" | "desc" | "")
            }
          >
            <option value="">Sort by Last Seen</option>
            <option value="desc">Newest First</option>
            <option value="asc">Oldest First</option>
          </Form.Select>
        </Col>

        <Col className="d-flex justify-content-end">
          <Button variant="primary" onClick={() => navigate("/")}>
            Back to Dashboard
          </Button>
        </Col>
      </Row>

      {/* ------------------------------------------------------------- */}
      {/* Table */}
      {/* ------------------------------------------------------------- */}
      <Table striped bordered hover responsive>
        <thead className="table-primary">
          <tr>
            <th>#</th>
            <th>Last Seen</th>
            <th>Asset</th>
            <th>Indicator</th>
            <th>Severity</th>
            <th>Confidence</th>
            <th>TTPs</th>
            <th>Source</th>
            <th>Hits</th>
            <th style={{ width: "100px" }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {filteredDetections.map((det, index) => (
            <tr key={det._id}>
              <td>{index + 1}</td>
              <td>{format(new Date(det.last_seen), "MMM dd, HH:mm")}</td>
              <td>{det.asset_name}</td>
              <td>
                <code className="small">{det.indicator}</code>
              </td>
              <td>
                <span className={`badge bg-${getSeverityBadge(det.severity)}`}>
                  {det.severity}
                </span>
              </td>
              <td>{det.confidence}%</td>
              <td>
                <div className="d-flex flex-wrap gap-1">
                  {det.ttp.map((t) => (
                    <span key={t} className="badge bg-secondary small">
                      {t}
                    </span>
                  ))}
                </div>
              </td>
              <td>{det.source}</td>
              <td>{det.hit_count}</td>
              <td>
                <Button
                  variant="info"
                  size="sm"
                  onClick={() => navigate(`/detection/${det._id}`)}
                >
                  View
                </Button>
              </td>
            </tr>
          ))}
          {filteredDetections.length === 0 && (
            <tr>
              <td colSpan={10} className="text-center text-muted">
                No detections found.
              </td>
            </tr>
          )}
        </tbody>
      </Table>
    </div>
  );
}