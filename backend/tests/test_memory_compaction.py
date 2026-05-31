from app.graphs.state import AgentSnapshot, CareerAgentState
from app.memory.compaction import compact_state
from app.memory.manager import MemoryManager
from app.schemas.memory import CompactionSnapshot, LongTermMemoryItem


def test_compaction_snapshot_schema_tracks_structured_context() -> None:
    snapshot = CompactionSnapshot(
        id="compact-thread-1",
        thread_id="thread-1",
        message_summary="Assistant summarized the current plan.",
        facts=["User targets backend roles."],
        decisions=["Use FastAPI for the MVP."],
        pending_items=["Confirm salary range."],
        agent_summaries={"profile": "Parsed resume."},
        skill_refs=["profile/resume_parsing"],
        artifact_ids=["profile-1"],
    )

    assert snapshot.id == "compact-thread-1"
    assert snapshot.thread_id == "thread-1"
    assert snapshot.message_summary == "Assistant summarized the current plan."
    assert snapshot.facts == ["User targets backend roles."]
    assert snapshot.decisions == ["Use FastAPI for the MVP."]
    assert snapshot.pending_items == ["Confirm salary range."]
    assert snapshot.agent_summaries == {"profile": "Parsed resume."}
    assert snapshot.skill_refs == ["profile/resume_parsing"]
    assert snapshot.artifact_ids == ["profile-1"]


def test_long_term_memory_item_schema_tracks_allowed_memory_fields() -> None:
    item = LongTermMemoryItem(
        id="memory-1",
        scope="profile",
        fact="User has 5 years of Python experience.",
        source_artifact_id="profile-1",
        confidence=0.92,
    )

    assert item.id == "memory-1"
    assert item.scope == "profile"
    assert item.fact == "User has 5 years of Python experience."
    assert item.source_artifact_id == "profile-1"
    assert item.confidence == 0.92


def test_compact_state_preserves_public_thread_skills_artifacts_and_agent_summaries() -> None:
    state = CareerAgentState(
        thread_id="thread-1",
        user_message="帮我规划后端求职",
        messages=[
            {"role": "user", "content": "帮我规划后端求职"},
            {"role": "assistant", "content": "先整理简历，再匹配岗位。"},
            {"role": "assistant", "content": "最终建议先投递 Python 后端岗位。", "hidden_reasoning": "private"},
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
        metadata={"hidden": "internal note", "chain-of-thought": "private"},
    )

    snapshot = compact_state(state)
    dumped = snapshot.model_dump()
    dumped_text = str(dumped).lower()

    assert snapshot.thread_id == "thread-1"
    assert snapshot.message_summary == "最终建议先投递 Python 后端岗位。"
    assert snapshot.pending_items == ["你偏好的城市是哪里？"]
    assert snapshot.agent_summaries == {
        "profile": "Extracted backend experience.",
        "match": "Compared profile with target JD.",
    }
    assert snapshot.skill_refs == ["profile/resume_parsing", "match/gap_diagnosis"]
    assert snapshot.artifact_ids == ["profile-1", "match-1"]
    assert "private" not in dumped_text
    assert "hidden" not in dumped
    assert "hidden" not in dumped_text
    assert "chain_of_thought" not in dumped_text
    assert "chain-of-thought" not in dumped_text


def test_compact_state_uses_user_message_when_no_assistant_message_exists() -> None:
    state = CareerAgentState(thread_id="thread-2", user_message="请分析我的简历")

    snapshot = compact_state(state)

    assert snapshot.thread_id == "thread-2"
    assert snapshot.message_summary == "请分析我的简历"
    assert snapshot.pending_items == []
    assert snapshot.agent_summaries == {}
    assert snapshot.skill_refs == []
    assert snapshot.artifact_ids == []


def test_memory_manager_evaluate_candidates_accepts_only_allowed_scopes_with_facts() -> None:
    manager = MemoryManager()
    accepted = manager.evaluate_candidates(
        [
            {"scope": "profile", "fact": "User knows FastAPI.", "source_artifact_id": "profile-1", "confidence": 0.8},
            {"scope": "history", "fact": "User interviewed at ByteDance."},
            {"scope": "preferences", "fact": "User prefers remote roles.", "confidence": 0.7},
            {"scope": "career_history", "fact": "Should not use legacy scope."},
            {"scope": "artifacts", "fact": "Artifacts are not long-term facts."},
            {"scope": "profile", "fact": ""},
            {"scope": "preferences"},
        ]
    )

    assert [item.scope for item in accepted] == ["profile", "history", "preferences"]
    assert [item.fact for item in accepted] == [
        "User knows FastAPI.",
        "User interviewed at ByteDance.",
        "User prefers remote roles.",
    ]
    assert accepted[0].source_artifact_id == "profile-1"
    assert accepted[0].confidence == 0.8
