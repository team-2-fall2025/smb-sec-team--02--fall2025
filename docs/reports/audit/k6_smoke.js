import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:5173";
const API = `${BASE_URL}/api`;

export const options = {
  stages: [
    { duration: "30s", target: 5 },
    { duration: "60s", target: 20 },
    { duration: "30s", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<800"],
  },
};

export default function () {
  const r1 = http.get(`${API}/ping`);
  check(r1, { "ping 200": (res) => res.status === 200 });
  sleep(1);
}
