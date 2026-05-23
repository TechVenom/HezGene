/**
 * API base URL configuration.
 */
const isProd = import.meta.env.PROD;
const API_BASE = isProd ? '' : 'http://127.0.0.1:8000';
const WS_BASE = isProd
  ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
  : 'ws://127.0.0.1:8000';

export { API_BASE, WS_BASE };

/**
 * Generic fetch wrapper with error handling.
 */
async function apiFetch<T = any>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || err.message || 'Request failed');
  }
  return res.json();
}

export async function getHealth() {
  return apiFetch('/api/health');
}

// ── Project Management ───────────────────────────────────────────

export async function uploadProjectZip(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE_URL}/api/project/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to upload project zip');
  }
  return res.json();
}

export async function connectGitHub(url: string) {
  return apiFetch('/api/project/github', {
    method: 'POST',
    body: JSON.stringify({ url }),
  });
}

export async function getProjectTree(path: string = '.') {
  return apiFetch(`/api/project/tree?path=${encodeURIComponent(path)}`);
}

export async function evolveProject(params: {
  project_path?: string;
  file_path?: string;
  function_name?: string;
  use_llm: boolean;
  apply: boolean;
  generations: number;
}) {
  return apiFetch('/api/project/evolve', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function pauseProjectEvolution(sessionId: string) {
  return apiFetch(`/api/project/evolve/${sessionId}/pause`, { method: 'POST' });
}

export async function resumeProjectEvolution(sessionId: string) {
  return apiFetch(`/api/project/evolve/${sessionId}/resume`, { method: 'POST' });
}

export async function cancelProjectEvolution(sessionId: string) {
  return apiFetch(`/api/project/evolve/${sessionId}/cancel`, { method: 'POST' });
}

// ── File Management ──────────────────────────────────────────────

export async function uploadFiles(files: FileList) {
  const formData = new FormData();
  Array.from(files).forEach((f) => formData.append('files', f));
  const res = await fetch(`${API_BASE}/api/upload`, { method: 'POST', body: formData });
  return res.json();
}

export async function getFiles() {
  return apiFetch('/api/files');
}

export async function getFileDetails(fileId: string) {
  const safeId = fileId === '.' ? '__PROJECT__' : encodeURIComponent(fileId);
  return apiFetch(`/api/files/${safeId}`);
}

export async function deleteFile(fileId: string) {
  return apiFetch(`/api/files/${encodeURIComponent(fileId)}`, { method: 'DELETE' });
}

// ── Evolution ────────────────────────────────────────────────────

export interface EvolutionParams {
  file_id: string;
  function_name?: string;
  use_llm?: boolean;
  apply?: boolean;
  generations?: number;
}

export async function startEvolution(params: EvolutionParams) {
  return apiFetch('/api/evolve', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getEvolutionStatus(sessionId: string) {
  return apiFetch(`/api/evolve/${sessionId}`);
}

// ── DNA & Analysis ───────────────────────────────────────────────

export async function getFunctions() {
  return apiFetch('/api/functions');
}

export async function getDNA(fileId: string, functionName: string) {
  return apiFetch(`/api/dna/${encodeURIComponent(fileId)}/${encodeURIComponent(functionName)}`);
}

export async function scanFile(fileId: string) {
  const safeId = fileId === '.' ? '__PROJECT__' : encodeURIComponent(fileId);
  return apiFetch(`/api/scan/${safeId}`, { method: 'POST' });
}

// ── Configuration ────────────────────────────────────────────────

export async function getConfig() {
  return apiFetch('/api/config');
}

export async function updateConfig(key: string, value: any) {
  return apiFetch('/api/config', {
    method: 'PUT',
    body: JSON.stringify({ key, value }),
  });
}

export async function testLLM(provider: string, model: string, baseUrl?: string, apiKey?: string) {
  return apiFetch('/api/config/test-llm', {
    method: 'POST',
    body: JSON.stringify({ provider, model, base_url: baseUrl || '', api_key: apiKey || '' }),
  });
}

// ── History ──────────────────────────────────────────────────────

export async function getHistory(limit = 50, status?: string) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (status) params.set('status', status);
  return apiFetch(`/api/history?${params}`);
}

export async function getHistoryDetail(target: string) {
  const encoded = target.replace(':', '--');
  return apiFetch(`/api/history/${encodeURIComponent(encoded)}`);
}

// ── Stats ────────────────────────────────────────────────────────

export async function getStats() {
  return apiFetch('/api/stats');
}

// ── Freeze / Unfreeze ────────────────────────────────────────────

export async function freezeFunction(fileId: string, functionName: string) {
  return apiFetch(`/api/freeze/${encodeURIComponent(fileId)}/${encodeURIComponent(functionName)}`, { method: 'POST' });
}

export async function unfreezeFunction(fileId: string, functionName: string) {
  return apiFetch(`/api/unfreeze/${encodeURIComponent(fileId)}/${encodeURIComponent(functionName)}`, { method: 'POST' });
}

// ── Clear / Delete History & Sandbox ─────────────────────────────

export async function clearHistory() {
  return apiFetch('/api/history', { method: 'DELETE' });
}

export async function deleteHistoryItem(target: string) {
  const encoded = target.replace(':', '--');
  return apiFetch(`/api/history/${encodeURIComponent(encoded)}`, { method: 'DELETE' });
}

export async function clearSandbox() {
  return apiFetch('/api/sandbox', { method: 'DELETE' });
}

export async function cleanSystem() {
  return apiFetch('/api/system/clean', { method: 'DELETE' });
}

export async function deleteSandboxItem(target: string) {
  const encoded = target.replace(':', '--');
  return apiFetch(`/api/sandbox/${encodeURIComponent(encoded)}`, { method: 'DELETE' });
}

export async function deployEvolvedCode(target: string) {
  return apiFetch('/api/deploy', {
    method: 'POST',
    body: JSON.stringify({ target }),
  });
}

