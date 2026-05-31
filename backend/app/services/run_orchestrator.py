from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from app.agents.runtime import PermissionDenied
from app.graphs.workflow import run_career_graph_state as run_career_graph
from app.providers.base import ProviderError
from app.repositories.json_repository import JsonArtifactRepository
from app.repositories.json_thread_repository import (
    JsonConversationRepository,
    JsonMemoryRepository,
    JsonWorkspaceContextRepository,
)
from app.schemas.memory import CompactionSnapshot, MemoryItem, MemoryScope, MemoryStatus
from app.schemas.runs import (
    ArtifactChainItem,
    ConversationMessage,
    ConversationRole,
    RunResponse,
    RunStatus,
    SupervisorDecision,
    WorkspaceContext,
    WorkspaceDelta,
)
from app.services.workspace import artifact_chain_from_context, build_active_artifact_facts, update_context_from_artifacts


BACKFILL_KIND_ORDER = [
    "profile",
    "job_analysis",
    "match",
    "plan",
    "training_result",
    "interview_summary",
    "report",
    "compaction_snapshot",
]


class RunOrchestrator:
    def __init__(self, root: Path) -> None:
        self.artifact_repo = JsonArtifactRepository(root)
        self.message_repo = JsonConversationRepository(root)
        self.context_repo = JsonWorkspaceContextRepository(root)
        self.memory_repo = JsonMemoryRepository(root)

    def run(self, thread_id: str, message: str) -> RunResponse:
        run_id = f"run-{uuid4().hex[:12]}"
        user_message = ConversationMessage(
            id=f"msg-{uuid4().hex[:12]}",
            thread_id=thread_id,
            role=ConversationRole.USER,
            content=message,
            run_id=run_id,
        )
        self.message_repo.save(user_message)

        before_refs = self.artifact_repo.list_by_thread(thread_id)
        before_ids = {artifact["id"] for artifact in before_refs}
        current_context = self.context_repo.get(thread_id) or self._backfill_context_from_thread_artifacts(
            thread_id,
            run_id,
            before_refs,
        )
        run_metadata = self._metadata_from_context(current_context)
        try:
            state, trace = run_career_graph(
                thread_id,
                message,
                self.artifact_repo,
                run_id=run_id,
                metadata=run_metadata,
            )
        except PermissionDenied as exc:
            return self._error_response(
                thread_id=thread_id,
                run_id=run_id,
                content="当前 Agent 没有权限执行该操作。",
                run_status=RunStatus.PERMISSION_DENIED,
                retryable=False,
                warning="permission_denied",
            )
        except ProviderError as exc:
            return self._error_response(
                thread_id=thread_id,
                run_id=run_id,
                content="模型服务暂时不可用，可以稍后重试或切换 Mock Provider。",
                run_status=RunStatus.PROVIDER_ERROR,
                retryable=True,
                warning="provider_error",
            )
        except Exception:
            return self._error_response(
                thread_id=thread_id,
                run_id=run_id,
                content="本轮处理失败，请稍后重试。",
                run_status=RunStatus.FAILED,
                retryable=True,
                warning="unexpected_runtime_error",
            )

        metadata = state.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        after_refs = self.artifact_repo.list_by_thread(thread_id)
        created_ids = [artifact["id"] for artifact in after_refs if artifact["id"] not in before_ids]
        supervisor_decision = _supervisor_decision(state, metadata)
        last_business_agent = metadata.get("last_business_agent") or state.get("last_business_agent")
        current_runtime_node = metadata.get("current_runtime_node") or state.get("current_runtime_node")
        context = update_context_from_artifacts(
            thread_id=thread_id,
            run_id=run_id,
            created_artifact_ids=created_ids,
            active_goal=_active_goal(message, supervisor_decision),
            artifact_repo=self.artifact_repo,
            context_repo=self.context_repo,
        )
        chain = artifact_chain_from_context(context, self.artifact_repo)
        assistant_message = ConversationMessage(
            id=f"msg-{uuid4().hex[:12]}",
            thread_id=thread_id,
            role=ConversationRole.ASSISTANT,
            content=_assistant_summary(supervisor_decision, created_ids),
            run_id=run_id,
            artifact_refs=created_ids,
            last_business_agent=last_business_agent,
            current_runtime_node=current_runtime_node,
            warnings=state.get("warnings", []),
        )
        self.message_repo.save(assistant_message)
        memory_updates = self._save_memory_candidates(
            thread_id=thread_id,
            source_message_id=user_message.id,
            message=message,
            supervisor_decision=supervisor_decision,
        )

        return RunResponse(
            run_id=run_id,
            thread_id=thread_id,
            run_status=_status_from_state(state, supervisor_decision),
            active_agent=state.get("active_agent", "supervisor"),
            last_business_agent=last_business_agent,
            current_runtime_node=current_runtime_node,
            assistant_message=assistant_message,
            supervisor_decision=supervisor_decision,
            workspace_delta=WorkspaceDelta(
                created_artifacts=_created_chain_items(created_ids, self.artifact_repo),
                updated_context=context,
            ),
            artifact_chain=chain,
            used_skill_runtime_refs=state.get("loaded_skill_runtime_refs", []),
            compaction_snapshot=_latest_compaction(chain, self.artifact_repo),
            memory_updates=memory_updates,
            blocking_reason=_blocking_reason(supervisor_decision),
            missing_artifacts=supervisor_decision.missing_prerequisites if supervisor_decision else [],
            missing_capabilities=supervisor_decision.missing_capabilities if supervisor_decision else [],
            retryable=False,
            agent_trace_summary=trace,
            used_skill_refs=state.get("loaded_skill_refs", []),
            artifacts=after_refs,
            next_actions=supervisor_decision.next_actions if supervisor_decision else ["继续职业工作流"],
            warnings=state.get("warnings", []),
        )

    def _metadata_from_context(self, context: WorkspaceContext | None) -> dict[str, Any]:
        if context is None:
            return {}
        chain = artifact_chain_from_context(context, self.artifact_repo)
        return {
            "active_artifact_kinds": [item.kind for item in chain],
            "active_artifact_ids": [item.id for item in chain],
            "active_facts": build_active_artifact_facts(context, self.artifact_repo).model_dump(mode="json"),
            "active_context": context.model_dump(mode="json"),
        }

    def _backfill_context_from_thread_artifacts(
        self,
        thread_id: str,
        run_id: str,
        artifact_refs: list[dict[str, str]],
    ) -> WorkspaceContext | None:
        artifacts_by_id: dict[str, dict[str, Any]] = {}
        for artifact_ref in artifact_refs:
            try:
                artifact = self.artifact_repo.get(artifact_ref["id"])
            except (FileNotFoundError, KeyError, ValueError):
                continue
            if artifact.get("source_thread_id") != thread_id:
                continue
            kind = str(artifact.get("kind"))
            if kind not in BACKFILL_KIND_ORDER:
                continue
            artifacts_by_id[str(artifact["id"])] = artifact
        artifact_ids = _backfill_chain_ids(list(artifacts_by_id.values()), artifacts_by_id)
        if not artifact_ids:
            return None
        return update_context_from_artifacts(
            thread_id=thread_id,
            run_id=run_id,
            created_artifact_ids=artifact_ids,
            active_goal=None,
            artifact_repo=self.artifact_repo,
            context_repo=self.context_repo,
        )

    def _save_memory_candidates(
        self,
        thread_id: str,
        source_message_id: str,
        message: str,
        supervisor_decision: SupervisorDecision | None,
    ) -> list[MemoryItem]:
        if (
            supervisor_decision is None
            or supervisor_decision.missing_prerequisites
            or supervisor_decision.missing_capabilities
        ):
            return []
        if supervisor_decision.intent.value not in {"build_profile", "analyze_job", "plan"}:
            return []
        memory = MemoryItem(
            id=f"memory-{uuid4().hex[:12]}",
            thread_id=thread_id,
            scope=MemoryScope.GOAL,
            fact=message[:160],
            source_message_id=source_message_id,
            confidence=0.72,
            status=MemoryStatus.PENDING_CONFIRMATION,
        )
        return [self.memory_repo.save(memory)]

    def _error_response(
        self,
        thread_id: str,
        run_id: str,
        content: str,
        run_status: RunStatus,
        retryable: bool,
        warning: str,
    ) -> RunResponse:
        context = self.context_repo.get(thread_id)
        if context is None:
            context = self.context_repo.save(
                WorkspaceContext(thread_id=thread_id, active_goal="职业发展规划", updated_by_run_id=run_id)
            )
        chain = artifact_chain_from_context(context, self.artifact_repo)
        assistant_message = ConversationMessage(
            id=f"msg-{uuid4().hex[:12]}",
            thread_id=thread_id,
            role=ConversationRole.ASSISTANT,
            content=content,
            run_id=run_id,
            artifact_refs=[],
            current_runtime_node="error",
            warnings=[warning],
        )
        self.message_repo.save(assistant_message)
        return RunResponse(
            run_id=run_id,
            thread_id=thread_id,
            run_status=run_status,
            active_agent="supervisor",
            current_runtime_node="error",
            assistant_message=assistant_message,
            artifacts=self.artifact_repo.list_by_thread(thread_id),
            artifact_chain=chain,
            workspace_delta=WorkspaceDelta(created_artifacts=[], updated_context=context),
            memory_updates=[],
            retryable=retryable,
            next_actions=["重试本轮请求"] if retryable else ["调整请求后继续"],
            warnings=[warning],
        )


