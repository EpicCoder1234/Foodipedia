from flask import Flask, request, jsonify
import pickle
import numpy as np

app = Flask(__name__)

# Load the trained model
with open('model/model.pkl', 'rb') as f:
    model = pickle.load(f)

def convert_food_to_feature(food):
    # Implement your conversion logic here
    return food  # Example: this should be the processed feature

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    user_foods = data['foods']
    
    # Process user_foods to the format your model expects
    feature_vector = [convert_food_to_feature(food) for food in user_foods]
    
    # Predict cuisine type
    prediction = model.predict([feature_vector])
    
    return jsonify({'predicted_cuisine': prediction[0]})

if __name__ == '__main__':
    app.run(debug=True)
