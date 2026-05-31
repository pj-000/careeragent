from app.agents.supervisor import decide_user_message
from app.schemas.memory import CompactionSnapshot, MemoryItem, MemoryScope, MemoryStatus
from app.schemas.runs import (
    ActiveArtifactFacts,
    ArtifactChainItem,
    ConversationMessage,
    ConversationRole,
    RunResponse,
    RunStatus,
    SupervisorDecision,
    SupervisorIntent,
    WorkspaceContext,
    WorkspaceDelta,
    WorkspaceResponse,
)
from app.schemas.skills import SkillRuntimeRef


def test_workspace_context_defaults_and_message_metadata_are_strict_v31_contract() -> None:
    context = WorkspaceContext(thread_id="thread-1", updated_by_run_id="run-1")
    message = ConversationMessage(
        id="msg-1",
        thread_id="thread-1",
        role=ConversationRole.ASSISTANT,
        content="继续推进。",
    )

    context_payload = context.model_dump(mode="json")
    message_payload = message.model_dump(mode="json")

    assert context.active_goal == "职业发展规划"
    assert "active_compaction_snapshot_id" in context_payload
    assert "created_at" not in context_payload
    assert context_payload["updated_at"]
    assert WorkspaceContext.model_fields["updated_by_run_id"].is_required()
    assert message.warnings == []
    assert message_payload["created_at"]


def test_run_response_exposes_v31_chat_workbench_contract() -> None:
    context = WorkspaceContext(
        thread_id="thread-1",
        active_goal="转向 Agent 开发工程师",
        active_profile_id="profile-1",
        active_job_analysis_id="job-1",
        active_match_id="match-1",
        updated_by_run_id="run-1",
    )
    assistant_message = ConversationMessage(
        id="msg-assistant-1",
        thread_id="thread-1",
        role=ConversationRole.ASSISTANT,
        content="我已完成匹配诊断。",
        run_id="run-1",
        artifact_refs=["match-1"],
        last_business_agent="match",
        current_runtime_node="memory_manager",
    )
    response = RunResponse(
        run_id="run-1",
        thread_id="thread-1",
        run_status=RunStatus.COMPLETED,
        active_agent="memory_manager",
        last_business_agent="match",
        current_runtime_node="memory_manager",
        assistant_message=assistant_message,
        supervisor_decision=SupervisorDecision(
            intent=SupervisorIntent.MATCH,
            target_agent="match",
            required_input_artifact_kinds=["profile", "job_analysis"],
            required_capabilities=[],
            expected_output_artifact_kinds=["match"],
            missing_prerequisites=[],
            missing_capabilities=[],
            user_facing_reason="需要根据画像和岗位做匹配。",
            next_actions=["查看能力差距", "生成三个月计划"],
        ),
        workspace_delta=WorkspaceDelta(
            created_artifacts=[
                ArtifactChainItem(
                    id="match-1",
                    kind="match",
                    source_thread_id="thread-1",
                    source_agent="match",
                    parent_artifact_ids=["profile-1", "job-1"],
                )
            ],
            updated_context=context,
        ),
        artifact_chain=[
            ArtifactChainItem(id="profile-1", kind="profile", source_thread_id="thread-1", source_agent="profile"),
            ArtifactChainItem(id="job-1", kind="job_analysis", source_thread_id="thread-1", source_agent="job"),
            ArtifactChainItem(id="match-1", kind="match", source_thread_id="thread-1", source_agent="match"),
        ],
        used_skill_runtime_refs=[
            SkillRuntimeRef(
                skill_id="match/gap_diagnosis",
                version="1",
                section_ids=["rubric", "gaps"],
                detail_level="summary",
                summary_digest="识别岗位要求和学生画像之间的关键差距。",
            )
        ],
        memory_updates=[],
    )

    payload = response.model_dump(mode="json")
    assert payload["run_status"] == "completed"
    assert payload["last_business_agent"] == "match"
    assert payload["current_runtime_node"] == "memory_manager"
    assert payload["assistant_message"]["artifact_refs"] == ["match-1"]
    assert payload["assistant_message"]["warnings"] == []
    assert payload["workspace_delta"]["updated_context"]["active_match_id"] == "match-1"
    assert set(payload["workspace_delta"]) == {"created_artifacts", "updated_context"}
    assert WorkspaceDelta.model_fields["updated_context"].is_required()


