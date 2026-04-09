import json
import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from agent import Agent 

load_dotenv()
client = OpenAI()
# LLM as judge prompt
JUDGE_PROMPT = """
You are a Senior Data Auditor. Grade this agent's response based on:
1. Grounding (1-5): Did it use ONLY the ingredients the tools provided?
2. Constraint (1-5): Did it follow dietary rules (Vegan, No Nuts, Allergens)?
3. Edibility (1-5): Is this a real, logical recipe?

Return ONLY JSON: {"grounding": int, "constraints": int, "edibility": int, "justification": str}
"""

# --- evaluation ---
def run_benchmark(test_file="data/tests.json"):
    agent = Agent()
    with open(test_file, "r") as f:
        test_cases = json.load(f)
    
    results = []

    for case in test_cases:
        print(f"Running Test {case['id']}: {case['input'][:30]}...")
        
        # Track "Architectural Efficiency" (Steps)
        agent.reset() #start fresh for every test
        full_response = ""
        
        # run the agent and capture the output
        for chunk in agent.chat(case['input']):
            full_response += chunk
        
        # Track metrics from the agent instance
        steps = agent.last_run_metadata.get('steps', 0)
        tool_calls = agent.last_run_metadata.get('tool_names', [])

        # Call the judge to get  scores
        judge_output = client.chat.completions.create(
            model="gpt-4o", # use a smarter model to grade smaller model
            messages=[
                {"role": "system", "content": JUDGE_PROMPT},
                {"role": "user", "content": f"Query: {case['input']}\nResponse: {full_response}\nLogs: {agent.current_run_logs}"}
            ],
            response_format={"type": "json_object"}
        )
        
        scores = json.loads(judge_output.choices[0].message.content)
        
        # Combine everything into one record
        results.append({
            "id": case['id'],
            "steps": steps,
            "grounding_score": scores['grounding'],
            "constraint_score": scores['constraints'],
            "success": 1 if scores['edibility'] >= 4 else 0,
            "tool_sequence": " -> ".join(tool_calls)
        })

    return results

# --- report generator ---
def generate_eval_report(results):
    df = pd.DataFrame(results)
    
    # Calculate your Quantitative Metrics
    tsr = df['success'].mean() * 100
    avg_steps = df['steps'].mean()
    avg_grounding = df['grounding_score'].mean()

    # Print a summary for your video
    print("\n" + "="*30)
    print("FINAL AGENT EVALUATION")
    print("="*30)
    print(f"Task Success Rate (TSR): {tsr:.1f}%")
    print(f"Mean Steps to Resolution: {avg_steps:.2f}")
    print(f"Average Grounding Score: {avg_grounding:.2f}/5.0")
    
    # Save to CSV 
    df.to_csv("eval_results.csv", index=False)

if __name__ == "__main__":
    raw_results = run_benchmark()
    generate_eval_report(raw_results)