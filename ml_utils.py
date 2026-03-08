import os
import pickle
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline

models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models')

if not os.path.exists(models_dir):
    os.makedirs(models_dir)

CLASSIFIER_PATH = os.path.join(models_dir, 'classifier.pkl')
PREDICTOR_PATH = os.path.join(models_dir, 'predictor.pkl')

def train_classifier():
    # Synthetic dataset for expense classification
    data = {
        'description': [
            'diesel for van', 'petrol', 'fuel for truck', 'gas station',
            'driver salary', 'employee wages', 'manager pay', 'staff salary',
            'tire repair', 'oil change', 'truck service', 'engine maintenance',
            'office rent', 'warehouse lease', 'building rent',
            'electricity bill', 'water bill', 'internet service', 'utility bill',
            'office supplies', 'printing paper', 'coffee', 'miscellaneous items'
        ],
        'category': [
            'Fuel', 'Fuel', 'Fuel', 'Fuel',
            'Salary', 'Salary', 'Salary', 'Salary',
            'Maintenance', 'Maintenance', 'Maintenance', 'Maintenance',
            'Rent', 'Rent', 'Rent',
            'Utilities', 'Utilities', 'Utilities', 'Utilities',
            'Miscellaneous', 'Miscellaneous', 'Miscellaneous', 'Miscellaneous'
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Text classification pipeline
    model = make_pipeline(TfidfVectorizer(), MultinomialNB())
    model.fit(df['description'], df['category'])
    
    with open(CLASSIFIER_PATH, 'wb') as f:
        pickle.dump(model, f)
    print("Classification model trained and saved.")

def predict_category(description):
    try:
        with open(CLASSIFIER_PATH, 'rb') as f:
            model = pickle.load(f)
        return model.predict([description])[0]
    except FileNotFoundError:
        return "Miscellaneous"

def train_predictor():
    # Synthetic dataset for linear regression (predicting next month expense based on previous months)
    # X: month index (1, 2, 3...), Y: total expenses in that month
    # A small upward trend
    X = np.array([[1], [2], [3], [4], [5], [6]])
    y = np.array([20000, 21000, 20500, 22000, 22500, 23000])
    
    model = LinearRegression()
    model.fit(X, y)
    
    with open(PREDICTOR_PATH, 'wb') as f:
        pickle.dump(model, f)
    print("Prediction model trained and saved.")
    
def predict_next_month(month_index):
    try:
        with open(PREDICTOR_PATH, 'rb') as f:
            model = pickle.load(f)
        return float(model.predict([[month_index]])[0])
    except FileNotFoundError:
        return 0.0

if __name__ == "__main__":
    train_classifier()
    train_predictor()
