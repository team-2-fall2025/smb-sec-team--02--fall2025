import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Form, Button, Row, Col, Card } from "react-bootstrap";
import type { Asset } from "../../models/Asset";

export function AssetEditPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  //@ts-ignore
  const URL = import.meta.env.VITE_API_URL;

  const [asset, setAsset] = useState<Asset | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${URL}/api/assets/${id}`)
      .then((res) => res.json())
      .then((res) => {
        setAsset(res.data);
        setLoading(false);
      })
      .catch((err) => console.error("Error fetching asset:", err));
  }, [id]);

  if (loading) return <p className="text-center mt-4">Loading asset...</p>;
  if (!asset) return <p className="text-center mt-4 text-danger">Asset not found.</p>;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setAsset((prev) => prev ? { ...prev, [name]: value } : prev);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${URL}/api/assets/`, {
        method: "PUT", // or POST depending on your API
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(asset),
      });

      if (!res.ok) throw new Error("Update failed");

      alert("Asset updated successfully!");
      navigate("/assets"); // return to asset list
    } catch (err) {
      console.error(err);
      alert("Error updating asset");
    }
  };

  return (
    <div className="container mt-4">
      <h3 className="mb-3 fw-bold text-primary">Edit Asset: {asset.name}</h3>
      <Card>
        <Card.Body>
          <Form onSubmit={handleSubmit}>
            <Row className="mb-3">
              <Col md={4}>
                <Form.Group>
                  <Form.Label>Organization</Form.Label>
                  <Form.Control name="org" value={asset.org} onChange={handleChange} />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group>
                  <Form.Label>Name</Form.Label>
                  <Form.Control name="name" value={asset.name} onChange={handleChange} />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group>
                  <Form.Label>Type</Form.Label>
                  <Form.Control name="type" value={asset.type} onChange={handleChange} />
                </Form.Group>
              </Col>
            </Row>

            <Row className="mb-3">
              <Col md={4}>
                <Form.Group>
                  <Form.Label>IP Address</Form.Label>
                  <Form.Control name="ip" value={asset.ip} onChange={handleChange} />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group>
                  <Form.Label>Hostname</Form.Label>
                  <Form.Control name="hostname" value={asset.hostname} onChange={handleChange} />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group>
                  <Form.Label>Owner</Form.Label>
                  <Form.Control name="owner" value={asset.owner} onChange={handleChange} />
                </Form.Group>
              </Col>
            </Row>

            <Row className="mb-3">
              <Col md={4}>
                <Form.Group>
                  <Form.Label>Business Unit</Form.Label>
                  <Form.Control name="business_unit" value={asset.business_unit} onChange={handleChange} />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group>
                  <Form.Label>Criticality</Form.Label>
                  <Form.Control
                    type="number"
                    name="criticality"
                    value={asset.criticality}
                    onChange={handleChange}
                  />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group>
                  <Form.Label>Data Sensitivity</Form.Label>
                  <Form.Control name="data_sensitivity" value={asset.data_sensitivity} onChange={handleChange} />
                </Form.Group>
              </Col>
            </Row>

            <Button type="submit" variant="primary">
              Save Changes
            </Button>
            <Button variant="secondary" className="ms-2" onClick={() => navigate("/assets")}>
              Cancel
            </Button>
          </Form>
        </Card.Body>
      </Card>
    </div>
  );
}
