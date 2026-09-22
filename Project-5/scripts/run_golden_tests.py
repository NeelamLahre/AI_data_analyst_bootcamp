import json
from config import DATA_PROCESSED
from intent_router import route
from orchestrator import answer_question

golden = json.load(open(DATA_PROCESSED / "golden_qa.json"))

passed = 0
for case in golden:
    actual_route = route(case["question"])
    route_ok = actual_route == case["expect_route"]

    result = answer_question(case["question"])
    has_answer = bool(result["answer"]) and "don't have enough information" not in result["answer"]

    status = "PASS" if route_ok and has_answer else "FAIL"
    passed += status == "PASS"
    print(f"{status} | route: {actual_route} (expected {case['expect_route']}) | {case['question']}")
    if status == "FAIL":
        print(f"     -> answer: {result['answer'][:150]}")

print(f"\n{passed}/{len(golden)} passed")