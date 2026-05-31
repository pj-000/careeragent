from app.repositories.json_thread_repository import (
    JsonConversationRepository,
    JsonMemoryRepository,
    JsonWorkspaceContextRepository,
)
from app.schemas.memory import MemoryItem, MemoryScope, MemoryStatus
from app.schemas.runs import ConversationMessage, ConversationRole, WorkspaceContext


def test_conversation_repository_persists_messages_by_thread(tmp_path):
    repo = JsonConversationRepository(tmp_path)
    user_message = ConversationMessage(
        id="msg-user-1",
        thread_id="thread-a",
        role=ConversationRole.USER,
        content="我想转 Agent 开发",
        run_id="run-1",
    )
    assistant_message = ConversationMessage(
        id="msg-assistant-1",
        thread_id="thread-a",
        role=ConversationRole.ASSISTANT,
        content="我会先建立画像。",
        run_id="run-1",
        artifact_refs=["profile-1"],
    )
    other_thread = ConversationMessage(
        id="msg-other-1",
        thread_id="thread-b",
        role=ConversationRole.USER,
        content="另一个线程",
    )

    repo.save(user_message)
    repo.save(assistant_message)
    repo.save(other_thread)

    restored = repo.list_by_thread("thread-a")
    assert [message.id for message in restored] == ["msg-user-1", "msg-assistant-1"]
    assert restored[1].artifact_refs == ["profile-1"]


def test_workspace_context_repository_keeps_active_chain_by_thread(tmp_path):
    repo = JsonWorkspaceContextRepository(tmp_path)
    first = WorkspaceContext(
        thread_id="thread-a",
        active_goal="Agent 开发",
        active_job_analysis_id="job-first",
        active_match_id="match-first",
        updated_by_run_id="run-1",
    )
    second = WorkspaceContext(
        thread_id="thread-b",
        active_goal="产品经理",
        active_job_analysis_id="job-second",
        updated_by_run_id="run-2",
    )

    repo.save(first)
    repo.save(second)

    assert repo.get("thread-a").active_match_id == "match-first"
    assert repo.get("thread-b").active_job_analysis_id == "job-second"


def test_workspace_context_repository_handles_unsafe_thread_ids(tmp_path):
    repo = JsonWorkspaceContextRepository(tmp_path)
    context = WorkspaceContext(
        thread_id="student/a b?career",
        active_goal="Agent 开发",
        updated_by_run_id="run-unsafe-thread",
    )

    repo.save(context)

    assert repo.get("student/a b?career").active_goal == "Agent 开发"
    assert not (tmp_path / "workspace-contexts" / "student/a b?career.json").exists()


def test_memory_repository_filters_and_updates_status(tmp_path):
    repo = JsonMemoryRepository(tmp_path)
    item = MemoryItem(
        id="memory-1",
        thread_id="thread-a",
        scope=MemoryScope.GOAL,
        fact="目标是 Agent 开发岗位",
        confidence=0.8,
        status=MemoryStatus.PENDING_CONFIRMATION,
    )
    repo.save(item)

    assert repo.list_by_thread("thread-a")[0].status == MemoryStatus.PENDING_CONFIRMATION
    assert repo.list_by_scope("thread-a", MemoryScope.GOAL)[0].fact == "目标是 Agent 开发岗位"
    repo.set_status("thread-a", "memory-1", MemoryStatus.CONFIRMED)
    assert repo.get("thread-a", "memory-1").status == MemoryStatus.CONFIRMED


def test_memory_repository_rejects_cross_thread_reads(tmp_path):
    repo = JsonMemoryRepository(tmp_path)
    repo.save(
        MemoryItem(
            id="memory-cross-thread",
            thread_id="thread-a",
            scope=MemoryScope.GOAL,
            fact="目标是 Agent 开发岗位",
        )
    )

    try:
        repo.get("thread-b", "memory-cross-thread")
    except KeyError as exc:
        assert "thread-b" in str(exc)
    else:
        raise AssertionError("Expected cross-thread memory read to raise KeyError")