def test_supervisor_decision_requires_route_target_and_user_reason() -> None:
    assert SupervisorDecision.model_fields["target_agent"].is_required()
    assert SupervisorDecision.model_fields["user_facing_reason"].is_required()


def test_supervisor_decision_maps_training_submission_to_training_agent() -> None:
    decision = decide_user_message(
        "我的训练答案：我会设计 FastAPI + LangGraph demo。",
        {"profile", "job_analysis", "match", "plan", "training_result"},
    )

    assert decision.intent == SupervisorIntent.SUBMIT_TRAINING
    assert decision.target_agent == "training"
    assert decision.required_input_artifact_kinds == ["match", "plan"]
    assert decision.expected_output_artifact_kinds == ["training_result"]
    assert decision.missing_prerequisites == []
    assert "训练" in decision.user_facing_reason


def test_supervisor_decision_reports_missing_prerequisites_for_report() -> None:
    decision = decide_user_message(
        "请导出报告",
        {"profile", "job_analysis", "match", "plan"},
    )

    assert decision.intent == SupervisorIntent.EXPORT_REPORT
    assert decision.target_agent == "report"
    assert decision.missing_prerequisites == ["training_result", "interview_summary"]
    assert decision.missing_capabilities == []
    assert "训练" in decision.next_actions[0]


def test_supervisor_blocks_interview_until_training_is_scored() -> None:
    decision = decide_user_message(
        "开始模拟面试",
        {"profile", "job_analysis", "match", "plan", "training_result"},
        active_facts=ActiveArtifactFacts(
            training_submitted=False,
            training_scored=False,
        ),
    )

    assert decision.intent == SupervisorIntent.START_INTERVIEW
    assert decision.missing_prerequisites == []
    assert decision.required_capabilities == ["training_scored"]
    assert decision.missing_capabilities == ["training_scored"]
    assert "训练答案" in decision.next_actions[0]


def test_supervisor_blocks_report_until_three_interview_turns_are_complete() -> None:
    decision = decide_user_message(
        "请导出报告",
        {"profile", "job_analysis", "match", "plan", "training_result", "interview_summary"},
        active_facts=ActiveArtifactFacts(
            training_submitted=True,
            training_scored=True,
            has_interview_summary=True,
            interview_turn_count=2,
            interview_completed=False,
        ),
    )

    assert decision.intent == SupervisorIntent.EXPORT_REPORT
    assert decision.missing_prerequisites == []
    assert decision.required_capabilities == ["training_scored", "interview_completed"]
    assert decision.missing_capabilities == ["interview_completed"]
    assert "三轮模拟面试" in decision.next_actions[0]


def test_supervisor_decision_prefers_profile_for_first_demo_prompt() -> None:
    decision = decide_user_message(
        "我会 Python FastAPI，想匹配 Agent 开发岗位",
        set(),
    )

    assert decision.intent == SupervisorIntent.BUILD_PROFILE
    assert decision.target_agent == "profile"
    assert decision.missing_prerequisites == []


def test_supervisor_decision_checks_answer_intent_before_continue_clarify() -> None:
    decision = decide_user_message(
        "继续回答1：我会用 StateGraph 组织节点。",
        {"profile", "job_analysis", "match", "plan", "training_result"},
        active_facts=ActiveArtifactFacts(training_scored=True),
    )

    assert decision.intent == SupervisorIntent.ANSWER_INTERVIEW
    assert decision.target_agent == "interview"


def test_supervisor_decision_detects_chinese_resume_prompt_as_profile() -> None:
    decision = decide_user_message("这是我的简历，请帮我整理", set())

    assert decision.intent == SupervisorIntent.BUILD_PROFILE
    assert decision.target_agent == "profile"
    assert decision.missing_prerequisites == []


def test_supervisor_does_not_infer_training_scored_from_artifact_presence() -> None:
    decision = decide_user_message(
        "开始模拟面试",
        {"profile", "job_analysis", "match", "plan", "training_result"},
    )

    assert decision.intent == SupervisorIntent.START_INTERVIEW
    assert decision.missing_prerequisites == []
    assert decision.missing_capabilities == ["training_scored"]


