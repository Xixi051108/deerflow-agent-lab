"""Immutable thread-owned snapshots; the checkpoint alone selects the current one."""

import hashlib
import json
import os
import tempfile
from pathlib import Path

from pydantic import ValidationError

from deerflow.agents.research.data import MAX_READ_BYTES, MAX_SNAPSHOT_BYTES, SECTIONS, DataRuleError, ResearchResult, ResultRef, Section
from deerflow.agents.research.evidence import assess_claim_evidence
from deerflow.agents.research.scope import ResearchScope
from deerflow.config.paths import as_windows_extended_path, get_paths


def _path(reference: ResultRef, *, user_id: str, thread_id: str) -> Path:
    try:
        base = as_windows_extended_path(get_paths().thread_dir(thread_id, user_id=user_id)).resolve()
        directory = base / "research" / reference.research_id / f"scope-{reference.scope_version}"
        path = (directory / f"{reference.sha256}.json").resolve()
        if not path.is_relative_to(directory):
            raise ValueError("研究文件路径越界")
        return path
    except (ValueError, OSError) as exc:
        raise DataRuleError("invalid_path", "result", "研究文件路径不合法") from exc


def save_result(result: ResearchResult) -> ResultRef:
    result = ResearchResult.model_validate(result)
    raw = result.model_dump_json().encode("utf-8")
    if len(raw) > MAX_SNAPSHOT_BYTES:
        raise DataRuleError("snapshot_too_large", "result", "结果快照超过 2 MiB")
    reference = ResultRef(
        research_id=result.research_id,
        scope_version=result.scope_version,
        revision=result.revision,
        sha256=hashlib.sha256(raw).hexdigest(),
        counts={section: len(getattr(result, section)) for section in SECTIONS},
        preview=tuple(product.name[:80] for product in result.products[:3]),
    )
    path = _path(reference, user_id=result.user_id, thread_id=result.thread_id)
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            _read_bytes(path, reference.sha256)
            return reference
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    except OSError as exc:
        raise DataRuleError("snapshot_write_failed", "result", "结果快照保存失败，当前状态未更新") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return reference


def _read_bytes(path: Path, digest: str) -> bytes:
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_SNAPSHOT_BYTES + 1)
    except FileNotFoundError as exc:
        raise DataRuleError("snapshot_missing", "result", "研究快照不存在") from exc
    except OSError as exc:
        raise DataRuleError("snapshot_read_failed", "result", "研究快照无法读取") from exc
    if len(raw) > MAX_SNAPSHOT_BYTES or hashlib.sha256(raw).hexdigest() != digest:
        raise DataRuleError("snapshot_corrupt", "result", "研究快照大小或哈希不匹配")
    return raw


def load_result(reference: ResultRef, *, user_id: str, thread_id: str, agent_name: str) -> ResearchResult:
    reference = ResultRef.model_validate(reference)
    raw = _read_bytes(_path(reference, user_id=user_id, thread_id=thread_id), reference.sha256)
    try:
        result = ResearchResult.model_validate_json(raw)
    except ValidationError as exc:
        raise DataRuleError("snapshot_corrupt", "result", "研究快照不符合契约") from exc
    if (result.user_id, result.thread_id, result.agent_name, result.research_id, result.scope_version, result.revision) != (user_id, thread_id, agent_name, reference.research_id, reference.scope_version, reference.revision):
        raise DataRuleError("ownership_mismatch", "result", "快照不属于当前研究运行")
    if reference.counts != {section: len(getattr(result, section)) for section in SECTIONS}:
        raise DataRuleError("snapshot_corrupt", "result", "研究快照与索引计数不匹配")
    return result


def read_page(result: ResearchResult, section: Section, *, ids: list[str] | None = None, offset: int = 0, limit: int = 20, scope: ResearchScope | None = None) -> dict:
    if section not in SECTIONS or type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 100:
        raise DataRuleError("invalid_page", "page", "集合、偏移或数量不合法（limit 1–100）")
    rows = getattr(result, section)
    if ids is not None:
        wanted = set(ids)
        if not wanted.issubset({row.id for row in rows}):
            raise DataRuleError("record_missing", "ids", "请求的记录不存在")
        rows = tuple(row for row in rows if row.id in wanted)
    page = {
        "research_id": result.research_id,
        "scope_version": result.scope_version,
        "revision": result.revision,
        "section": section,
        "total": len(rows),
        "offset": offset,
        "records": [],
        "next_offset": None,
        "authority": "unverified_research_data",
    }
    for row in rows[offset : offset + limit]:
        record = row.model_dump(mode="json")
        if section == "claims" and scope is not None:
            record["evidence_assessment"] = assess_claim_evidence(scope, result, row.id)
        proposed = [*page["records"], record]
        next_offset = offset + len(proposed)
        candidate = {**page, "records": proposed, "next_offset": next_offset if next_offset < len(rows) else None}
        if len(json.dumps(candidate, ensure_ascii=False).encode("utf-8")) > MAX_READ_BYTES:
            if not page["records"]:
                raise DataRuleError("record_too_large", section, "单条记录超过 16 KiB 读取上限，未截断或省略正文")
            break
        page = candidate
    return page
