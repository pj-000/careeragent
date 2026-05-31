from __future__ import annotations

from typing import Any

from app.agents.manifests import AGENT_MANIFESTS
from app.agents.runtime import coerce_state, make_runtime
from app.graphs.state import AgentSnapshot
from app.repositories.interfaces import ArtifactRepository
from app.schemas.runs import ActiveArtifactFacts, SupervisorDecision, SupervisorIntent


REQUIRED_BY_INTENT: dict[SupervisorIntent, list[str]] = {
    SupervisorIntent.BUILD_PROFILE: [],
    SupervisorIntent.ANALYZE_JOB: [],
    SupervisorIntent.MATCH: ["profile", "job_analysis"],
    SupervisorIntent.PLAN: ["profile", "job_analysis", "match"],
    SupervisorIntent.CREATE_TRAINING: ["match", "plan"],
    SupervisorIntent.SUBMIT_TRAINING: ["match", "plan"],
    SupervisorIntent.START_INTERVIEW: ["profile", "job_analysis", "match", "plan", "training_result"],
    SupervisorIntent.ANSWER_INTERVIEW: ["profile", "job_analysis", "match", "plan", "training_result"],
    SupervisorIntent.EXPORT_REPORT: [
        "profile",
        "job_analysis",
        "match",
        "plan",
        "training_result",
        "interview_summary",
    ],
    SupervisorIntent.CLARIFY: [],
}

REQUIRED_CAPABILITIES_BY_INTENT: dict[SupervisorIntent, list[str]] = {
    SupervisorIntent.BUILD_PROFILE: [],
    SupervisorIntent.ANALYZE_JOB: [],
    SupervisorIntent.MATCH: [],
    SupervisorIntent.PLAN: [],
    SupervisorIntent.CREATE_TRAINING: [],
    SupervisorIntent.SUBMIT_TRAINING: [],
    SupervisorIntent.START_INTERVIEW: ["training_scored"],
    SupervisorIntent.ANSWER_INTERVIEW: ["training_scored"],
    SupervisorIntent.EXPORT_REPORT: ["training_scored", "interview_completed"],
    SupervisorIntent.CLARIFY: [],
}

EXPECTED_OUTPUT_BY_INTENT: dict[SupervisorIntent, list[str]] = {
    SupervisorIntent.BUILD_PROFILE: ["profile"],
    SupervisorIntent.ANALYZE_JOB: ["job_analysis"],
    SupervisorIntent.MATCH: ["match"],
    SupervisorIntent.PLAN: ["plan"],
    SupervisorIntent.CREATE_TRAINING: ["training_result"],
    SupervisorIntent.SUBMIT_TRAINING: ["training_result"],
    SupervisorIntent.START_INTERVIEW: ["interview_summary"],
    SupervisorIntent.ANSWER_INTERVIEW: ["interview_summary"],
    SupervisorIntent.EXPORT_REPORT: ["report"],
    SupervisorIntent.CLARIFY: [],
}

TARGET_BY_INTENT: dict[SupervisorIntent, str] = {
    SupervisorIntent.BUILD_PROFILE: "profile",
    SupervisorIntent.ANALYZE_JOB: "job",
    SupervisorIntent.MATCH: "match",
    SupervisorIntent.PLAN: "planning",
    SupervisorIntent.CREATE_TRAINING: "training",
    SupervisorIntent.SUBMIT_TRAINING: "training",
    SupervisorIntent.START_INTERVIEW: "interview",
    SupervisorIntent.ANSWER_INTERVIEW: "interview",
    SupervisorIntent.EXPORT_REPORT: "report",
    SupervisorIntent.CLARIFY: "memory_manager",
}


def supervisor_node(state: dict[str, Any], artifact_repo: ArtifactRepository) -> dict[str, Any]:
    career_state = coerce_state(state)
    runtime = make_runtime(career_state, "supervisor", artifact_repo)
    available_artifact_kinds = _available_artifact_kinds(career_state.metadata, career_state.thread_id, artifact_repo)
    active_facts = _active_facts(
        career_state.metadata,
        career_state.thread_id,
        available_artifact_kinds,
        artifact_repo,
    )
    decision = decide_user_message(career_state.user_message, available_artifact_kinds, active_facts=active_facts)
    target = decision.target_agent
    career_state.supervisor_decision = decision.model_dump(mode="json")
    career_state.metadata["supervisor_decision"] = decision.model_dump(mode="json")
    career_state.loaded_skill_refs = _append_unique(
        career_state.loaded_skill_refs,
        AGENT_MANIFESTS["supervisor"].skill_policy.default_skill_ids,
    )
    career_state.agent_snapshots["supervisor"] = AgentSnapshot(
        agent_id="supervisor",
        summary=f"Routed current message to {target}.",
        private_context={"route": target, "decision": decision.model_dump(mode="json")},
        last_artifact_ids=[],
        used_skill_refs=list(AGENT_MANIFESTS["supervisor"].skill_policy.default_skill_ids),
    )
    career_state.active_agent = "supervisor"
    career_state.current_runtime_node = "supervisor"
    career_state.metadata["current_runtime_node"] = "supervisor"
    if decision.missing_prerequisites or decision.missing_capabilities:
        career_state.pending_question = decision.user_facing_reason
        career_state.last_business_agent = None
        career_state.metadata["last_business_agent"] = None
        if decision.missing_prerequisites:
            career_state.warnings = _append_unique(
                career_state.warnings,
                [f"Missing required artifact kinds: {', '.join(decision.missing_prerequisites)}"],
            )
        if decision.missing_capabilities:
            career_state.warnings = _append_unique(
                career_state.warnings,
                [f"Missing required capabilities: {', '.join(decision.missing_capabilities)}"],
            )
        career_state.next_agent = runtime.handoff_to("memory_manager")
        return career_state.model_dump()

    last_business_agent = target if target != "memory_manager" else None
    career_state.last_business_agent = last_business_agent
    career_state.metadata["last_business_agent"] = last_business_agent
    career_state.next_agent = runtime.handoff_to(target)
    return career_state.model_dump()


