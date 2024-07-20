from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import requests
import json
from datetime import datetime
import os

global wave_number
wave_number=0

app = Flask(__name__)

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'your-database-url')
API_KEY = os.getenv('SPOONACULAR_API_KEY', 'bdbc6045a8d941a88fd09e1e443ff33b')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    preferences = db.relationship('FoodPreference', backref='user', lazy=True)

class FoodPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    preference = db.Column(db.String(120), nullable=False)

class UserChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_id = db.Column(db.Integer, nullable=False)
    food_title = db.Column(db.String(120), nullable=False)
    food_image = db.Column(db.String(250), nullable=False)
    cuisine = db.Column(db.PickleType, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    

    def __init__(self, user_id, food_id, food_title, food_image, cuisine):
        self.user_id = user_id
        self.food_id = food_id
        self.food_title = food_title
        self.food_image = food_image
        self.cuisine = cuisine

# Create tables
with app.app_context():
    db.drop_all()  # Drop all tables to ensure a clean slate
    db.create_all()  # Create all tables

@app.route('/signup', methods=['GET','POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if User.query.filter_by(username=username).first():
        return jsonify({"message": "User already exists"}), 400
    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

# User Login
@app.route('/signin', methods=['GET','POST'])
def signin():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username, password=password).first()
    if not user:
        return jsonify({"message": "Invalid credentials"}), 401
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token), 200

# Foodie Test
@app.route('/foodie_test', methods=['GET','POST'])
@jwt_required()
def foodie_test():
    user_id = get_jwt_identity()
    data = request.get_json()
    preferences = data.get('preferences')
    for pref in preferences:
        new_pref = FoodPreference(user_id=user_id, preference=pref)
        db.session.add(new_pref)
    db.session.commit()
    return jsonify({"message": "Preferences saved successfully"}), 201


@app.route('/get_ingredients', methods=['GET'])
@jwt_required()
def get_ingredients():
    api_key = API_KEY
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.get(f'https://api.spoonacular.com/food/ingredients', headers=headers, params={'apiKey': api_key})

    print(response)

    if response.status_code != 200:
        return jsonify({"message": "Error fetching ingredients"}), response.status_code

    try:
        ingredients = response.json()
        organized_ingredients = {}
        for ingredient in ingredients:
            category = ingredient.get('aisle', 'Miscellaneous')
            if category not in organized_ingredients:
                organized_ingredients[category] = []
            organized_ingredients[category].append({
                'id': ingredient['id'],
                'name': ingredient['name']
            })
        return jsonify(organized_ingredients), 200
    except Exception as e:
        return jsonify({"message": "Error processing ingredients", "error": str(e)}), 500

@app.route('/get_recipes', methods=['GET','POST'])
@jwt_required()
def get_recipes():
    user_id = get_jwt_identity()
    data = request.get_json()
    ingredients = data.get('ingredients')

    if not isinstance(ingredients, list):
        return jsonify({"message": "Ingredients must be a list"}), 400

    preferences = FoodPreference.query.filter_by(user_id=user_id).all()
    preferences_list = [pref.preference for pref in preferences]

    api_key = API_KEY
    headers = {
        'Content-Type': 'application/json'
    }
    params = {
        'apiKey': api_key,
        'ingredients': ','.join(ingredients),
        'number': 10,
        'ranking': 1
    }
    response = requests.get('https://api.spoonacular.com/recipes/findByIngredients', headers=headers, params=params)
    
    try:
        recipes = response.json()
    except ValueError:
        return jsonify({"message": "Error parsing response from Spoonacular API"}), 500

    if not isinstance(recipes, list):
        return jsonify({"message": "Unexpected response format from Spoonacular API", "response": recipes}), 500
    
    filtered_recipes = []
    for recipe in recipes:
        if recipe.get('missedIngredientCount', 0) == 0:
            matches_preferences = any(pref in recipe.get('title', '') for pref in preferences_list)
            if matches_preferences:
                filtered_recipes.append(recipe)

        if len(filtered_recipes) == 0:
            from groq import Groq

            client = Groq()
            completion = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {
                        "role": "user",
                        "content": f"Create as many recipes as possible using the following ingredients: {','.join(ingredients)}, and make sure each recipe fits at least one of these cuisines: {','.join(preferences_list)}. Your response should be just the recipe name, measurements of ingredients, and the recipe steps. Don't type any other text in your response. Don't say \"Here are the recipes,\" just say the recipes"
                    },
                    {
                        "role": "assistant",
                        "content": "**Italian Chicken and Rice**\n\n* 1 lb chicken, 2 cups rice, 1 tomato, 1 tsp salt, 1 tsp pepper, 2 cups water\n* 1. Heat water in a pot and add salt. Bring to a boil and then add rice. Reduce heat and cover for 18-20 minutes or until cooked.\n* 2. Grill or sauté chicken with pepper until cooked through.\n* 3. Chop tomato and add to cooked rice. Serve with chicken on top.\n\n**Mexican Chicken and Tomato Rice Bowl**\n\n* 1 lb chicken, 1 cup rice, 2 tomatoes, 1 tsp salt, 1 tsp pepper, 1 cup water\n* 1. Cook rice with salt and water in a pot until done.\n* 2. Grill or sauté chicken with pepper until cooked through.\n* 3. Sauté diced tomatoes with salt and pepper. Serve on top of cooked rice with chicken.\n\n**Chicken and Rice Fritters (Italian-Style)**\n\n* 1 lb chicken, 1 cup rice, 1 tomato, 1 tsp salt, 1 tsp pepper, 1 cup water\n* 1. Cook rice with salt and water in a pot until done.\n* 2. Chop cooked chicken and mix with cooked rice, diced tomato, salt, and pepper.\n* 3. Shape into patties and fry in a pan until crispy and golden.\n\n**Arroz con Pollo (Mexican-Style Chicken and Rice)**\n\n* 1 lb chicken, 2 cups rice, 1 tomato, 1 tsp salt, 1 tsp pepper, 2 cups water\n* 1. Cook rice with salt and water in a pot until done.\n* 2. Grill or sauté chicken with pepper until cooked through.\n* 3. Add diced tomato to cooked rice and mix well. Serve with chicken on top.\n\n**Tomato and Chicken Rice Casserole (Italian-Inspired)**\n\n* 1 lb chicken, 1 cup rice, 2 tomatoes, 1 tsp salt, 1 tsp pepper, 1 cup water\n* 1. Cook rice with salt and water in a pot until done.\n* 2. Grill or sauté chicken with pepper until cooked through.\n* 3. Mix cooked rice with diced tomatoes, chicken, salt, and pepper. Transfer to a baking dish and bake at 350°F for 20-25 minutes."
                    }
                ],
                temperature=1,
                max_tokens=1024,
                top_p=1,
                stream=True,
                stop=None,
            )

            for chunk in completion:
                print(chunk.choices[0].delta.content or "", end="")

        
            return jsonify({"message": "No matching recipes found. Here's are some AI generated recipes that you might like instead:", "generated_recipe": completion}), 200
      
    return jsonify(filtered_recipes), 200

    # Print the filtered recipes for debugging
    print("Filtered Recipes:")
    print(filtered_recipes)
      
    return jsonify(filtered_recipes), 200

