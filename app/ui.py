import sys
from pathlib import Path

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# from agent.llm import get_llm
from agent.agent_state import AgentState 
from agent.graph import app

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

prompt = st.chat_input("Ask away your question..")
state: AgentState = {"user_query": prompt}

if prompt:
    with st.chat_message("user"):
        st.write(prompt)
        st.session_state.messages.append(HumanMessage(prompt))
        graph = app().compile()
        full_result = graph.invoke(state)

    with st.chat_message("assistant"):
        st.write(full_result["result"])
        st.session_state.messages.append(AIMessage(full_result["result"]))


