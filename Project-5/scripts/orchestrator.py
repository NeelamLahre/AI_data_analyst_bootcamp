import time
from intent_router import route
from text_to_sql_agent import run_query, ask_llm
from query_rag import retrieve
from logger import log_query


def sanitize_retrieved_text(chunk):
    banned = ["ignore previous", "ignore the above", "system prompt", "you are now", "new instructions"]
    lowered = chunk.lower()
    return "" if any(b in lowered for b in banned) else chunk


def answer_question(question):
    start = time.time()
    decision = route(question)

    sql_used, sql_rows, sql_cols = None, None, None
    rag_chunks = []

    try:
        if decision in ("sql", "both"):
            sql_used, sql_cols, sql_rows = run_query(question)

        if decision in ("rag", "both"):
            raw_chunks = retrieve(question, k=4)
            rag_chunks = [sanitize_retrieved_text(c) for c in raw_chunks if sanitize_retrieved_text(c)]

        context_parts = []
        if sql_rows is not None:
            table_str = "\n".join(str(r) for r in sql_rows[:20])
            context_parts.append(f"SQL query used:\n{sql_used}\n\nResults:\n{table_str}")
        if rag_chunks:
            context_parts.append("Retrieved document excerpts:\n" + "\n---\n".join(rag_chunks))

        if not context_parts:
            latency = int((time.time() - start) * 1000)
            log_query(question, decision, sql_used, "no_context", 0, latency)
            return {"answer": "I don't have enough information to answer that.",
                    "sql": sql_used, "sources": rag_chunks}

        synthesis_prompt = f"""Answer the user's question using ONLY the context below. If the context
doesn't contain enough information to answer confidently, say so explicitly rather than guessing.

Context:
{chr(10).join(context_parts)}

Question: {question}

Answer concisely, in plain language."""

        final_answer = ask_llm(synthesis_prompt)

        latency = int((time.time() - start) * 1000)
        log_query(question, decision, sql_used, "success",
                  len(sql_rows) if sql_rows else 0, latency)

        return {"answer": final_answer, "sql": sql_used, "sources": rag_chunks}

    except Exception as e:
        latency = int((time.time() - start) * 1000)
        log_query(question, decision, sql_used, "failed", 0, latency, str(e))
        return {"answer": "I ran into an error trying to answer that - please rephrase or try a simpler question.",
                "sql": sql_used, "sources": [], "error": str(e)}