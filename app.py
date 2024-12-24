from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import random

# Initialize the app and databasea
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://foodie_avwx_user:Xd4W4biEpvq7nfUhxu4X3ZMIWjkE5ECT@dpg-ctl2rj2j1k6c73cthtl0-a/foodie_avwx'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    preferences = db.Column(db.String(512), nullable=True)
    ingredients = db.Column(db.String(512), nullable=True)

# Initialize the database
db.create_all()

# Load the RecipeNLG dataset
recipes = pd.read_csv('RecipeNLG_dataset.csv')

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data['username']
    password = data['password']

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()
    username = data['username']
    password = data['password']

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Invalid username or password'}), 401

    return jsonify({'message': 'User signed in successfully'}), 200

@app.route('/quiz', methods=['POST'])
def quiz():
    data = request.get_json()
    username = data['username']
    preferences = data['preferences']  # Expecting a comma-separated string

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    user.preferences = preferences
    db.session.commit()

    return jsonify({'message': 'Preferences updated successfully'}), 200

@app.route('/select-ingredients', methods=['POST'])
def select_ingredients():
    data = request.get_json()
    username = data['username']
    ingredients = data['ingredients']  # Expecting a comma-separated string

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    user.ingredients = ingredients
    db.session.commit()

    return jsonify({'message': 'Ingredients updated successfully'}), 200

@app.route('/get-recipes', methods=['GET'])
def get_recipes():
    username = request.args.get('username')
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    if not user.ingredients:
        return jsonify({'message': 'No ingredients selected'}), 400

    selected_ingredients = user.ingredients.split(',')
    user_preferences = user.preferences.split(',') if user.preferences else []

    # Filter recipes based on ingredients
    filtered_recipes = recipes[recipes['ingredients'].apply(lambda x: all(ing in x for ing in selected_ingredients))]

    # Further filter recipes based on preferences
    if user_preferences:
        filtered_recipes = filtered_recipes[filtered_recipes['cuisine'].isin(user_preferences)]

    # Select a random subset of recipes
    result = filtered_recipes.sample(n=min(10, len(filtered_recipes))).to_dict(orient='records')

    return jsonify({'recipes': result}), 200

if __name__ == '__main__':
    app.run(debug=True)
