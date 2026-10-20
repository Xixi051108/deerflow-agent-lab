"""Frozen synthetic public pages for offline and opt-in live-model evaluation.

Only search/fetch are controlled. The live-model test must not script decisions.
"""

from datetime import date

from langchain_core.tools import tool

CATALOG = {
    "phone": [
        ("aurora", "极光 A1", "设备类型：智能手机；状态：全新；配置：8GB/256GB；影像：支持光学防抖；续航：电池5000mAh；当前售价：未提供。"),
        ("endurance", "长航 B2", "设备类型：智能手机；状态：全新；配置：12GB/256GB；影像：无光学防抖；续航：电池6000mAh；当前售价：未提供。"),
        ("used", "旧机 C3", "设备类型：智能手机；状态：仅二手；配置：8GB/256GB；影像：支持光学防抖；续航：电池4500mAh；当前售价：未提供。"),
    ],
    "laptop": [
        ("portable", "行远 L1", "设备类型：笔记本；状态：全新；配置：16GB/512GB；整机重量：1.35kg；兼容性：提供Linux驱动；接口：两个USB-C；当前售价：未提供。"),
        ("desktop", "桌面 D2", "设备类型：台式整机；状态：全新；配置：32GB/1TB；兼容性：支持Linux；整机重量：5kg；当前售价：未提供。"),
        ("heavy", "性能 L3", "设备类型：笔记本；状态：全新；配置：32GB/1TB；整机重量：2.6kg；兼容性：提供Linux驱动；当前售价：未提供。"),
    ],
}


def discovery_scope(category="phone", *, named_only=False):
    from deerflow.agents.research.scope import ResearchScope

    laptop = category == "laptop"
    return ResearchScope.with_defaults(
        {
            "topic": "笔记本" if laptop else "手机",
            "objective": "Python开发、Docker与日常携带" if laptop else "日常摄影与续航优先",
            "allow_discovery": not named_only,
            "named_candidates": ["极光 A1", "旧机 C3"] if named_only else [],
            "target_candidate_count": 2,
            "purchase_budget": {"mode": "unlimited"},
            "price_basis": "全新单台公开售价，当前价格未提供则保留缺口",
            "hard_constraints": ["只研究全新笔记本", "整机重量不超过1.5kg"] if laptop else ["只研究全新智能手机"],
            "research_focus": ["内存与开发兼容性", "便携与接口"] if laptop else ["影像", "续航"],
            "must_check": ["整机重量", "配置"] if laptop else ["配置"],
            "runtime_limits": {"max_duration_seconds": 180, "max_tool_calls": 12},
        },
        as_of_date=date(2026, 10, 20),
    )


def controlled_web_tools(category="phone", calls=None):
    """Return only external-tool replacements; no model decisions are encoded."""
    import json

    calls = calls if calls is not None else []
    results = [{"title": name, "url": f"https://example.com/research-fixtures/{slug}", "content": text} for slug, name, text in CATALOG[category]]

    @tool("web_search")
    def search(query: str, max_results: int = 5) -> str:
        """Search frozen synthetic public pages; returned snippets are discovery leads, not verified facts."""
        calls.append(("web_search", {"query": query}))
        return json.dumps({"query": query, "collected_at": "2026-10-20T10:00:00+08:00", "results": results[:max_results]}, ensure_ascii=False)

    @tool("web_fetch")
    def fetch(url: str) -> str:
        """Read an exact URL previously returned by web_search; these synthetic pages do not prove live prices."""
        calls.append(("web_fetch", {"url": url}))
        page = next((row for row in results if row["url"] == url), None)
        return json.dumps({"error": "page_unavailable"} if page is None else {**page, "collected_at": "2026-10-20T10:00:00+08:00"}, ensure_ascii=False)

    return [search, fetch]


def planning_batch(category="phone"):
    """Known valid planning records; independent of scripted model replies."""
    laptop = category == "laptop"
    name = "行远 L1" if laptop else "极光 A1"
    slug = "portable" if laptop else "aurora"
    text = CATALOG[category][0][2]
    return {
        "products": [{"id": "p1", "name": name, "reason": "可比较的便携开发对象，价格待核实" if laptop else "影像及续航与用途相关，价格待核实", "discovery_source_ids": ["s1"]}],
        "configurations": [{"id": "c1", "product_id": "p1", "label": "16GB/512GB" if laptop else "8GB/256GB"}],
        "sources": [
            {"id": "s1", "url": f"https://example.com/research-fixtures/{slug}", "title": name, "kind": "other", "status": "available", "collected_at": "2026-10-20T10:00:00+08:00", "text": text, "product_id": "p1", "product_wide": True}
        ],
        "dimensions": [
            {
                "id": "primary",
                "name": "便携重量" if laptop else "影像能力",
                "kind": "measurement" if laptop else "qualitative",
                "unit": "kg" if laptop else None,
                "description": "对应日常携带的硬约束" if laptop else "对应日常摄影用途",
                "basis": "相同整机配置，不含电源" if laptop else "分别比较防抖、成像条件，不用单一像素值代替画质",
            },
            {"id": "price", "name": "当前价格", "kind": "price", "unit": "CNY", "description": "记录价格缺口，留待销售渠道核实", "basis": "同配置、同地区、全新单台公开售价，优惠条件另列"},
        ],
        "gaps": [
            {"id": "price-gap", "product_id": "p1", "dimension_id": "price", "reason": "current_price_unverified", "description": "固定样本未提供当前销售价格，不能认定满足价格条件"},
            {"id": "candidate-gap", "reason": "partial_fixture", "description": "本受控批次只保存一个候选，尚未达到数量目标，不代表市场没有其他产品"},
        ],
    }
