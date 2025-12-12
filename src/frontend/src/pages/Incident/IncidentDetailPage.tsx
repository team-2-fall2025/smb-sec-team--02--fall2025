// src/pages/IncidentDetailPage.tsx
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Card,
  Badge,
  Button,
  Table,
  Alert,
  ListGroup,
  Form,
  Modal,
  Row,
  Col,
  ProgressBar,
  Tab,
  Tabs,
  Accordion
} from "react-bootstrap";
import { format, formatDistanceToNow } from "date-fns";
import { Asset } from "../../models/Asset";
import { Detection } from "../../models/Detection";
import { RiskItem } from "../../models/RiskItem";


interface IncidentTask {
  _id: string;
  incident_id: string;
  phase: string;
  title: string;
  assignee: string;
  due_at: string;
  status: "Open" | "Done" | "Skipped";
  notes: string;
  order: number;
  created_at: string;
  updated_at: string;
}

interface TimelineEvent {
  _id: string;
  incident_id: string;
  ts: string;
  actor: string; // "system" or "user:{id}"
  event_type: "opened" | "status_change" | "note" | "comms" | "evidence" | "task_update" | "link_added";
  detail: any;
  metadata?: any;
}

interface EvidenceItem {
  _id: string;
  incident_id: string;
  type: string;
  location: string;
  hash?: string;
  submitted_by: string;
  submitted_at: string;
  chain_of_custody: Array<{
    who: string;
    when: string;
    action: string;
  }>;
  asset_id?: string;
  detection_id?: string;
  task_id?: string;
}

interface IncidentDetail {
  _id: string;
  title: string;
  severity: number;
  status: "Open" | "Triage" | "Containment" | "Eradication" | "Recovery" | "Closed";
  opened_at: string;
  updated_at: string;
  closed_at: string | null;
  owner: string | null;
  sla_due_at: string;
  sla_status: "ok" | "warning" | "breached";
  primary_asset_id: string;
  summary: string;
  root_cause: string;
  lessons_learned: string;
  tags: string[];
  dedup_key: {
    rule_id?: string;
    hash?: string;
  };
  asset_refs: Asset[];
  detection_refs: Detection[];
  risk_item_refs: RiskItem[];
  tasks: IncidentTask[];
  timelines: TimelineEvent[];
  evidence: EvidenceItem[];
}

