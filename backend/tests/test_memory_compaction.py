from app.graphs.state import AgentSnapshot, CareerAgentState
from app.memory.compaction import compact_state
from app.memory.manager import MemoryManager
from app.schemas.memory import CompactionSnapshot, LongTermMemoryItem


def test_compaction_snapshot_schema_tracks_structured_context() -> None:
    snapshot = CompactionSnapshot(
        id="compact-thread-1",
        thread_id="thread-1",
        source_run_id="run-1",
        current_goal="Land a backend role.",
        confirmed_facts=["User targets backend roles."],
        decisions_made=["Use FastAPI for the MVP."],
        active_artifact_refs=["profile-1"],
        next_actions=["Confirm salary range."],
        dropped_context_summary="Assistant summarized the current plan.",
    )

    assert snapshot.id == "compact-thread-1"
    assert snapshot.thread_id == "thread-1"
    assert snapshot.source_run_id == "run-1"
    assert snapshot.current_goal == "Land a backend role."
    assert snapshot.confirmed_facts == ["User targets backend roles."]
    assert snapshot.decisions_made == ["Use FastAPI for the MVP."]
    assert snapshot.active_artifact_refs == ["profile-1"]
    assert snapshot.next_actions == ["Confirm salary range."]
    assert snapshot.dropped_context_summary == "Assistant summarized the current plan."


def test_long_term_memory_item_schema_tracks_allowed_memory_fields() -> None:
    item = LongTermMemoryItem(
        id="memory-1",
        thread_id="thread-1",
        scope="profile",
        fact="User has 5 years of Python experience.",
        source_artifact_id="profile-1",
        confidence=0.92,
    )

    assert item.id == "memory-1"
    assert item.thread_id == "thread-1"
    assert item.scope == "profile"
    assert item.fact == "User has 5 years of Python experience."
    assert item.source_artifact_id == "profile-1"
    assert item.confidence == 0.92


def test_compact_state_returns_v31_public_snapshot_without_hidden_reasoning() -> None:
    state = CareerAgentState(
        thread_id="thread-1",
        user_message="帮我规划后端求职",
        messages=[
            {"role": "user", "content": "帮我规划后端求职"},
            {"role": "assistant", "content": "先整理简历，再匹配岗位。"},
            {
                "role": "assistant",
                "content": "最终建议先投递 Python 后端岗位。",
                "hidden_reasoning": "private",
                "reasoning_content": "private",
            },
        ],
        pending_question="你偏好的城市是哪里？",
        loaded_skill_refs=["profile/resume_parsing", "match/gap_diagnosis"],
        artifact_ids=["profile-1", "match-1"],
        agent_snapshots={
            "profile": AgentSnapshot(
                agent_id="profile",
                summary="Extracted backend experience.",
                private_context={"chain_of_thought": "do not persist"},
                last_artifact_ids=["profile-1"],
            ),
            "match": AgentSnapshot(
                agent_id="match",
                summary="Compared profile with target JD.",
                private_context={"hidden": "internal"},
                last_artifact_ids=["match-1"],
            ),
        },
        metadata={
            "run_id": "run-1",
            "active_goal": "后端求职规划",
            "confirmed_facts": ["目标岗位是 Python 后端", 3],
            "decisions_made": ["优先投递中小型 SaaS 团队"],
            "next_actions": ["完善项目经历", "确认期望城市"],
            "hidden": "internal note",
            "chain-of-thought": "private",
            "reasoning_content": "private",
        },
    )

    snapshot = compact_state(state)
    dumped = snapshot.model_dump()
    dumped_text = str(dumped).lower()

    assert snapshot.id == "compact-thread-1"
    assert snapshot.thread_id == "thread-1"
    assert snapshot.source_run_id == "run-1"
    assert snapshot.current_goal == "后端求职规划"
    assert snapshot.confirmed_facts == ["目标岗位是 Python 后端", "3"]
    assert snapshot.decisions_made == ["优先投递中小型 SaaS 团队"]
    assert snapshot.active_artifact_refs == ["profile-1", "match-1"]
    assert snapshot.next_actions == ["完善项目经历", "确认期望城市"]
    assert snapshot.dropped_context_summary == "最终建议先投递 Python 后端岗位。"
    assert "private" not in dumped_text
    assert "hidden" not in dumped
    assert "hidden" not in dumped_text
    assert "hidden_reasoning" not in dumped_text
    assert "reasoning_content" not in dumped_text
    assert "chain_of_thought" not in dumped_text
    assert "chain-of-thought" not in dumped_text


