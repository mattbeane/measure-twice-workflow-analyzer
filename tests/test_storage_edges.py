"""storage.py — fills for `get_prompt_results` filtering."""
from workflow_analyzer.storage import AnalysisStorage


def test_get_prompt_results_filters_by_prompt_id(tmp_db, make_result):
    """Multiple prompts in the same session — `get_prompt_results` returns
    only the ones matching the requested id."""
    storage = AnalysisStorage(str(tmp_db))
    cycle_runs = [
        make_result(prompt_id="cycle_time", run_number=i + 1,
                    extracted_metrics={"x": 1.0})
        for i in range(3)
    ]
    bottleneck_runs = [
        make_result(prompt_id="bottleneck",
                    prompt_title="2. Bottleneck Identification",
                    run_number=i + 1,
                    extracted_metrics={"y": 2.0})
        for i in range(2)
    ]
    sid = storage.create_session(
        workflow_data="x", runs_per_prompt=3,
        results=cycle_runs + bottleneck_runs,
        workflow_name="multi",
    )
    only_cycle = storage.get_prompt_results(sid, "cycle_time")
    assert len(only_cycle) == 3
    assert all(r.prompt_id == "cycle_time" for r in only_cycle)

    only_bottle = storage.get_prompt_results(sid, "bottleneck")
    assert len(only_bottle) == 2
    assert all(r.prompt_id == "bottleneck" for r in only_bottle)


def test_get_prompt_results_for_unknown_prompt_returns_empty(tmp_db, successful_results):
    storage = AnalysisStorage(str(tmp_db))
    sid = storage.create_session(
        workflow_data="x", runs_per_prompt=5,
        results=successful_results, workflow_name="t",
    )
    assert storage.get_prompt_results(sid, "does_not_exist") == []
