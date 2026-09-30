import sys
from pathlib import Path

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.agent_state import AgentState 
from agent.llm import get_llm 
from agent.graph import app

llm = get_llm()

st.title("Agentic Data Analyst")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.write(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.write(message.content)
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
        full_result = app.invoke(state)

    with st.chat_message("assistant"):

        final_prompt = f"""
            You are a senior data analyst.

            The user asked:
            {prompt}

            The database analysis produced this result:
            {full_result["result"]}

            Write a clear, concise answer to the user's question.

            Rules:
            - Do not return JSON.
            - Do not mention the internal workflow, agents, SQL, or LangGraph.
            - Give the user the actual answer first.
            - Include important numbers or findings from the result.
            - Do not invent information that is not present in the result.
            - Use normal natural language.
        """

        response = llm.invoke(final_prompt)
        st.markdown(response.content)

        additional_kwargs = {}
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

            chart_response = llm.invoke(chart_prompt)
            st.caption(chart_response.content)

        if chart_response:
            additional_kwargs["chart_caption"] = chart_response.content

        st.session_state.messages.append(AIMessage(content=response.content, additional_kwargs=additional_kwargs))

    # with st.chat_message("assistant"):

    #     st.markdown(llm.invoke(full_result["result"]))
    #     if full_result.get("chart"):
    #         st.plotly_chart(full_result["chart"])
    #     st.session_state.messages.append(AIMessage(full_result["result"]))


