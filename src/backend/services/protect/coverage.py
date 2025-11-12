from typing import Dict, Set
from collections import defaultdict

async def compute_csf_coverage(db) -> Dict[str, float]:
    """
    Coverage by CSF function: % of subcategories addressed by at least one non-declined control.
    For MVP we derive denominators from what exists in your `controls` catalog.
    """
    by_func_subcats: Dict[str, Set[str]] = defaultdict(set)
    addressed: Dict[str, Set[str]] = defaultdict(set)

    async for c in db.controls.find({}):
        f = c.get("csf_function")
        sub = c.get("subcategory") or ""
        if f and sub:
            by_func_subcats[f].add(sub)

    async for c in db.controls.find({"implementation_status": {"$ne": "Declined"}}):
        f = c.get("csf_function")
        sub = c.get("subcategory") or ""
        if f and sub:
            addressed[f].add(sub)

    coverage = {}
    for f, all_subs in by_func_subcats.items():
        denom = max(1, len(all_subs))
        num = len(addressed.get(f, set()))
        coverage[f"CSF.{f}"] = round(num / denom, 2)
    return coverage
