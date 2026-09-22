import re


def route(question):
    q = question.lower()
    sql_keywords = ["how many", "top", "list", "count", "average", "which subscriber",
                    "circle", "churn rate", "segment", "score", "subscriber", "risk"]
    doc_keywords = ["offer", "catalogue", "policy", "regulation", "target", "approved",
                    "budget", "brief", "programme"]

    has_subscriber_id = bool(re.search(r"jio\d+", q))

    needs_sql = has_subscriber_id or any(k in q for k in sql_keywords)
    needs_rag = any(k in q for k in doc_keywords)

    if needs_sql and needs_rag:
        return "both"
    if needs_rag:
        return "rag"
    return "sql"


if __name__ == "__main__":
    tests = [
        "Top 5 circles by port-out requests last month",
        "What retention offers are approved for Bihar this quarter",
        "Why is subscriber JIO10037241 high risk, and what should we offer",
    ]
    for t in tests:
        print(f"{t!r} -> {route(t)}")