def decide_user_message(
    message: str,
    available_artifact_kinds: set[str] | list[str] | tuple[str, ...],
    active_facts: ActiveArtifactFacts | dict[str, Any] | None = None,
) -> SupervisorDecision:
    available = set(available_artifact_kinds)
    facts = _coerce_active_facts(active_facts, available)
    intent = _detect_intent(message)
    required_inputs = REQUIRED_BY_INTENT[intent]
    required_capabilities = REQUIRED_CAPABILITIES_BY_INTENT[intent]
    missing_prerequisites = [kind for kind in required_inputs if kind not in available]
    missing_capabilities = (
        [capability for capability in required_capabilities if not _has_capability(facts, capability)]
        if not missing_prerequisites
        else []
    )

    return SupervisorDecision(
        intent=intent,
        target_agent=TARGET_BY_INTENT[intent],
        required_input_artifact_kinds=list(required_inputs),
        required_capabilities=list(required_capabilities),
        expected_output_artifact_kinds=list(EXPECTED_OUTPUT_BY_INTENT[intent]),
        missing_prerequisites=missing_prerequisites,
        missing_capabilities=missing_capabilities,
        user_facing_reason=_user_facing_reason(intent, missing_prerequisites, missing_capabilities),
        next_actions=_next_actions_for(intent, missing_prerequisites, missing_capabilities),
    )


def route_user_message(message: str) -> str:
    return TARGET_BY_INTENT[_detect_intent(message)]


def _append_unique(existing: list[str], additions: list[str]) -> list[str]:
    values = list(existing)
    for item in additions:
        if item not in values:
            values.append(item)
    return values


def _detect_intent(message: str) -> SupervisorIntent:
    normalized = message.lower()
    if message.startswith("回答") or "回答1" in message or "回答2" in message or "回答3" in message or "面试答案" in message:
        return SupervisorIntent.ANSWER_INTERVIEW
    if "训练答案" in message or "我的训练答案" in message or "training answer" in normalized:
        return SupervisorIntent.SUBMIT_TRAINING
    if "我的简历" in message or "简历" in message or "我会" in message or "我有" in message or "resume" in normalized or "profile" in normalized:
        return SupervisorIntent.BUILD_PROFILE
    if "岗位" in message or "jd" in normalized or "job" in normalized:
        return SupervisorIntent.ANALYZE_JOB
    if "训练" in message or "training task" in normalized or "practice" in normalized:
        return SupervisorIntent.CREATE_TRAINING
    if "报告" in message or "report" in normalized:
        return SupervisorIntent.EXPORT_REPORT
    if "面试" in message or "interview" in normalized:
        return SupervisorIntent.START_INTERVIEW
    if "计划" in message or "路径" in message or "plan" in normalized:
        return SupervisorIntent.PLAN
    if "匹配" in message or "match" in normalized:
        return SupervisorIntent.MATCH
    if "继续" in message or "记忆" in message or "压缩" in message:
        return SupervisorIntent.CLARIFY
    return SupervisorIntent.MATCH


def _available_artifact_kinds(
    metadata: dict[str, Any],
    thread_id: str,
    artifact_repo: ArtifactRepository,
) -> set[str]:
    active_artifact_kinds = metadata.get("active_artifact_kinds")
    if isinstance(active_artifact_kinds, list):
        return {str(kind) for kind in active_artifact_kinds}
    return {artifact["kind"] for artifact in artifact_repo.list_by_thread(thread_id)}


def _active_facts(
    metadata: dict[str, Any],
    thread_id: str,
    available_artifact_kinds: set[str],
    artifact_repo: ArtifactRepository,
) -> ActiveArtifactFacts:
    active_facts = metadata.get("active_facts")
    if isinstance(active_facts, dict):
        return _coerce_active_facts(active_facts, available_artifact_kinds)
    return _active_facts_from_artifacts(thread_id, available_artifact_kinds, artifact_repo)


