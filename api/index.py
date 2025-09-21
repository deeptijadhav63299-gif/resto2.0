from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import json

# Initialize Flask app
app = Flask(__name__,
            static_folder='../static',
            template_folder='../templates',
            instance_relative_config=True)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'resto2.0-secret-key')

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # For Vercel, use a temporary SQLite database (not recommended for production)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///resto.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(200))
    dietary_info = db.Column(db.String(100))  # Comma-separated values like "vegan,gluten-free"
    available = db.Column(db.Boolean, default=True)
    
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120))
    customer_phone = db.Column(db.String(20))
    order_type = db.Column(db.String(20), nullable=False)  # dine-in, takeaway, delivery
    table_number = db.Column(db.String(10))
    delivery_address = db.Column(db.Text)
    order_status = db.Column(db.String(20), default='received')  # received, cooking, ready, served/delivered
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")
    payment = db.relationship('Payment', backref='order', lazy=True, uselist=False)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    menu_item = db.relationship('MenuItem')

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # card, upi, paypal, cash
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    transaction_id = db.Column(db.String(100))
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    loyalty_points = db.Column(db.Integer, default=0)
    reviews = db.relationship('Review', backref='customer', lazy=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    """Initialize the database with sample data"""
    with app.app_context():
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@resto.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/menu')
def menu():
    menu_items = MenuItem.query.filter_by(available=True).all()
    return render_template('menu.html', menu_items=menu_items)

@app.route('/order')
def order():
    return render_template('order.html')

@app.route('/reviews')
def reviews():
    reviews = Review.query.order_by(Review.date_posted.desc()).all()
    return render_template('reviews.html', reviews=reviews)

@app.route('/api/menu')
def api_menu():
    menu_items = MenuItem.query.filter_by(available=True).all()
    menu_data = []
    for item in menu_items:
        menu_data.append({
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'price': item.price,
            'category': item.category,
            'image_url': item.image_url,
            'dietary_info': item.dietary_info.split(',') if item.dietary_info else []
        })
    return jsonify(menu_data)

@app.route('/api/place_order', methods=['POST'])
def place_order():
    try:
        data = request.get_json()
        
        # Create new order
        order = Order(
            customer_name=data['customer_name'],
            customer_email=data.get('customer_email'),
            customer_phone=data.get('customer_phone'),
            order_type=data['order_type'],
            table_number=data.get('table_number'),
            delivery_address=data.get('delivery_address'),
            total_amount=data['total_amount']
        )
        
        db.session.add(order)
        db.session.flush()  # Get the order ID
        
        # Add order items
        for item in data['items']:
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item['menu_item_id'],
                quantity=item['quantity'],
                price=item['price']
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        return jsonify({'success': True, 'order_id': order.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/order_status/<int:order_id>')
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({
        'id': order.id,
        'status': order.order_status,
        'order_date': order.order_date.isoformat()
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    # Get dashboard statistics
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(order_status='received').count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    total_menu_items = MenuItem.query.count()
    
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         total_revenue=total_revenue,
                         total_menu_items=total_menu_items,
                         recent_orders=recent_orders)

@app.route('/admin/menu')
@login_required
def admin_menu():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    menu_items = MenuItem.query.all()
    return render_template('admin/menu.html', menu_items=menu_items)

@app.route('/admin/menu/add', methods=['GET', 'POST'])
@login_required
def admin_add_menu_item():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        menu_item = MenuItem(
            name=request.form['name'],
            description=request.form['description'],
            price=float(request.form['price']),
            category=request.form['category'],
            image_url=request.form['image_url'],
            dietary_info=request.form.get('dietary_info', ''),
            available=bool(request.form.get('available'))
        )
        
        db.session.add(menu_item)
        db.session.commit()
        flash('Menu item added successfully!')
        return redirect(url_for('admin_menu'))
    
    return render_template('admin/menu.html')

@app.route('/admin/menu/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_menu_item(item_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    menu_item = MenuItem.query.get_or_404(item_id)
    
    if request.method == 'POST':
        menu_item.name = request.form['name']
        menu_item.description = request.form['description']
        menu_item.price = float(request.form['price'])
        menu_item.category = request.form['category']
        menu_item.image_url = request.form['image_url']
        menu_item.dietary_info = request.form.get('dietary_info', '')
        menu_item.available = bool(request.form.get('available'))
        
        db.session.commit()
        flash('Menu item updated successfully!')
        return redirect(url_for('admin_menu'))
    
    return render_template('admin/menu.html', edit_item=menu_item)

@app.route('/admin/menu/delete/<int:item_id>')
@login_required
def admin_delete_menu_item(item_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    menu_item = MenuItem.query.get_or_404(item_id)
    db.session.delete(menu_item)
    db.session.commit()
    flash('Menu item deleted successfully!')
    return redirect(url_for('admin_menu'))

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/order/<int:order_id>')
@login_required
def admin_order_detail(order_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
@login_required
def admin_update_order_status(order_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    order = Order.query.get_or_404(order_id)
    new_status = request.json.get('status')
    
    if new_status in ['received', 'cooking', 'ready', 'served', 'delivered']:
        order.order_status = new_status
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid status'}), 400

@app.route('/admin/customers')
@login_required
def admin_customers():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    customers = Customer.query.all()
    return render_template('admin/customers.html', customers=customers)

@app.route('/admin/reports')
@login_required
def admin_reports():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    return render_template('admin/reports.html')

@app.route('/api/reports/sales')
@login_required
def api_sales_report():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get sales data for the last 30 days
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Daily sales
    daily_sales = db.session.query(
        db.func.date(Order.order_date).label('date'),
        db.func.sum(Order.total_amount).label('total'),
        db.func.count(Order.id).label('orders')
    ).filter(
        Order.order_date >= start_date,
        Order.order_date <= end_date
    ).group_by(
        db.func.date(Order.order_date)
    ).all()
    
    # Category sales
    category_sales = db.session.query(
        MenuItem.category,
        db.func.sum(OrderItem.price * OrderItem.quantity).label('total')
    ).join(
        OrderItem, MenuItem.id == OrderItem.menu_item_id
    ).join(
        Order, OrderItem.order_id == Order.id
    ).filter(
        Order.order_date >= start_date,
        Order.order_date <= end_date
    ).group_by(MenuItem.category).all()
    
    # Top selling items
    top_items = db.session.query(
        MenuItem.name,
        db.func.sum(OrderItem.quantity).label('quantity'),
        db.func.sum(OrderItem.price * OrderItem.quantity).label('revenue')
    ).join(
        OrderItem, MenuItem.id == OrderItem.menu_item_id
    ).join(
        Order, OrderItem.order_id == Order.id
    ).filter(
        Order.order_date >= start_date,
        Order.order_date <= end_date
    ).group_by(MenuItem.id, MenuItem.name).order_by(
        db.func.sum(OrderItem.quantity).desc()
    ).limit(10).all()
    
    return jsonify({
        'daily_sales': [{'date': str(row.date), 'total': float(row.total), 'orders': row.orders} for row in daily_sales],
        'category_sales': [{'category': row.category, 'total': float(row.total)} for row in category_sales],
        'top_items': [{'name': row.name, 'quantity': row.quantity, 'revenue': float(row.revenue)} for row in top_items]
    })

# Initialize database on startup
# Note: @app.before_first_request is deprecated, using app context instead

# Initialize the database and create sample data
with app.app_context():
    db.create_all()
    
    # Create admin user if it doesn't exist
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@resto.com',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

# For Vercel deployment - export the app
# This is the main entry point that Vercel will use