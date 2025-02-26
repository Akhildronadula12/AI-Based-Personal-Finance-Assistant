import datetime
import os
import re
from typing import Dict, List, Optional

import openai  # Assuming OpenAI wrapper is used for Mistral AI
import pandas as pd

# --- Mistral AI Configuration ---
MISTRAL_API_KEY = 'Mistral_API_KEY'
openai.api_key = MISTRAL_API_KEY

# --- Categorizer Class with Mistral AI Integration ---
class Categorizer:
    def __init__(self):
        # Default categories
        self.default_categories = [
            'food', 'transport', 'entertainment', 
            'utilities', 'housing', 'health', 'miscellaneous'
        ]
    
    def categorize_expense(self, description: str) -> str:
        # Constructing Mistral AI Prompt
        prompt = (
            f"Categorize the following expense description into one of the categories: "
            f"{', '.join(self.default_categories)}.\n"
            f"Description: {description}\n"
            f"Category:"
        )
        
        try:
            # Sending request to Mistral AI
            response = openai.ChatCompletion.create(
                model="mistral-7b-chat",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.2
            )
            
            # Extracting category from the response
            category = response['choices'][0]['message']['content'].strip().lower()
            
            # Validate if the category is among default ones
            if category in self.default_categories:
                return category
            else:
                return 'miscellaneous'
        
        except Exception as e:
            print(f"Error with Mistral AI categorization: {e}")
            return 'miscellaneous'

# --- ExpenseManager Class ---
class ExpenseManager:
    def __init__(self, storage_file: str = "expenses.csv"):
        self.storage_file = storage_file
        self.categorizer = Categorizer()
        self.expenses = self.load_expenses()

    def capture_expense(self, date: str, description: str, amount: float) -> Dict:
        # Validate date format
        try:
            expense_date = datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD."}

        # Categorize the expense using Mistral AI
        category = self.categorizer.categorize_expense(description)
        
        # Capture expense details
        expense = {
            "date": expense_date.strftime("%Y-%m-%d"),
            "description": description,
            "amount": amount,
            "category": category
        }

        # Save expense
        self.save_expense(expense)
        return expense
    
    def save_expense(self, expense: Dict) -> None:
        # Save to CSV for now; can be replaced with DB in future
        df = pd.DataFrame([expense])
        if not os.path.isfile(self.storage_file):
            df.to_csv(self.storage_file, index=False)
        else:
            df.to_csv(self.storage_file, mode='a', header=False, index=False)
    
    def load_expenses(self) -> pd.DataFrame:
        # Load expenses from CSV
        if os.path.isfile(self.storage_file):
            return pd.read_csv(self.storage_file)
        else:
            return pd.DataFrame(columns=['date', 'description', 'amount', 'category'])

    def list_expenses(self) -> pd.DataFrame:
        return self.expenses

    def delete_expense(self, index: int) -> str:
        if index < 0 or index >= len(self.expenses):
            return "Invalid index."
        self.expenses = self.expenses.drop(index).reset_index(drop=True)
        self.expenses.to_csv(self.storage_file, index=False)
        return "Expense deleted successfully."

# --- AnomalyDetector Class ---
class AnomalyDetector:
    def __init__(self, threshold: float = 500.0):
        self.threshold = threshold

    def detect_anomalies(self, expenses: pd.DataFrame) -> List[str]:
        anomalies = []
        for idx, row in expenses.iterrows():
            if row['amount'] > self.threshold:
                anomalies.append(f"Large expense detected: {row['description']} - ${row['amount']}")
        return anomalies

# --- Main Functionality ---
def main():
    manager = ExpenseManager()
    detector = AnomalyDetector()

    print("\n--- AI-Based Personal Finance Assistant ---")
    while True:
        print("\nChoose an option:")
        print("1. Add Expense")
        print("2. List Expenses")
        print("3. Delete Expense")
        print("4. Detect Anomalies")
        print("5. Exit")

        choice = input("Enter your choice: ")
        if choice == '1':
            date = input("Enter date (YYYY-MM-DD): ")
            description = input("Enter description: ")
            try:
                amount = float(input("Enter amount: "))
                expense = manager.capture_expense(date, description, amount)
                if "error" in expense:
                    print(expense["error"])
                else:
                    print("Expense added successfully!")
            except ValueError:
                print("Invalid amount. Please enter a number.")
        
        elif choice == '2':
            expenses = manager.list_expenses()
            if expenses.empty:
                print("No expenses found.")
            else:
                print("\nExpense List:")
                print(expenses)
        
        elif choice == '3':
            expenses = manager.list_expenses()
            print(expenses)
            try:
                index = int(input("Enter the index of the expense to delete: "))
                result = manager.delete_expense(index)
                print(result)
            except ValueError:
                print("Invalid index. Please enter a number.")
        
        elif choice == '4':
            expenses = manager.list_expenses()
            anomalies = detector.detect_anomalies(expenses)
            if anomalies:
                print("\nAnomalies Detected:")
                for anomaly in anomalies:
                    print(anomaly)
            else:
                print("No anomalies found.")
        
        elif choice == '5':
            print("Exiting... Have a great day!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
