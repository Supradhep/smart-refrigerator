from flask import Flask, render_template, request, redirect, url_for, flash, session
import subprocess
import os
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai
from config import GEMINI_API_KEY
from datetime import datetime, timedelta

genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure random key in production

users = {}

class Ingredient:
    def __init__(self, name, quantity, unit, added_date, expires_in):
        self.name = name
        self.quantity = quantity
        self.unit = unit
        self.added_date = added_date
        self.expires_in = expires_in
        self.expiry_date = (datetime.strptime(added_date, "%Y-%m-%d") + timedelta(days=expires_in)).strftime("%Y-%m-%d")
        self.days_remaining = (datetime.strptime(self.expiry_date, "%Y-%m-%d").date() - datetime.now().date()).days

def load_ingredients():
    ingredients = []
    try:
        with open('ingredients.txt', 'r') as file:
            for line in file:
                if line.strip():
                    parts = line.strip().split('|')
                    if len(parts) == 5:
                        ingredient = Ingredient(
                            name=parts[0],
                            quantity=float(parts[1]),
                            unit=parts[2],
                            added_date=parts[3],
                            expires_in=int(parts[4])
                        )
                        ingredients.append(ingredient)
    except FileNotFoundError:
        print("Ingredients file not found. Starting fresh.")
    return ingredients

def load_singredients():
    singredients = []
    try:
        with open('singredients.txt', 'r') as file:
            for line in file:
                if line.strip():
                    parts = line.strip().split('|')
                    if len(parts) >= 1:  # Only name is required
                        ingredient = Ingredient(
                            name=parts[0],
                            quantity=float(parts[1]) if len(parts) > 1 else 0,
                            unit=parts[2] if len(parts) > 2 else "",
                            added_date=parts[3] if len(parts) > 3 else datetime.now().strftime("%Y-%m-%d"),
                            expires_in=int(parts[4]) if len(parts) > 4 else 0
                        )
                        singredients.append(ingredient)
    except FileNotFoundError:
        print("Standard ingredients file not found. Starting fresh.")
    return singredients

def save_ingredients(ingredients):
    with open('ingredients.txt', 'w') as file:
        for ing in ingredients:
            file.write(f"{ing.name}|{ing.quantity}|{ing.unit}|{ing.added_date}|{ing.expires_in}\n")

def save_singredients(singredients):
    with open('singredients.txt', 'w') as file:
        for ing in singredients:
            file.write(f"{ing.name}|{ing.quantity}|{ing.unit}|{ing.added_date}|{ing.expires_in}\n")

def is_in_ingredients(name, ingredients):
    return any(ing.name.lower() == name.lower() for ing in ingredients)

def generate_shopping_list():
    ingredients = load_ingredients()
    singredients = load_singredients()
    shopping_list = []
    
    # 1. Check for ingredients that need restocking (quantity < 1 kg/liter or expires in 2 days)
    for ing in ingredients:
        if ((ing.unit.lower() in ['kg', 'kgs'] and ing.quantity < 1.0) or
            (ing.unit.lower() in ['l', 'liter', 'liters'] and ing.quantity < 1.0) or
            ing.days_remaining <= 2):
            
            reason = []
            if ing.quantity < 1.0 and ing.unit.lower() in ['kg', 'kgs', 'l', 'liter', 'liters']:
                reason.append(f"Low quantity ({ing.quantity} {ing.unit})")
            if ing.days_remaining <= 2:
                reason.append(f"Expires in {ing.days_remaining} days")
            
            shopping_list.append({
                'name': ing.name,
                'details': f"{ing.quantity} {ing.unit}",
                'reason': ", ".join(reason),
                'priority': "high" if ing.days_remaining <= 2 else "medium",
                'type': "restock"
            })
    
    # 2. Check for standard ingredients not in inventory
    for sing in singredients:
        if not is_in_ingredients(sing.name, ingredients):
            shopping_list.append({
                'name': sing.name,
                'details': sing.unit if hasattr(sing, 'unit') else "",
                'reason': "Standard item not in inventory",
                'priority': "medium",
                'type': "standard"
            })
    
    # Sort by priority (high first) then by name
    priority_order = {"high": 0, "medium": 1, "low": 2}
    shopping_list.sort(key=lambda x: (priority_order[x['priority']], x['name']))
    
    return shopping_list

def get_low_quantity_ingredients(ingredients):
    return [ing for ing in ingredients if 
            ((ing.unit.lower() in ['kg', 'kgs'] and ing.quantity < 1.0) or
             (ing.unit.lower() in ['l', 'liter', 'liters'] and ing.quantity < 1.0))]