import random

@app.route('/random_food_choices', methods=['GET'])
@jwt_required()
def random_food_choices():
    user_id = get_jwt_identity()
    wave_number+=1
    # Check if user already has preferences
    user_preferences = FoodPreference.query.filter_by(user_id=user_id).first()
    if user_preferences:
        return jsonify({"message": "User already has preferences"}), 200

    wave = int(request.args.get('wave', 1))
    
    response = requests.get(
        'https://api.spoonacular.com/recipes/random',
        params={
            'number': 4,
            'apiKey': API_KEY
        }
    )

    if response.status_code != 200:
        return jsonify({"message": "Error fetching random foods"}), response.status_code

    random_foods = response.json().get('recipes', [])
    choices = [
        {
            'id': food.get('id', 'N/A'),
            'title': food.get('title', 'No Title'),
            'image': food.get('image'),  # Default image if not present
            'cuisine': food.get('cuisines', [])
        }
    for food in random_foods]

    return jsonify({"wave": wave, "choices": choices}), 200

@app.route('/store_choice', methods=['POST'])
@jwt_required()
def store_choice():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    selected_food = data.get('selected_food')

    if not selected_food:
        return jsonify({"message": "No food choice provided"}), 400

    # Store the current choice
    choice = UserChoice(
        user_id=current_user_id,
        food_id=selected_food['id'],
        food_title=selected_food['title'],
        food_image=selected_food['image'],
        cuisine=selected_food['cuisine'],
    )
    db.session.add(choice)
    db.session.commit()

    # Fetch all choices by the user
    user_choices = UserChoice.query.filter_by(user_id=current_user_id).all()
    cuisine_count = {}
    taste_profile_count = {}

    for choice in user_choices:
        for cuisine in choice.cuisine:
            if cuisine not in cuisine_count:
                cuisine_count[cuisine] = 0
            cuisine_count[cuisine] += 1

        # Fetch taste profile for each food choice
        taste_response = requests.get(
            f"https://api.spoonacular.com/recipes/{choice.food_id}/tasteWidget.json",
            params={'apiKey': 'bdbc6045a8d941a88fd09e1e443ff33b'}
        )
        if taste_response.status_code == 200:
            taste_data = taste_response.json()
            for taste, value in taste_data.items():
                if taste not in taste_profile_count:
                    taste_profile_count[taste] = 0
                taste_profile_count[taste] += value

    # Determine top 3 cuisines
    sorted_cuisines = sorted(cuisine_count.items(), key=lambda item: item[1], reverse=True)

    if wave_number == 14:
        top_cuisines = [cuisine for cuisine, count in sorted_cuisines[:3]]
        for pref in top_cuisines:
            cuisine_pref = FoodPreference(user_id=current_user_id, preference=pref)
            db.session.add(cuisine_pref)
        db.session.commit()

    # Determine top 7 taste profiles
    sorted_taste_profiles = sorted(taste_profile_count.items(), key=lambda item: item[1], reverse=True)

    if wave_number == 14:
        top_taste_profiles = [taste for taste, count in sorted_taste_profiles[:7]]
        for pref in top_taste_profiles:
            taste_pref = FoodPreference(user_id=current_user_id, preference=pref)
            db.session.add(taste_pref)
        db.session.commit()

    return jsonify({
        "message": "Choice stored successfully",
        "top_cuisines": top_cuisines,
        "top_taste_profiles": top_taste_profiles
    }), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

