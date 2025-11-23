// src/pages/ControlDetailPage.tsx
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Badge, ListGroup, Button, Table, Alert } from "react-bootstrap";
import { format } from "date-fns";

interface ControlDetail {
  control_id: string;
  title: string;
  family: string;
  csf_function: string;
  csf_category: string;
  implementation_status: string;
  applicability_rule: any;
  sop_html: string;
  applicable_assets: Array<{
    asset_id: string;
    name: string;
    ip_address?: string;
    asset_type?: string;
    tags: string[];
    assignment_status: string;
  }>;
  evidence: Array<{
    _id: string;
    evidence_type: string;
    location: string;
    submitted_by: string;
    submitted_at: string;
  }>;
  created_at: string;
}

export function ControlDetailPage() {
  const { control_id } = useParams<{ control_id: string }>();
  const navigate = useNavigate();
  // @ts-ignore
  const URL = import.meta.env.VITE_API_URL;

  const [control, setControl] = useState<ControlDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${URL}/api/protect/${control_id}`)
      .then((r) => {
        if (!r.ok) throw new Error("Not found");
        return r.json();
      })
      .then((data) => {
        setControl(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [control_id, URL]);

  if (loading) return <div className="container mt-4">Loading control...</div>;
  if (!control) return <div className="container mt-4">Control not found.</div>;

  return (
    <div className="container mt-4">
      <h3 className="mb-3 fw-bold text-primary">
        Control: {control.control_id} – {control.title}
      </h3>

      <div className="row g-4">
        {/* Header Info */}
        <div className="col-12">
          <div className="d-flex gap-3 align-items-center flex-wrap">
            <Badge bg="dark" className="fs-6">
              {control.family} Family
            </Badge>
            <Badge bg="info">{control.csf_category}</Badge>
            <Badge bg={control.implementation_status === "Implemented" ? "success" : "warning"}>
              {control.implementation_status}
            </Badge>
          </div>
        </div>

        {/* SOP */}
        <div className="col-lg-8">
          <Card>
            <Card.Header className="bg-primary text-white">
              <strong>Implementation SOP</strong>
            </Card.Header>
            <Card.Body>
              <div
                dangerouslySetInnerHTML={{ __html: control.sop_html || "<p>No SOP defined yet.</p>" }}
                className="markdown-content"
                style={{ lineHeight: "1.6" }}
              />
            </Card.Body>
          </Card>
        </div>

        {/* Applicable Assets */}
        <div className="col-lg-4">
          <Card className="h-100">
            <Card.Header className="bg-info text-white">
              <strong>Applicable Assets ({control.applicable_assets.length})</strong>
            </Card.Header>
            <Card.Body className="p-0">
              <ListGroup variant="flush">
                {control.applicable_assets.length > 0 ? (
                  control.applicable_assets.map((asset) => (
                    <ListGroup.Item key={asset.asset_id}>
                      <div>
                        <strong>{asset.name}</strong>
                        <Badge bg="secondary" className="ms-2 small">
                          {asset.assignment_status}
                        </Badge>
                      </div>
                      <small className="text-muted">
                        {asset.ip_address || asset.asset_type}
                      </small>
                      {asset.tags.length > 0 && (
                        <div className="mt-1">
                          {asset.tags.map((t) => (
                            <Badge key={t} bg="light" text="dark" className="me-1 small">
                              {t}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </ListGroup.Item>
                  ))
                ) : (
                  <ListGroup.Item>
                    <em className="text-muted">No assets assigned yet</em>
                  </ListGroup.Item>
                )}
              </ListGroup>
            </Card.Body>
          </Card>
        </div>

        {/* Evidence */}
        <div className="col-12">
          <Card>
            <Card.Header className="bg-success text-white">
              <strong>Evidence Records ({control.evidence.length})</strong>
            </Card.Header>
            <Card.Body>
              {control.evidence.length > 0 ? (
                <Table striped hover>
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Location</th>
                      <th>Submitted By</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {control.evidence.map((ev) => (
                      <tr key={ev._id}>
                        <td>{ev.evidence_type}</td>
                        <td>
                          <code className="small">{ev.location}</code>
                        </td>
                        <td>{ev.submitted_by}</td>
                        <td>{format(new Date(ev.submitted_at), "PPp")}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              ) : (
                <Alert variant="light">No evidence submitted yet.</Alert>
              )}
            </Card.Body>
          </Card>
        </div>
      </div>

      <div className="mt-4">
        <Button variant="secondary" onClick={() => navigate("/controls")}>
          ← Back to Controls List
        </Button>
      </div>
    </div>
  );
}