def _coerce_active_facts(
    active_facts: ActiveArtifactFacts | dict[str, Any] | None,
    available_artifact_kinds: set[str],
) -> ActiveArtifactFacts:
    if isinstance(active_facts, ActiveArtifactFacts):
        return active_facts
    if isinstance(active_facts, dict):
        return ActiveArtifactFacts.model_validate(active_facts)
    return ActiveArtifactFacts(
        has_profile="profile" in available_artifact_kinds,
        has_job_analysis="job_analysis" in available_artifact_kinds,
        has_match="match" in available_artifact_kinds,
        has_plan="plan" in available_artifact_kinds,
        has_training_result="training_result" in available_artifact_kinds,
        training_submitted=False,
        training_scored=False,
        has_interview_summary="interview_summary" in available_artifact_kinds,
        interview_turn_count=0,
        interview_completed=False,
    )


def _active_facts_from_artifacts(
    thread_id: str,
    available_artifact_kinds: set[str],
    artifact_repo: ArtifactRepository,
) -> ActiveArtifactFacts:
    training = _latest_artifact_content(thread_id, "training_result", available_artifact_kinds, artifact_repo)
    interview = _latest_artifact_content(thread_id, "interview_summary", available_artifact_kinds, artifact_repo)
    training_submitted = (
        bool(training.get("has_submission"))
        and training.get("submission") is not None
    )
    training_scored = training_submitted and training.get("score") is not None
    turn_count = interview.get("turn_count")
    if not isinstance(turn_count, int):
        turn_count = 0
    return ActiveArtifactFacts(
        has_profile="profile" in available_artifact_kinds,
        has_job_analysis="job_analysis" in available_artifact_kinds,
        has_match="match" in available_artifact_kinds,
        has_plan="plan" in available_artifact_kinds,
        has_training_result="training_result" in available_artifact_kinds,
        training_submitted=training_submitted,
        training_scored=training_scored,
        has_interview_summary="interview_summary" in available_artifact_kinds,
        interview_turn_count=turn_count,
        interview_completed=turn_count >= 3,
    )


def _latest_artifact_content(
    thread_id: str,
    kind: str,
    available_artifact_kinds: set[str],
    artifact_repo: ArtifactRepository,
) -> dict[str, Any]:
    if kind not in available_artifact_kinds:
        return {}
    records = []
    for artifact in artifact_repo.list_by_kind(thread_id, kind):
        record = artifact_repo.get(artifact["id"])
        payload = record.get("payload", {})
        content = payload.get("content") if isinstance(payload, dict) else None
        records.append(
            (
                str(record.get("updated_at", "")),
                str(record.get("created_at", "")),
                str(record.get("id", "")),
                content if isinstance(content, dict) else {},
            )
        )
    if not records:
        return {}
    return dict(sorted(records, key=lambda item: item[:3])[-1][3])


def _has_capability(facts: ActiveArtifactFacts, capability: str) -> bool:
    if capability == "training_scored":
        return facts.training_scored
    if capability == "interview_completed":
        return facts.interview_completed
    return False


def _user_facing_reason(
    intent: SupervisorIntent,
    missing_prerequisites: list[str],
    missing_capabilities: list[str],
) -> str:
    if missing_prerequisites:
        labels = "、".join(_artifact_label(kind) for kind in missing_prerequisites)
        return f"需要先补齐{labels}，再继续处理该请求。"
    if "training_scored" in missing_capabilities:
        return "需要先提交并完成训练答案评分，才能进入模拟面试或导出报告。"
    if "interview_completed" in missing_capabilities:
        return "需要先完成三轮模拟面试，才能导出最终报告。"
    if intent == SupervisorIntent.SUBMIT_TRAINING:
        return "已识别为训练答案提交，将交给训练 Agent 评分并保存训练结果。"
    return f"已识别用户意图为{intent.value}，将交给{TARGET_BY_INTENT[intent]}处理。"


def _next_actions_for(
    intent: SupervisorIntent,
    missing_prerequisites: list[str],
    missing_capabilities: list[str],
) -> list[str]:
    if missing_prerequisites:
        first_missing = missing_prerequisites[0]
        if first_missing == "training_result":
            return ["先完成训练任务并提交训练答案", "再继续模拟面试或导出报告"]
        if first_missing == "interview_summary":
            return ["先完成三轮模拟面试", "再导出报告"]
        return [f"先生成{_artifact_label(first_missing)}", "再继续当前请求"]
    if "training_scored" in missing_capabilities:
        return ["先提交训练答案并完成评分", "再开始模拟面试"]
    if "interview_completed" in missing_capabilities:
        return ["先完成三轮模拟面试", "再导出报告"]
    if intent == SupervisorIntent.SUBMIT_TRAINING:
        return ["保存训练答案并生成训练结果"]
    return []


def _artifact_label(kind: str) -> str:
    return {
        "profile": "画像",
        "job_analysis": "岗位分析",
        "match": "匹配分析",
        "plan": "路径规划",
        "training_result": "训练结果",
        "interview_summary": "面试总结",
        "report": "报告",
    }.get(kind, kind)
