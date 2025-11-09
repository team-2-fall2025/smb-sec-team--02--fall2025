export interface RiskItem {
  _id?: string;
  title: string;
  asset_id: string;
  status: string; 
  owner: string; 
  due: string;
  score: number;
  hit_count: number;
  created_at: string;
  updated_at: string;
}