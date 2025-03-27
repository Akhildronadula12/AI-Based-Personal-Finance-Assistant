from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
from forms import RegisterForm, LoginForm, ExpenseForm, BudgetForm, SavingsPlanForm, InvestmentForm, ChatbotForm
from flask_wtf.csrf import CSRFProtect
import matplotlib.pyplot as plt
import io
import base64
from sqlalchemy import func
import requests
import json
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
csrf = CSRFProtect(app)


### <----------------- Models ------------------------>
# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

# Expense Model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=db.func.current_timestamp())

# Budget Model
class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    limit_amount = db.Column(db.Float, nullable=False)

# Savings Plan Model
class SavingsPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    goal_name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    saved_amount = db.Column(db.Float, default=0.0)

# Investment Model
class Investment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    asset_name = db.Column(db.String(100), nullable=False)
    invested_amount = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(50))

### <----------------- Chatbot Route ------------------------>###
# Mistral API settings
MISTRAL_API_KEY = ""
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

def use_mistral_ai(prompt):
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistral-small",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Please give me a financial recommendation based on my data."}
        ]
    }

    response = requests.post(MISTRAL_API_URL, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code} - {response.text}"

@app.route('/chatbot', methods=['POST'])
@login_required
def chatbot():
    user_query = request.json.get('query')

    if not user_query:
        return jsonify({"message": "No query provided"}), 400

    # Fetching financial data (example data structure, adjust as needed)
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    savings_plans = SavingsPlan.query.filter_by(user_id=current_user.id).all()
    investments = Investment.query.filter_by(user_id=current_user.id).all()

    # Calculate totals (add your calculation logic)
    total_expenses = sum(expense.amount for expense in expenses)
    total_budget_used = sum(budget.limit_amount for budget in budgets)
    total_savings = sum(savings_plan.saved_amount for savings_plan in savings_plans)
    total_savings_goal = sum(savings_plan.target_amount for savings_plan in savings_plans)
    total_investment = sum(investment.invested_amount for investment in investments)

    # Prepare the prompt with all queries included
    expense_details = "\n".join([f"- {expense.category}: ${expense.amount}" for expense in expenses])
    budget_details = "\n".join([f"- {budget.category}: ${budget.limit_amount}" for budget in budgets])
    savings_details = "\n".join([f"- {savings_plan.goal_name}: Saved ${savings_plan.saved_amount} (Goal: ${savings_plan.target_amount})" for savings_plan in savings_plans])
    investment_details = "\n".join([f"- {investment.asset_name}: ${investment.invested_amount}" for investment in investments])

    system_prompt = f"""
    You are a helpful financial assistant. Here is the financial data for the current user:

    Total Expenses: ${total_expenses}
    Total Budget Used: ${total_budget_used}
    Total Savings: ${total_savings} (Goal: ${total_savings_goal})
    Total Investments: ${total_investment}

    Detailed Information:

    Expenses:
    {expense_details}

    Budgets:
    {budget_details}

    Savings:
    {savings_details}

    Investments:
    {investment_details}

    User query: {user_query}

    Based on the above information, please provide a personalized response or recommendation.
    """

    # Get response from Mistral API
    ai_response = use_mistral_ai(system_prompt)

    return jsonify({"message": ai_response})

### <----------------- Login Manager ------------------------>
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

### <----------------- Routes ------------------------>
@app.route('/')
def home():
    return render_template('index.html')

