"""
Integration tests for legal chat conversation quality.
Runs multi-turn conversations against the live API and validates:
  - Anti-repetition across turns
  - Language matching
  - Situational awareness (phone snatched, escalation)
  - Response structure and conciseness

Usage:
    python -m tests.test_legal_conversations          # from backend/
    python tests/test_legal_conversations.py           # standalone
"""
import io
import json
import os
import re
import sys
import time
import uuid
import requests
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Optional

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api/v1"

TEST_EMAIL = f"testbot_{uuid.uuid4().hex[:8]}@test.com"
TEST_PASSWORD = "TestPass123!"


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class TurnResult:
    query: str
    answer: str
    recommended_action: str
    sections: list
    fine_range: Optional[dict]
    raw: dict
    checks: list = field(default_factory=list)


def register_and_login() -> str:
    """Register a test user and return an access token."""
    reg = requests.post(f"{API}/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": "Test Bot User",
        "state": "Maharashtra",
    })
    if reg.status_code not in (201, 200):
        if "already" in reg.text.lower():
            pass
        else:
            print(f"[WARN] Register failed ({reg.status_code}): {reg.text[:200]}")

    login = requests.post(f"{API}/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    if login.status_code != 200:
        print(f"[FATAL] Login failed ({login.status_code}): {login.text[:300]}")
        sys.exit(1)

    return login.json()["access_token"]


def send_message(token: str, query: str, thread_id: str,
                 state: str = "maharashtra", city: str = "Mumbai",
                 language: str = "mr") -> dict:
    """Send a chat message and return the full response dict."""
    resp = requests.post(
        f"{API}/legal/query",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": query,
            "state": state,
            "city": city,
            "language": language,
            "thread_id": thread_id,
        },
        timeout=120,
    )
    if resp.status_code != 200:
        return {"error": resp.status_code, "detail": resp.text[:500]}
    data = resp.json()
    data["_thread_id"] = data.get("thread_id", thread_id)
    return data


def extract_answer(data: dict) -> TurnResult:
    """Pull the answer fields out of the API response."""
    resp = data.get("response", {})
    return TurnResult(
        query="",
        answer=resp.get("answer", str(resp)),
        recommended_action=resp.get("recommended_action", ""),
        sections=resp.get("sections_cited", []),
        fine_range=resp.get("fine_range"),
        raw=data,
    )


def text_similarity(a: str, b: str) -> float:
    """Return 0-1 similarity ratio between two texts."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def sentences(text: str) -> list[str]:
    """Split text into sentences."""
    return [s.strip() for s in re.split(r'[।.!?\n]', text) if len(s.strip()) > 10]


def check_no_repetition(prev: TurnResult, curr: TurnResult) -> CheckResult:
    """Verify current answer doesn't repeat previous answer."""
    sim = text_similarity(prev.answer, curr.answer)
    if sim > 0.65:
        return CheckResult(
            "anti-repetition", False,
            f"Answers are {sim:.0%} similar — likely repeated content"
        )
    prev_sents = sentences(prev.answer)
    curr_sents = sentences(curr.answer)
    for ps in prev_sents:
        for cs in curr_sents:
            if text_similarity(ps, cs) > 0.75:
                return CheckResult(
                    "anti-repetition", False,
                    f"Repeated sentence: \"{ps[:60]}...\" ≈ \"{cs[:60]}...\""
                )
    return CheckResult("anti-repetition", True, f"Similarity {sim:.0%} — OK")


def check_valid_json_structure(turn: TurnResult) -> CheckResult:
    """Verify response has expected JSON fields."""
    resp = turn.raw.get("response", {})
    required = ["answer", "recommended_action", "disclaimer"]
    missing = [k for k in required if k not in resp]
    if missing:
        return CheckResult("json-structure", False, f"Missing fields: {missing}")
    if not resp["answer"] or len(resp["answer"]) < 5:
        return CheckResult("json-structure", False, "Answer is empty or too short")
    return CheckResult("json-structure", True, "All required fields present")


def check_conciseness(turn: TurnResult, max_words: int = 120) -> CheckResult:
    """Verify answer is concise."""
    word_count = len(turn.answer.split())
    if word_count > max_words:
        return CheckResult(
            "conciseness", False,
            f"Answer is {word_count} words (max {max_words})"
        )
    return CheckResult("conciseness", True, f"{word_count} words — OK")


