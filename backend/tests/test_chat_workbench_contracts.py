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
    assert payload["workspace_delta"]["updated_context"]["active_match_id"] == "match-1"


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
        status=MemoryStatus.PENDING_CONFIRMATION,
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
    assert "hidden_reasoning" not in str(snapshot.model_dump())
    assert len(skill_ref.summary_digest) <= 240
