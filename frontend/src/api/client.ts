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
  source_thread_id?: string | null;
  source_agent?: string | null;
}

export type RunStatus =
  | "pending"
  | "running"
  | "completed"
  | "needs_input"
  | "blocked_by_prerequisite"
  | "provider_error"
  | "permission_denied"
  | "failed";

export interface ConversationMessage {
  id: string;
  thread_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  run_id?: string | null;
  created_at: string;
  artifact_refs: string[];
  last_business_agent?: string | null;
  current_runtime_node?: string | null;
  warnings?: string[];
}

export interface SupervisorDecision {
  intent: string;
  target_agent: string;
  required_input_artifact_kinds: string[];
  required_capabilities: string[];
  expected_output_artifact_kinds: string[];
  missing_prerequisites: string[];
  missing_capabilities: string[];
  user_facing_reason: string;
  next_actions: string[];
}

export interface WorkspaceContext {
  thread_id: string;
  active_goal: string;
  active_profile_id?: string | null;
  active_job_analysis_id?: string | null;
  active_match_id?: string | null;
  active_plan_id?: string | null;
  active_training_result_id?: string | null;
  active_interview_summary_id?: string | null;
  active_report_id?: string | null;
  active_compaction_snapshot_id?: string | null;
  updated_by_run_id: string;
  updated_at: string;
}

export interface ArtifactChainItem extends ArtifactRef {
  parent_artifact_ids: string[];
  updated_at?: string | null;
}

export interface WorkspaceResponse {
  thread_id: string;
  active_context: WorkspaceContext;
  workspace_artifacts: Record<string, Record<string, unknown>>;
  artifact_chain: ArtifactChainItem[];
}

export interface SkillRuntimeRef {
  skill_id: string;
  version: string;
  section_ids: string[];
  detail_level: "summary" | "full" | "skipped";
  summary_digest: string;
}

export interface MemoryItem {
  id: string;
  thread_id: string;
  scope: "profile" | "preference" | "goal" | "skill" | "evidence";
  fact: string;
  confidence: number;
  status: "confirmed" | "pending_confirmation" | "rejected";
  source_artifact_id?: string | null;
  source_message_id?: string | null;
}

export interface RunResponse {
  run_id: string;
  thread_id: string;
  active_agent: string;
  run_status: RunStatus;
  last_business_agent?: string | null;
  current_runtime_node?: string | null;
  assistant_message?: ConversationMessage | null;
  supervisor_decision?: SupervisorDecision | null;
  agent_trace_summary: AgentTraceItem[];
  used_skill_refs: string[];
  used_skill_runtime_refs: SkillRuntimeRef[];
  artifacts: ArtifactRef[];
  artifact_chain: ArtifactChainItem[];
  workspace_delta?: {
    created_artifacts: ArtifactChainItem[];
    updated_context: WorkspaceContext;
  } | null;
  compaction_snapshot?: Record<string, unknown> | null;
  memory_updates: MemoryItem[];
  blocking_reason?: string | null;
  missing_artifacts: string[];
  missing_capabilities: string[];
  retryable: boolean;
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

export async function getWorkspace(threadId: string): Promise<WorkspaceResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/threads/${encodeURIComponent(threadId)}/workspace`,
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<WorkspaceResponse>;
}

export async function getMessages(threadId: string): Promise<ConversationMessage[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/threads/${encodeURIComponent(threadId)}/messages`,
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<ConversationMessage[]>;
}
