import { useState, useMemo, useEffect } from "react";
import { Button, Table, Form, Row, Col, Modal } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import type { Asset } from "../models/Asset";
export function Assets() {
    const navigate = useNavigate();
    const initialAssets: Asset[] = [
        {
            _id: "1",
            org: "AcmeRetail",
            name: "vpn-gw",
            type: "Service",
            ip: "203.0.113.50",
            hostname: "vpn.acmeretail.local",
            owner: "netops",
            business_unit: "IT",
            criticality: "4",
            data_sensitivity: "Moderate",
        },
        {
            _id: "2",
            org: "AcmeRetail",
            name: "db-server-1",
            type: "Server",
            ip: "203.0.113.51",
            hostname: "db1.acmeretail.local",
            owner: "dbadmin",
            business_unit: "IT",
            criticality: "3",
            data_sensitivity: "High",
        },
        {
            _id: "3",
            org: "AcmeWholesale",
            name: "router-1",
            type: "Network Device",
            ip: "10.0.0.1",
            hostname: "router1.acmewhole.local",
            owner: "netops",
            business_unit: "Networking",
            criticality: "5",
            data_sensitivity: "Low",
        },
    ];
    // @ts-ignore
    const URL = import.meta.env.VITE_API_URL;
    const [assets, setAssets] = useState<Asset[]>(initialAssets);
    const [searchName, setSearchName] = useState("");
    const [filterType, setFilterType] = useState("");
    const [filterOwner, setFilterOwner] = useState("");
    // const [filterOrg, setFilterOrg] = useState("");
    const [sortByCriticality, setSortByCriticality] = useState<
        "asc" | "desc" | ""
    >("");
    const [csvFile, setCsvFile] = useState<File | null>(null);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);

    // Open modal
    const handleDeleteClick = (asset: Asset) => {
        setSelectedAsset(asset);
        setShowDeleteModal(true);
    };

    // Confirm delete
    const confirmDelete = async () => {
        if (!selectedAsset) return;

        try {
            const res = await fetch(`${URL}/api/assets/${selectedAsset._id}`, {
                method: "DELETE",
            });
            if (!res.ok) throw new Error("Delete failed");

            setAssets(assets.filter((a) => a._id !== selectedAsset._id));
            setShowDeleteModal(false);
            setSelectedAsset(null);
            alert("Asset deleted successfully!");
        } catch (err) {
            console.error(err);
            alert("Failed to delete asset.");
        }
    };

    // CSV Upload handler
    const handleCsvChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setCsvFile(e.target.files[0]);
        }
    };

    const handleCsvUpload = async () => {
        if (!csvFile) return alert("Please select a CSV file first.");

        const formData = new FormData();
        formData.append("file", csvFile);

        try {
            const res = await fetch(`${URL}/api/assets/import`, {
                method: "POST",
                body: formData,
            });

            if (!res.ok) throw new Error("Upload failed");

            const data = await res.json();
            alert("CSV uploaded successfully!");

            // Optionally refresh the assets list
            if (data.new_assets) setAssets(data.new_assets);
        } catch (err) {
            console.error(err);
            alert("CSV upload failed");
        }
    };

    useEffect(() => {
        fetch(`${URL}/api/assets/`)
            .then((r) => r.json())
            .then(res => setAssets(res.data))
            .catch((err) => console.error("Assets fetch error:", err));
    }, []);

    const filteredAssets = useMemo(() => {
        let filtered = assets;
        if (searchName) {
            filtered = filtered.filter((a) =>
                a.name.toLowerCase().includes(searchName.toLowerCase())
            );
        }

        if (filterType) {
            filtered = filtered.filter((a) => a.type === filterType);
        }

        if (filterOwner) {
            filtered = filtered.filter((a) =>
                a.owner.toLowerCase().includes(filterOwner.toLowerCase())
            );
        }

        // if (filterOrg) {
        //   filtered = filtered.filter((a) =>
        //     a.org.toLowerCase().includes(filterOrg.toLowerCase())
        //   );
        // }

        if (sortByCriticality === "asc") {
            filtered = [...filtered].sort(
                (a, b) => getRiskLevel(a) - getRiskLevel(b)
            );
        } else if (sortByCriticality === "desc") {
            filtered = [...filtered].sort(
                (a, b) => getRiskLevel(b) - getRiskLevel(a)
            );
        }

        return filtered;
    }, [assets, searchName, filterType, filterOwner, sortByCriticality]);

    function getRiskLevel(asset: Asset): number {
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

    const types = Array.from(new Set(assets.map((a) => a.type)));

    return (
        <div className="container mt-4">
            <h3 className="mb-3 fw-bold text-primary">Assets</h3>

            {/* CSV Upload Button */}
            <div className="mb-3 d-flex gap-2 align-items-center">
                <Form.Control type="file" accept=".csv" onChange={handleCsvChange} style={{ maxWidth: "300px" }} />
                <Button onClick={handleCsvUpload} variant="success">
                    Upload CSV
                </Button>
            </div>

            {/* Filters */}
            <Row className="mb-3 g-2">
                <Col md={2}>
                    <Form.Control
                        placeholder="Search by Name"
                        value={searchName}
                        onChange={(e) => setSearchName(e.target.value)}
                    />
                </Col>
                <Col md={2}>
                    <Form.Select
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                    >
                        <option value="">All Types</option>
                        {types.map((type) => (
                            <option key={type} value={type}>
                                {type}
                            </option>
                        ))}
                    </Form.Select>
                </Col>
                <Col md={2}>
                    <Form.Control
                        placeholder="Filter by Owner"
                        value={filterOwner}
                        onChange={(e) => setFilterOwner(e.target.value)}
                    />
                </Col>
                {/* <Col md={2}>
          <Form.Control
            placeholder="Filter by Org"
            value={filterOrg}
            onChange={(e) => setFilterOrg(e.target.value)}
          />
        </Col> */}
                <Col md={2}>
                    <Form.Select
                        value={sortByCriticality}
                        onChange={(e) =>
                            setSortByCriticality(e.target.value as "asc" | "desc" | "")
                        }
                    >
                        <option value="">Sort by Criticality</option>
                        <option value="asc">Low → High</option>
                        <option value="desc">High → Low</option>
                    </Form.Select>
                </Col>
            </Row>

            {/* Assets Table */}
            <Table striped bordered hover responsive>
                <thead className="table-primary">
                    <tr>
                        <th>#</th>
                        <th>Org</th>
                        <th>Name</th>
                        <th>Type</th>
                        <th>IP</th>
                        <th>Hostname</th>
                        <th>Owner</th>
                        <th>Business Unit</th>
                        <th>Criticality</th>
                        <th>Data Sensitivity</th>
                        <th>Risk Level</th>
                        <th style={{ width: "220px" }}>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {filteredAssets.map((asset, index) => (
                        <tr key={asset._id}>
                            <td>{index + 1}</td>
                            <td>{asset.org}</td>
                            <td>{asset.name}</td>
                            <td>{asset.type}</td>
                            <td>{asset.ip}</td>
                            <td>{asset.hostname}</td>
                            <td>{asset.owner}</td>
                            <td>{asset.business_unit}</td>
                            <td>{asset.criticality}</td>
                            <td>{asset.data_sensitivity}</td>
                            <td>{getRiskLevel(asset)}</td>
                            <td>
                                <div className="d-flex gap-2">
                                    <Button
                                        variant="info"
                                        size="sm"
                                        onClick={() => navigate(`/assets/${asset._id}`)}
                                    >
                                        View
                                    </Button>
                                    <Button
                                        variant="warning"
                                        size="sm"
                                        onClick={() => navigate(`/assets/edit/${asset._id}`)}
                                    >
                                        Edit
                                    </Button>
                                    <Button
                                        variant="danger"
                                        size="sm"
                                        onClick={() => handleDeleteClick(asset)}
                                    >
                                        Delete
                                    </Button>
                                </div>
                            </td>
                        </tr>
                    ))}
                    {filteredAssets.length === 0 && (
                        <tr>
                            <td colSpan={11} className="text-center text-muted">
                                No assets found.
                            </td>
                        </tr>
                    )}
                </tbody>
            </Table>

            {/* Delete Confirmation Modal */}
            <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
                <Modal.Header closeButton>
                    <Modal.Title>Confirm Delete</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    Are you sure you want to delete{" "}
                    <strong>{selectedAsset?.name}</strong>?
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
                        Cancel
                    </Button>
                    <Button variant="danger" onClick={confirmDelete}>
                        Delete
                    </Button>
                </Modal.Footer>
            </Modal>

        </div>
    );
}
