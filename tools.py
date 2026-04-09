import requests 
import os 

API_KEY = os.getenv("RECIPE_API")
BASE_URL = "https://api.spoonacular.com"

"""Defining all tools agent can use"""

def get_recipes(ingredients, allergens: str = ""):
    # returns list of 10 recipes in database that has your ingredients with basic nutrition included
    params = {"includeIngredients": ingredients, 
              "fillIngredients": True,
              "apiKey": API_KEY, 
              "number": 10,
              "addRecipeNutrition": True, 
              "ignorePantry": True}
    if allergens:
        params['excludeIngredients'] = allergens
    # get api response
    response = requests.get(f"{BASE_URL}/recipes/complexSearch", params=params)
    data = response.json()
    results = [] 
    # go through results to filter / reduce size of output to llm 
    for r in data.get("results", []):
        nutrition_map = {}
        # only care about basic nutrition info
        for n in r.get("nutrition", {}).get("nutrients", []):
            if n["name"] in ("Calories", "Protein", "Fat", "Sugar", "Cholesterol", "Carbohydrates"):
                nutrition_map[n["name"]] = f"{round(n['amount'])} {n['unit']}"
        # what we want to return for future use
        results.append({
            "id": r["id"],
            "title": r['title'], 
            "usedIngredientCount": r.get("usedIngredientCount", 0), 
            "missedIngredientCount": r.get("missedIngredientCount", 0),
            "missedIngredients": [i["name"] for i in r.get("missedIngredients", [])],

            "nutrition": nutrition_map
        })
    return results

def get_recipe_details(recipe_id):
    # returns full ingredient list and nutrition facts for a recipe
    url = f"{BASE_URL}/recipes/{recipe_id}/information"
    params = {"apiKey": API_KEY, "includeNutrition": True}
    # get response
    response = requests.get(url, params=params)
    recipe = response.json()
    # get basics of ingredients
    ingredients = [
        {
            "name": ingredient["name"],
            "amount": ingredient["amount"],
            "unit": ingredient["unit"]}
        for ingredient in recipe.get("extendedIngredients", [])

    ]
    # get basics of nutrition
    nutrients = {
        n["name"]: f"{round(n['amount'])} {n['unit']}"
        for n in recipe.get("nutrition", {}).get("nutrients", [])
        if n["name"] in ("Calories", "Protein", "Fat", "Carbohydrates", "Sugar", "Fiber", "Sodium", "Cholesterol")
    }
    # return only stuff we care about
    return {
        "id": recipe_id, 
        "title": recipe.get("title", "Unknown"), 
        "servings": recipe.get("servings", 1), 
        "instructions": recipe.get("instructions", ""),
        "ingredients": ingredients,
        "nutrition_per_serving": nutrients, 
        "sourceUrl": recipe.get("sourceUrl", ""), 
        "image": recipe.get("image", "")
    }

def get_missing_ingredients(user_ingredients, recipe_id):
    # check what ingredients are in pantry vs in recipe
    details = get_recipe_details(recipe_id)
    # get ingredients of recipe
    recipe_ingredients = details["ingredients"]
    have = []
    missing = []
    # standardize info of our ingredients on hand
    pantry = {item.strip().lower() for item in user_ingredients}
    for ingredient in recipe_ingredients:
        # for ingredients, check if we have it matched in our pantry, if not add to missing list
        ingredient_name = ingredient["name"].lower()
        matched = any(p in ingredient_name or ingredient_name in p for p in pantry)
        entry = f"{ingredient['amount']} {ingredient['unit']} {ingredient['name']}".strip()
        if matched:
            have.append(entry)
        else:
            missing.append(entry)
    return {
        "recipe_title": details['title'], 
        "have": have, 
        "missing": missing, 
        "missing_count": len(missing),
    } 

def get_nutrition_summary(recipe_id):
    
    # return nutrition breakdown for a recipe per serving
    # Useful when the user asks about calories, macros, or dietary goals.
    
    details = get_recipe_details(recipe_id)
    # only return the nutrition info
    return {
        "recipe_title": details["title"], 
        "servings": details["servings"], 
        "nutrition_per_serving": details["nutrition_per_serving"], 
        "source_url": details["sourceUrl"], 
        "image_url": details["image"]
    }

# schemas of tools for agent 

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_recipes",
            "description": (
                "Search for recipes that use the user's ingredients."
                "Always call this first. Returns up to 10 recipe candidates with basic nutrition information."

            ),
            "parameters": {
                "type": "object", 
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Explain your reasoning or thought process before searching for these ingredients."
                    },
                    "ingredients": {
                        "type": "string", 
                        "description": "Comma separated list of ingredients the user has, e.g. 'banans,greek yogurt,oats'",
                    },
                    "allergens": {
                        "type": "string", 
                        "description": "Comma separated ingredients to exclude because of allergies and intolerances. Leave empty if none.",
                    },
                },
                "required": ['thought', 'ingredients'],
            },

        },
    },
    
    {
        "type": "function",
        "function": {
            "name": "get_recipe_details",
            "description": (
                "Returns the full ingredient list, quantities, instructions, and nutrition for a specific recipe."
                "Use this after get_recipes to see exact amounts before adapting to the user's pantry."

            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Explain why you are retrieving details for this specific recipe."
                    },
                    "recipe_id": {
                        "type": "integer", 
                        "description": "The numeric recipe ID returned by get_recipes.",
                        
                    },
                },
                "required": ['thought', 'recipe_id'],

            
                },
        },

    },
    {
        "type": "function",
        "function": {
            "name": "get_missing_ingredients",
            "description": (
                "Compare the user's pantry to a recipe and identify which ingredients they have vs. are missing."
                "Use this before recommending a recipe so you can tell the user exactly what to buy or substitute."

            ), 
            "parameters": {
                "type": "object", 
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Explain why you are comparing the pantry to this recipe."
                    },
                    "user_ingredients": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "List of ingredient names the user has on hand.",
                    },
                    "recipe_id": {
                        "type": "integer", 
                        "description": "The numeric recipe ID to check against.", 

                    },
                }, 
                "required": ['thought', 'user_ingredients', 'recipe_id'],
            },
        
            },

    }, 
    {
        "type": "function", 
        "function": {
            "name": "get_nutrition_summary",
            "description": (
                "Return a macro/calorie breakdown for a recipe per serving." 
                "Use to provide a user a summary of their nutrition information AND when considering what recipes to return if a user mentions nutrition goals, low-carb, low-sugar, high-protein, etc."
            ), 
            "parameters":{
                "type": "object", 
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Explain why you need the nutrition summary."
                    },
                    "recipe_id": {
                        "type": "integer", 
                        "description": "The numeric recipe ID to retrieve nutrition for.",
                    }, 
                }, 
                "required": ["thought", "recipe_id"],
                },
            },
    },

]

TOOL_FUNCTIONS = {
    "get_recipes": get_recipes, 
    "get_recipe_details": get_recipe_details, 
    "get_missing_ingredients": get_missing_ingredients, 
    "get_nutrition_summary": get_nutrition_summary, 

}