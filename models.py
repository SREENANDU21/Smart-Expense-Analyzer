from sqlalchemy import create_engine, Column, Integer, Date, Float, String
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Expense(Base):
    __tablename__ = 'expense'
    
    id = Column(Integer, primary_key=True)
    business_name = Column(String(100), nullable=False, default="Main Business")
    date = Column(Date, nullable=False, default=datetime.utcnow)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(String(200))
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d'),
            'amount': self.amount,
            'category': self.category,
            'description': self.description
        }

# Database setup
engine = create_engine('sqlite:///database.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