def test_supervisor_does_not_infer_interview_completed_from_summary_presence() -> None:
    decision = decide_user_message(
        "请导出报告",
        {"profile", "job_analysis", "match", "plan", "training_result", "interview_summary"},
    )

    assert decision.intent == SupervisorIntent.EXPORT_REPORT
    assert decision.missing_prerequisites == []
    assert decision.missing_capabilities == ["training_scored", "interview_completed"]


def test_run_response_accepts_raw_compaction_snapshot_payload() -> None:
    response = RunResponse(
        run_id="run-1",
        thread_id="thread-1",
        active_agent="memory_manager",
        compaction_snapshot={"id": "compact-1", "dropped_context_summary": "省略已完成的画像追问。"},
    )

    assert response.model_dump(mode="json")["compaction_snapshot"] == {
        "id": "compact-1",
        "dropped_context_summary": "省略已完成的画像追问。",
    }


def test_workspace_response_uses_active_context_not_latest_kind() -> None:
    response = WorkspaceResponse(
        thread_id="thread-1",
        active_context=WorkspaceContext(
            thread_id="thread-1",
            active_goal="第一条 Agent 岗位链路",
            active_job_analysis_id="job-first",
            active_match_id="match-first",
            updated_by_run_id="run-first",
        ),
        workspace_artifacts={
            "job_analysis": {"id": "job-first", "kind": "job_analysis"},
            "match": {"id": "match-first", "kind": "match"},
        },
        artifact_chain=[
            ArtifactChainItem(
                id="job-first",
                kind="job_analysis",
                source_thread_id="thread-1",
                source_agent="job",
            ),
            ArtifactChainItem(
                id="match-first",
                kind="match",
                source_thread_id="thread-1",
                source_agent="match",
            ),
        ],
    )

    assert set(response.model_dump(mode="json")) == {
        "thread_id",
        "active_context",
        "workspace_artifacts",
        "artifact_chain",
    }
    assert response.workspace_artifacts["match"]["id"] == "match-first"
    assert [item.id for item in response.artifact_chain] == ["job-first", "match-first"]


def test_active_artifact_facts_distinguish_artifact_presence_from_completion() -> None:
    facts = ActiveArtifactFacts(
        has_profile=True,
        has_job_analysis=True,
        has_match=True,
        has_plan=True,
        has_training_result=True,
        training_submitted=False,
        training_scored=False,
        has_interview_summary=True,
        interview_turn_count=2,
        interview_completed=False,
    )

    assert facts.has_training_result is True
    assert facts.training_scored is False
    assert facts.has_interview_summary is True
    assert facts.interview_completed is False


def test_memory_compaction_and_skill_runtime_refs_are_bounded_public_contracts() -> None:
    memory = MemoryItem(
        id="memory-1",
        thread_id="thread-1",
        scope=MemoryScope.GOAL,
        fact="目标是转向 Agent 开发工程师",
        confidence=0.91,
    )
    snapshot = CompactionSnapshot(
        id="compact-1",
        thread_id="thread-1",
        source_run_id="run-1",
        current_goal="转向 Agent 开发工程师",
        confirmed_facts=["会 Python 和 FastAPI"],
        decisions_made=["先补 LangGraph 项目证据"],
        active_artifact_refs=["profile-1", "match-1"],
        next_actions=["生成三个月计划"],
        dropped_context_summary="省略已完成的画像追问。",
    )
    skill_ref = SkillRuntimeRef(
        skill_id="match/gap_diagnosis",
        version="1",
        section_ids=["inputs", "rubric"],
        detail_level="summary",
        summary_digest="识别岗位要求和学生画像之间的关键差距。",
    )

    assert memory.status == MemoryStatus.PENDING_CONFIRMATION
    assert {scope.value for scope in MemoryScope} == {"profile", "preference", "goal", "skill", "evidence"}
    assert MemoryItem.model_fields["thread_id"].is_required()
    assert snapshot.dropped_context_summary == "省略已完成的画像追问。"
    assert set(snapshot.model_dump(mode="json")) == {
        "id",
        "thread_id",
        "source_run_id",
        "current_goal",
        "confirmed_facts",
        "decisions_made",
        "active_artifact_refs",
        "next_actions",
        "dropped_context_summary",
        "created_at",
    }
    assert len(skill_ref.summary_digest) <= 240
