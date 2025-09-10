from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime, date
from app.agents.base_agent import agent_tool

# --- Static demo data ---------------------------------------------------------
# Keys are normalized vehicle numbers: uppercase, no spaces/hyphens.
_VEHICLE_POLICY_DB: Dict[str, Dict[str, Any]] = {
    "MH12AB1234": {
        "policy_number": "POL-MH-2025-001",
        "insurer": "Bharat General Insurance Co.",
        "insured": {"name": "Rohit Kulkarni"},
        "coverage": {"od": True, "tp": True, "addons": ["zero_depreciation", "engine_protect"]},
        "financials": {"idv": 940000, "deductibles": {"compulsory": 1000, "voluntary": 0}, "ncb_percent": 20},
        "period": {"effective_from": "2025-01-01", "effective_to": "2026-01-01"},
        "exclusions": [],
        "garage_preference": "network",
    },
    "DL8CAF4321": {
        "policy_number": "POL-DL-2024-777",
        "insurer": "Shakti Insurance Ltd.",
        "insured": {"name": "Neha Arora"},
        "coverage": {"od": True, "tp": True, "addons": ["zero_depreciation"]},
        "financials": {"idv": 1350000, "deductibles": {"compulsory": 1500, "voluntary": 2500}, "ncb_percent": 35},
        "period": {"effective_from": "2024-06-15", "effective_to": "2025-06-14"},  # expired in this demo
        "exclusions": [],
        "garage_preference": "network",
    },
    "RJ14CT9876": {
        "policy_number": "POL-RJ-2025-123",
        "insurer": "Suraksha General",
        "insured": {"name": "Amit Singh"},
        "coverage": {"od": True, "tp": True, "addons": []},
        "financials": {"idv": 820000, "deductibles": {"compulsory": 1000, "voluntary": 0}, "ncb_percent": 0},
        "period": {"effective_from": "2025-08-01", "effective_to": "2026-07-31"},
        "exclusions": ["consumables_without_addon"],
        "garage_preference": "non_network",
    },
}

def _normalize_vehicle_number(v: str) -> str:
    return "".join(ch for ch in v.upper() if ch.isalnum())

def _parse_iso_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def _is_active(period: Dict[str, str], on_date: date) -> bool:
    start = _parse_iso_date(period["effective_from"])
    end = _parse_iso_date(period["effective_to"])
    return start <= on_date <= end

# --- Tool ---------------------------------------------------------------------
@agent_tool
def get_policy_details(vehicle_number: str, date_of_loss: Optional[str] = None) -> Dict[str, Any]:
    """
    Lookup policy by vehicle number and return coverage/financial details.
    - vehicle_number: e.g., "MH12 AB 1234" (spacing/case doesn't matter)
    - date_of_loss: optional ISO date "YYYY-MM-DD". If omitted, uses today.
    Returns:
      {
        "ok": True/False,
        "vehicle_number": "<normalized>",
        "date_of_loss": "YYYY-MM-DD",
        "policy_active": True/False,
        "policy": { ...full static record... }
      }
    """
    try:
        normalized = _normalize_vehicle_number(vehicle_number or "")
        if not normalized:
            return {"ok": False, "error": "Vehicle number is required"}

        record = _VEHICLE_POLICY_DB.get(normalized)
        if not record:
            return {
                "ok": False,
                "error": "Vehicle not found",
                "hint": "Try one of: " + ", ".join(_VEHICLE_POLICY_DB.keys()),
                "vehicle_number": normalized,
            }

        dol = datetime.utcnow().date() if not date_of_loss else _parse_iso_date(date_of_loss)
        active = _is_active(record["period"], dol)

        return {
            "ok": True,
            "source": "static_map_v1",
            "vehicle_number": normalized,
            "date_of_loss": dol.isoformat(),
            "policy_active": active,
            "policy": record,
        }
    except Exception as e:
        return {"ok": False, "error": f"Unexpected error: {e}"}
