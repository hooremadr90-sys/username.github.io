from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, User, Farm, Crop, Monitoring, SaleRecord
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///farm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        user = User(email=email, password=password, full_name=name)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('setup_farm'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            if not user.farm_id:
                return redirect(url_for('setup_farm'))
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/setup-farm', methods=['GET', 'POST'])
@login_required
def setup_farm():
    if request.method == 'POST':
        farm = Farm(
            name=request.form['farm_name'],
            location=request.form['location'],
            owner_id=current_user.id
        )
        db.session.add(farm)
        db.session.commit()
        
        current_user.farm_id = farm.id
        db.session.commit()
        
        # Create mock sales data for charts
        crops = ['Tomato', 'Lettuce', 'Basil', 'Cucumber']
        for i in range(30):
            sale = SaleRecord(
                crop_name=random.choice(crops),
                quantity_sold=random.randint(10, 100),
                revenue=random.randint(500, 5000),
                sale_date=datetime.now() - timedelta(days=i),
                farm_id=farm.id
            )
            db.session.add(sale)
        db.session.commit()
        
        return redirect(url_for('dashboard'))
    return render_template('setup_farm.html')

@app.route('/dashboard')
@login_required
def dashboard():
    farm = Farm.query.get(current_user.farm_id)
    crops = Crop.query.filter_by(farm_id=farm.id).all()
    latest_monitoring = Monitoring.query.filter_by(farm_id=farm.id).order_by(Monitoring.created_at.desc()).first()
    
    # KPIs
    total_crops = len(crops)
    total_revenue = sum([s.revenue for s in SaleRecord.query.filter_by(farm_id=farm.id).all()])
    total_profit = int(total_revenue * 0.4)  # Mock profit margin
    active_orders = 5  # Mock for now
    
    # Sales data for chart (last 30 days)
    sales_by_day = {}
    for i in range(30):
        day = datetime.now() - timedelta(days=i)
        day_sales = sum([s.revenue for s in SaleRecord.query.filter_by(farm_id=farm.id).filter(SaleRecord.sale_date >= day.replace(hour=0, minute=0, second=0)).filter(SaleRecord.sale_date <= day.replace(hour=23, minute=59, second=59)).all()])
        sales_by_day[day.strftime('%Y-%m-%d')] = day_sales
    
    # Crop performance
    crop_performance = {}
    for crop in crops:
        total_sold = sum([s.quantity_sold for s in SaleRecord.query.filter_by(farm_id=farm.id, crop_name=crop.name).all()])
        crop_performance[crop.name] = total_sold or crop.quantity
    
    return render_template('dashboard.html', 
                         farm=farm, 
                         crops=crops, 
                         monitoring=latest_monitoring,
                         total_crops=total_crops,
                         total_revenue=total_revenue,
                         total_profit=total_profit,
                         active_orders=active_orders,
                         sales_data=sales_by_day,
                         crop_performance=crop_performance)

@app.route('/add-monitoring', methods=['POST'])
@login_required
def add_monitoring():
    farm = Farm.query.get(current_user.farm_id)
    monitoring = Monitoring(
        temperature=float(request.form['temperature']),
        ph=float(request.form['ph']),
        ec=float(request.form['ec']),
        water_level=int(request.form['water_level']),
        farm_id=farm.id
    )
    db.session.add(monitoring)
    db.session.commit()
    flash('Reading added')
    return redirect(url_for('dashboard'))

@app.route('/add-crop', methods=['POST'])
@login_required
def add_crop():
    farm = Farm.query.get(current_user.farm_id)
    crop = Crop(
        name=request.form['crop_name'],
        quantity=int(request.form['quantity']),
        farm_id=farm.id
    )
    db.session.add(crop)
    db.session.commit()
    flash('Crop added')
    return redirect(url_for('dashboard'))

@app.route('/update-crop-stage/<int:crop_id>')
@login_required
def update_crop_stage(crop_id):
    crop = Crop.query.get(crop_id)
    stages = ['Growing', 'Harvested', 'Ready to Sell', 'Sold Out']
    current_index = stages.index(crop.stage)
    if current_index < len(stages) - 1:
        crop.stage = stages[current_index + 1]
        db.session.commit()
        
        # Record sale when harvested
        if crop.stage == 'Harvested':
            sale = SaleRecord(
                crop_name=crop.name,
                quantity_sold=crop.quantity,
                revenue=crop.quantity * 50,  # Mock price per unit
                farm_id=crop.farm_id
            )
            db.session.add(sale)
            db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete-crop/<int:crop_id>')
@login_required
def delete_crop(crop_id):
    crop = Crop.query.get(crop_id)
    db.session.delete(crop)
    db.session.commit()
    flash('Crop deleted')
    return redirect(url_for('dashboard'))

@app.route('/reports')
@login_required
def reports():
    farm = Farm.query.get(current_user.farm_id)
    sales = SaleRecord.query.filter_by(farm_id=farm.id).order_by(SaleRecord.sale_date.desc()).all()
    
    total_revenue = sum([s.revenue for s in sales])
    total_crops_sold = len(set([s.crop_name for s in sales]))
    
    crop_summary = {}
    for sale in sales:
        if sale.crop_name not in crop_summary:
            crop_summary[sale.crop_name] = {'quantity': 0, 'revenue': 0}
        crop_summary[sale.crop_name]['quantity'] += sale.quantity_sold
        crop_summary[sale.crop_name]['revenue'] += sale.revenue
    
    return render_template('reports.html', 
                         sales=sales[:50],
                         total_revenue=total_revenue,
                         total_crops_sold=total_crops_sold,
                         crop_summary=crop_summary)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('landing'))

if __name__ == '__main__':
    app.run(debug=True)
    