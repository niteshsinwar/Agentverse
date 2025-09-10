# file: app/tools/rate_card_tool.py
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.agents.base_agent import agent_tool

# ------------------------- Static Rate Cards (Demo) --------------------------
# Currency: INR; GST kept at 18% for demo. Adjust for your org.
# All keys are lowercase "slugs" (e.g., "front_bumper", "headlamp_left").

_RATE_CARDS: Dict[str, Dict[str, Any]] = {
    "scorpio_2017_2021": {
        "model_name": "Mahindra Scorpio S5/S7 (2017–2021)",
        "currency": "INR",
        "gst_percent": 18,
        "labour_rates": {
            "hourly_general": 1500,
            "paint_per_panel": 2800,
            "fitment_flat": 900,
        },
        "materials_pct_for_repair": 0.12,  # % of labour for consumables in repair
        "standard_hours": {
            "front_bumper": {"replace": 1.5, "repair_minor": 1.0, "repair_major": 2.5, "paint": 1.0},
            "rear_bumper":  {"replace": 1.6, "repair_minor": 1.0, "repair_major": 2.2, "paint": 1.0},
            "left_fender":  {"replace": 2.0, "repair_minor": 1.5, "paint": 1.0},
            "right_fender": {"replace": 2.0, "repair_minor": 1.5, "paint": 1.0},
            "hood":         {"replace": 2.5, "repair_minor": 2.0, "paint": 1.5},
            "headlamp_left":  {"replace": 0.6},
            "headlamp_right": {"replace": 0.6},
            "tail_lamp_left": {"replace": 0.5},
            "tail_lamp_right":{"replace": 0.5},
            "windshield":     {"replace": 1.8},
        },
        "parts_catalog": {
            "front_bumper":   {"mrp": 17800, "oem": True},
            "rear_bumper":    {"mrp": 16500, "oem": True},
            "left_fender":    {"mrp": 6200,  "oem": True},
            "right_fender":   {"mrp": 6200,  "oem": True},
            "hood":           {"mrp": 28500, "oem": True},
            "headlamp_left":  {"mrp": 9300,  "oem": True},
            "headlamp_right": {"mrp": 9300,  "oem": True},
            "tail_lamp_left": {"mrp": 4400,  "oem": True},
            "tail_lamp_right":{"mrp": 4400,  "oem": True},
            "windshield":     {"mrp": 14500, "oem": True},
        },
    },

    "swift_2018_2023": {
        "model_name": "Maruti Swift (2018–2023)",
        "currency": "INR",
        "gst_percent": 18,
        "labour_rates": {
            "hourly_general": 1300,
            "paint_per_panel": 2400,
            "fitment_flat": 800,
        },
        "materials_pct_for_repair": 0.10,
        "standard_hours": {
            "front_bumper": {"replace": 1.2, "repair_minor": 0.8, "repair_major": 2.0, "paint": 1.0},
            "rear_bumper":  {"replace": 1.2, "repair_minor": 0.8, "repair_major": 1.8, "paint": 1.0},
            "left_fender":  {"replace": 1.6, "repair_minor": 1.2, "paint": 0.8},
            "right_fender": {"replace": 1.6, "repair_minor": 1.2, "paint": 0.8},
            "hood":         {"replace": 2.0, "repair_minor": 1.6, "paint": 1.2},
            "headlamp_left":  {"replace": 0.5},
            "headlamp_right": {"replace": 0.5},
            "windshield":     {"replace": 1.4},
        },
        "parts_catalog": {
            "front_bumper":   {"mrp": 9600,  "oem": True},
            "rear_bumper":    {"mrp": 9100,  "oem": True},
            "left_fender":    {"mrp": 4100,  "oem": True},
            "right_fender":   {"mrp": 4100,  "oem": True},
            "hood":           {"mrp": 18800, "oem": True},
            "headlamp_left":  {"mrp": 6500,  "oem": True},
            "headlamp_right": {"mrp": 6500,  "oem": True},
            "windshield":     {"mrp": 9600,  "oem": True},
        },
    },

    "nexon_2020_2024": {
        "model_name": "Tata Nexon (2020–2024)",
        "currency": "INR",
        "gst_percent": 18,
        "labour_rates": {
            "hourly_general": 1400,
            "paint_per_panel": 2600,
            "fitment_flat": 850,
        },
        "materials_pct_for_repair": 0.11,
        "standard_hours": {
            "front_bumper": {"replace": 1.3, "repair_minor": 0.9, "repair_major": 2.1, "paint": 1.0},
            "rear_bumper":  {"replace": 1.3, "repair_minor": 0.9, "repair_major": 1.9, "paint": 1.0},
            "left_fender":  {"replace": 1.7, "repair_minor": 1.3, "paint": 0.9},
            "right_fender": {"replace": 1.7, "repair_minor": 1.3, "paint": 0.9},
            "hood":         {"replace": 2.2, "repair_minor": 1.7, "paint": 1.3},
            "headlamp_left":  {"replace": 0.6},
            "headlamp_right": {"replace": 0.6},
            "windshield":     {"replace": 1.5},
        },
        "parts_catalog": {
            "front_bumper":   {"mrp": 11200, "oem": True},
            "rear_bumper":    {"mrp": 10700, "oem": True},
            "left_fender":    {"mrp": 5200,  "oem": True},
            "right_fender":   {"mrp": 5200,  "oem": True},
            "hood":           {"mrp": 21400, "oem": True},
            "headlamp_left":  {"mrp": 7200,  "oem": True},
            "headlamp_right": {"mrp": 7200,  "oem": True},
            "windshield":     {"mrp": 11800, "oem": True},
        },
    },
}