def _supervisor_decision(state: dict[str, Any], metadata: dict[str, Any]) -> SupervisorDecision | None:
    decision_payload = metadata.get("supervisor_decision") or state.get("supervisor_decision")
    if not isinstance(decision_payload, dict):
        return None
    return SupervisorDecision.model_validate(decision_payload)


def _active_goal(message: str, decision: SupervisorDecision | None) -> str | None:
    if decision is not None and decision.intent.value in {"analyze_job", "match", "plan"}:
        return message[:80]
    return None


def _assistant_summary(decision: SupervisorDecision | None, artifact_ids: list[str]) -> str:
    if decision is not None and (decision.missing_prerequisites or decision.missing_capabilities):
        details: list[str] = []
        if decision.missing_prerequisites:
            details.append(f"缺少前置产物：{', '.join(decision.missing_prerequisites)}。")
        if decision.missing_capabilities:
            details.append(f"缺少能力状态：{', '.join(decision.missing_capabilities)}。")
        return f"{decision.user_facing_reason} {' '.join(details)}".strip()
    if artifact_ids:
        return f"已完成本轮处理，并生成 {len(artifact_ids)} 个运行产物。"
    return "本轮已处理完成，可以继续输入下一步。"


def _status_from_state(state: dict[str, Any], decision: SupervisorDecision | None) -> RunStatus:
    if decision is not None and (decision.missing_prerequisites or decision.missing_capabilities):
        return RunStatus.BLOCKED_BY_PREREQUISITE
    if state.get("pending_question"):
        return RunStatus.NEEDS_INPUT
    return RunStatus.COMPLETED


