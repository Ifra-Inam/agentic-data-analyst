import math
import logging
import re
import sys
from pathlib import Path

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.agent_state import AgentState 
from agent.llm import get_llm 

st.title("📊 Agentic Data Analyst")

st.markdown("Ask questions about the **AdventureWorks** database and get data-driven answers, SQL analysis, and visualizations.")

st.info("AdventureWorks is a bicycle manufacturing company with data covering customers, products, sales, employees, and more.")

st.subheader("Try asking")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **💰 Revenue & Sales**
    
    - What is the total net revenue?
    - What are the top 10 best-selling products by quantity?
    """)

with col2:
    st.markdown("""
    **📈 Customers & Trends**
    
    - How has the number of customers changed over time?
    - Which products generate the most revenue?
    """)

st.caption("Ask a question below once the documentation is ready.")

from agent.graph import app

llm = get_llm()

def format_retry_wait(error):
    match = re.search(
        r"please try again in\s+((?:\d+(?:\.\d+)?(?:ms|s|m|h|d))+)",
        str(error),
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    unit_seconds = {"ms": 0.001, "s": 1, "m": 60, "h": 3600, "d": 86400}
    parts = re.findall(r"(\d+(?:\.\d+)?)(ms|s|m|h|d)", match.group(1), flags=re.IGNORECASE)
    total_seconds = sum(float(amount) * unit_seconds[unit.lower()] for amount, unit in parts)
    minutes, seconds = divmod(round(total_seconds), 60)

    if minutes:
        minute_label = f"{minutes} minute" if minutes == 1 else f"{minutes} minutes"
        if seconds:
            second_label = f"{seconds} second" if seconds == 1 else f"{seconds} seconds"
            return f"{minute_label} {second_label}"
        return minute_label

    seconds = max(seconds, 1)
    return f"{seconds} second" if seconds == 1 else f"{seconds} seconds"

def show_processing_error(error):
    logging.exception("Question processing failed")
    error_text = str(error).lower()
    if (
        getattr(error, "status_code", None) == 429
        or "rate_limit_exceeded" in error_text
        or "rate limit" in error_text
    ):
        retry_wait = format_retry_wait(error)
        if retry_wait:
            st.error(f"The AI service is temporarily rate-limited. Please try again in about {retry_wait}.")
        else:
            st.error("The AI service is temporarily rate-limited. Please wait a few seconds and try again.")
    else:
        st.error("Something went wrong while processing your question. Please try again.")
    st.stop()

def stream_updates(state, progress):
    try:
        yield from app.stream(state, stream_mode="updates")
    except Exception as error:
        progress.update(label="Analysis couldn't be completed.", state="error", expanded=False)
        show_processing_error(error)

def invoke_llm(prompt):
    try:
        return llm.invoke(prompt)
    except Exception as error:
        show_processing_error(error)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.write(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.write(message.content)
            validated_sql = message.additional_kwargs.get("validated_sql")
            if validated_sql:
                with st.expander("Final validated SQL"):
                    st.code(validated_sql, language="sql")
        chart = message.additional_kwargs.get("chart")
        chart_caption = message.additional_kwargs.get("chart_caption")
        if chart and chart_caption:
            st.plotly_chart(chart)
            st.caption(chart_caption)

prompt = st.chat_input("Ask away your question..")
state: AgentState = {"user_query": prompt}

if prompt:
    with st.chat_message("user"):
        st.write(prompt)
        st.session_state.messages.append(HumanMessage(prompt))

    full_result = dict(state)
    validated_sql = None
    stage_labels = {
        "rag": "Documentation search complete.",
        "schema": "Database schema loaded.",
        "sql": "SQL draft generated.",
        "validate": "SQL validation complete.",
        "execute": "Query executed.",
        "check": "Query result checked.",
        "analyze": "Analysis complete.",
        "chart": "Chart created.",
    }

    with st.status("Searching business documentation...", expanded=True) as progress:
        for update in stream_updates(state, progress):
            for node_name, node_update in update.items():
                full_result.update(node_update)
                progress.write(stage_labels.get(node_name, f"Completed: {node_name}"))

                if node_name == "rag":
                    if node_update.get("route_after_rag") == "END":
                        next_stage = "Preparing an answer from documentation..."
                    else:
                        next_stage = "Reading the database schema..."
                elif node_name == "schema":
                    next_stage = "Drafting a database query..."
                elif node_name == "sql":
                    next_stage = "Validating the query..."
                elif node_name == "validate":
                    if node_update.get("sql_valid"):
                        next_stage = "Running the validated query..."
                    else:
                        progress.write("The query needs another pass; revising it.")
                        next_stage = "Revising the query after validation..."
                elif node_name == "execute":
                    next_stage = "Checking whether the result answers your question..."
                elif node_name == "check":
                    if node_update.get("result_valid"):
                        validated_sql = full_result.get("generated_sql")
                        next_stage = "Preparing the final analysis..."
                    else:
                        progress.write("The result needs another pass; adjusting the query.")
                        next_stage = "Revising the query based on its result..."
                elif node_name == "analyze":
                    if node_update.get("chart_needed"):
                        next_stage = "Creating a chart..."
                    else:
                        next_stage = "Preparing the final answer..."
                else:
                    next_stage = "Preparing the final answer..."

                progress.update(label=next_stage)

        progress.update(label="Analysis complete.", state="complete", expanded=False)

    with st.chat_message("assistant"):

        final_prompt = f"""
            You are a senior data analyst.

            The user asked:
            {prompt}

            The database analysis produced this result:
            {full_result["result"]}

            Result completeness: {"partial preview; some rows or cell text were omitted" if full_result.get("result_truncated") else "complete"}

            Write a clear, concise answer to the user's question.

            Rules:
            - Do not return JSON.
            - Do not mention the internal workflow, agents, SQL, or LangGraph.
            - Give the user the actual answer first.
            - Include important numbers or findings from the result.
            - Do not invent information that is not present in the result.
            - If the result is partial, say so and do not present it as a complete list or total.
            - Do not create any visualizations or charts. 
            - Use normal natural language.
        """

        response = invoke_llm(final_prompt)
        if full_result.get("result_truncated"):
            st.warning("Showing a bounded preview; some result rows or cell text were omitted.")
        st.markdown(response.content)

        additional_kwargs = {}

        if validated_sql:
            additional_kwargs["validated_sql"] = validated_sql
            with st.expander("Final validated SQL"):
                st.code(validated_sql, language="sql")
        
        chart_response = None

        if full_result.get("chart"):

            st.plotly_chart(full_result["chart"])
            additional_kwargs["chart"] = full_result["chart"]

            chart_prompt = f"""
            Briefly explain what this chart represents based on the user's question:

            User question:
            {prompt}

            Analysis result:
            {full_result["result"]}

            Give 1-2 sentences describing what the chart shows and the main takeaway.
            Do not invent trends or values.
            """

            chart_response = invoke_llm(chart_prompt)
            st.caption(chart_response.content)

        if chart_response:
            additional_kwargs["chart_caption"] = chart_response.content

        st.session_state.messages.append(AIMessage(content=response.content, additional_kwargs=additional_kwargs))