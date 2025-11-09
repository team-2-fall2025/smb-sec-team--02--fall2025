import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, Form, Button, Row, Col } from "react-bootstrap";
import { Asset } from "../../models/Asset";

export function AssetCreatePage() {
    const navigate = useNavigate();
    const [asset, setAsset] = useState<Partial<Asset>>({
        org: "",
        name: "",
        type: "",
        ip: "",
        hostname: "",
        owner: "",
        business_unit: "",
        criticality: 1,
        data_sensitivity: "",
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    // @ts-ignore
    const URL = import.meta.env.VITE_API_URL;

    const handleChange = (field: keyof Asset, value: any) => {
        setAsset((prev: any) => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            const res = await fetch(`${URL}/api/assets/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(asset),
            });
            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Failed to create asset");
            }
            const data = await res.json();
            navigate(`/assets/${data.data._id}`); // go to the new asset view
        } catch (err: any) {
            setError(err.message || "Unexpected error");
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container mt-4">
            <h3>Create New Asset</h3>
            <Card className="mt-3">
                <Card.Body>
                    {error && <p className="text-danger">{error}</p>}
                    <Form onSubmit={handleSubmit}>
                        <Row className="mb-3">
                            <Col md={6}>
                                <Form.Label>Organization</Form.Label>
                                <Form.Control
                                    type="text"
                                    value={asset.org}
                                    onChange={(e) => handleChange("org", e.target.value)}
                                    required
                                />
                            </Col>
                            <Col md={6}>
                                <Form.Label>Name</Form.Label>
                                <Form.Control
                                    type="text"
                                    value={asset.name}
                                    onChange={(e) => handleChange("name", e.target.value)}
                                    required
                                />
                            </Col>
                        </Row>

                        <Row className="mb-3">
                            <Col md={4}>
                                <Form.Label>Type</Form.Label>
                                <Form.Control
                                    type="text"
                                    value={asset.type}
                                    onChange={(e) => handleChange("type", e.target.value)}
                                    required
                                />
                            </Col>
                            <Col md={4}>
                                <Form.Label>IP Address</Form.Label>
                                <Form.Control
                                    type="text"
                                    value={asset.ip}
                                    onChange={(e) => handleChange("ip", e.target.value)}
                                />
                            </Col>
                            <Col md={4}>
                                <Form.Label>Hostname</Form.Label>
                                <Form.Control
                                    type="text"
                                    value={asset.hostname}
                                    onChange={(e) => handleChange("hostname", e.target.value)}
                                />
                            </Col>
                        </Row>

                        <Row className="mb-3">
                            <Col md={4}>
                                <Form.Label>Owner</Form.Label>
                                <Form.Control
                                    type="text"
                                    value={asset.owner}
                                    onChange={(e) => handleChange("owner", e.target.value)}
                                />
                            </Col>
                            <Col md={4}>
                                <Form.Label>Business Unit</Form.Label>
                                <Form.Control
                                    type="text"
                                    value={asset.business_unit}
                                    onChange={(e) => handleChange("business_unit", e.target.value)}
                                />
                            </Col>
                            <Col md={4}>
                                <Form.Label>Criticality</Form.Label>
                                <Form.Control
                                    type="number"
                                    min={1}
                                    max={5}
                                    value={asset.criticality}
                                    onChange={(e) => handleChange("criticality", parseInt(e.target.value))}
                                />
                            </Col>
                        </Row>

                        <Row className="mb-3">
                            <Col md={6}>
                                <Form.Label>Data Sensitivity</Form.Label>
                                <Form.Control
                                    type="text"
                                    value={asset.data_sensitivity}
                                    onChange={(e) => handleChange("data_sensitivity", e.target.value)}
                                />
                            </Col>
                        </Row>

                        <Button type="submit" disabled={loading}>
                            {loading ? "Creating..." : "Create Asset"}
                        </Button>
                    </Form>
                </Card.Body>
            </Card>
        </div>
    );
}
