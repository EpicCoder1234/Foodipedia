from flask import Flask, request, jsonify
import pandas as pd

# Load the recipes dataset
recipes_df = pd.read_csv('recipes.csv')

app = Flask(__name__)

# Endpoint for filtering recipes by ingredients
@app.route('/filter-recipes', methods=['POST'])
def filter_recipes_by_ingredients():
    # Get the ingredients from the request
    data = request.get_json()
    print("Received JSON data:", data)  # Print the JSON data received
    requested_ingredients = data.get('ingredients', [])
    print("Requested ingredients:", requested_ingredients)  # Print the ingredients list extracted

    # Normalize requested ingredients for comparison
    normalized_requested_ingredients = sorted([ingredient.strip().lower().strip('"') for ingredient in requested_ingredients])
    print("Normalized requested ingredients:", normalized_requested_ingredients)

    # Print normalized ingredients for the first 5 recipes for debugging
    for i, recipe in recipes_df.iterrows():
        if i >= 5:
            break
        recipe_ingredients = [ingredient.strip().lower().strip('"') for ingredient in recipe['RecipeIngredientParts'].strip("c()").split(", ")]
        print(f"Recipe {i + 1} - {recipe['Name']}:")
        print("Recipe ingredients:", sorted(recipe_ingredients))

    # Filter recipes that contain exactly the requested ingredients
    filtered_recipes = []
    for _, recipe in recipes_df.iterrows():
        # Normalize recipe ingredients for comparison
        recipe_ingredients = [ingredient.strip().lower().strip('"') for ingredient in recipe['RecipeIngredientParts'].strip("c()").split(", ")]
        
        # Check if the recipe ingredients match the requested ingredients exactly
        if sorted(recipe_ingredients) == normalized_requested_ingredients:
            filtered_recipes.append({
                'RecipeId': recipe['RecipeId'],
                'Name': recipe['Name'],
                'AuthorName': recipe['AuthorName'],
                'CookTime': recipe['CookTime'],
                'PrepTime': recipe['PrepTime'],
                'TotalTime': recipe['TotalTime'],
                'DatePublished': recipe['DatePublished'],
                'Description': recipe['Description'],
                'Images': recipe['Images'],
                'RecipeCategory': recipe['RecipeCategory'],
                'Keywords': recipe['Keywords'],
                'RecipeIngredientParts': recipe['RecipeIngredientParts'],
                'AggregatedRating': recipe['AggregatedRating'],
                'ReviewCount': recipe['ReviewCount'],
                'Calories': recipe['Calories'],
                'FatContent': recipe['FatContent'],
                'SaturatedFatContent': recipe['SaturatedFatContent'],
                'CholesterolContent': recipe['CholesterolContent'],
                'SodiumContent': recipe['SodiumContent'],
                'CarbohydrateContent': recipe['CarbohydrateContent'],
                'FiberContent': recipe['FiberContent'],
                'SugarContent': recipe['SugarContent'],
                'ProteinContent': recipe['ProteinContent'],
                'RecipeServings': recipe['RecipeServings'],
                'RecipeYield': recipe['RecipeYield'],
                'RecipeInstructions': recipe['RecipeInstructions']
            })

    return jsonify({'recipes': filtered_recipes})

if __name__ == '__main__':
    app.run(debug=True)
