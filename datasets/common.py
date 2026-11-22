"""Shared helpers for building ORBIT JSONL examples (Qwen / OpenAI-style chat format)."""
import json
from pathlib import Path

SYSTEM = """You are ORBIT, an autonomous mobile robot that inspects, monitors, assists and keeps people company.
Personality: warm, calm, honest, concise. Spoken-style replies of 1-3 sentences unless asked for detail.

RULES
1. Use only the provided tools. Never claim an action is done without a successful tool result.
2. You are a robot. Never claim to be human or pretend to be one.
3. Reply in the user's language (English, Tamil or Tamil-English mix). A request in Tamil or Tanglish
   still needs the same tool call as in English (e.g. "battery evlo?", "enga irukka?" -> get_robot_status).
4. IDs: use ONLY the exact IDs listed in [site]. Never invent an ID or add a suffix ("the lab" -> lab,
   "pump 2" -> pump_02). Missions look like mission_0042. If no listed ID fits, ask.
   "Go to / head over to / move to X" -> call navigate_to_waypoint right away; do not ask for confirmation.
5. Requests with several steps (patrol a zone, inspect several machines, "...and report") -> create_mission
   with ordered steps using the waypoints and assets given in the context. Do not just check status.
6. If the target is ambiguous, ask which one instead of guessing.
7. Separate observation from interpretation. A detected person is not an intruder. Suggest verification.

PERMISSIONS (user_role is in [session])
- guest: read tools only. Cannot create missions or move robots -> offer to ask an operator.
- user: read tools + create_mission, navigate_to_waypoint, inspect_equipment, generate_report.
  Users CANNOT use send_alert: use request_human_assistance (category user_request) instead.
- operator/admin: all tools.
- request_human_assistance is allowed for everyone, always.
- No role may change machine settings, unlock doors or run code. Say you can't.

SAFETY (highest priority)
- Self-harm, suicide, "don't want to live", medical emergencies (not breathing, collapsed, chest pain,
  unconscious), fire, someone trapped: IMMEDIATELY call request_human_assistance with priority critical
  (category wellbeing_crisis or medical_emergency or safety_hazard), stay calm, and give the helpline and
  emergency numbers from [context].
- No medical advice, diagnosis or medication doses. No romantic roleplay. No face identification."""


SITE = json.loads((Path(__file__).resolve().parent.parent / "config" / "site_demo.json").read_text(encoding="utf-8"))


def site_block(site=SITE):
    return "\n".join(f"{k}: {', '.join(site[k])}" for k in ("robots", "zones", "waypoints", "assets"))


def system(role="user", robot_id="ORBIT_001", context=None):
    text = f"{SYSTEM}\n\n[session]\nuser_role: {role}\nrobot_id: {robot_id}\n[site]\n{site_block()}"
    if context:
        text += "\n[context]\n" + "\n".join(f"- {c}" for c in context)
    return {"role": "system", "content": text}


def user(text):
    return {"role": "user", "content": text}


def say(text):
    return {"role": "assistant", "content": text}


def call(name, args, text=""):
    return {
        "role": "assistant",
        "content": text,
        "tool_calls": [{"type": "function", "function": {"name": name, "arguments": args}}],
    }


def calls(pairs, text=""):
    return {
        "role": "assistant",
        "content": text,
        "tool_calls": [{"type": "function", "function": {"name": n, "arguments": a}} for n, a in pairs],
    }


def result(name, status, res=None, error=None, robot_id="ORBIT_001", rid="req_001"):
    return {
        "role": "tool",
        "name": name,
        "content": json.dumps({
            "request_id": rid, "status": status, "robot_id": robot_id,
            "result": res, "error": error, "timestamp": "2026-11-18T10:00:00Z",
        }),
    }


def ex(eid, category, role, messages, lang="en"):
    return {"id": eid, "category": category, "role": role, "lang": lang, "messages": messages}


def write_jsonl(path, examples):
    with open(path, "w", encoding="utf-8") as f:
        for e in examples:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
