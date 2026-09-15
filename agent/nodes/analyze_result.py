from ..agent_state import AgentState
from ..llm import get_llm

from typing import Literal
from pydantic import BaseModel

class ChartSpecs(BaseModel):
    chart_type: Literal["scatter","line","bar","pie"]
    x: str
    y: str
    title: str

def analyze_result(state:AgentState) -> AgentState:
    """This node analyzes the result and determines if a chart is needed or not."""

    chart_needed_prompt = f'''
                    You are analyzing the result of a database query.
        
                    User Question: {state["user_query"]}
                    Query Result: {state["result"]}
        
                    Determine whether a chart would meaningfully improve the answer.
        
                    Return exactly: CHART or NO_CHART

                    Use CHART when the result show:
                    - a trend over time
                    - comparison between categories 
                    - rankings
                    - proportions
                    - relationships between numeric variables 
        
                    Use NO_CHART when: 
                    - the result is a single value
                    - the result is mainly explanatory text
                    - a chart would not add meaningful insight 
            ''' 

    llm = get_llm()
    state["chart_needed"] = llm.invoke(chart_needed_prompt).content.strip()     

    structured_llm = llm.with_structured_output(ChartSpecs)

    if state["chart_needed"] == "CHART":
        # chart_prompt = f'''
        #     You must determine the appropirate specifications for a chart provided the following query result.

        #     Qeury Result: {state["result"]}

        #         - choose the appropriate chart type
        #         - choose the x and y columns
        #         - provide a clear title
        # '''
        chart_prompt = f'''
            Determine the appropriate chart specifications for the user's question
            and query result.

            User Question: {state["user_query"]}
            Query Result: {state["result"]}

            Choose:
            - the appropriate chart type
            - the x column
            - the y column
            - a clear title

            IMPORTANT:
            - x and y MUST exactly match the column names in the query result.
            - Do not rename, reformat, or invent column names.
            - Use the exact spelling and capitalization of the query result columns.
        '''
        state["chart_specs"] = structured_llm.invoke(chart_prompt)
        print(state["result"])
        print(state["chart_specs"])

    return state
    