def get_recipe_suggestions(ingredients):
    """Fetch AI-generated recipe suggestions based on available ingredients."""
    ingredient_list = [f"{ing.name} ({ing.quantity} {ing.unit})" for ing in ingredients]
    prompt = f"I have these ingredients: {', '.join(ingredient_list)}. Suggest 3 detailed recipes with step-by-step instructions, cooking time, and difficulty level."

    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else "No recipe suggestions available."
    except Exception as e:
        return f"Error fetching recipe suggestions: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email in users and check_password_hash(users[email], password):
            session['user'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email in users:
            flash('Email already exists.', 'error')
        else:
            hashed_password = generate_password_hash(password)
            users[email] = hashed_password
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'user' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    
    ingredients = load_ingredients()
    today = datetime.now().date()
    expired = []
    nearly_expired = []
    low_quantity = get_low_quantity_ingredients(ingredients)
    
    for ing in ingredients:
        if ing.days_remaining < 0:
            expired.append(f"{ing.name} (expired {abs(ing.days_remaining)} days ago)")
        elif ing.days_remaining <= 3:
            nearly_expired.append(f"{ing.name} (expires in {ing.days_remaining} days)")
    
    # Generate shopping list preview (top 3 items)
    shopping_list = generate_shopping_list()
    shopping_preview = shopping_list[:3]
    more_items_count = len(shopping_list) - 3 if len(shopping_list) > 3 else 0
    
    singredients = load_singredients()
    
    return render_template('main.html', 
                         ingredients=ingredients,
                         expired=expired,
                         nearly_expired=nearly_expired,
                         low_quantity=low_quantity,
                         shopping_preview=shopping_preview,
                         more_items_count=more_items_count,
                         singredients=singredients,
                         user=session['user'])

@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'user' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        name = request.form['name'].strip()
        quantity = float(request.form['quantity'])
        unit = request.form['unit']
        expires_in = int(request.form['expires_in'])
        
        try:
            exe_path = os.path.join(os.getcwd(), "fridge_logic.exe")
            subprocess.run([exe_path, "add", name, str(quantity), unit, str(expires_in)], check=True)
            flash(f"Added {quantity} {unit} of {name} (expires in {expires_in} days)", "success")
        except subprocess.CalledProcessError as e:
            flash(f"Failed to add ingredient: {str(e)}", "error")
        except FileNotFoundError:
            flash("Executable not found.", "error")
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
        
        return redirect(url_for('add'))
    
    return render_template('add.html')

@app.route('/taking', methods=['GET', 'POST'])
def taking():
    if 'user' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))

    ingredients = load_ingredients()
    
    if request.method == 'POST':
        name = request.form['name'].strip()
        quantity = float(request.form.get('quantity', 1))  # Default to 1 if not specified
        
        found = False
        updated_ingredients = []
        
        for ing in ingredients:
            if ing.name.lower() == name.lower():
                found = True
                if quantity >= ing.quantity:
                    flash(f"Removed all {ing.quantity} {ing.unit} of {ing.name}", "success")
                else:
                    ing.quantity -= quantity
                    updated_ingredients.append(ing)
                    flash(f"Took {quantity} {ing.unit} of {ing.name} (remaining: {ing.quantity})", "success")
            else:
                updated_ingredients.append(ing)
        
        if not found:
            flash(f"Ingredient {name} not found", "error")
        else:
            save_ingredients(updated_ingredients)
            ingredients = updated_ingredients
        
        return redirect(url_for('taking'))
    
    return render_template('taking.html', ingredients=ingredients)

@app.route('/recipe')
def recipe():
    if 'user' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))

    ingredients = load_ingredients()
    recipe_suggestions = get_recipe_suggestions(ingredients)
    
    return render_template('recipe.html', 
                         ingredients=ingredients, 
                         recipe_suggestions=recipe_suggestions)

@app.route('/shoppinglist', methods=['GET', 'POST'])
def shoppinglist():
    if 'user' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Handle adding new standard ingredient
        if 'name' in request.form:
            name = request.form['name'].strip()
            if name:
                singredients = load_singredients()
                if not is_in_ingredients(name, singredients):
                    new_ing = Ingredient(
                        name=name,
                        quantity=0,
                        unit="",
                        added_date=datetime.now().strftime("%Y-%m-%d"),
                        expires_in=0
                    )
                    singredients.append(new_ing)
                    save_singredients(singredients)
                    flash(f"Added {name} to standard ingredients", "success")
                else:
                    flash(f"{name} is already a standard ingredient", "warning")
        
        # Handle removing standard ingredient
        elif 'remove_name' in request.form:
            name = request.form['remove_name'].strip()
            singredients = load_singredients()
            updated = [ing for ing in singredients if ing.name.lower() != name.lower()]
            if len(updated) < len(singredients):
                save_singredients(updated)
                flash(f"Removed {name} from standard ingredients", "success")
            else:
                flash(f"{name} not found in standard ingredients", "error")
        
        return redirect(url_for('shoppinglist'))
    
    shopping_list = generate_shopping_list()
    singredients = load_singredients()
    
    return render_template('shoppinglist.html', 
                         shopping_list=shopping_list,
                         singredients=singredients)

@app.route('/remove_singredient/<name>')
def remove_singredient(name):
    if 'user' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    
    singredients = load_singredients()
    updated = [ing for ing in singredients if ing.name.lower() != name.lower()]
    
    if len(updated) < len(singredients):
        save_singredients(updated)
        flash(f"Removed {name} from standard ingredients", "success")
    else:
        flash(f"{name} not found in standard ingredients", "error")
    
    return redirect(url_for('shoppinglist'))

@app.route('/notes')
def notes():
    if 'user' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    return render_template('notes.html')

@app.route('/change')
def change():
    if 'user' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    return render_template('change.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)