import { useEffect, useState } from "react";

export default function Health() {
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    fetch("/health").then(r => r.json()).then(setData).catch(() => setData({error: true}));
  }, []);
  return (
    <div>
      <h1>Platform Health</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}