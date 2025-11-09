import { useState, useEffect } from "react";
import { Card, Badge, ListGroup, Button } from "react-bootstrap";
import { format } from "date-fns";
import { RiskItem } from "../../models/RiskItem";


export function RiskItemsPanel(data: any) {
  // @ts-ignore
  const URL = import.meta.env.VITE_API_URL;

  const [riskItems, setRiskItems] = useState<RiskItem[]>([]);
  const [loading, setLoading] = useState(true);
    
  // Fetch risk items for this asset
  useEffect(() => {
    fetch(`${URL}/api/detect/risk_items?asset_id=${data.assetId}`)
      .then((r) => r.json())
      .then((data) => {
        setRiskItems(data.data || data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load risk items:", err);
        setLoading(false);
      });
  }, [data.assetId, URL]);

  const getStatusBadge = (status: string) => {
    const variants: { [key: string]: string } = {
      Open: "danger",
      InProgress: "warning",
      Closed: "success",
    };
    return variants[status] || "secondary";
  };

  if (loading) return null;

  return (
    <div className="col-12">
      <Card>
        <Card.Header className="bg-success text-white d-flex justify-content-between align-items-center">
          <strong>Risk Items</strong>
          {riskItems.length === 0 && (
            <Button variant="light" size="sm" /*onClick={}*/>
              Open Risk Item
            </Button>
          )}
        </Card.Header>
        <Card.Body>
          {riskItems.length > 0 ? (
            <ListGroup variant="flush">
              {riskItems.map((item) => (
                <ListGroup.Item
                  key={item._id}
                  className="d-flex justify-content-between align-items-center"
                >
                  <div>
                    <strong>{item.title}</strong>
                    <div className="small text-muted">
                      Status: <Badge bg={getStatusBadge(item.status)}>{item.status}</Badge> | 
                      Owner: {item.owner} | 
                      Due: {format(new Date(item.due), "PP")} | 
                      Score: <Badge bg="dark">{item.score}</Badge>
                    </div>
                  </div>
                  <Button
                    variant="outline-success"
                    size="sm"
                    onClick={() => window.open(`/risk-items/${item._id}`, "_blank")}
                  >
                    View
                  </Button>
                </ListGroup.Item>
              ))}
            </ListGroup>
          ) : (
            <div className="text-center py-3">
              <p className="text-muted">No risk items for this asset.</p>
            </div>
          )}
        </Card.Body>
      </Card>
    </div>
  );
}