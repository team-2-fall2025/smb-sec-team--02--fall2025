import { useState, useMemo, useEffect } from "react";
import { Button, Table, Form, Row, Col, Badge } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { format } from "date-fns";

interface IntelEvent {
  _id: string;
  source: string;
  event_type: string;
  indicator: string;
  indicator_type: string;
  severity: number;
  summary?: string;
  created_at: string;
}

export function IntelEvents() {
  const navigate = useNavigate();
  // @ts-ignore
  const URL = import.meta.env.VITE_API_URL;

  const [events, setEvents] = useState<IntelEvent[]>([]);
  const [filterSource, setFilterSource] = useState("");
  const [searchIndicator, setSearchIndicator] = useState("");

  useEffect(() => {
    fetch(`${URL}/api/events`)
      .then((r) => r.json())
      .then((data) => setEvents(Array.isArray(data) ? data : data.data || []))
      .catch((err) => console.error("Failed to load intel events:", err));
  }, [URL]);

  const filteredEvents = useMemo(() => {
    let filtered = [...events];

    if (filterSource) {
      filtered = filtered.filter((e) => e.source.toLowerCase() === filterSource.toLowerCase());
    }
    if (searchIndicator) {
      filtered = filtered.filter((e) =>
        e.indicator.toLowerCase().includes(searchIndicator.toLowerCase())
      );
    }

    return filtered.sort((a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  }, [events, filterSource, searchIndicator]);

  const sources = Array.from(new Set(events.map((e) => e.source))).sort();

  const getSeverityBadge = (sev: number) => {
    const map: Record<number, string> = {
      1: "secondary",
      2: "info",
      3: "primary",
      4: "warning",
      5: "danger",
    };
    return map[sev] || "dark";
  };

  const getIndicatorTypeBadge = (type: string) => {
    const map: Record<string, string> = {
      ipv4: "success",
      domain: "info",
      md5: "warning",
      sha256: "danger",
      url: "primary",
    };
    return map[type.toLowerCase()] || "secondary";
  };

  return (
    <div className="container mt-4">
      <h3 className="mb-3 fw-bold text-primary">Threat Intelligence Events</h3>

      <Row className="mb-3 g-2">
        <Col md={3}>
          <Form.Select value={filterSource} onChange={(e) => setFilterSource(e.target.value)}>
            <option value="">All Sources</option>
            {sources.map((src) => (
              <option key={src} value={src}>
                {src.toUpperCase()}
              </option>
            ))}
          </Form.Select>
        </Col>

        <Col md={4}>
          <Form.Control
            placeholder="Search Indicator (IP, domain, hash...)"
            value={searchIndicator}
            onChange={(e) => setSearchIndicator(e.target.value)}
          />
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
            <th>#</th>
            <th>Date</th>
            <th>Source</th>
            <th>Indicator</th>
            <th>Type</th>
            <th>Severity</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          {filteredEvents.map((event, index) => (
            <tr key={event._id}>
              <td>{index + 1}</td>
              <td>{format(new Date(event.created_at), "MMM dd, HH:mm")}</td>
              <td>
                <Badge bg="dark">{event.source.toUpperCase()}</Badge>
              </td>
              <td>
                <code className="small text-primary">{event.indicator}</code>
              </td>
              <td>
                <Badge bg={getIndicatorTypeBadge(event.indicator_type)}>
                  {event.indicator_type}
                </Badge>
              </td>
              <td>
                <Badge bg={getSeverityBadge(event.severity)}>
                  {event.severity}
                </Badge>
              </td>
              <td>
                <small className="text-muted">
                  {event.summary || "—"}
                </small>
              </td>
            </tr>
          ))}
          {filteredEvents.length === 0 && (
            <tr>
              <td colSpan={8} className="text-center text-muted">
                No threat intelligence events found.
              </td>
            </tr>
          )}
        </tbody>
      </Table>
    </div>
  );
}