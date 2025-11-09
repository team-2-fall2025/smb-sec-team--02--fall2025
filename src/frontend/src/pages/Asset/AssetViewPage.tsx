import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Card, Table, Badge, Row, Col } from "react-bootstrap";
import { Asset } from "../../models/Asset";

export function AssetViewPage() {
    const { id } = useParams(); // get asset id from route
    const [asset, setAsset] = useState<Asset>();

    // Replace with your API base URL
    // @ts-ignore
    const URL = import.meta.env.VITE_API_URL;

    useEffect(() => {
        fetch(`${URL}/api/assets/${id}`)
            .then((res) => res.json())
            .then((res) => setAsset(res.data))
            .catch((err) => console.error("Error fetching asset:", err));
    }, [id]);

    if (!asset) {
        return <p className="text-center mt-4">Loading asset...</p>;
    }

    function getRiskLevel(asset: Asset): number {
        let crit = asset.criticality;
        let max_sev =  Math.max(...asset.intel_events.map((ie) => ie.severity), 0);
        return crit * max_sev;
    }

    return (
        <div className="container mt-4">
            <h3 className="mb-3 fw-bold text-primary">Assets</h3>
            {/* Header */}
            <div className="d-flex align-items-center justify-content-between mb-4">
                <h2>{asset.name}</h2>
                <div className="d-flex gap-2">
                    <Badge bg="primary">{asset.type}</Badge>
                    <Badge bg="danger">Criticality: {asset.criticality}</Badge>
                    <Badge bg="warning" text="dark">
                        Sensitivity: {asset.data_sensitivity}
                    </Badge>
                </div>
            </div>

            {/* General Details */}
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
        </div>
    );
}
