import re
import datetime
from typing import List, Dict
import pandas as pd

# Simulating Mistral AI categorization (replace with actual Mistral AI integration)
def categorize_expense(description: str) -> str:
    categories = {
        'food': ['restaurant', 'grocery', 'dining'],
        'transport': ['bus', 'train', 'uber', 'taxi'],
        'entertainment': ['movie', 'concert', 'event'],
        'utilities': ['electricity', 'water', 'internet'],
        'housing': ['rent', 'mortgage'],
        'health': ['pharmacy', 'doctor', 'medication'],
    }
    
    for category, keywords in categories.items():
        if any(keyword in description.lower() for keyword in keywords):
            return category
    return 'miscellaneous'

# Simulating expense data input (either manual or uploaded receipt)
def capture_expense(date: str, description: str, amount: float) -> Dict:
    # Validate date format
    try:
        expense_date = datetime.datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}
    
    # Categorize the expense
    category = categorize_expense(description)
    
    # Capture expense details
    expense = {
        "date": expense_date,
        "description": description,
        "amount": amount,
        "category": category
    }
    
    return expense

# Simulating anomaly detection based on spending patterns (simple thresholding)
def detect_anomalies(expenses: pd.DataFrame) -> List[str]:
    threshold = 500  # Example threshold for large expenses
    anomalies = []
    
    for idx, row in expenses.iterrows():
        if row['amount'] > threshold:
            anomalies.append(f"Large expense detected: {row['description']} - ${row['amount']}")
    
    return anomalies


# Test the functions

# Sample Expenses List
expenses = [
    capture_expense("2025-01-01", "grocery shopping", 150.0),
    capture_expense("2025-01-02", "movie tickets", 20.0),
    capture_expense("2025-01-05", "electricity bill", 100.0),
    capture_expense("2025-01-10", "restaurant dining", 70.0),
    capture_expense("2025-01-12", "doctor appointment", 200.0),
    capture_expense("2025-01-15", "taxi ride", 30.0),
    capture_expense("2025-01-17", "hotel stay", 600.0)  # This could be considered an anomaly
]

# Convert to DataFrame for easier manipulation
df_expenses = pd.DataFrame(expenses)

# Anomaly Detection
anomalies = detect_anomalies(df_expenses)

# Output Anomalies
for anomaly in anomalies:
    print(anomaly)

# Output expense details
print("\nExpense Details:")
print(df_expenses)
