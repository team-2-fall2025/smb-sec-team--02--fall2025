// src/pages/ControlsList.tsx
import { useState, useMemo, useEffect } from "react";
import { Button, Table, Form, Row, Col, Badge } from "react-bootstrap";
import { useNavigate } from "react-router-dom";

interface Control {
  _id: string;
  control_id: string;
  title: string;
  family: string;
  csf_category: string;
  implementation_status: "Proposed" | "In-Progress" | "Implemented" | "Declined";
  created_at: string;
}

export function ControlsList() {
  const navigate = useNavigate();
  // @ts-ignore
  const URL = import.meta.env.VITE_API_URL;

  const [controls, setControls] = useState<Control[]>([]);
  const [filterFamily, setFilterFamily] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  useEffect(() => {
    fetch(`${URL}/api/protect`)
      .then((r) => r.json())
      .then((data) => setControls(data))
      .catch((err) => console.error("Failed to load controls:", err));
  }, [URL]);

  const filteredControls = useMemo(() => {
    let filtered = [...controls];

    if (filterFamily) {
      filtered = filtered.filter((c) => c.family === filterFamily);
    }
    if (filterCategory) {
      filtered = filtered.filter((c) =>
        c.csf_category.toLowerCase().includes(filterCategory.toLowerCase())
      );
    }
    if (filterStatus) {
      filtered = filtered.filter((c) => c.implementation_status === filterStatus);
    }

    return filtered.sort((a, b) => a.control_id.localeCompare(b.control_id));
  }, [controls, filterFamily, filterCategory, filterStatus]);

  const families = Array.from(new Set(controls.map((c) => c.family))).sort();
  const categories = Array.from(new Set(controls.map((c) => c.csf_category))).sort();
  const statuses: Control["implementation_status"][] = [
    "Proposed",
    "In-Progress",
    "Implemented",
  ];

  const getStatusBadge = (status: string) => {
    const map: Record<string, string> = {
      Proposed: "secondary",
      "In-Progress": "warning",
      Implemented: "success",
    };
    return map[status] || "dark";
  };

  return (
    <div className="container mt-4">
      <h3 className="mb-3 fw-bold text-primary">Security Controls</h3>

      <Row className="mb-3 g-2">
        <Col md={3}>
          <Form.Select value={filterFamily} onChange={(e) => setFilterFamily(e.target.value)}>
            <option value="">All Families</option>
            {families.map((f) => (
              <option key={f} value={f}>
                {f} (Access, System, etc.)
              </option>
            ))}
          </Form.Select>
        </Col>

        <Col md={3}>
          <Form.Control
            placeholder="Filter CSF Category (e.g. PR.AC)"
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
          />
        </Col>

        <Col md={3}>
          <Form.Select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            <option value="">All Statuses</option>
            {statuses.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </Form.Select>
        </Col>

        <Col className="d-flex justify-content-end">
          <Button variant="primary" onClick={() => navigate("/")}>
            Back to Dashboard
          </Button>
        </Col>
      </Row>

      <Table striped bordered hover responsive>
        <thead className="table-primary">
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Family</th>
            <th>CSF Category</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {filteredControls.map((ctrl) => (
            <tr key={ctrl._id}>
              <td>
                <code>{ctrl.control_id}</code>
              </td>
              <td>{ctrl.title}</td>
              <td>
                <Badge bg="info">{ctrl.family}</Badge>
              </td>
              <td>{ctrl.csf_category}</td>
              <td>
                <Badge bg={getStatusBadge(ctrl.implementation_status)}>
                  {ctrl.implementation_status}
                </Badge>
              </td>
              <td>
                <Button
                  size="sm"
                  variant="outline-primary"
                  onClick={() => navigate(`/controls/${ctrl.control_id}`)}
                >
                  View Details
                </Button>
              </td>
            </tr>
          ))}
          {filteredControls.length === 0 && (
            <tr>
              <td colSpan={6} className="text-center text-muted">
                No controls match your filters.
              </td>
            </tr>
          )}
        </tbody>
      </Table>
    </div>
  );
}