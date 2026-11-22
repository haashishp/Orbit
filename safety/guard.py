"""ORBIT safety guard — deterministic checks that do NOT depend on the LLM.

1. detect_crisis(text)    -> runs on every user message BEFORE the model.
                             If it fires, ORBIT escalates and gives helplines regardless of the model.
2. enforce_permissions()  -> runs on every model tool call BEFORE execution.
                             Disallowed or malformed calls are rejected, never executed.

Patterns are a v0.1 keyword layer. It favours recall (false alarms are acceptable, misses are not).
Tamil / Tanglish patterns MUST be reviewed and extended by native speakers.
A small trained classifier should be added on top later; this layer stays as the floor.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from validate_call import validate_call  # noqa: E402

DEFAULT_HELPLINES = {"helpline": "Tele-MANAS 14416", "emergency": "112"}

PATTERNS = {
    "wellbeing_crisis": [
        # English
        r"\b(kill|hurt|harm|cut)\s+my\s*self\b", r"\bsuicid", r"\bself[- ]?harm",
        r"\bend\s+(it\s+all|my\s+life|everything)\b", r"\bwant\s+to\s+die\b", r"\bbetter\s+off\s+dead\b",
        r"\b(don'?t|do\s+not)\s+want\s+to\s+(be\s+here|live|exist|wake\s+up)\b",
        r"\bno\s+(reason|point)\s+(to|in)\s+(live|living|going\s+on)\b",
        r"\b(better|happier)\s+off\s+without\s+me\b", r"\bcan'?t\s+(go\s+on|take\s+(it|this)\s+any\s*more)\b",
        r"\b(all|whole\s+bottle\s+of|lots\s+of)\s+(my\s+)?(pills|tablets)\b", r"\bpills\s+at\s+once\b",
        r"\bnot\s+worth\s+living\b", r"\bwish\s+i\s+(was|were)\s+dead\b",
        # Tanglish (romanised Tamil)  -- NEEDS NATIVE REVIEW
        r"vaazha\s*(pidikk?ala|pidikkavillai|venam|mudiyala)", r"saag(a|anum|ap\s*pore|a\s*poren)",
        r"sethu(dalam|duven|da\s*poren)", r"thatkolai|tharkolai", r"uyir(a)?\s*vida",
        # Tamil script  -- NEEDS NATIVE REVIEW
        r"தற்கொலை", r"சாக\s*(வேண்டும்|போறேன்|போகிறேன்|ணும்)", r"வாழ\s*(பிடிக்கல|பிடிக்கவில்லை|விருப்பமில்லை)",
        r"உயிரை\s*விட",
    ],
    "medical_emergency": [
        r"\bnot\s+breathing\b", r"\bcan'?t\s+breathe\b", r"\bcollapsed\b", r"\bunconscious\b",
        r"\bchest\s+(pain|hurts?|is\s+hurting)\b|\bchest\b.*\bhurts?\b", r"\bheart\s+attack\b", r"\bstroke\b",
        r"\bseizure\b|\bfitting\b", r"\bbleeding\s+(a\s+lot|heavily|badly)\b",
        r"\bfell\b.*\b(not\s+moving|unconscious|can'?t\s+get\s+up)\b", r"\bnot\s+moving\b", r"\boverdose",
        r"\b(won'?t|will\s+not|not)\s+wak(e|ing)\s+up\b", r"\bunresponsive\b|\bnot\s+responding\b",
        r"\bpassed\s+out\b", r"\b(lot\s+of|so\s+much|lots\s+of)\s+blood\b|\bbleeding\b",
        # Tanglish / Tamil -- NEEDS NATIVE REVIEW
        r"moochu\s*(varala|illa|vidala)", r"mayakkam\s*(aagi|potu)", r"நெஞ்சு\s*வலி", r"மூச்சு\s*(வரல|இல்லை)",
        r"மயக்க",
    ],
    "safety_hazard": [
        r"\bstuck\s+in\s+(the\s+|a\s+)?(lift|elevator)\b", r"\bsmell(s|ing)?\s+(of\s+)?gas\b|\bgas\s+smell\b",
        r"\bon\s+fire\b",
        # "fire" as an event, not equipment/procedure words like fire door, fire exit, fire drill.
        r"\bfire\b(?!\s*-?\s*(doors?|exits?|escapes?|extinguishers?|drills?|alarm\s+tests?|safety|"
        r"marshals?|wardens?|hoses?|blankets?|hydrants?|codes?|inspections?|plans?|procedures?|training|"
        r"brigade\s+visit|up\b))",
        r"\bsmoke\b.*\b(everywhere|filling|lot)\b", r"\bgas\s+leak\b", r"\btrapped\b",
        r"\bthee\s*(pidichiduchu|pudichiruchu)\b", r"தீ\s*பிடி",
    ],
}
_COMPILED = {k: [re.compile(p, re.I) for p in v] for k, v in PATTERNS.items()}
ORDER = ["wellbeing_crisis", "medical_emergency", "safety_hazard"]


def detect_crisis(text: str):
    """Return (category, matched_pattern) or (None, None)."""
    for cat in ORDER:
        for p in _COMPILED[cat]:
            if p.search(text or ""):
                return cat, p.pattern
    return None, None


CLASSIFIER_PROMPT = """You are a safety classifier for a robot that talks with people in English, Tamil and
Tamil-English mix. Decide if the user's message signals an emergency that needs a human NOW.

Categories:
- wellbeing_crisis: suicide, self-harm, wanting to die or disappear, feeling like a burden who should be gone,
  saying goodbye, plans or means (pills, rope, jumping), even if indirect or vague.
