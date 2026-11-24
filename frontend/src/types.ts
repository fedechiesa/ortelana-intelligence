export type Risk = "NORMAL" | "ADVERTENCIA" | "CRITICO" | "SIN_BASE";
export interface Summary {
  base_total: number | null;
  current_total: number | null;
  observed_base: number | null;
  observed_current: number | null;
  variation: number | null;
  status: Risk;
  matched_pairs: number;
  excluded_pairs: number;
  coverage_pct: number;
  base_records: number;
  current_records: number;
}
export interface Ranking extends Summary {
  id: string | number;
  name: string;
  line: string | null;
}
export interface Filters {
  anio_base: number;
  anio_actual: number;
  sucursal_id?: number;
  producto_id?: string;
  linea_textil?: string;
}
export interface Policy {
  version: number;
  warning: number;
  critical: number;
  actor?: string;
  created_at?: string;
}
export interface Execution {
  ejecucion_id: string;
  thread_id: string;
  trace_id: string;
  fecha: string;
  duracion_ms: number;
  request: Filters;
  technical_status: string;
  approval_status: string;
  estado: Risk | "ERROR" | null;
  business_status: Risk | null;
  producto?: string;
  variacion?: number | null;
  recomendacion?: string;
  agentes?: string[];
  sales?: Summary;
  products?: Ranking[];
  branches?: Ranking[];
  steps: {
    node: string;
    started_at: string;
    duration_ms: number;
    outcome: string;
  }[];
  error: string | null;
  policy: Policy;
  limitations?: string[];
  dataset_id: string;
}
export interface Collection<T> {
  items: T[];
  total: number;
}
export interface Dataset {
  id: string;
  mode: "demo" | "historical";
  rows: number;
  years: number[];
  branches: number;
  products: number;
  missing_combinations: number;
  expected_combinations: number;
  formats: Record<string, number>;
  limitations: string[];
  source_sha256: string;
}
export interface Indicators {
  executions: number;
  successful: number;
  errors: number;
  success_rate: number | null;
  pending_reviews: number;
  critical: number;
  average_duration_ms: number | null;
  states: Record<string, number>;
  risks: Record<string, number>;
}
export interface Analytics {
  summary: Summary;
  products: Ranking[];
  branches: Ranking[];
  trends: { year: number; total: number; records: number }[];
  policy: Policy;
}
export interface Decision {
  execution_id: string;
  decision: string;
  actor: string;
  comment: string;
  created_at: string;
  policy: Policy;
}
export interface Audit {
  id: number;
  execution_id: string | null;
  actor: string;
  event: string;
  trace_id: string;
  detail: Record<string, unknown>;
  created_at: string;
}
