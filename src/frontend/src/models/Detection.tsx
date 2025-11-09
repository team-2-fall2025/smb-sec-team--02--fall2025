import { Asset } from "./Asset";

export interface Detection {
  _id: string;
  asset_id: string;
  asset_name?: string | null;
  asset?: Asset | null;
  source: string;
  indicator: string;
  ttp: string[];
  severity: number; // 1-5
  confidence: number; // 0-100
  first_seen: string; // ISO string
  last_seen: string; // ISO string
  hit_count: number;
  analyst_note: string;
  raw_ref: Record<string, any>;
}