def _blocking_reason(decision: SupervisorDecision | None) -> str | None:
    if decision is not None and (decision.missing_prerequisites or decision.missing_capabilities):
        return decision.user_facing_reason
    return None


def _created_chain_items(artifact_ids: list[str], artifact_repo: JsonArtifactRepository) -> list[ArtifactChainItem]:
    items: list[ArtifactChainItem] = []
    for artifact_id in artifact_ids:
        try:
            items.append(_chain_item(artifact_repo.get(artifact_id)))
        except (FileNotFoundError, KeyError, ValueError):
            continue
    return items


def _backfill_chain_ids(
    artifacts: list[dict[str, Any]],
    artifacts_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    if not artifacts:
        return []
    sorted_artifacts = sorted(artifacts, key=_artifact_sort_key)
    anchor = sorted_artifacts[-1]
    parent_chain = _transitive_chain(anchor, artifacts_by_id)
    if _parent_ids(anchor) or _kind_index(str(anchor.get("kind"))) > _kind_index("job_analysis"):
        return _ordered_ids_by_kind(parent_chain or [anchor])
    return _latest_prefix_ids(sorted_artifacts, str(anchor.get("kind")))


def _transitive_chain(
    artifact: dict[str, Any],
    artifacts_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    visited: set[str] = set()
    chain: list[dict[str, Any]] = []

    def visit(current: dict[str, Any]) -> None:
        artifact_id = str(current.get("id", ""))
        if not artifact_id or artifact_id in visited:
            return
        visited.add(artifact_id)
        for parent_id in _parent_ids(current):
            parent = artifacts_by_id.get(parent_id)
            if parent is not None:
                visit(parent)
        chain.append(current)

    visit(artifact)
    return chain


def _latest_prefix_ids(artifacts: list[dict[str, Any]], anchor_kind: str) -> list[str]:
    max_index = _kind_index(anchor_kind)
    latest_by_kind: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        kind = str(artifact.get("kind"))
        kind_index = _kind_index(kind)
        if kind_index > _kind_index("job_analysis") or kind_index > max_index:
            continue
        current = latest_by_kind.get(kind)
        if current is None or _artifact_sort_key(artifact) > _artifact_sort_key(current):
            latest_by_kind[kind] = artifact
    return [latest_by_kind[kind]["id"] for kind in BACKFILL_KIND_ORDER if kind in latest_by_kind]


def _ordered_ids_by_kind(artifacts: list[dict[str, Any]]) -> list[str]:
    latest_by_kind: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        kind = str(artifact.get("kind"))
        if kind not in BACKFILL_KIND_ORDER:
            continue
        current = latest_by_kind.get(kind)
        if current is None or _artifact_sort_key(artifact) > _artifact_sort_key(current):
            latest_by_kind[kind] = artifact
    return [latest_by_kind[kind]["id"] for kind in BACKFILL_KIND_ORDER if kind in latest_by_kind]


def _parent_ids(artifact: dict[str, Any]) -> list[str]:
    parent_ids = artifact.get("parent_artifact_ids")
    if not isinstance(parent_ids, list):
        return []
    return [str(parent_id) for parent_id in parent_ids]


def _kind_index(kind: str) -> int:
    try:
        return BACKFILL_KIND_ORDER.index(kind)
    except ValueError:
        return len(BACKFILL_KIND_ORDER)


def _artifact_sort_key(artifact: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(artifact.get("updated_at", "")),
        str(artifact.get("created_at", "")),
        str(artifact.get("id", "")),
    )


def _chain_item(artifact: dict[str, Any]) -> ArtifactChainItem:
    return ArtifactChainItem(
        id=artifact["id"],
        kind=artifact["kind"],
        source_thread_id=artifact["source_thread_id"],
        source_agent=artifact["source_agent"],
        parent_artifact_ids=artifact.get("parent_artifact_ids", []),
        updated_at=artifact.get("updated_at"),
    )


def _latest_compaction(chain: list[ArtifactChainItem], artifact_repo: JsonArtifactRepository) -> dict[str, Any] | None:
    for item in reversed(chain):
        if item.kind != "compaction_snapshot":
            continue
        try:
            artifact = artifact_repo.get(item.id)
        except (FileNotFoundError, KeyError, ValueError):
            return None
        payload = artifact.get("payload")
        if not isinstance(payload, dict):
            return None
        allowed = {field: payload[field] for field in CompactionSnapshot.model_fields if field in payload}
        try:
            return CompactionSnapshot.model_validate(allowed).model_dump(mode="json")
        except ValueError:
            return None
    return None
