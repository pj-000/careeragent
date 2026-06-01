from pathlib import Path

from app.agents.manifests import AGENT_MANIFESTS
from app.agents.runtime import append_skill_runtime_refs
from app.schemas.skills import LoadedSkill, SkillDocument
from app.skills.loader import SkillLoader
from app.skills.registry import AGENT_SKILLS, SkillRegistry


def test_registry_reads_markdown_frontmatter_and_body(tmp_path: Path) -> None:
    skill_path = tmp_path / "profile" / "resume_parsing.md"
    skill_path.parent.mkdir()
    skill_path.write_text(
        """---
id: profile/resume_parsing
version: 1
agent_scope: profile
tags:
  - resume
  - profile
summary: Extract structured career facts from a resume.
token_budget: 320
---
# Resume Parsing

## 输入
Resume text.

## 输出
Structured profile fields.
""",
        encoding="utf-8",
    )

    document = SkillRegistry(tmp_path).get("profile/resume_parsing")

    assert isinstance(document, SkillDocument)
    assert document.id == "profile/resume_parsing"
    assert document.version == 1
    assert document.agent_scope == "profile"
    assert document.tags == ["resume", "profile"]
    assert document.summary == "Extract structured career facts from a resume."
    assert document.token_budget == 320
    assert document.body.startswith("# Resume Parsing")
    assert "---" not in document.body


def test_builtin_registry_resolves_profile_resume_parsing() -> None:
    document = SkillRegistry.builtin().get("profile/resume_parsing")

    assert document.id == "profile/resume_parsing"
    assert document.version == 1
    assert document.summary
    assert "# " in document.body
    assert "## 输入" in document.body
    assert "## 输出" in document.body


def test_loader_resolves_match_skills_with_versioned_refs_and_summaries() -> None:
    loaded = SkillLoader.builtin().resolve_for_agent("match", "gap_analysis", budget=1200)

    assert [skill.ref for skill in loaded] == [
        "match/match_scoring_rubric@v1",
        "match/gap_diagnosis@v1",
    ]
    assert all(isinstance(skill, LoadedSkill) for skill in loaded)
    assert all(skill.summary for skill in loaded)
    assert all(skill.content for skill in loaded)


def test_loader_downgrades_content_to_summary_when_budget_is_too_small() -> None:
    loaded = SkillLoader.builtin().resolve_for_agent("match", "gap_analysis", budget=1)

    assert [skill.ref for skill in loaded] == [
        "match/match_scoring_rubric@v1",
        "match/gap_diagnosis@v1",
    ]
    assert all(skill.content == skill.summary for skill in loaded)


def test_loader_returns_bounded_runtime_refs_by_intent_and_budget() -> None:
    loaded = SkillLoader.builtin().resolve_for_agent("match", "gap_analysis", budget=1200)
    refs = [skill.runtime_ref for skill in loaded]

    assert refs[0].skill_id == "match/match_scoring_rubric"
    assert refs[0].detail_level in {"summary", "full"}
    assert len(refs[0].summary_digest) <= 240
    assert all("# " not in ref.summary_digest for ref in refs)


def test_loader_marks_skipped_when_budget_is_zero() -> None:
    loaded = SkillLoader.builtin().resolve_for_agent("match", "gap_analysis", budget=0)

    assert all(skill.runtime_ref.detail_level == "skipped" for skill in loaded)
    assert all(skill.content == "" for skill in loaded)


def test_runtime_ref_dedup_keeps_same_skill_with_different_sections() -> None:
    create_ref = SkillLoader.builtin().resolve_for_agent("training", "create_training", budget=1200)[0]
    submit_ref = SkillLoader.builtin().resolve_for_agent("training", "submit_training", budget=1200)[0]

    refs = append_skill_runtime_refs([], [create_ref.runtime_ref])
    refs = append_skill_runtime_refs(refs, [submit_ref.runtime_ref])

    assert create_ref.runtime_ref.skill_id == submit_ref.runtime_ref.skill_id
    assert create_ref.runtime_ref.section_ids != submit_ref.runtime_ref.section_ids
    assert len(refs) == 2


def test_agent_skills_align_with_manifest_skill_refs() -> None:
    manifest_refs = {
        agent_id: manifest.skill_policy.default_skill_ids
        for agent_id, manifest in AGENT_MANIFESTS.items()
    }

    assert AGENT_SKILLS == manifest_refs