def check_phone_snatched_logic(turn: TurnResult) -> CheckResult:
    """When phone is snatched, bot should not blindly say 'call karo'."""
    answer_lower = turn.answer.lower()
    bad_phrases = ["112 वर कॉल कर", "112 dial kar", "call karo", "112 pe call", "कॉल कर"]
    has_call_advice = any(p in answer_lower for p in bad_phrases)

    good_phrases = ["दुकान", "shop", "dukaan", "dhaba", "petrol pump", "passerby",
                    "kisi ka phone", "कोणाचा फोन", "कुणाचा", "wahan se"]
    has_alternative = any(p in answer_lower for p in good_phrases)

    if has_call_advice and not has_alternative:
        return CheckResult(
            "phone-snatched-logic", False,
            "Says 'call karo' without explaining HOW when phone is taken"
        )
    if has_alternative:
        return CheckResult("phone-snatched-logic", True, "Gives physical alternative for calling")
    return CheckResult("phone-snatched-logic", True, "No call advice (OK)")


def check_extortion_identified(turn: TurnResult) -> CheckResult:
    """Verify the bot identifies extortion/overcharging."""
    keywords = ["extortion", "एक्स्टॉर्शन", "बेकायदेशीर", "illegal", "galat",
                "गलत", "overcharg", "zyada", "ज्यादा"]
    if any(k in turn.answer.lower() for k in keywords):
        return CheckResult("extortion-id", True, "Correctly identifies extortion")
    return CheckResult("extortion-id", False, "Did NOT identify extortion/overcharging")


def check_language_match(turn: TurnResult, expected_script: str) -> CheckResult:
    """Check if response is in the expected language (script or Romanized form).
    When users type in Roman script, the bot may respond in Roman script too — that's valid."""
    script_ranges = {
        "devanagari": r'[\u0900-\u097F]',
        "latin": r'[a-zA-Z]',
        "gujarati": r'[\u0A80-\u0AFF]',
        "tamil": r'[\u0B80-\u0BFF]',
        "telugu": r'[\u0C00-\u0C7F]',
        "bengali": r'[\u0980-\u09FF]',
    }
    pattern = script_ranges.get(expected_script)
    if not pattern:
        return CheckResult("language", True, "No script check needed")
    matches = re.findall(pattern, turn.answer)
    ratio = len(matches) / max(len(turn.answer), 1)
    if ratio > 0.15:
        return CheckResult("language", True, f"{expected_script} script {ratio:.0%} — OK")

    if expected_script == "devanagari":
        latin_matches = re.findall(r'[a-zA-Z]', turn.answer)
        latin_ratio = len(latin_matches) / max(len(turn.answer), 1)
        hindi_marathi_markers = [
            "hai", "nahi", "karo", "mein", "toh", "aahe", "kar",
            "tum", "aur", "agar", "challan", "fine", "police",
            "maang", "dena", "rakh", "haq", "likhi", "bol",
        ]
        marker_count = sum(1 for m in hindi_marathi_markers if m in turn.answer.lower())
        if latin_ratio > 0.3 and marker_count >= 3:
            return CheckResult(
                "language", True,
                f"Romanized Hindi/Marathi ({marker_count} markers) — matches user's Roman input"
            )

    return CheckResult(
        "language", False,
        f"Expected {expected_script} script but found only {ratio:.0%}"
    )


def print_turn(i: int, query: str, turn: TurnResult):
    """Print a formatted turn result."""
    status_symbols = {True: "PASS", False: "FAIL"}
    print(f"\n  {'─' * 70}")
    print(f"  Turn {i}: \"{query}\"")
    print(f"  Answer: {turn.answer[:200]}{'...' if len(turn.answer) > 200 else ''}")
    print(f"  Recommended: {turn.recommended_action}")
    print(f"  Sections: {turn.sections}")
    for c in turn.checks:
        sym = status_symbols[c.passed]
        print(f"    [{sym}] {c.name}: {c.detail}")


