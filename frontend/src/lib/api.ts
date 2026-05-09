export interface CatalogResponse {
  product_id: string;
  embedding_dims: number;
}

export interface VerifyResponse {
  decision: string;
  confidence: number;
  latency_ms: number;
  product_id: string;
  spatial_diff_image: string | null;
  explanation: string | null;
  suspect_reason: string | null;
  baseline_threshold: number | null;
}

export interface HealthResponse {
  status: string;
  gpu_available: boolean;
  model_loaded: boolean;
  cache_size: number;
  ollama_provider: string;
  ollama_connected: boolean;
}

export interface ErrorResponse {
  error: string;
  detail?: string;
}

export interface CalibrateRequest {
  product_id: string;
  category: string;
  decision: string;
  human_label: string;
  cosine_sim: number;
}

export interface CalibrationStatsResponse {
  categories: Record<string, { type1_rate: number; type2_rate: number; total: number }> | null;
  status?: string;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = (await res.json().catch(() => null)) as ErrorResponse | null;
    throw new Error(err?.detail ?? err?.error ?? `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export async function catalogProduct(productId: string, image: File): Promise<CatalogResponse> {
  const form = new FormData();
  form.append('product_id', productId);
  form.append('image', image);
  const res = await fetch('/catalog', { method: 'POST', body: form });
  return handleResponse<CatalogResponse>(res);
}

export async function verifyReturn(productId: string, image: File): Promise<VerifyResponse> {
  const form = new FormData();
  form.append('product_id', productId);
  form.append('image', image);
  const res = await fetch('/verify', { method: 'POST', body: form });
  return handleResponse<VerifyResponse>(res);
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch('/health');
  return handleResponse<HealthResponse>(res);
}

export async function postCalibrate(req: CalibrateRequest): Promise<{ status: string }> {
  const res = await fetch('/calibrate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  return handleResponse<{ status: string }>(res);
}

export async function getCalibrationStats(): Promise<CalibrationStatsResponse> {
  const res = await fetch('/calibration/stats');
  return handleResponse<CalibrationStatsResponse>(res);
}
