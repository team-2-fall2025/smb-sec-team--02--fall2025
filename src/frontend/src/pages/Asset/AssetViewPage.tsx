// src/pages/AssetViewPage.tsx (updated version)
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Table, Badge, Row, Col, Tabs, Tab, Button, Modal, Form, Alert } from "react-bootstrap";
import { format } from "date-fns";
import { Asset } from "../../models/Asset";

interface PolicyAssignment {
  _id: string;
  control_id: string;
  control_title: string;
  family: string;
  csf_category: string;
  status: "Proposed" | "In-Progress" | "Implemented";
  evidence?: Array<{
    _id: string;
    evidence_type: string;
    location: string;
    submitted_by: string;
    submitted_at: string;
  }>;
}

export function AssetViewPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [asset, setAsset] = useState<Asset | null>(null);
  const [assignments, setAssignments] = useState<PolicyAssignment[]>([]);
  const [showEvidenceModal, setShowEvidenceModal] = useState(false);
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<string>("");
  const [evidenceNote, setEvidenceNote] = useState("");

  // @ts-ignore
  const URL = import.meta.env.VITE_API_URL;

  useEffect(() => {
    // Load asset
    console.log("Fetching asset data... " + id);
    fetch(`${URL}/api/assets/${id}`)
      .then(r => r.json())
      .then(res => setAsset(res.data));

    // Load applicable controls for this asset
    fetch(`${URL}/api/protect/get-assignments/${id}`)
      .then(r => r.json())
      .then(data => setAssignments(data))
      .catch(() => setAssignments([]));
  }, [id, URL]);

  const handleStatusChange = async (assignmentId: string, newStatus: string) => {
    await fetch(`${URL}/api/protect/update_assignment/${assignmentId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    setAssignments(prev => prev.map(a => a._id === assignmentId ? { ...a, status: newStatus as any } : a));
  };

  const handleUploadEvidence = async () => {
    if (!evidenceNote.trim()) return;

    const payload = {
      control_assignment_id: selectedAssignmentId,
      evidence_type: "screenshot",
      location: `/evidence/${crypto.randomUUID()}`,
      notes: evidenceNote
    };

    await fetch(`${URL}/api/protect/upload_evidence`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    setShowEvidenceModal(false);
    setEvidenceNote("");
    // Reload assignments
    fetch(`${URL}/api/protect/get-assignments/${id}`)
      .then(r => r.json())
      .then(data => setAssignments(data))
      .catch(() => setAssignments([]));
  };

  if (!asset) return <p className="text-center mt-4">Loading asset...</p>;

  const getStatusBadge = (status: string) => {
    const map: Record<string, string> = {
      Proposed: "secondary",
      "In-Progress": "warning",
      Implemented: "success"
    };
    return map[status] || "dark";
  };

  return (
    <div className="container mt-4">
      <h3 className="mb-3 fw-bold text-primary">Assets</h3>

      {/* Header */}
      <div className="d-flex align-items-center justify-content-between mb-4">
        <h2>{asset.name}</h2>
        <div className="d-flex gap-2">
          <Badge bg="primary">{asset.type}</Badge>
          <Badge bg="danger">Criticality: {asset.criticality}</Badge>
          <Badge bg="warning" text="dark">Sensitivity: {asset.data_sensitivity}</Badge>
        </div>
      </div>

      <Tabs defaultActiveKey="details" className="mb-4">
        {/* Existing Tabs */}
        <Tab eventKey="details" title="General">
          <Card className="mb-4">
                <Card.Header>General Details</Card.Header>
                <Card.Body>
                <Row className="mb-2">
                    <Col md={4}><strong>Organization:</strong> {asset.org}</Col>
                    <Col md={4}><strong>IP Address:</strong> {asset.ip}</Col>
                    <Col md={4}><strong>Hostname:</strong> {asset.hostname}</Col>
                </Row>
                <Row className="mb-2">
                    <Col md={4}><strong>Owner:</strong> {asset.owner}</Col>
                    <Col md={4}><strong>Business Unit:</strong> {asset.business_unit}</Col>
                    <Col md={4}><strong>Status:</strong> {asset.risk.score > 0 ? "At Risk" : "Normal"}</Col>
                </Row>
                </Card.Body>
            </Card>

            {/* Recent Intel Table */}
            <Card className="mb-4">
                <Card.Header>Recent Intel</Card.Header>
                <Card.Body>
                    {asset.intel_events.length === 0 ? (
                        <p className="text-muted">No recent intel found.</p>
                    ) : (
                        <Table striped bordered hover responsive>
                            <thead className="table-secondary">
                                <tr>
                                    <th>Summary</th>
                                    <th>Source</th>
                                    <th>Indicator Type</th>
                                    <th>Indicator</th>
                                    <th>Severity</th>
                                    <th>Created Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                {asset.intel_events.map((intel, idx) => (
                                    <tr key={idx}>
                                        <td>{intel.summary}</td>
                                        <td>{intel.source}</td>
                                        <td>{intel.indicator_type}</td>
                                        <td>{intel.indicator}</td>
                                        <td>{intel.severity}</td>
                                        <td>{intel.created_at}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </Table>
                    )}
                </Card.Body>
            </Card>

            {/* Risk Panel */}
            <Card>
                <Card.Header>Risk</Card.Header>
                <Card.Body>
                    <div className="d-flex justify-content-between align-items-center mb-2">
                        <div>
                            <h4 className="mb-0">Current Score: {asset.risk.score}</h4>
                            <small className="text-muted">{asset.risk.explain}</small>
                        </div>
                        <div>
                            {/* Placeholder sparkline (just a gray box) */}
                            <div
                                style={{
                                    width: "150px",
                                    height: "50px",
                                    backgroundColor: "#e9ecef",
                                    borderRadius: "4px",
                                }}
                            >
                                <p
                                    className="text-center mt-2 text-muted"
                                    style={{ fontSize: "0.8rem" }}
                                >
                                    7-day sparkline
                                </p>
                            </div>
                        </div>
                    </div>
                </Card.Body>
            </Card>
        </Tab>

        {/* NEW CONTROLS TAB */}
        <Tab eventKey="controls" title={`Controls (${assignments.length})`}>
          <Card className="mt-3">
            <Card.Header className="bg-success text-white">
              <strong>Applicable Security Controls</strong>
            </Card.Header>
            <Card.Body>
              {assignments.length === 0 ? (
                <Alert variant="info">No controls assigned to this asset yet.</Alert>
              ) : (
                <Table striped bordered hover responsive>
                  <thead className="table-primary">
                    <tr>
                      <th>Control ID</th>
                      <th>Title</th>
                      <th>Family</th>
                      <th>CSF</th>
                      <th>Status</th>
                      <th>Evidence</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assignments.map((assign) => (
                      <tr key={assign._id}>
                        <td><code>{assign.control_id}</code></td>
                        <td>{assign.control_title}</td>
                        <td><Badge bg="info">{assign.family}</Badge></td>
                        <td><small>{assign.csf_category}</small></td>
                        <td>
                          <Form.Select
                            size="sm"
                            value={assign.status}
                            onChange={(e) => handleStatusChange(assign._id, e.target.value)}
                            style={{ width: "140px" }}
                          >
                            <option value="Proposed">Proposed</option>
                            <option value="In-Progress">In-Progress</option>
                            <option value="Implemented">Implemented</option>
                          </Form.Select>
                        </td>
                        <td>
                          {assign.evidence && assign.evidence.length > 0 ? (
                            <Badge bg="success">Yes ({assign.evidence.length})</Badge>
                          ) : (
                            <Badge bg="light" text="dark">None</Badge>
                          )}
                        </td>
                        <td>
                          <Button
                            size="sm"
                            variant="outline-primary"
                            onClick={() => {
                              setSelectedAssignmentId(assign._id);
                              setShowEvidenceModal(true);
                            }}
                          >
                            Upload Evidence
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Card.Body>
          </Card>
        </Tab>
      </Tabs>

      {/* Evidence Upload Modal */}
      <Modal show={showEvidenceModal} onHide={() => setShowEvidenceModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Upload Evidence (Metadata)</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group>
            <Form.Label>Notes / Description</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={evidenceNote}
              onChange={(e) => setEvidenceNote(e.target.value)}
              placeholder="e.g., Screenshot of MFA policy applied to this server"
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowEvidenceModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleUploadEvidence}>
            Submit Evidence
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}