def run_scenario(name: str, token: str, messages: list[dict],
                 state: str = "maharashtra", city: str = "Mumbai",
                 language: str = "mr") -> list[TurnResult]:
    """Run a multi-turn conversation scenario."""
    print(f"\n{'=' * 74}")
    print(f"  SCENARIO: {name}")
    print(f"{'=' * 74}")

    thread_id = str(uuid.uuid4())
    turns: list[TurnResult] = []

    for i, msg in enumerate(messages, 1):
        query = msg["query"]
        msg_lang = msg.get("language", language)
        msg_state = msg.get("state", state)

        data = send_message(token, query, thread_id,
                            state=msg_state, city=city, language=msg_lang)

        if "error" in data:
            print(f"  [ERROR] Turn {i} failed: {data}")
            continue

        thread_id = data.get("_thread_id", thread_id)
        turn = extract_answer(data)
        turn.query = query

        turn.checks.append(check_valid_json_structure(turn))
        turn.checks.append(check_conciseness(turn))

        for check_fn in msg.get("checks", []):
            turn.checks.append(check_fn(turn))

        if turns:
            turn.checks.append(check_no_repetition(turns[-1], turn))

        turns.append(turn)
        print_turn(i, query, turn)
        time.sleep(1)

    return turns


def scenario_a1_marathi_escalation(token: str) -> list[TurnResult]:
    """Test A1: Late night stop → bribe → phone snatched (Marathi)."""
    return run_scenario(
        "A1: Marathi Escalation — Bribe → Phone Snatched",
        token,
        messages=[
            {
                "query": "police ne mala thambavla, helmet nahi aahe",
                "checks": [
                    lambda t: check_language_match(t, "devanagari"),
                ],
            },
            {
                "query": "te 20000 magtayet, gadi japat karaychi dhamki det aahet",
                "checks": [
                    check_extortion_identified,
                ],
            },
            {
                "query": "tyani maza phone hiskavun ghetla",
                "checks": [
                    check_phone_snatched_logic,
                ],
            },
            {
                "query": "mi dukanat aalo, koni tari cha phone vaaparto aahe",
                "checks": [],
            },
        ],
        state="maharashtra",
        language="mr",
    )


def scenario_a2_hindi_highway(token: str) -> list[TurnResult]:
    """Test A2: Highway stop — insurance expired + overcharge (Hindi)."""
    return run_scenario(
        "A2: Hindi Highway — Insurance + Overcharge",
        token,
        messages=[
            {
                "query": "bhai highway pe police ne roka insurance expired hai",
                "language": "hi",
                "checks": [
                    lambda t: check_language_match(t, "devanagari"),
                ],
            },
            {
                "query": "police 10000 maang raha hai nahi to gaadi rakh lenge",
                "language": "hi",
                "checks": [
                    check_extortion_identified,
                ],
            },
            {
                "query": "challan dene ko mana kar raha hai, bol raha cash do",
                "language": "hi",
                "checks": [],
            },
        ],
        state="rajasthan",
        city="Jaipur",
        language="hi",
    )


def scenario_a3_hinglish_student(token: str) -> list[TurnResult]:
    """Test A3: College student, first time caught (Hinglish)."""
    return run_scenario(
        "A3: Hinglish Student — First Time Scared",
        token,
        messages=[
            {
                "query": "bro i got stopped by police first time ever, no helmet and no licence",
                "language": "en",
                "checks": [],
            },
            {
                "query": "he is saying 15000 pay or he will take me to station",
                "language": "en",
                "checks": [
                    check_extortion_identified,
                ],
            },
            {
                "query": "ok he took the bike and gave me a receipt, what now",
                "language": "en",
                "checks": [],
            },
        ],
        state="delhi",
        city="Delhi",
        language="en",
    )


def scenario_b3_vague_followups(token: str) -> list[TurnResult]:
    """Test B3: Vague follow-ups — should stay on topic and not repeat."""
    return run_scenario(
        "B3: Vague Follow-ups — ok / aur kuch / kya karu",
        token,
        messages=[
            {
                "query": "police pakda signal jump ke liye, kitna fine hai",
                "language": "hi",
                "checks": [],
            },
            {
                "query": "theek hai, aur kuch bata",
                "language": "hi",
                "checks": [],
            },
            {
                "query": "kya karu isko contest karna hai",
                "language": "hi",
                "checks": [],
            },
        ],
        state="maharashtra",
        city="Pune",
        language="hi",
    )


def scenario_b4_topic_pivot(token: str) -> list[TurnResult]:
    """Test B4: User switches topic mid-conversation."""
    return run_scenario(
        "B4: Topic Pivot — Insurance → Drunk Driving",
        token,
        messages=[
            {
                "query": "got caught without insurance, what is the fine",
                "language": "en",
                "checks": [],
            },
            {
                "query": "by the way what is the fine for drunk driving",
                "language": "en",
                "checks": [],
            },
        ],
        state="karnataka",
        city="Bangalore",
        language="en",
    )