### <----------------- Authentication Routes ------------------------>

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already exists. Please log in.", "danger")
            return redirect(url_for('login'))

        new_user = User(
            name=form.name.data,
            email=form.email.data,
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()

        flash("Account successfully created! You can now log in.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard')) 
        else:
            flash('Invalid credentials', 'danger')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

### <----------------- Dashboard Route ------------------------>
@app.route('/dashboard')
@login_required
def dashboard():
    # Fetching data for the logged-in user
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    savings_plans = SavingsPlan.query.filter_by(user_id=current_user.id).all()
    investments = Investment.query.filter_by(user_id=current_user.id).all()

    # Calculate Total Expenses
    total_expenses = sum(expense.amount for expense in expenses)
    
    # Calculate Budget usage
    total_budget_used = sum(budget.limit_amount for budget in budgets)

    # Calculate Savings Progress
    total_savings = sum(savings_plan.saved_amount for savings_plan in savings_plans)
    total_savings_goal = sum(savings_plan.target_amount for savings_plan in savings_plans)

    # Calculate Total Investment
    total_investment = sum(investment.invested_amount for investment in investments)

    # Plot Expense Distribution (example: Pie chart)
    categories = [expense.category for expense in expenses]
    expense_amounts = [expense.amount for expense in expenses]
    
    # Generate Pie Chart for Expenses
    fig, ax = plt.subplots()
    ax.pie(expense_amounts, labels=categories, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    
    # Save the pie chart to a BytesIO object and encode it to base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    pie_chart = base64.b64encode(img.getvalue()).decode('utf8')

    return render_template('dashboard.html',
                           username=current_user.name,
                           total_expenses=total_expenses,
                           total_budget_used=total_budget_used,
                           total_savings=total_savings,
                           total_savings_goal=total_savings_goal,
                           total_investment=total_investment,
                           pie_chart=pie_chart)

###<---------------------------- Expenses Routes ------------------------>

# Route to show all expenses for the logged-in user
@app.route('/expenses')
@login_required
def expenses():
    user_expenses = Expense.query.filter_by(user_id=current_user.id).all()
    return render_template('expenses.html', expenses=user_expenses)

# Route to create a new expense
@app.route('/expense/new', methods=['GET', 'POST'])
@login_required
def new_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        category = form.category.data  # Selected category from the dropdown
        amount = form.amount.data
        # Create new Expense object
        new_exp = Expense(user_id=current_user.id, category=category, amount=amount)
        db.session.add(new_exp)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expenses'))
    
    return render_template('new_expense.html', form=form)


# Route to update an expense
@app.route('/expense/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.user_id != current_user.id:
        flash('You are not authorized to edit this expense', 'danger')
        return redirect(url_for('expenses'))
    
    form = ExpenseForm(obj=expense)
    if form.validate_on_submit():
        expense.category = form.category.data
        expense.amount = form.amount.data
        # Optionally, update the date if needed
        # expense.date = datetime.now()

        db.session.commit()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('expenses'))
    
    return render_template('edit_expense.html', form=form, expense=expense)

# Route to delete an expense
@app.route('/expense/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.user_id != current_user.id:
        flash('You are not authorized to delete this expense', 'danger')
        return redirect(url_for('expenses'))

    # Create an empty form for CSRF protection
    form = ExpenseForm()

    if request.method == 'POST':
        db.session.delete(expense)
        db.session.commit()
        flash('Expense deleted successfully!', 'success')
        return redirect(url_for('expenses'))
    
    return render_template('confirm_delete_expense.html', expense=expense, form=form)

### <----------------- Budget Routes ------------------------>
@app.route('/budget')
@login_required
def budget():
    user_budgets = Budget.query.filter_by(user_id=current_user.id).all()
    return render_template('budgets.html', budgets=user_budgets)

@app.route('/budget/new', methods=['GET', 'POST'])
@login_required
def new_budget():
    form = BudgetForm()
    # Check if the user already has a budget for the selected category
    if form.validate_on_submit():
        existing_budget = Budget.query.filter_by(user_id=current_user.id, category=form.category.data).first()
        if existing_budget:
            flash('You already have a budget for this category.', 'danger')
            return redirect(url_for('budgets'))
        
        new_budget = Budget(
            user_id=current_user.id,
            category=form.category.data,
            limit_amount=form.limit_amount.data
        )
        db.session.add(new_budget)
        db.session.commit()
        flash('Budget created successfully!', 'success')
        return redirect(url_for('budget'))
    
    return render_template('new_budget.html', form=form)

@app.route('/budget/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_budget(id):
    budget = Budget.query.get_or_404(id)
    if budget.user_id != current_user.id:
        flash('You are not authorized to edit this budget', 'danger')
        return redirect(url_for('budget'))

    form = BudgetForm(obj=budget)
    if form.validate_on_submit():
        budget.category = form.category.data
        budget.limit_amount = form.limit_amount.data
        db.session.commit()
        flash('Budget updated successfully!', 'success')
        return redirect(url_for('budget'))

    return render_template('edit_budget.html', form=form, budget=budget)

@app.route('/budget/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_budget(id):
    budget = Budget.query.get_or_404(id)
    if budget.user_id != current_user.id:
        flash('You are not authorized to delete this budget', 'danger')
        return redirect(url_for('budget'))

    form = BudgetForm()  # CSRF protection

    if request.method == 'POST':
        db.session.delete(budget)
        db.session.commit()
        flash('Budget deleted successfully!', 'success')
        return redirect(url_for('budget'))

    return render_template('confirm_delete_budget.html', budget=budget, form=form)

### <----------------- Savings Plan Routes ------------------------>
# Route to see all savings plans
@app.route('/savings', methods=['GET'])
@login_required
def savings_plans():
    savings_plans = SavingsPlan.query.filter_by(user_id=current_user.id).all()
    return render_template('savings_plans.html', savings_plans=savings_plans)

# Route to create a new savings plan
@app.route('/savings/new', methods=['GET', 'POST'])
@login_required
def new_savings_plan():
    form = SavingsPlanForm()
    if form.validate_on_submit():
        savings_plan = SavingsPlan(
            goal_name=form.goal_name.data,
            target_amount=form.target_amount.data,
            saved_amount=form.saved_amount.data,
            user_id=current_user.id
        )
        db.session.add(savings_plan)
        db.session.commit()
        flash('Your savings plan has been created!', 'success')
        return redirect(url_for('savings_plans'))
    return render_template('create_savings_plan.html', form=form)

# Route to edit an existing savings plan
@app.route('/savings/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_savings_plan(id):
    savings_plan = SavingsPlan.query.get_or_404(id)
    if savings_plan.user_id != current_user.id:
        flash('You cannot edit this savings plan', 'danger')
        return redirect(url_for('savings_plans'))

    form = SavingsPlanForm()
    if form.validate_on_submit():
        savings_plan.goal_name = form.goal_name.data
        savings_plan.target_amount = form.target_amount.data
        savings_plan.saved_amount = form.saved_amount.data
        db.session.commit()
        flash('Your savings plan has been updated!', 'success')
        return redirect(url_for('savings_plans'))

    # Pre-fill the form with existing values
    form.goal_name.data = savings_plan.goal_name
    form.target_amount.data = savings_plan.target_amount
    form.saved_amount.data = savings_plan.saved_amount

    # Pass the savings_plan variable to the template
    return render_template('edit_savings_plan.html', form=form, savings_plan=savings_plan)


# Route to delete a savings plan
@app.route('/savings/delete/<int:id>', methods=['POST'])
@login_required
def delete_savings_plan(id):
    savings_plan = SavingsPlan.query.get_or_404(id)
    if savings_plan.user_id != current_user.id:
        flash('You cannot delete this savings plan', 'danger')
        return redirect(url_for('savings_plans'))

    db.session.delete(savings_plan)
    db.session.commit()
    flash('Your savings plan has been deleted.', 'success')
    return redirect(url_for('savings_plans'))



### <----------------- Investment Routes ------------------------>
# Route to view all investments
@app.route('/investments', methods=['GET'])
@login_required
def investments():
    form = InvestmentForm()
    investments = Investment.query.filter_by(user_id=current_user.id).all()
    return render_template('investments.html', investments=investments, form=form)

# Route to create a new investment
@app.route('/investments/new', methods=['GET', 'POST'])
@login_required
def new_investment():
    form = InvestmentForm()
    if form.validate_on_submit():
        investment = Investment(
            asset_name=form.asset_name.data,
            invested_amount=form.invested_amount.data,
            risk_level=form.risk_level.data,
            user_id=current_user.id
        )
        db.session.add(investment)
        db.session.commit()
        flash('Your investment has been added!', 'success')
        return redirect(url_for('investments'))
    return render_template('create_investment.html', form=form)

# Route to edit an existing investment
@app.route('/investments/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_investment(id):
    investment = Investment.query.get_or_404(id)
    if investment.user_id != current_user.id:
        flash('You cannot edit this investment', 'danger')
        return redirect(url_for('investments'))

    form = InvestmentForm()
    if form.validate_on_submit():
        investment.asset_name = form.asset_name.data
        investment.invested_amount = form.invested_amount.data
        investment.risk_level = form.risk_level.data
        db.session.commit()
        flash('Your investment has been updated!', 'success')
        return redirect(url_for('investments'))

    # Pre-fill the form with existing investment values
    form.asset_name.data = investment.asset_name
    form.invested_amount.data = investment.invested_amount
    form.risk_level.data = investment.risk_level

    return render_template('edit_investment.html', form=form)

# Route to delete an investment
@app.route('/investments/delete/<int:id>', methods=['POST'])
@login_required
def delete_investment(id):
    investment = Investment.query.get_or_404(id)
    if investment.user_id != current_user.id:
        flash('You cannot delete this investment', 'danger')
        return redirect(url_for('investments'))

    db.session.delete(investment)
    db.session.commit()
    flash('Your investment has been deleted.', 'success')
    return redirect(url_for('investments'))


### <----------------- Error Handlers ------------------------>
# 404 Error Handler
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

# 500 Error Handler
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()  # If it's a database-related issue, rollback any changes
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_unexpected_error(error):
    return render_template('500.html'), 500


### <----------------- Main ------------------------>
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
