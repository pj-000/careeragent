const DEFAULT_API_BASE = "http://127.0.0.1:8000";

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE
).replace(/\/$/, "");

export interface AgentTraceItem {
  agent_id: string;
  summary: string;
  artifact_ids: string[];
  used_skill_refs: string[];
}

export interface ArtifactRef {
  id: string;
  kind: string;
  source_thread_id?: string;
  source_agent?: string;
}

export interface RunResponse {
  run_id: string;
  thread_id: string;
  active_agent: string;
  agent_trace_summary: AgentTraceItem[];
  used_skill_refs: string[];
  artifacts: ArtifactRef[];
  next_actions: string[];
  warnings: string[];
}

async function readError(response: Response): Promise<string> {
  const fallback = `请求失败：${response.status} ${response.statusText}`;
  try {
    const payload = await response.json();
    if (typeof payload?.detail === "string") {
      return payload.detail;
    }
    return JSON.stringify(payload);
  } catch {
    return fallback;
  }
}

export async function createRun(threadId: string, message: string): Promise<RunResponse> {
  const response = await fetch(`${API_BASE_URL}/api/runs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      thread_id: threadId,
      message,
    }),
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<RunResponse>;
}

export async function downloadReport(threadId: string): Promise<string> {
  const response = await fetch(
    `${API_BASE_URL}/api/reports/${encodeURIComponent(threadId)}/markdown`,
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.text();
}
