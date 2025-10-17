import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Card, Table, Badge, Row, Col } from "react-bootstrap";

// TypeScript interface for Asset view
interface AssetView {
    _id: string;
    org: string;
    name: string;
    type: string;
    ip: string;
    hostname: string;
    owner: string;
    business_unit: string;
    criticality: string;
    data_sensitivity: string;
    recent_intel: Array<{
        time: string;
        source: string;
        indicator: string;
        severity: string;
        link?: string;
    }>;
    risk: {
        score: number;
        components: {
            criticality: number;
            intel_max_severity_7d: number;
        };
        explain: string;
        window_days: number;
    };
}

export function AssetViewPage() {
    const { id } = useParams(); // get asset id from route
    const [asset, setAsset] = useState<AssetView | null>(null);

    // Replace with your API base URL
    // @ts-ignore
    const URL = import.meta.env.VITE_API_URL;

    useEffect(() => {
        debugger;
        fetch(`${URL}/api/assets/${id}`)
            .then((res) => res.json())
            .then((res) => setAsset(res.data))
            .catch((err) => console.error("Error fetching asset:", err));
    }, [id]);

    if (!asset) {
        return <p className="text-center mt-4">Loading asset...</p>;
    }

    function getRiskLevel(asset: AssetView): number {
        let q_sens: number = 0;
        let q_crit: number = Number(asset.criticality);
        switch (asset.data_sensitivity) {
            case "Low":
                q_sens = 1;
                break;
            case "Moderate":
                q_sens = 2;
                break;
            case "High":
                q_sens = 3;
                break;
        }
        return q_sens * q_crit;
    }

    return (
        <div className="container mt-4">
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
                    {asset.recent_intel.length === 0 ? (
                        <p className="text-muted">No recent intel found.</p>
                    ) : (
                        <Table striped bordered hover responsive>
                            <thead className="table-secondary">
                                <tr>
                                    <th>Time</th>
                                    <th>Source</th>
                                    <th>Indicator</th>
                                    <th>Severity</th>
                                    <th>Link</th>
                                </tr>
                            </thead>
                            <tbody>
                                {asset.recent_intel.map((intel, idx) => (
                                    <tr key={idx}>
                                        <td>{intel.time}</td>
                                        <td>{intel.source}</td>
                                        <td>{intel.indicator}</td>
                                        <td>{intel.severity}</td>
                                        <td>
                                            {intel.link ? (
                                                <a href={intel.link} target="_blank" rel="noreferrer">
                                                    View
                                                </a>
                                            ) : (
                                                "-"
                                            )}
                                        </td>
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
                            <h4 className="mb-0">Current Score: {getRiskLevel(asset)}</h4>
                            {/* <small className="text-muted">{asset.risk.explain}</small> */}
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
