export interface Asset {
  _id: string;
  org: string;
  name: string;
  type: string;
  ip: string;
  hostname: string;
  owner: string;
  business_unit: string;
  criticality: number;       
  data_sensitivity: string;  
  intel_events: IntelEvent[];
  risk: {
    score: number;
    explain: string;
    intel_max_severity_7d: number;
  };
}
