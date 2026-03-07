from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import os
import numpy as np
from sklearn.linear_model import LinearRegression

app = Flask(__name__)
CORS(app)

# Database config
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

from models import Expense
from ml_utils import predict_category, predict_next_month

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    data = request.json
    try:
        new_expense = Expense(
            amount=data['amount'],
            category=data['category'],
            description=data.get('description', '')
        )
        # Parse date if provided
        if 'date' in data and data['date']:
            # Assuming 'YYYY-MM-DD'
            new_expense.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        db.session.add(new_expense)
        db.session.commit()
        return jsonify(new_expense.to_dict()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    return jsonify([e.to_dict() for e in expenses])

@app.route('/api/classify', methods=['POST'])
def classify_expense():
    data = request.json
    description = data.get('description', '')
    category = predict_category(description)
    return jsonify({"category": category})

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    expenses = Expense.query.all()
    
    # Simple category-wise spending
    category_totals = {}
    for e in expenses:
        category_totals[e.category] = category_totals.get(e.category, 0) + e.amount
        
    return jsonify({
        "category_totals": category_totals
    })

@app.route('/api/predict', methods=['GET'])
def get_prediction():
    expenses = Expense.query.order_by(Expense.date).all()
    
    if not expenses:
        return jsonify({"predicted_amount": 0.0, "message": "No data to predict."})

    min_date = expenses[0].date
    max_date = expenses[-1].date
    timespan = (max_date - min_date).days + 1
    total_amount = sum(e.amount for e in expenses)

    # If less than 30 days of data, simply extrapolate the daily average to a 30-day month
    if timespan < 30:
        daily_avg = total_amount / timespan
        predicted_amount = daily_avg * 30
        return jsonify({"predicted_amount": predicted_amount, "message": "Extrapolated from daily average (less than 1 month data)."})

    # Group expenses by year-month to get monthly totals
    monthly_totals = {}
    for e in expenses:
        month_key = e.date.strftime('%Y-%m')
        monthly_totals[month_key] = monthly_totals.get(month_key, 0) + e.amount
    
    sorted_months = sorted(monthly_totals.keys())
    
    import calendar
    from datetime import date
    
    today = date.today()
    current_month_key = today.strftime('%Y-%m')
    
    # Handle the incomplete current month which skews linear regression downwards
    if current_month_key in monthly_totals and current_month_key == sorted_months[-1]:
        day_of_month = today.day
        if day_of_month < 28: # If not end of month
            _, days_in_month = calendar.monthrange(today.year, today.month)
            # Extrapolate current incomplete month to its full projected value
            extrapolated = (monthly_totals[current_month_key] / day_of_month) * days_in_month
            monthly_totals[current_month_key] = extrapolated

    if len(monthly_totals) < 2:
        return jsonify({"predicted_amount": float(list(monthly_totals.values())[0]), "message": "Need data from multiple months for trend analysis."})
        
    def months_since(d_str, origin_str):
        y, m = map(int, d_str.split('-'))
        oy, om = map(int, origin_str.split('-'))
        return (y - oy) * 12 + (m - om)

    origin = sorted_months[0]
    
    # Prepare data for Linear Regression based on months elapsed
    X = np.array([[months_since(m, origin)] for m in sorted_months])
    y = np.array([monthly_totals[m] for m in sorted_months])
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict for the *next* month 
    last_month_str = sorted_months[-1]
    next_month_idx = months_since(last_month_str, origin) + 1
    
    predicted_amount = float(model.predict([[next_month_idx]])[0])
    
    # Blend regression with a moving average to soften extreme slopes caused by few data points
    if len(sorted_months) <= 3:
        avg_monthly = sum(y) / len(y)
        predicted_amount = (predicted_amount + avg_monthly) / 2
    
    # Prevent negative predictions
    if predicted_amount < 0:
        predicted_amount = sum(y) / len(y)
        
    return jsonify({"predicted_amount": predicted_amount})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
