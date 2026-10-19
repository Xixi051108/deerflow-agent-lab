"""Synthetic research observations; these are not real products or verified prices."""


def sample_batch(category="phone"):
    laptop = category == "laptop"
    text = "合成评测：16GB 配置在固定亮度下续航 8 小时，重量 1.4 kg。" if laptop else "合成官方资料：256GB 配置重量 190 g。"
    return {
        "products": [{"id": "product", "name": "合成笔记本" if laptop else "合成手机", "brand": "Synthetic", "model": "Demo"}],
        "configurations": [
            {"id": "base", "product_id": "product", "label": "16GB/512GB" if laptop else "8GB/256GB", "attributes": {"memory": "16GB" if laptop else "8GB", "storage": "512GB" if laptop else "256GB"}},
            {"id": "other", "product_id": "product", "label": "32GB/1TB" if laptop else "12GB/512GB", "attributes": {"memory": "32GB" if laptop else "12GB"}},
        ],
        "dimensions": [{"id": "weight", "name": "重量", "unit": "kg" if laptop else "g", "basis": "整机重量"}, {"id": "price", "name": "价格", "kind": "price", "unit": "CNY", "basis": "全新单台"}],
        "sources": [
            {
                "id": "source",
                "url": "https://example.com/synthetic",
                "title": "合成受控来源",
                "kind": "review" if laptop else "official",
                "status": "available",
                "collected_at": "2026-10-19T08:00:00+08:00",
                "published_at": None,
                "text": text,
                "product_id": "product",
                "configuration_ids": ["base"],
            }
        ],
        "claims": [
            {
                "id": "weight-fact",
                "kind": "fact",
                "product_id": "product",
                "configuration_id": "base",
                "dimension_id": "weight",
                "value": "1.4" if laptop else "190",
                "unit": "kg" if laptop else "g",
                "conditions": "固定评测配置" if laptop else "官方标称",
            },
            {"id": "unknown-price", "kind": "fact", "product_id": "product", "configuration_id": "base", "dimension_id": "price", "value": None, "unit": "CNY", "missing_reason": "合成样本未提供当前销售价格"},
        ],
        "citations": [{"id": "citation", "claim_id": "weight-fact", "source_id": "source", "quote": "重量 1.4 kg" if laptop else "重量 190 g", "locator": "合成资料第一段"}],
        "gaps": [{"id": "price-gap", "product_id": "product", "configuration_id": "base", "dimension_id": "price", "reason": "current_price_unverified", "description": "合成数据不证明当前价格"}],
    }