def test_compact_state_uses_v31_schema_and_excludes_provider_reasoning() -> None:
    state = CareerAgentState(
        thread_id="thread-v31-compact",
        user_message="继续规划",
        artifact_ids=["profile-1", "match-1"],
        messages=[
            {"role": "user", "content": "继续规划"},
            {"role": "assistant", "content": "下一步补齐项目证据。", "reasoning_content": "private"},
        ],
        metadata={
            "run_id": "run-v31",
            "active_goal": "转向 Agent 开发工程师",
            "confirmed_facts": ["会 Python"],
            "decisions_made": ["先补 LangGraph 项目"],
            "next_actions": ["生成计划"],
            "hidden_reasoning": "private",
        },
    )

    snapshot = compact_state(state)
    dumped = snapshot.model_dump()
    dumped_text = str(dumped).lower()

    assert snapshot.source_run_id == "run-v31"
    assert snapshot.current_goal == "转向 Agent 开发工程师"
    assert snapshot.active_artifact_refs == ["profile-1", "match-1"]
    assert "hidden_reasoning" not in dumped_text
    assert "chain_of_thought" not in dumped_text
    assert "reasoning_content" not in dumped_text


def test_compact_state_uses_user_message_when_no_assistant_message_exists() -> None:
    state = CareerAgentState(
        thread_id="thread-2",
        user_message="请分析我的简历",
        metadata={"run_id": "run-2"},
    )

    snapshot = compact_state(state)

    assert snapshot.thread_id == "thread-2"
    assert snapshot.source_run_id == "run-2"
    assert snapshot.current_goal == "职业发展规划"
    assert snapshot.dropped_context_summary == "请分析我的简历"
    assert snapshot.confirmed_facts == []
    assert snapshot.decisions_made == []
    assert snapshot.active_artifact_refs == []
    assert snapshot.next_actions == []


def test_memory_manager_evaluate_candidates_accepts_only_allowed_scopes_with_facts() -> None:
    manager = MemoryManager()
    accepted = manager.evaluate_candidates(
        [
            {
                "scope": "profile",
                "fact": "User knows FastAPI.",
                "thread_id": "thread-1",
                "source_artifact_id": "profile-1",
                "confidence": 0.8,
            },
            {"scope": "goal", "fact": "User wants backend roles.", "thread_id": "thread-1"},
            {"scope": "preference", "fact": "User prefers remote roles.", "thread_id": "thread-1", "confidence": 0.7},
            {"scope": "skill", "fact": "User knows FastAPI.", "thread_id": "thread-1"},
            {"scope": "evidence", "fact": "Profile artifact mentions Python experience.", "thread_id": "thread-1"},
            {"scope": "profile", "fact": "Missing thread id should not leak a placeholder."},
            {"scope": "history", "fact": "Should not use legacy scope."},
            {"scope": "preferences", "fact": "Should not use legacy plural scope."},
            {"scope": "career_history", "fact": "Should not use legacy scope."},
            {"scope": "artifacts", "fact": "Artifacts are not long-term facts."},
            {"scope": "profile", "fact": ""},
            {"scope": "preference"},
        ]
    )

    assert [item.scope for item in accepted] == ["profile", "goal", "preference", "skill", "evidence"]
    assert [item.fact for item in accepted] == [
        "User knows FastAPI.",
        "User wants backend roles.",
        "User prefers remote roles.",
        "User knows FastAPI.",
        "Profile artifact mentions Python experience.",
    ]
    assert [item.thread_id for item in accepted] == [
        "thread-1",
        "thread-1",
        "thread-1",
        "thread-1",
        "thread-1",
    ]
    assert accepted[0].source_artifact_id == "profile-1"
    assert accepted[0].confidence == 0.8
