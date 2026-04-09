import json 
from openai import OpenAI
from typing import Dict, List, Any, Generator
import os 
from dotenv import load_dotenv
from tools import TOOL_FUNCTIONS, TOOL_SCHEMAS
import streamlit as st

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SYSTEM_PROMPT = """
 
            You are a Master Chef and Recipe Recommender Agent. Your goal is to help users find recipes 
        based on the ingredients that they tell you they have on hand and based on the specifications of the user (e.g. nutrition optimization, diet preferences, allergies and intolerances).
            For EVERY request, this is your process:
            1. ALWAYS call get_recipes first with the user's ingredients (and any allergens or ingredients they want to exclude).
            2. If get_recipes returns an empty list, DO NOT give up. Broaden your search by trying again with just 1 main ingredient.

            3. From the results, call get_missing_ingredients so you know what the user has vs. needs and get_nutrition_summary.
            4. ALWAYS pick the top 3 recipes based on ingredient overlap and nutrition facts (if user has nutrition specifications) and call get_recipes for those 3.
            5. Present your 3 recommendations clearly:
               - Recipe name
               - What Ingredients they already have
               - What's missing and how to substitute if possible
               - Adapted instructions scaled to their quantities

            KEY RULES:
            - Adapt recipes to user's actual quantities - don't just paste the original recipe.
            - If an ingredient is missing, suggest a realistic substitute from common pantry staples.
            - If the user specifies dietary restrictions (low-sugar, vegan, gluten-free, etc.), filter and flag accordingly.
            - Be conversational and encouraging - cooking with what you have is a skill
            - ALWAYS explain your reasoning before executing tool calls or if you have to resort to inventing a custom recipe.

            - ALWAYS use the `thought` parameter in your tool calls to explain your reasoning before executing them.   
            - If get_recipes returns no results, explain in your thought parameter exactly which ingredients made it difficult and how you are substituting them to create a custom recipe instead."
"""
class Agent():
    def __init__(self):
        #self.name = name 
        #self.role = role
        #self.tools = {tool.__name__: tool for tool in tools}
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.last_run_metadata = {"steps": 0, "tool_names": []}
        self.current_run_logs = []
    # incase reset needed
    def reset(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.last_run_metadata = {"steps": 0, "tool_names": []}
        self.current_run_logs = []
    # actual agent loop
    def chat(self, message: str) -> Generator[str, None, None]:
        self.messages.append({"role": "user", "content": message})
        steps = 0 
        # track metadata for logging and evaluation
        self.last_run_metadata['steps'] = 0
        # enter agent tool loop
        while True:
            steps += 1
            self.last_run_metadata['steps'] += 1
            # generate actual agent response
            response = client.chat.completions.create(model = "gpt-4.1-mini", messages = self.messages, 
                            tools = TOOL_SCHEMAS, 
                            tool_choice = "auto")
            # check if llm wants to talk or act
            if not response.choices[0].message.tool_calls:
                content = response.choices[0].message.content
                # add to history
                self.messages.append({"role": "assistant", "content": content})
                # Yield in chunks to simulate a stream for the UI
                chunk_size = 20
                for i in range(0, len(content), chunk_size):
                    yield content[i:i+chunk_size]
                break
            else:
                # append and print action
                self.messages.append(response.choices[0].message)
                print(response.choices[0].message)
                # if tool call
                for tool_call in response.choices[0].message.tool_calls:
                    # basically run or execute this tool 
                    function_name = tool_call.function.name
                    # parse JSON string into dict
                    args = json.loads(tool_call.function.arguments)
                    
                    # Extract the thought process and log it so we can see how it's deciding
                    thought = args.pop("thought", None)
                    if thought:
                        st.session_state.logs.append({
                            "action": f"Thought ({function_name})",
                            "result": thought
                        })
                    # call tool
                    try:
                        fn = TOOL_FUNCTIONS[function_name]
                        result = fn(**args)
                    except Exception as e:
                        result = f"Error: {str(e)}"
                    # log it and display in streamlit 
                    log_entry = {"action": function_name, "result": result}
                    self.current_run_logs.append(log_entry)
                    self.last_run_metadata["tool_names"].append(function_name)
                    st.session_state.logs.append({
                    "action": function_name,
                    "result": json.dumps(result, indent=2)
                    })
                    self.messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result)})
    