def check_asks_clarification(turn: TurnResult) -> CheckResult:
    """Verify the bot asks a clarifying question about DL or cash vs challan."""
    answer_lower = turn.answer.lower()
    clarification_markers = [
        "?", "ka?", "ki?", "aahe ka", "hai kya", "ya ", "athva",
        "ghar pe", "forgot", "visarla", "mparivahan", "digital",
        "likhit challan", "cash", "receipt", "15 din", "15 days",
    ]
    has_clarification = sum(1 for m in clarification_markers if m in answer_lower) >= 2
    if has_clarification:
        return CheckResult(
            "clarification", True,
            "Asks clarifying question or covers both possibilities"
        )
    return CheckResult(
        "clarification", False,
        "Does NOT ask clarifying question (DL forgot vs never had, cash vs challan)"
    )


def check_empathy_first_message(turn: TurnResult) -> CheckResult:
    """Verify the first message is warm/empathetic, not jumping to legal facts."""
    answer_lower = turn.answer.lower()
    empathy_markers = [
        "tension", "worry", "don't worry", "darr", "fikar",
        "nako", "mat", "help", "madat", "sang", "bata",
        "tell me", "what happened", "kai zhala", "kya hua",
    ]
    has_empathy = sum(1 for m in empathy_markers if m in answer_lower) >= 1
    if has_empathy:
        return CheckResult("empathy", True, "Warm/empathetic first response")
    return CheckResult("empathy", False, "Missing empathy in first message")


def scenario_a5_solapur_no_dl(token: str) -> list[TurnResult]:
    """Test A5: User's exact scenario — no DL, ₹5,000 demand in Solapur."""
    return run_scenario(
        "A5: Solapur No-DL — Clarification + Cash vs Challan",
        token,
        messages=[
            {
                "query": "i am facing issue",
                "checks": [
                    check_empathy_first_message,
                ],
            },
            {
                "query": "police ne mala pakadle ani dl naslyamule te mala 5000 mangat ahe",
                "checks": [
                    check_asks_clarification,
                ],
            },
        ],
        state="maharashtra",
        city="Solapur",
        language="mr",
    )


def summarize(all_turns: list[TurnResult]):
    """Print final test summary."""
    total_checks = 0
    passed = 0
    failed = 0
    failures = []

    for turn in all_turns:
        for c in turn.checks:
            total_checks += 1
            if c.passed:
                passed += 1
            else:
                failed += 1
                failures.append((turn.query[:50], c.name, c.detail))

    print(f"\n{'=' * 74}")
    print(f"  FINAL SUMMARY")
    print(f"{'=' * 74}")
    print(f"  Total checks: {total_checks}")
    print(f"  Passed:       {passed}")
    print(f"  Failed:       {failed}")

    if failures:
        print(f"\n  FAILURES:")
        for query, name, detail in failures:
            print(f"    - [{name}] \"{query}...\" → {detail}")
    else:
        print(f"\n  ALL CHECKS PASSED!")

    return failed


def main():
    print("=" * 74)
    print("  Traffic Justice AI — Conversation Quality Test Suite")
    print("=" * 74)

    print("\n[1/5] Checking backend health...")
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=10)
        if health.status_code != 200:
            print(f"  Backend unhealthy: {health.status_code}")
            sys.exit(1)
        print(f"  Backend is healthy: {health.json()}")
    except requests.ConnectionError:
        print("  Cannot connect to backend at localhost:8000. Is it running?")
        sys.exit(1)

    print("\n[2/5] Registering test user...")
    token = register_and_login()
    print(f"  Logged in successfully")

    print("\n[3/5] Running test scenarios...")
    all_turns = []

    all_turns.extend(scenario_a1_marathi_escalation(token))
    all_turns.extend(scenario_a2_hindi_highway(token))
    all_turns.extend(scenario_a3_hinglish_student(token))
    all_turns.extend(scenario_b3_vague_followups(token))
    all_turns.extend(scenario_b4_topic_pivot(token))
    all_turns.extend(scenario_a5_solapur_no_dl(token))

    print("\n[4/5] Analyzing results...")
    failed = summarize(all_turns)

    print(f"\n[5/5] Done. {'SOME TESTS FAILED' if failed else 'ALL TESTS PASSED'}")
    return failed


if __name__ == "__main__":
    sys.exit(main())
