import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Badge, ListGroup, Button, Alert } from "react-bootstrap";
import { format } from "date-fns";
import { Detection } from "../../models/Detection";
import { Asset } from "../../models/Asset";
import { RiskItem } from "../../models/RiskItem";
import { RiskItemsPanel } from "../RiskItem/RiskItemsPanel";

// Single API response type (matches your JSON)
interface DetectionResponse {
    _id: string;
    asset_id: string;
    asset_name: string;
    asset_criticality: string;
    asset_owner: string;
    asset_bu: string;
    source: string;
    indicator: string;
    ttp: string[];
    severity: number;
    confidence: number;
    first_seen: string;
    last_seen: string;
    hit_count: number;
    analyst_note: string;
    raw_ref: { intel_ids?: string[] };
    intel_samples: {
        _id: string;
        source: string;
        indicator: string;
        indicator_type: string;
        severity: string;
        summary: string;
        created_at: string;
    }[];
}

export function DetectionViewPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    // @ts-ignore
    const URL = import.meta.env.VITE_API_URL;

    const [detection, setDetection] = useState<DetectionResponse | null>(null);
    const [riskItemExists, setRiskItemExists] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${URL}/api/detect/detections/${id}`)
            .then((r) => r.json())
            .then((data) => {
                setDetection(data);
                setLoading(false);
            })
            .catch((err) => {
                console.error("Failed to load detection:", err);
                setLoading(false);
            });
    }, [id, URL]);

    const handleOpenRiskItem = async () => {
        if (!detection) return;

        const payload = {
            title: `Detection: ${detection.source} ${detection.indicator}`,
            asset_id: detection.asset_id,
            status: "Open",
            owner: "security-team@smb.com", // fallback
            due: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
            score: 5 * detection.severity, // placeholder
        };

        try {
            const res = await fetch(`${URL}/api/risk_items`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            if (res.ok) {
                setRiskItemExists(true);
                alert("Risk item created!");
            }
        } catch (err) {
            alert("Failed to create risk item.");
        }
    };

    const getSeverityBadge = (sev: number) => {
        const variants: { [k: number]: string } = {
            5: "danger",
            4: "warning",
            3: "primary",
            2: "info",
            1: "secondary",
        };
        return variants[sev] || "secondary";
    };

    if (loading) return <div className="container mt-4">Loading...</div>;
    if (!detection) return <div className="container mt-4">Detection not found.</div>;

    return (
        <div className="container mt-4">
            <h3 className="mb-3 fw-bold text-primary">Detections</h3>
            {/* Header: Asset Name + Severity Badge */}
            <div className="d-flex align-items-center gap-3 mb-4">
                <h3 className="mb-0 fw-bold">{detection.asset_name}</h3>
                <Badge bg={getSeverityBadge(detection.severity)} className="fs-6">
                    Severity {detection.severity}
                </Badge>
            </div>

            <div className="row g-4">
                {/* Panel 1: What We Saw */}
                <div className="col-lg-6">
                    <Card className="h-100">
                        <Card.Header className="bg-primary text-white">
                            <strong>What We Saw</strong>
                        </Card.Header>
                        <Card.Body>
                            <ListGroup variant="flush">
                                <ListGroup.Item>
                                    <strong>Indicator:</strong>{" "}
                                    <code className="text-primary">{detection.indicator}</code>
                                </ListGroup.Item>
                                <ListGroup.Item>
                                    <strong>Source:</strong> {detection.source}
                                </ListGroup.Item>
                                <ListGroup.Item>
                                    <strong>First Seen:</strong>{" "}
                                    {format(new Date(detection.first_seen), "PPpp")}
                                </ListGroup.Item>
                                <ListGroup.Item>
                                    <strong>Last Seen:</strong>{" "}
                                    {format(new Date(detection.last_seen), "PPpp")}
                                </ListGroup.Item>
                                <ListGroup.Item>
                                    <strong>Hit Count:</strong>{" "}
                                    <Badge bg="dark">{detection.hit_count}</Badge>
                                </ListGroup.Item>
                            </ListGroup>
                        </Card.Body>
                    </Card>
                </div>

                {/* Panel 2: Why It Matters */}
                <div className="col-lg-6">
                    <Card className="h-100">
                        <Card.Header className="bg-warning text-dark">
                            <strong>Why It Matters</strong>
                        </Card.Header>
                        <Card.Body>
                            <Alert variant="light" className="mb-0">
                                {detection.analyst_note}
                            </Alert>
                        </Card.Body>
                    </Card>
                </div>

                {/* Panel 3: Context */}
                <div className="col-12">
                    <Card>
                        <Card.Header className="bg-info text-white">
                            <strong>Context</strong>
                        </Card.Header>
                        <Card.Body>
                            <div className="row">
                                <div className="col-md-6">
                                    <h6>Recent Intel Samples</h6>
                                    {detection.intel_samples.length > 0 ? (
                                        <ListGroup variant="flush">
                                            {detection.intel_samples.map((intel) => (
                                                <ListGroup.Item key={intel._id}>
                                                    <small>
                                                        <strong>{intel.source}:</strong> {intel.summary || intel.indicator}
                                                        <br />
                                                        <em>{format(new Date(intel.created_at), "PPpp")}</em>
                                                    </small>
                                                </ListGroup.Item>
                                            ))}
                                        </ListGroup>
                                    ) : (
                                        <p className="text-muted">No intel samples.</p>
                                    )}
                                </div>
                                <div className="col-md-6">
                                    <h6>Asset Context</h6>
                                    <ListGroup variant="flush">
                                        <ListGroup.Item>
                                            <strong>Name:</strong> {detection.asset_name}
                                        </ListGroup.Item>
                                        <ListGroup.Item>
                                            <strong>Criticality:</strong> {detection.asset_criticality}
                                        </ListGroup.Item>
                                        <ListGroup.Item>
                                            <strong>Owner:</strong> {detection.asset_owner}
                                        </ListGroup.Item>
                                        <ListGroup.Item>
                                            <strong>Business Unit:</strong> {detection.asset_bu}
                                        </ListGroup.Item>
                                    </ListGroup>
                                </div>
                            </div>
                        </Card.Body>
                    </Card>
                </div>

                {/* Risk Item Action */}
                <div className="col-12 text-end">
                    {/* {riskItemExists ? (
            // <Button
            //   variant="success"
            //   onClick={() => alert("Risk item already exists!")}
            // >
            //   View Risk Item
            // </Button>
            <RiskItemsPanel assetId={detection.asset_id} />
          ) : (
            <Button variant="danger" onClick={handleOpenRiskItem}>
              Open Risk Item
            </Button>
          )} */}
                    <RiskItemsPanel assetId={detection.asset_id} />
                </div>
            </div>

            <div className="mt-4">
                <Button variant="secondary" onClick={() => navigate("/detections")}>
                    Back to Detections
                </Button>
            </div>
        </div>
    );
}