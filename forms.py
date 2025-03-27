from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField,  SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', 
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ExpenseForm(FlaskForm):
    category = SelectField('Category', choices=[
        ('', 'Select Category'),
        ('Food', 'Food'),
        ('Transport', 'Transport'),
        ('Entertainment', 'Entertainment'),
        ('Healthcare', 'Healthcare'),
        ('Utilities', 'Utilities'),
        ('Shopping', 'Shopping'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    submit = SubmitField('Submit')

class BudgetForm(FlaskForm):
    category = SelectField('Category', choices=[
        ('Food', 'Food'),
        ('Transport', 'Transport'),
        ('Entertainment', 'Entertainment'),
        ('Healthcare', 'Healthcare'),
        ('Utilities', 'Utilities'),
        ('Shopping', 'Shopping'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    limit_amount = FloatField('Budget Limit', validators=[DataRequired(), NumberRange(min=0, message="Amount must be positive")])
    submit = SubmitField('Set Budget')

class SavingsPlanForm(FlaskForm):
    goal_name = StringField('Goal Name', validators=[DataRequired()])
    target_amount = FloatField('Target Amount', validators=[DataRequired(), NumberRange(min=0, message="Amount must be positive")])
    saved_amount = FloatField('Saved Amount', validators=[NumberRange(min=0, message="Amount must be positive")])
    submit = SubmitField('Save Plan')

class InvestmentForm(FlaskForm):
    asset_name = StringField('Asset Name', validators=[DataRequired()])
    invested_amount = FloatField('Invested Amount', validators=[DataRequired(), NumberRange(min=0, message="Amount must be positive")])
    risk_level = SelectField('Risk Level', choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High')
    ], validators=[DataRequired()])
    submit = SubmitField('Save Investment')
    
class ChatbotForm(FlaskForm):
    user_query = StringField('Ask me anything...', validators=[DataRequired()])
    submit = SubmitField('Ask')
