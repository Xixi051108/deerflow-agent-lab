"""Snapshot persistence and paging through the research storage API."""

import json
import os

import pytest
from support.research_samples import sample_batch


@pytest.fixture
def study(tmp_path, monkeypatch):
    from deerflow.agents.research.data import ResearchBatch, ResearchResult, apply_batch

    monkeypatch.setenv("DEER_FLOW_HOME", str(tmp_path))
    monkeypatch.setattr("deerflow.config.paths._paths", None)
    return apply_batch(ResearchResult(research_id="study", scope_version=1, user_id="user", thread_id="thread", agent_name="agent"), ResearchBatch.model_validate(sample_batch()))


def test_snapshot_round_trip_and_paging(study):
    from deerflow.agents.research.storage import load_result, read_page, save_result

    reference = save_result(study)
    assert len(reference.model_dump_json().encode("utf-8")) <= 16384
    assert reference.counts["claims"] == 2
    restored = load_result(reference, user_id="user", thread_id="thread", agent_name="agent")
    assert restored == study
    first = read_page(restored, "claims", limit=1)
    assert first["records"][0]["value"] == "190"
    assert first["next_offset"] == 1
    second = read_page(restored, "claims", offset=first["next_offset"], limit=1)
    assert second["records"][0]["value"] is None
    assert second["next_offset"] is None
    assert read_page(restored, "configurations", ids=["other"])["records"][0]["id"] == "other"
    assert json.loads(json.dumps(second))["revision"] == 1


def test_missing_corrupt_and_foreign_snapshots_are_explicit(study):
    from deerflow.agents.research.data import DataRuleError
    from deerflow.agents.research.storage import load_result, save_result
    from deerflow.config.paths import get_paths

    reference = save_result(study)
    with pytest.raises(DataRuleError, match="不属于"):
        load_result(reference, user_id="user", thread_id="thread", agent_name="other")
    with pytest.raises(DataRuleError, match="不存在"):
        load_result(reference, user_id="other", thread_id="thread", agent_name="agent")
    path = next(get_paths().thread_dir("thread", user_id="user").rglob("*.json"))
    path.write_bytes(b"{}")
    with pytest.raises(DataRuleError, match="哈希"):
        load_result(reference, user_id="user", thread_id="thread", agent_name="agent")
    path.unlink()
    with pytest.raises(DataRuleError, match="不存在"):
        load_result(reference, user_id="user", thread_id="thread", agent_name="agent")


def test_failed_replace_keeps_previous_snapshot_and_removes_temporary(study, monkeypatch):
    from deerflow.agents.research.data import DataRuleError, ResearchBatch, apply_batch
    from deerflow.agents.research.storage import load_result, save_result
    from deerflow.config.paths import get_paths

    reference = save_result(study)
    newer = apply_batch(study, ResearchBatch(products=[{"id": "second", "name": "合成第二款"}]))

    def fail_replace(*args):
        raise OSError("synthetic disk failure")

    monkeypatch.setattr("deerflow.agents.research.storage.os.replace", fail_replace)
    with pytest.raises(DataRuleError, match="保存失败"):
        save_result(newer)
    assert load_result(reference, user_id="user", thread_id="thread", agent_name="agent") == study
    assert len(list(get_paths().thread_dir("thread", user_id="user").rglob("*.*"))) == 1


def test_unreferenced_snapshot_does_not_replace_checkpoint_selection(study):
    from deerflow.agents.research.data import ResearchBatch, apply_batch
    from deerflow.agents.research.storage import load_result, save_result

    selected = save_result(study)
    newer = apply_batch(study, ResearchBatch(products=[{"id": "second", "name": "合成第二款"}]))
    unreferenced = save_result(newer)
    assert unreferenced.revision == 2
    assert load_result(selected, user_id="user", thread_id="thread", agent_name="agent").revision == 1


def test_snapshot_projection_read_and_identifier_limits(study):
    from pydantic import ValidationError

    from deerflow.agents.research.data import DataRuleError, ResearchBatch, ResultRef, apply_batch
    from deerflow.agents.research.storage import read_page, save_result

    reference = save_result(study)
    with pytest.raises(ValidationError):
        ResultRef.model_validate({**reference.model_dump(), "research_id": "../other"})
    with pytest.raises(ValidationError, match="16 KiB"):
        ResultRef.model_validate({**reference.model_dump(), "preview": ["字" * 6000]})
    too_large = apply_batch(study, ResearchBatch(sources=[{**study.sources[0].model_dump(), "text": study.sources[0].text + "字" * 800000}]))
    with pytest.raises(DataRuleError) as caught:
        save_result(too_large)
    assert caught.value.code == "snapshot_too_large"
    with pytest.raises(DataRuleError):
        read_page(study, "claims", offset=-1)
    with pytest.raises(DataRuleError):
        read_page(study, "claims", ids=["missing"])
    with pytest.raises(DataRuleError) as caught:
        read_page(too_large, "sources")
    assert caught.value.code == "record_too_large"


def test_model_cannot_supply_a_thread_path(study):
    from deerflow.agents.research.data import DataRuleError, ResearchResult
    from deerflow.agents.research.storage import save_result

    invalid = ResearchResult.model_validate({**study.model_dump(), "thread_id": "../thread"})
    with pytest.raises(DataRuleError) as caught:
        save_result(invalid)
    assert caught.value.code == "invalid_path"


def test_pages_stop_before_byte_limit_without_losing_records(study):
    from deerflow.agents.research.data import ResearchBatch, apply_batch
    from deerflow.agents.research.storage import read_page

    result = apply_batch(study, ResearchBatch(products=[{"id": f"long-{i}", "name": "字" * 1800} for i in range(5)]))
    offset, found = 0, []
    while True:
        page = read_page(result, "products", offset=offset)
        assert len(json.dumps(page, ensure_ascii=False).encode("utf-8")) <= 16384
        found.extend(row["id"] for row in page["records"])
        if page["next_offset"] is None:
            break
        offset = page["next_offset"]
    assert found == ["product", "long-0", "long-1", "long-2", "long-3", "long-4"]


def test_research_directory_cannot_redirect_into_the_sandbox(study):
    from deerflow.agents.research.data import DataRuleError
    from deerflow.agents.research.storage import save_result
    from deerflow.config.paths import get_paths

    base = get_paths().thread_dir("thread", user_id="user")
    target = base / "user-data" / "workspace"
    target.mkdir(parents=True)
    link = base / "research"
    if os.name == "nt":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    else:
        link.symlink_to(target, target_is_directory=True)
    with pytest.raises(DataRuleError) as caught:
        save_result(study)
    assert caught.value.code == "invalid_path"
    assert not list(target.rglob("*.json"))
