"""Prompt catalog invariants.

The workshop facilitator promises "14 prompts (8 process + 6 skill)." If that
shape changes, the cost banner and the README both go stale at once.
"""
from workflow_analyzer import prompts
from workflow_analyzer.prompts import ALL_PROMPTS, PROCESS_PROMPTS, SKILL_PROMPTS


def test_catalog_has_8_process_and_6_skill():
    # If this becomes 16/8 or 7/5, that's a real product change and the README
    # has to move at the same time.
    assert len(PROCESS_PROMPTS) == 8
    assert len(SKILL_PROMPTS) == 6
    assert len(ALL_PROMPTS) == 14


def test_all_prompt_ids_are_unique():
    ids = [p.id for p in ALL_PROMPTS]
    assert len(ids) == len(set(ids)), f"duplicate prompt id(s): {ids}"


def test_every_prompt_has_required_fields():
    for p in ALL_PROMPTS:
        assert p.id
        assert p.title
        assert hasattr(p, "prompt_template")
        assert p.prompt_template


def test_every_prompt_template_has_workflow_data_placeholder():
    # Without `{workflow_data}` the runner can't substitute the participant's
    # actual content, and the analysis would run against the prompt template.
    for p in ALL_PROMPTS:
        assert "{workflow_data}" in p.prompt_template, (
            f"prompt {p.id!r} is missing the {{workflow_data}} placeholder"
        )


def test_process_and_skill_groups_are_disjoint():
    process_ids = {p.id for p in PROCESS_PROMPTS}
    skill_ids = {p.id for p in SKILL_PROMPTS}
    assert process_ids.isdisjoint(skill_ids)


def test_named_process_prompts_present():
    # These IDs are referenced by name elsewhere (stats.py, schemas.py).
    # Renaming any of them is a coordinated change.
    expected = {"cycle_time", "bottleneck", "handoff", "decision",
                "value_waste", "information_flow", "exception", "approval"}
    actual = {p.id for p in PROCESS_PROMPTS}
    assert expected == actual