# ------------------------------ Helpers --------------------------------------
def _slug(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum() or ch == "_").replace("__", "_").strip("_")

def _resolve_model_key(vehicle_model: str) -> Optional[str]:
    k = _slug(vehicle_model)
    # direct match or fuzzy contains
    if k in _RATE_CARDS:
        return k
    for key, data in _RATE_CARDS.items():
        if k.startswith(key) or any(x in key for x in key.split("_")):
            return key
        if _slug(data["model_name"]) in k:
            return key
    # light fuzzy: check base tokens (e.g., "scorpio", "swift", "nexon")
    base = [("scorpio", "scorpio_2017_2021"), ("swift", "swift_2018_2023"), ("nexon", "nexon_2020_2024")]
    for token, key in base:
        if token in k:
            return key
    return None

# ------------------------------- Tools ---------------------------------------

@agent_tool
def get_rate_card(vehicle_model: str) -> Dict[str, Any]:
    """
    Return the static company rate card (MRP + standard labour) for a vehicle model.
    Args:
        vehicle_model: e.g. "Scorpio 2017-2021"
    Returns:
        { ok, model_key, model_name, currency, gst_percent, labour_rates,
          materials_pct_for_repair, standard_hours, parts_catalog, last_updated }
    """
    model_key = _resolve_model_key(vehicle_model or "")
    if not model_key:
        return {"ok": False, "error": "Unknown vehicle model", "hint": "Try one of: " + ", ".join(_RATE_CARDS.keys())}

    rc = _RATE_CARDS[model_key]
    return {
        "ok": True,
        "model_key": model_key,
        "model_name": rc["model_name"],
        "currency": rc["currency"],
        "gst_percent": rc["gst_percent"],
        "labour_rates": rc["labour_rates"],
        "materials_pct_for_repair": rc["materials_pct_for_repair"],
        "standard_hours": rc["standard_hours"],
        "parts_catalog": rc["parts_catalog"],
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "source": "static_ratecard_v1",
    }

@agent_tool
def price_parts_and_labour(
    vehicle_model: str,
    items: List[Dict[str, str]],
    include_tax: bool = False
) -> Dict[str, Any]:
    """
    Compute a quick price using the static rate card.
    items: list of {"part": "<slug or name>", "action": "replace|repair_minor|repair_major|paint"}
    Notes:
        - For 'replace', parts MRP is charged; labour uses standard_hours * hourly_general.
        - For 'repair_*', parts MRP is 0; materials = materials_pct_for_repair * labour.
        - 'paint' uses paint_per_panel (not hourly) if panel has 'paint' in standard_hours; else hourly.
    """
    model_key = _resolve_model_key(vehicle_model or "")
    if not model_key:
        return {"ok": False, "error": "Unknown vehicle model", "hint": "Try one of: " + ", ".join(_RATE_CARDS.keys())}
    rc = _RATE_CARDS[model_key]

    hourly = rc["labour_rates"]["hourly_general"]
    paint_per_panel = rc["labour_rates"]["paint_per_panel"]
    fitment_flat = rc["labour_rates"]["fitment_flat"]
    mat_pct = rc["materials_pct_for_repair"]
    gst = rc["gst_percent"] if include_tax else 0

    line_items = []
    totals = {"parts": 0.0, "labour": 0.0, "materials": 0.0, "gst": 0.0}

    for it in items or []:
        part = _slug(it.get("part", ""))
        action = _slug(it.get("action", ""))

        sh = rc["standard_hours"].get(part, {})
        part_info = rc["parts_catalog"].get(part, {"mrp": 0, "oem": False})

        hours = sh.get(action, 0.0)
        # Special handling for paint
        if action == "paint":
            labour_cost = paint_per_panel if hours else paint_per_panel  # per panel
            hours = sh.get("paint", 1.0) or 1.0
        elif action == "replace" and hours == 0.0:
            # If hours not specified, at least charge fitment
            labour_cost = fitment_flat
        else:
            labour_cost = hours * hourly

        parts_cost = part_info["mrp"] if action == "replace" else 0.0
        materials = 0.0 if action == "replace" else round(mat_pct * labour_cost, 2)

        taxable_base = parts_cost + labour_cost + materials
        tax = round(taxable_base * gst / 100.0, 2) if gst else 0.0
        payable = round(taxable_base + tax, 2)

        line_items.append({
            "part": part,
            "action": action,
            "standard_hours": hours,
            "labour_cost": round(labour_cost, 2),
            "parts_mrp": parts_cost,
            "materials": materials,
            "gst": tax,
            "payable": payable,
            "oem": bool(part_info.get("oem", False)),
        })

        totals["parts"] += parts_cost
        totals["labour"] += labour_cost
        totals["materials"] += materials
        totals["gst"] += tax

    grand_total = round(totals["parts"] + totals["labour"] + totals["materials"] + totals["gst"], 2)

    return {
        "ok": True,
        "model_key": model_key,
        "model_name": rc["model_name"],
        "currency": rc["currency"],
        "gst_percent": rc["gst_percent"] if include_tax else 0,
        "items": line_items,
        "subtotals": {k: round(v, 2) for k, v in totals.items()},
        "grand_total": grand_total,
        "source": "static_ratecard_v1",
        "computed_at": datetime.utcnow().isoformat() + "Z",
    }