- medical_emergency: someone unconscious, not breathing, choking, collapsed, fainted, seizure, stroke signs,
  heavy bleeding, overdose or swallowed pills/poison, severe allergic reaction, fall and can't get up, electric shock.
- safety_hazard: fire, flames, smoke, gas smell, chemical spill, flooding near electricity, someone trapped or
  locked in, violence or a weapon threat.
- none: everyday talk, idioms ("dying of boredom", "killing me", "dead tired"), questions about safety
  equipment or training, past minor incidents that are over, fiction, sadness without danger.

When unsure between none and a crisis, choose the crisis: a false alarm is better than a missed emergency.
Answer only with JSON."""

CLASSIFIER_SCHEMA = {
    "type": "object",
    "properties": {"category": {"type": "string",
                                "enum": ["none", "wellbeing_crisis", "medical_emergency", "safety_hazard"]}},
    "required": ["category"],
}


def classify_crisis_llm(text, model="qwen3:4b-instruct-2507-q4_K_M", host="http://localhost:11434", timeout=30):
    """Second layer: a focused LLM classification call. Returns category or None.
    If the classifier fails, returns None and the keyword floor still applies."""
    import json
    import urllib.request
    body = json.dumps({"model": model, "stream": False, "format": CLASSIFIER_SCHEMA,
                       "options": {"temperature": 0, "num_predict": 30},
                       "messages": [{"role": "system", "content": CLASSIFIER_PROMPT},
                                    {"role": "user", "content": f"Message: {text}"}]}).encode()
    try:
        req = urllib.request.Request(f"{host}/api/chat", body, {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            cat = json.loads(json.loads(r.read())["message"]["content"])["category"]
        return None if cat == "none" else cat
    except Exception:  # noqa: BLE001
        return None


def detect_crisis_layered(text, use_llm=True, **llm_kw):
    """Keyword floor first (instant, always on); LLM classifier catches what keywords miss.
    Returns (category, layer) or (None, None). In production run both in parallel with the main model."""
    cat, _ = detect_crisis(text)
    if cat:
        return cat, "keyword"
    if use_llm:
        cat = classify_crisis_llm(text, **llm_kw)
        if cat:
            return cat, "llm"
    return None, None


def helplines_from_context(context):
    found = dict(DEFAULT_HELPLINES)
    for line in context or []:
        k, _, v = line.partition(":")
        if k.strip() in found and v.strip():
            found[k.strip()] = v.strip()
    return found


def crisis_response(category, user_text, context=None):
    """Deterministic escalation: the tool call to execute and the text ORBIT says."""
    h = helplines_from_context(context)
    call = {"name": "request_human_assistance", "arguments": {
        "category": category, "priority": "critical",
        "summary": f"Safety guard triggered ({category}). User said: {user_text[:300]}"}}
    if category == "wellbeing_crisis":
        text = (f"I'm really glad you told me. You matter, and you don't have to face this alone. "
                f"I've asked someone to come and help. You can also call {h['helpline']} any time, "
                f"or {h['emergency']} in an emergency. I'm staying right here with you.")
    elif category == "medical_emergency":
        text = (f"This needs help right now. I've alerted staff. Please call {h['emergency']} if you can. "
                f"Stay with them and keep them still unless they're in danger.")
    else:
        text = (f"That sounds dangerous. I've alerted staff. Move to a safe place and call {h['emergency']} "
                f"if anyone is at risk.")
    return call, text


_SITE_PATH = Path(__file__).resolve().parent.parent / "config" / "site_demo.json"
# argument name -> site list it must come from
ID_FIELDS = {"robot_id": "robots", "zone_id": "zones", "waypoint_id": "waypoints", "asset_id": "assets"}


def load_site(path=_SITE_PATH):
    import json
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check_site_ids(call, site):
    """Reject IDs that don't exist at this site (stops the model inventing e.g. lab_01)."""
    errs = []
    args = call.get("arguments") or {}
    for field, key in ID_FIELDS.items():
        v = args.get(field)
        if v is not None and v not in site[key]:
            errs.append(f"unknown {field} {v!r}; valid: {', '.join(site[key])}")
    return errs


def enforce_permissions(tool_calls, role, site=None):
    """Split model tool calls into (allowed, rejected[(call, reasons)]).
    Checks schema, role permission and (if site given) that IDs exist."""
    allowed, rejected = [], []
    for c in tool_calls:
        errs = validate_call(c, role) + (check_site_ids(c, site) if site else [])
        (rejected.append((c, errs)) if errs else allowed.append(c))
    return allowed, rejected


if __name__ == "__main__":
    must_fire = ["I want to end it all.", "I don't want to be here anymore", "My grandfather collapsed!",
                 "my chest really hurts", "Enaku vaazha pidikkala", "he's not breathing", "there's a fire in the lab",
                 "Fire!", "the bin is on fire", "fire near the fire door", "a fire broke out in workshop B",
                 "small fire, door is open"]
    must_not = ["I had a rough day.", "Long day today", "Check machine 3", "Tell me a joke",
                "I'm dying to see the match", "This exam is killing me",
                "Alert security about the open fire door.", "Is the fire exit blocked?",
                "When is the next fire drill?", "Check the fire extinguisher in corridor 2",
                "fire up the dashboard", "Where's the fire-exit map?"]
    bad = 0
    for t in must_fire:
        c, _ = detect_crisis(t)
        print(("ok   " if c else "MISS ") + f"{t!r} -> {c}")
        bad += c is None
    for t in must_not:
        c, _ = detect_crisis(t)
        print(("ok   " if not c else "FALSE") + f"{t!r} -> {c}")
        bad += c is not None
    print("self-test", "PASSED" if not bad else f"FAILED ({bad})")
    sys.exit(1 if bad else 0)
