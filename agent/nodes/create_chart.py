from ..agent_state import AgentState

import plotly.express as px

def create_chart(state:AgentState) -> AgentState:

    results = state["result"]
    specs = state["chart_specs"]
    
    chart_type = specs.chart_type
    x = specs.x
    y = specs.y
    title = specs.title

    if x not in results[0] or y not in results[0]:
        raise ValueError("Chart columns not found in query results")

    if chart_type == "bar":
        fig = px.bar(results, x=x, y=y, title=title)

    elif chart_type == "line":
        fig = px.line(results, x=x, y=y, title=title)

    elif chart_type == "pie":
        fig = px.pie(results, names=x, values=y, title=title)

    elif chart_type == "scatter":
        fig = px.scatter(results, x=x, y=y, title=title)

    else:
        raise ValueError(f"Unsupported chart type: {chart_type}")

    state["chart"] = fig

    return state
