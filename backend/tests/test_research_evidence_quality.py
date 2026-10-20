"""Frozen quality checks cover observed model typos outside numeric value fields."""

import pytest
from test_research_evidence_live import assert_frozen_evidence_quality


@pytest.mark.parametrize("section,text", [("claims", "仅2GB/1TB版本，非目标配置"), ("gaps", "仅展示2919元条件价")])
def test_quality_audit_rejects_wrong_numbers_in_conditions_and_gaps(section, text):
    artifact = {"case": "laptop-mismatch" if section == "claims" else "conditional-unavailable", "scope": {}, "result": {"claims": [], "gaps": []}}
    artifact["result"][section] = [{"id": "typo", "value": "85", "conditions": text}] if section == "claims" else [{"id": "typo", "description": text}]
    with pytest.raises(AssertionError, match="Unsupported numeric detail"):
        assert_frozen_evidence_quality(artifact)
