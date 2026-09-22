import streamlit as st
from orchestrator import answer_question

st.set_page_config(page_title="Jio Retention Assistant")
st.title("Jio Retention Assistant")
st.caption("Ask about subscribers, churn, circles, or retention offers.")

question = st.text_input("Your question")

if question:
    with st.spinner("Thinking..."):
        result = answer_question(question)

    st.markdown("### Answer")
    st.write(result["answer"])

    if result.get("sql"):
        with st.expander("Generated SQL"):
            st.code(result["sql"], language="sql")

    if result.get("sources"):
        with st.expander("Retrieved sources"):
            for i, s in enumerate(result["sources"], 1):
                st.text(f"[{i}] {s[:300]}...")