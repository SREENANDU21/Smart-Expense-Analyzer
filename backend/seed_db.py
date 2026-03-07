from app import app, db
from models import Expense
from datetime import datetime, timedelta
import random

categories = ['Fuel', 'Salary', 'Maintenance', 'Rent', 'Utilities', 'Miscellaneous']
descriptions = {
    'Fuel': ['Diesel for van', 'Petrol for car', 'Gas station'],
    'Salary': ['Driver salary', 'Staff payment', 'Manager wages'],
    'Maintenance': ['Tire replacement', 'Oil change', 'Vehicle service'],
    'Rent': ['Office rent', 'Warehouse lease'],
    'Utilities': ['Electricity bill', 'Water bill', 'Internet connection'],
    'Miscellaneous': ['Office supplies', 'Coffee', 'Stationery']
}

def seed_database():
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # Generate some expenses for the last 6 months
        today = datetime.now()
        expenses = []
        for i in range(180): # 6 months
            date = today - timedelta(days=i)
            # Add 1-3 expenses per day
            for _ in range(random.randint(1, 3)):
                cat = random.choice(categories)
                desc = random.choice(descriptions[cat])
                amount = round(random.uniform(50, 1500), 2)
                
                if cat == 'Rent':
                    amount = round(random.uniform(2000, 5000), 2)
                if cat == 'Salary':
                    amount = round(random.uniform(1000, 3000), 2)
                    
                expense = Expense(
                    date=date.date(),
                    amount=amount,
                    category=cat,
                    description=desc
                )
                db.session.add(expense)
        
        db.session.commit()
        print("Database seeded completely!")

if __name__ == '__main__':
    seed_database()
