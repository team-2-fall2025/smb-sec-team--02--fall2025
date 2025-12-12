import { useState, useMemo, useEffect } from "react";
import { Button, Table, Form, Row, Col, Modal, Badge } from "react-bootstrap";
import { useNavigate } from "react-router-dom";

export interface Incident {
  _id: string;
  asset_name: string;
  severity: number;
  status: "Triage" | "Investigation" | "Containment" | "Remediation" | "Closed" | "Reopened";
  opened_at: string;
  owner: string | null;
  sla_status: "ok" | "warning" | "breached";
}

export function Incidents() {
  const navigate = useNavigate();

  // @ts-ignore
  const URL = import.meta.env.VITE_API_URL;
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [searchOwner, setSearchOwner] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterSeverity, setFilterSeverity] = useState("");
  const [filterSlaStatus, setFilterSlaStatus] = useState("");
  const [sortByDate, setSortByDate] = useState<"newest" | "oldest" | "">("newest");

  useEffect(() => {
    fetch(`${URL}/api/respond/getIncidents`)
      .then((r) => r.json())
      .then(res => setIncidents(res.data))
      .catch((err) => console.error("Incidents fetch error:", err));
  }, []);

  const filteredIncidents = useMemo(() => {
    let filtered = incidents;
    
    // Filter by title search
    if (searchOwner) {
      filtered = filtered.filter((i) =>
        i.owner?.toLowerCase().includes(searchOwner.toLowerCase())
      );
    }

    // Filter by status
    if (filterStatus) {
      filtered = filtered.filter((i) => i.status === filterStatus);
    }

    // Filter by severity
    if (filterSeverity) {
      filtered = filtered.filter((i) => i.severity === parseInt(filterSeverity));
    }

    // Filter by SLA status
    if (filterSlaStatus) {
      filtered = filtered.filter((i) => i.sla_status === filterSlaStatus);
    }

    // Sort by date
    if (sortByDate === "newest") {
      filtered = [...filtered].sort(
        (a, b) => new Date(b.opened_at).getTime() - new Date(a.opened_at).getTime()
      );
    } else if (sortByDate === "oldest") {
      filtered = [...filtered].sort(
        (a, b) => new Date(a.opened_at).getTime() - new Date(b.opened_at).getTime()
      );
    }

    return filtered;
  }, [incidents, searchOwner, filterStatus, filterSeverity, filterSlaStatus, sortByDate]);

  // Get severity badge color
  const getSeverityColor = (severity: number) => {
    switch (severity) {
      case 1: return "info";
      case 2: return "warning";
      case 3: return "danger";
      case 4: return "dark";
      default: return "secondary";
    }
  };

  // Get severity text
  const getSeverityText = (severity: number) => {
    switch (severity) {
      case 1: return "Low";
      case 2: return "Medium";
      case 3: return "High";
      case 4: return "Critical";
      default: return "Unknown";
    }
  };

  // Get SLA status badge color
  const getSlaStatusColor = (status: string) => {
    switch (status) {
      case "ok": return "success";
      case "warning": return "warning";
      case "breached": return "danger";
      default: return "secondary";
    }
  };

  // Get status badge color
  const getStatusColor = (status: string) => {
    switch (status) {
      case "Triage": return "primary";
      case "Investigation": return "info";
      case "Containment": return "warning";
      case "Remediation": return "danger";
      case "Closed": return "success";
      case "Reopened": return "secondary";
      default: return "light";
    }
  };

  // Get unique status values for filter
  const statuses = Array.from(new Set(incidents.map((i) => i.status)));
  // Get unique severity values for filter
  const severities = Array.from(new Set(incidents.map((i) => i.severity))).sort();
  // Get unique SLA status values for filter
  const slaStatuses = Array.from(new Set(incidents.map((i) => i.sla_status)));

  return (
    <div className="container mt-4">
      <h3 className="mb-3 fw-bold text-primary">Incidents</h3>

      {/* Filters */}
      <Row className="mb-3 g-2">
        <Col md={3}>
          <Form.Control
            placeholder="Search by Owner"
            value={searchOwner}
            onChange={(e) => setSearchOwner(e.target.value)}
          />
        </Col>
        <Col md={2}>
          <Form.Select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="">All Statuses</option>
            {statuses.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </Form.Select>
        </Col>
        <Col md={2}>
          <Form.Select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
          >
            <option value="">All Severities</option>
            {severities.map((severity) => (
              <option key={severity} value={severity}>
                {getSeverityText(severity)}
              </option>
            ))}
          </Form.Select>
        </Col>
        <Col md={2}>
          <Form.Select
            value={filterSlaStatus}
            onChange={(e) => setFilterSlaStatus(e.target.value)}
          >
            <option value="">All SLA Statuses</option>
            {slaStatuses.map((status) => (
              <option key={status} value={status}>
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </option>
            ))}
          </Form.Select>
        </Col>
        <Col md={2}>
          <Form.Select
            value={sortByDate}
            onChange={(e) =>
              setSortByDate(e.target.value as "newest" | "oldest" | "")
            }
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
          </Form.Select>
        </Col>
      </Row>

      {/* Incidents Table */}
      <Table striped bordered hover responsive>
        <thead className="table-primary">
          <tr>
            <th>#</th>
            {/* <th>Title</th> */}
            <th>Id</th>
            <th>Severity</th>
            <th>Status</th>
            <th>Asset</th>
            <th>Opened</th>
            <th>SLA Status</th>
            <th>Owner</th>
            <th style={{ width: "100px" }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {filteredIncidents.map((incident, index) => (
            <tr key={incident._id}>
              <td>{index + 1}</td>
              <td><div className="fw-semibold">{incident._id}</div></td>
              <td>
                <Badge bg={getSeverityColor(incident.severity)}>
                  {getSeverityText(incident.severity)}
                </Badge>
              </td>
              <td>
                <Badge bg={getStatusColor(incident.status)}>
                  {incident.status}
                </Badge>
              </td>
              <td>
                {incident.asset_name}
              </td>
              <td>
                {new Date(incident.opened_at).toLocaleDateString()} {new Date(incident.opened_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </td>
              <td>
                <Badge bg={getSlaStatusColor(incident.sla_status)}>
                  {incident.sla_status.toUpperCase()}
                </Badge>
              </td>
              <td>
                {incident.owner ? (
                  <span>{incident.owner}</span>
                ) : (
                  <span className="text-muted">Unassigned</span>
                )}
              </td>
              <td>
                <div className="d-flex gap-2">
                  <Button
                    variant="info"
                    size="sm"
                    onClick={() => navigate(`/incidents/${incident._id}`)}
                  >
                    View
                  </Button>
                  {/* <Button
                    variant="warning"
                    size="sm"
                    onClick={() => navigate(`/incidents/edit/${incident._id}`)}
                  >
                    Edit
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleDeleteClick(incident)}
                  >
                    Delete
                  </Button> */}
                </div>
              </td>
            </tr>
          ))}
          {filteredIncidents.length === 0 && (
            <tr>
              <td colSpan={11} className="text-center text-muted">
                No incidents found.
              </td>
            </tr>
          )}
        </tbody>
      </Table>

      {/* Delete Confirmation Modal */}
      {/* <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Delete</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to delete{" "}
          <strong>{selectedIncident?.title}</strong>?
          <div className="mt-2 text-danger">
            This action cannot be undone.
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmDelete}>
            Delete Incident
          </Button>
        </Modal.Footer>
      </Modal> */}
    </div>
  );
}