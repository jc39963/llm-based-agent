# 🍳 LLM-Based Recipe Agent

This project creates an intelligent cooking assistant that takes a list of ingredients you have at home and returns 1-3 highly curated recipes that you can cook right now. It adapts original recipes to match your actual quantities and dietary restrictions, making everyday cooking more accessible and reducing food waste.

Built using **OpenAI's GPT-4o-mini**, **Streamlit**, and the **Spoonacular API**.

## ✨ Features

- **Ingredient-Based Matching:** Finds real recipes using exactly what's already in your kitchen, if no recipes match your quantities, it will give ideas for what you can make.
- **Smart Substitutions:** Identifies missing ingredients and suggests realistic substitutions using common pantry staples.
- **Dietary & Nutritional Optimization:** Filters results based on user specifications (e.g., low-sugar, high-protein, vegan) and provides nutrition summaries per serving.
- **Transparent Reasoning:** Features a built-in logging system in the UI to display exactly which tools the agent is calling and what data it's fetching in real-time.

## 🛠️ Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/)
- **LLM:** [OpenAI](https://openai.com/) (`gpt-4o-mini`)
- **External APIs:** Spoonacular API
- **Language:** Python

## 📂 Project Structure

- `app.py`: The Streamlit frontend, featuring a chat interface and a sidebar for internal agent logs.
- `agent.py`: Defines the `Agent` class, handling conversation state, system prompting, tool selection, and simulated streaming.
- `tools.py`: Contains the external API integrations to Spoonacular, defining the functions and JSON schemas the agent uses to search recipes, get details, calculate missing ingredients, and fetch nutrition data.
- `eval.py`: Contains LLM as judge evaluation with benchmarking and scoring for:   

    1. Grounding (1-5): Did the agent use ONLY the ingredients the tools provided?
    2. Constraint (1-5): Did the agent follow dietary rules (Vegan, No Nuts, Allergens)?
    3. Edibility (1-5): Is this a real, logical recipe?

## 🚀 Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd llm-based-agent
   ```

2. **Install dependencies:**
   Ensure you have the required packages installed (you may want to use a virtual environment):
   ```bash
   pip install streamlit openai requests python-dotenv
   ```

3. **Set up Environment Variables:**
   Create a `.env` file in the root directory and add your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   RECIPE_API=your_spoonacular_api_key_here
   ```

4. **Run the Application:**
   ```bash
   streamlit run app.py
   ```