export function IncidentDetailPage() {
  const { incident_id } = useParams<{ incident_id: string }>();
  const navigate = useNavigate();
  // @ts-ignore
  const URL = import.meta.env.VITE_API_URL;

  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showEvidenceModal, setShowEvidenceModal] = useState(false);
  const [showAdvanceModal, setShowAdvanceModal] = useState(false);
  const [showCloseModal, setShowCloseModal] = useState(false);
  const [newTask, setNewTask] = useState({
    title: "",
    assignee: "",
    phase: "Triage",
    notes: ""
  });
  const [newEvidence, setNewEvidence] = useState({
    type: "log",
    location: "",
    hash: "",
    notes: ""
  });
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    fetchIncident();
  }, [incident_id, URL]);

  const fetchIncident = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${URL}/api/respond/getIncident/${incident_id}`);
      if (!response.ok) throw new Error("Incident not found");
      const data = await response.json();
      setIncident(data);
      setError(null);
    } catch (err) {
      setError("Failed to load incident");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

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
      case 1: return "P4 - Low";
      case 2: return "P3 - Medium";
      case 3: return "P2 - High";
      case 4: return "P1 - Critical";
      default: return "Unknown";
    }
  };

  // Get status badge color
  const getStatusColor = (status: string) => {
    switch (status) {
      case "Open": return "primary";
      case "Triage": return "info";
      case "Containment": return "warning";
      case "Eradication": return "danger";
      case "Recovery": return "success";
      case "Closed": return "secondary";
      default: return "light";
    }
  };

  // Get SLA status color
  const getSlaStatusColor = (status: string) => {
    switch (status) {
      case "ok": return "success";
      case "warning": return "warning";
      case "breached": return "danger";
      default: return "secondary";
    }
  };

  // Calculate SLA progress
  const calculateSlaProgress = () => {
    if (!incident) return { percent: 0, timeRemaining: "N/A" };
    
    const now = new Date();
    const opened = new Date(incident.opened_at);
    const due = new Date(incident.sla_due_at);
    
    const total = due.getTime() - opened.getTime();
    const elapsed = Math.abs(now.getTime() - opened.getTime());
    const remaining = due.getTime() - now.getTime();
    
    const percent = Math.min(100, Math.max(0, (elapsed / total) * 100));
    debugger;
    let timeRemaining = "";
    if (remaining < 0) {
      timeRemaining = `Breached ${formatDistanceToNow(due, { addSuffix: true })}`;
    } else if (remaining < 3600000) { // less than 1 hour
      timeRemaining = `${Math.ceil(remaining / 60000)} minutes remaining`;
    } else if (remaining < 86400000) { // less than 24 hours
      timeRemaining = `${Math.ceil(remaining / 3600000)} hours remaining`;
    } else {
      timeRemaining = `${Math.ceil(remaining / 86400000)} days remaining`;
    }
    console.log("SLA Progress:", percent, "%,", timeRemaining);
    return { percent, timeRemaining };
  };

  // Handle task status toggle
  const handleTaskToggle = async (taskId: string, currentStatus: "Open" | "Done" | "Skipped") => {
    try {
      const newStatus = currentStatus === "Open" ? "Done" : "Open";
      const response = await fetch(`${URL}/api/respond/incidents/${incident_id}/tasks/${taskId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      
      if (response.ok) {
        fetchIncident(); // Refresh incident data
      }
    } catch (err) {
      console.error("Failed to update task:", err);
    }
  };

  // Handle add new task
  const handleAddTask = async () => {
    try {
      const response = await fetch(`${URL}/api/respond/incidents/${incident_id}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newTask)
      });
      
      if (response.ok) {
        setNewTask({ title: "", assignee: "", phase: "Triage", notes: "" });
        setShowTaskModal(false);
        fetchIncident();
      }
    } catch (err) {
      console.error("Failed to add task:", err);
    }
  };

  // Handle add evidence
  const handleAddEvidence = async () => {
    try {
      const response = await fetch(`${URL}/api/respond/incidents/${incident_id}/evidence`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: newEvidence.type,
          location: newEvidence.location,
          hash: newEvidence.hash || undefined,
          submitted_by: "current_user", // Replace with actual user
          chain_of_custody: [{
            who: "current_user",
            when: new Date().toISOString(),
            action: "uploaded"
          }]
        })
      });
      
      if (response.ok) {
        setNewEvidence({ type: "log", location: "", hash: "", notes: "" });
        setShowEvidenceModal(false);
        fetchIncident();
      }
    } catch (err) {
      console.error("Failed to add evidence:", err);
    }
  };

  // Handle advance phase
  const handleAdvancePhase = async () => {
    if (!incident) return;
    
    const phaseOrder = ["Open", "Triage", "Containment", "Eradication", "Recovery", "Closed"];
    const currentIndex = phaseOrder.indexOf(incident.status);
    if (currentIndex < phaseOrder.length - 1) {
      try {
        const response = await fetch(`${URL}/api/respond/incidents/${incident_id}/status`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: phaseOrder[currentIndex + 1], actor: "john.doe" })
        });
        
        if (response.ok) {
          setShowAdvanceModal(false);
          fetchIncident();
        }
      } catch (err) {
        console.error("Failed to advance phase:", err);
      }
    }
  };

  // Handle close incident
  const handleCloseIncident = async () => {
    try {
      const response = await fetch(`${URL}/api/respond/incidents/${incident_id}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "Closed", actor: "john.doe" })
      });
      
      if (response.ok) {
        setShowCloseModal(false);
        fetchIncident();
      }
    } catch (err) {
      console.error("Failed to close incident:", err);
    }
  };

  // Handle export report
  const handleExportReport = async () => {
    try {
      const response = await fetch(`${URL}/api/incidents/${incident_id}/export?format=md`);
      const text = await response.text();
      
      // Create and download file
      const blob = new Blob([text], { type: "text/markdown" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `incident-${incident_id}-${format(new Date(), "yyyy-MM-dd")}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to export report:", err);
      alert("Failed to export report");
    }
  };

  // Group tasks by phase
  const tasksByPhase = incident?.tasks.reduce((acc, task) => {
    if (!acc[task.phase]) acc[task.phase] = [];
    acc[task.phase].push(task);
    return acc;
  }, {} as Record<string, IncidentTask[]>);

  if (loading) return <div className="container mt-4">Loading incident...</div>;
  if (error || !incident) return <div className="container mt-4">{error || "Incident not found"}</div>;

  const slaProgress = calculateSlaProgress();

  return (
    <div className="container mt-4">
      {/* Header */}
      <div className="d-flex justify-content-between align-items-start mb-4">
        <div>
          <h3 className="fw-bold text-primary">
            Incident: {incident.title}
          </h3>
          <div className="d-flex gap-2 align-items-center mb-2">
            <Badge bg={getSeverityColor(incident.severity)} className="fs-6">
              {getSeverityText(incident.severity)}
            </Badge>
            <Badge bg={getStatusColor(incident.status)} className="fs-6">
              {incident.status}
            </Badge>
            <Badge bg={getSlaStatusColor(incident.sla_status)} className="fs-6">
              SLA: {incident.sla_status.toUpperCase()}
            </Badge>
            <span className="text-muted">
              Opened: {format(new Date(incident.opened_at), "PPpp")}
            </span>
          </div>
          {incident.tags.length > 0 && (
            <div className="mt-1">
              {incident.tags.map((tag) => (
                <Badge key={tag} bg="light" text="dark" className="me-1">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </div>
        <div className="d-flex gap-2">
          <Button variant="outline-primary" onClick={handleExportReport}>
            Export Report
          </Button>
          {incident.status !== "Closed" && (
            <>
              <Button variant="warning" onClick={() => setShowAdvanceModal(true)}>
                Advance Phase
              </Button>
              <Button variant="danger" onClick={() => setShowCloseModal(true)}>
                Close Incident
              </Button>
            </>
          )}
        </div>
      </div>

      {/* SLA Progress Bar */}
      <Card className="mb-4">
        <Card.Body>
          <div className="d-flex justify-content-between mb-2">
            <span>SLA Progress</span>
            <span className={`fw-bold text-${getSlaStatusColor(incident.sla_status)}`}>
              {slaProgress.timeRemaining}
            </span>
          </div>
          <ProgressBar
            now={slaProgress.percent}
            variant={getSlaStatusColor(incident.sla_status)}
            label={`${Math.round(slaProgress.percent)}%`}
            className="mb-2"
          />
          <div className="d-flex justify-content-between small text-muted">
            <span>Opened: {format(new Date(incident.opened_at), "PPp")}</span>
            <span>Due: {format(new Date(incident.sla_due_at), "PPp")}</span>
          </div>
        </Card.Body>
      </Card>

      {/* Tabs */}
      <Tabs activeKey={activeTab} onSelect={(k) => k && setActiveTab(k)} className="mb-4">
        <Tab eventKey="overview" title="Overview">
          <Row className="g-4 mt-3">
            {/* Summary and Details */}
            <Col lg={8}>
              <Card>
                <Card.Header className="bg-primary text-white">
                  <strong>Incident Summary</strong>
                </Card.Header>
                <Card.Body>
                  <div className="mb-4">
                    <h5>Summary</h5>
                    <p>{incident.summary || "No summary provided."}</p>
                  </div>
                  
                  {/* <div className="mb-4">
                    <h5>Root Cause</h5>
                    <p>{incident.root_cause || "Root cause not yet identified."}</p>
                  </div>
                  
                  <div className="mb-4">
                    <h5>Lessons Learned</h5>
                    <p>{incident.lessons_learned || "Lessons learned not yet documented."}</p>
                  </div> */}
                  
                  <div>
                    <h5>Owner Information</h5>
                    <Table bordered size="sm">
                      <tbody>
                        <tr>
                          <td><strong>Owner</strong></td>
                          <td>{incident.owner || "Unassigned"}</td>
                        </tr>
                        <tr>
                          <td><strong>Primary Asset</strong></td>
                          <td>
                            {incident.asset_refs.find(a => a._id === incident.primary_asset_id)?.name || "Not specified"}
                          </td>
                        </tr>
                        <tr>
                          <td><strong>Deduplication Key</strong></td>
                          <td>
                            <code className="small">
                              {incident.dedup_key.rule_id || incident.dedup_key.hash || "N/A"}
                            </code>
                          </td>
                        </tr>
                      </tbody>
                    </Table>
                  </div>
                </Card.Body>
              </Card>
            </Col>
            
            {/* Stats and Quick Info */}
            <Col lg={4}>
              <Card className="mb-4">
                <Card.Header className="bg-info text-white">
                  <strong>Quick Stats</strong>
                </Card.Header>
                <Card.Body>
                  <ListGroup variant="flush">
                    <ListGroup.Item className="d-flex justify-content-between">
                      <span>Assets Involved</span>
                      <Badge bg="primary">{incident.asset_refs.length}</Badge>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between">
                      <span>Detections</span>
                      <Badge bg="warning">{incident.detection_refs.length}</Badge>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between">
                      <span>Risk Items</span>
                      <Badge bg="danger">{incident.risk_item_refs.length}</Badge>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between">
                      <span>Tasks</span>
                      <Badge bg="success">{incident.tasks.length}</Badge>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between">
                      <span>Evidence Items</span>
                      <Badge bg="secondary">{incident.evidence.length}</Badge>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between">
                      <span>Timeline Events</span>
                      <Badge bg="dark">{incident.timelines.length}</Badge>
                    </ListGroup.Item>
                  </ListGroup>
                </Card.Body>
              </Card>
              
              <Card>
                <Card.Header className="bg-success text-white">
                  <strong>Recent Timeline Events</strong>
                </Card.Header>
                <Card.Body>
                  <ListGroup variant="flush">
                    {incident.timelines.slice(-5).reverse().map((event) => (
                      <ListGroup.Item key={event._id}>
                        <div className="d-flex justify-content-between">
                          <small className="text-muted">
                            {format(new Date(event.ts), "HH:mm")}
                          </small>
                          <Badge bg="light" text="dark" className="small">
                            {event.event_type}
                          </Badge>
                        </div>
                        <div className="small">{event.actor}</div>
                        <div className="text-truncate small">
                          {typeof event.detail === 'string' ? event.detail : JSON.stringify(event.detail)}
                        </div>
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>
        
        <Tab eventKey="tasks" title="Tasks">
          <div className="mt-3">
            <div className="d-flex justify-content-between mb-3">
              <h5>Incident Tasks by Phase</h5>
              <Button variant="primary" size="sm" onClick={() => setShowTaskModal(true)}>
                + Add Task
              </Button>
            </div>
            
            <Accordion>
              {Object.entries(tasksByPhase || {}).map(([phase, phaseTasks]) => (
                <Accordion.Item key={phase} eventKey={phase}>
                  <Accordion.Header>
                    <Badge bg={getStatusColor(phase)} className="me-2">{phase}</Badge>
                    {phaseTasks.length} tasks
                    <Badge bg="light" text="dark" className="ms-2">
                      {phaseTasks.filter(t => t.status === "Done").length} completed
                    </Badge>
                  </Accordion.Header>
                  <Accordion.Body>
                    <ListGroup variant="flush">
                      {phaseTasks.sort((a, b) => a.order - b.order).map((task) => (
                        <ListGroup.Item key={task._id}>
                          <div className="d-flex align-items-center">
                            <Form.Check
                              type="checkbox"
                              checked={task.status === "Done"}
                              onChange={() => handleTaskToggle(task._id, task.status)}
                              className="me-3"
                            />
                            <div className="flex-grow-1">
                              <div className="d-flex justify-content-between">
                                <strong>{task.title}</strong>
                                <Badge bg={task.status === "Done" ? "success" : "secondary"} className="small">
                                  {task.status}
                                </Badge>
                              </div>
                              <div className="small text-muted">
                                Assignee: {task.assignee || "Unassigned"} | 
                                Due: {task.due_at ? format(new Date(task.due_at), "PP") : "No due date"}
                              </div>
                              {task.notes && (
                                <div className="mt-2 small">{task.notes}</div>
                              )}
                            </div>
                          </div>
                        </ListGroup.Item>
                      ))}
                    </ListGroup>
                  </Accordion.Body>
                </Accordion.Item>
              ))}
            </Accordion>
          </div>
        </Tab>
        
        <Tab eventKey="timeline" title="Timeline">
          <div className="mt-3">
            <h5>Incident Timeline</h5>
            <Card>
              <Card.Body>
                <ListGroup variant="flush">
                  {[...incident.timelines]
                    .sort((a, b) => new Date(b.ts).getTime() - new Date(a.ts).getTime())
                    .map((event) => (
                      <ListGroup.Item key={event._id}>
                        <div className="d-flex">
                          <div className="me-3 text-center" style={{ width: "120px" }}>
                            <div className="fw-bold">{format(new Date(event.ts), "MMM d")}</div>
                            <div className="text-muted small">{format(new Date(event.ts), "HH:mm:ss")}</div>
                          </div>
                          <div className="flex-grow-1">
                            <div className="d-flex justify-content-between align-items-start">
                              <div>
                                <Badge bg="light" text="dark" className="me-2">
                                  {event.event_type}
                                </Badge>
                                <span className="fw-bold">{event.actor}</span>
                              </div>
                            </div>
                            <div className="mt-2">
                              {typeof event.detail === 'string' ? (
                                <p className="mb-0">{event.detail}</p>
                              ) : (
                                <pre className="mb-0 small" style={{ whiteSpace: 'pre-wrap' }}>
                                  {JSON.stringify(event.detail, null, 2)}
                                </pre>
                              )}
                            </div>
                          </div>
                        </div>
                      </ListGroup.Item>
                    ))}
                </ListGroup>
              </Card.Body>
            </Card>
          </div>
        </Tab>
        
        <Tab eventKey="evidence" title="Evidence">
          <div className="mt-3">
            <div className="d-flex justify-content-between mb-3">
              <h5>Evidence Collection</h5>
              <Button variant="primary" size="sm" onClick={() => setShowEvidenceModal(true)}>
                + Add Evidence
              </Button>
            </div>
            
            {incident.evidence.length > 0 ? (
              <Table striped hover responsive>
                <thead className="table-dark">
                  <tr>
                    <th>Type</th>
                    <th>Location</th>
                    <th>Hash</th>
                    <th>Submitted By</th>
                    <th>Date</th>
                    {/* <th>Chain of Custody</th> */}
                  </tr>
                </thead>
                <tbody>
                  {incident.evidence.map((item) => (
                    <tr key={item._id}>
                      <td>
                        <Badge bg="info">{item.type}</Badge>
                      </td>
                      <td>
                        <code className="small">{item.location}</code>
                      </td>
                      <td>
                        {item.hash ? (
                          <small className="font-monospace">{item.hash.substring(0, 16)}...</small>
                        ) : (
                          <span className="text-muted">N/A</span>
                        )}
                      </td>
                      <td>{item.submitted_by}</td>
                      <td>{format(new Date(item.submitted_at), "PPp")}</td>
                      {/* <td>
                        <Badge bg="secondary">
                          {item.chain_of_custody.length} entries
                        </Badge>
                      </td> */}
                    </tr>
                  ))}
                </tbody>
              </Table>
            ) : (
              <Alert variant="light" className="text-center">
                No evidence has been collected yet.
              </Alert>
            )}
          </div>
        </Tab>
        
        <Tab eventKey="linked" title="Linked Items">
          <Row className="mt-3 g-4">
            {/* Linked Assets */}
            <Col md={4}>
              <Card>
                <Card.Header className="bg-primary text-white">
                  <strong>Linked Assets ({incident.asset_refs.length})</strong>
                </Card.Header>
                <Card.Body className="p-0">
                  <ListGroup variant="flush">
                    {incident.asset_refs.map((asset) => (
                      <ListGroup.Item key={asset._id} action onClick={() => navigate(`/assets/${asset._id}`)}>
                        <div>
                          <strong>{asset.name}</strong>
                          <Badge bg="secondary" className="ms-2">
                            {asset.type}
                          </Badge>
                          {asset._id === incident.primary_asset_id && (
                            <Badge bg="warning" className="ms-1">Primary</Badge>
                          )}
                        </div>
                        <small className="text-muted">
                          {asset.ip} | {asset.hostname}
                        </small>
                        <div className="mt-1">
                          <small>
                            Owner: {asset.owner} | Criticality: {asset.criticality}
                          </small>
                        </div>
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </Card.Body>
              </Card>
            </Col>
            
            {/* Linked Detections */}
            <Col md={4}>
              <Card>
                <Card.Header className="bg-warning text-dark">
                  <strong>Linked Detections ({incident.detection_refs.length})</strong>
                </Card.Header>
                <Card.Body className="p-0">
                  <ListGroup variant="flush">
                    {incident.detection_refs.map((detection) => (
                      <ListGroup.Item key={detection._id} action onClick={() => navigate(`/detection/${detection._id}`)}>
                        <div>
                          <strong>{detection.name}</strong>
                          <Badge bg={getSeverityColor(detection.severity)} className="ms-2">
                            Sev: {detection.severity}
                          </Badge>
                        </div>
                        <small className="text-muted">
                          {detection.description || "No description"}
                        </small>
                        <div className="mt-1">
                          <small>
                            Confidence: {detection.confidence}% | 
                            Created: {new Date(detection.first_seen).toLocaleDateString()}
                          </small>
                        </div>
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </Card.Body>
              </Card>
            </Col>
            
            {/* Linked Risk Items */}
            <Col md={4}>
              <Card>
                <Card.Header className="bg-danger text-white">
                  <strong>Linked Risk Items ({incident.risk_item_refs.length})</strong>
                </Card.Header>
                <Card.Body className="p-0">
                  <ListGroup variant="flush">
                    {incident.risk_item_refs.map((risk) => (
                      <ListGroup.Item key={risk._id}>
                        <div>
                          <strong>{risk.title}</strong>
                          {/* <Badge bg={risk.risk_level === "High" ? "danger" : "warning"} className="ms-2">
                            {risk.risk_level}
                          </Badge> */}
                        </div>
                        <div className="mt-1">
                          <Badge bg={risk.status === "Open" ? "info" : "success"}>
                            {risk.status}
                          </Badge>
                        </div>
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>
      </Tabs>

      {/* Back Button */}
      <div className="mt-4">
        <Button variant="secondary" onClick={() => navigate("/incidents")}>
          ← Back to Incidents List
        </Button>
      </div>

      {/* Add Task Modal */}
      <Modal show={showTaskModal} onHide={() => setShowTaskModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Add New Task</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Task Title</Form.Label>
              <Form.Control
                type="text"
                value={newTask.title}
                onChange={(e) => setNewTask({...newTask, title: e.target.value})}
                placeholder="Enter task title"
              />
            </Form.Group>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Assignee</Form.Label>
                  <Form.Control
                    type="text"
                    value={newTask.assignee}
                    onChange={(e) => setNewTask({...newTask, assignee: e.target.value})}
                    placeholder="Unassigned"
                  />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Phase</Form.Label>
                  <Form.Select
                    value={newTask.phase}
                    onChange={(e) => setNewTask({...newTask, phase: e.target.value})}
                  >
                    <option value="Triage">Triage</option>
                    <option value="Containment">Containment</option>
                    <option value="Eradication">Eradication</option>
                    <option value="Recovery">Recovery</option>
                    <option value="Close">Close</option>
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>
            <Form.Group className="mb-3">
              <Form.Label>Notes</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                value={newTask.notes}
                onChange={(e) => setNewTask({...newTask, notes: e.target.value})}
                placeholder="Additional notes or instructions"
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowTaskModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleAddTask} disabled={!newTask.title.trim()}>
            Add Task
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Add Evidence Modal */}
      <Modal show={showEvidenceModal} onHide={() => setShowEvidenceModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Add Evidence</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Evidence Type</Form.Label>
              <Form.Select
                value={newEvidence.type}
                onChange={(e) => setNewEvidence({...newEvidence, type: e.target.value})}
              >
                <option value="log">Log File</option>
                <option value="screenshot">Screenshot</option>
                <option value="pcap">Network Capture</option>
                <option value="config">Configuration</option>
                <option value="ticket">Ticket/Alert</option>
                <option value="other">Other</option>
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Location/URL</Form.Label>
              <Form.Control
                type="text"
                value={newEvidence.location}
                onChange={(e) => setNewEvidence({...newEvidence, location: e.target.value})}
                placeholder="e.g., s3://bucket/evidence/file.log"
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Hash (Optional)</Form.Label>
              <Form.Control
                type="text"
                value={newEvidence.hash}
                onChange={(e) => setNewEvidence({...newEvidence, hash: e.target.value})}
                placeholder="SHA256 hash"
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Notes</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                value={newEvidence.notes}
                onChange={(e) => setNewEvidence({...newEvidence, notes: e.target.value})}
                placeholder="Description of the evidence"
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowEvidenceModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleAddEvidence} disabled={!newEvidence.location.trim()}>
            Add Evidence
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Advance Phase Modal */}
      <Modal show={showAdvanceModal} onHide={() => setShowAdvanceModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Advance Incident Phase</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Alert variant="warning">
            <strong>Current Phase:</strong> {incident.status}
          </Alert>
          <p>
            Are you sure you want to advance this incident to the next phase?
            This action will update the incident status and may trigger notifications.
          </p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowAdvanceModal(false)}>
            Cancel
          </Button>
          <Button variant="warning" onClick={handleAdvancePhase}>
            Advance to Next Phase
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Close Incident Modal */}
      <Modal show={showCloseModal} onHide={() => setShowCloseModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Close Incident</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Alert variant="danger">
            <strong>Warning:</strong> Closing an incident is a final action.
          </Alert>
          <p>
            Are you sure you want to close incident "{incident.title}"?
            This action cannot be undone.
          </p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowCloseModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleCloseIncident}>
            Close Incident
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}