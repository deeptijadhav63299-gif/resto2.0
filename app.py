from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import json

# Initialize Flask app
app = Flask(__name__,
            static_folder='static',
            template_folder='templates',
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
    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'resto.db')

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

# Create database tables
def init_db():
    with app.app_context():
        db.create_all()
        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@resto.com',
                is_admin=True
            )
            admin.set_password('admin123')  # Set a default password
            db.session.add(admin)
            db.session.commit()

# Initialize database
init_db()

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
    return render_template('index.html', reviews=reviews)

@app.route('/api/menu')
def api_menu():
    menu_items = MenuItem.query.filter_by(available=True).all()
    result = []
    for item in menu_items:
        result.append({
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'price': item.price,
            'category': item.category,
            'image_url': item.image_url,
            'dietary_info': item.dietary_info.split(',') if item.dietary_info else []
        })
    return jsonify(result)

@app.route('/api/place_order', methods=['POST'])
def place_order():
    data = request.json
    
    # Create new order
    order = Order(
        customer_name=data['customerName'],
        customer_email=data['customerEmail'],
        customer_phone=data['customerPhone'],
        order_type=data['orderType'],
        table_number=data.get('tableNumber'),
        delivery_address=data.get('deliveryAddress'),
        total_amount=data['totalAmount']
    )
    db.session.add(order)
    db.session.flush()  # Get order ID without committing
    
    # Add order items
    for item in data['items']:
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item['id'],
            quantity=item['quantity'],
            price=item['price']
        )
        db.session.add(order_item)
    
    # Create payment record
    payment = Payment(
        order_id=order.id,
        payment_method=data['paymentMethod'],
        payment_status='completed' if data['paymentMethod'] != 'cash' else 'pending',
        transaction_id=data.get('transactionId'),
        amount=data['totalAmount']
    )
    db.session.add(payment)
    
    # Update or create customer for loyalty points
    customer = Customer.query.filter_by(email=data['customerEmail']).first()
    if customer:
        customer.loyalty_points += int(data['totalAmount'])
    else:
        customer = Customer(
            name=data['customerName'],
            email=data['customerEmail'],
            phone=data['customerPhone'],
            loyalty_points=int(data['totalAmount'])
        )
        db.session.add(customer)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'order_id': order.id,
        'order_status': order.order_status
    })

@app.route('/api/order_status/<int:order_id>')
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({
        'order_id': order.id,
        'status': order.order_status,
        'updated_at': order.order_date.strftime('%Y-%m-%d %H:%M:%S')
    })

# Admin routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
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
        flash('You do not have permission to access the admin dashboard')
        return redirect(url_for('index'))
    
    # Get counts for dashboard
    orders_count = Order.query.count()
    pending_orders = Order.query.filter(Order.order_status != 'served').filter(Order.order_status != 'delivered').count()
    menu_items_count = MenuItem.query.count()
    customers_count = Customer.query.count()
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                          orders_count=orders_count,
                          pending_orders=pending_orders,
                          menu_items_count=menu_items_count,
                          customers_count=customers_count,
                          recent_orders=recent_orders)

@app.route('/admin/menu')
@login_required
def admin_menu():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    menu_items = MenuItem.query.all()
    return render_template('admin/menu.html', menu_items=menu_items)

@app.route('/admin/menu/add', methods=['GET', 'POST'])
@login_required
def admin_add_menu_item():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Process form data
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        category = request.form.get('category')
        image_url = request.form.get('image_url')
        dietary_info = ','.join(request.form.getlist('dietary_info'))
        available = 'available' in request.form
        
        menu_item = MenuItem(
            name=name,
            description=description,
            price=price,
            category=category,
            image_url=image_url,
            dietary_info=dietary_info,
            available=available
        )
        
        db.session.add(menu_item)
        db.session.commit()
        
        flash('Menu item added successfully')
        return redirect(url_for('admin_menu'))
    
    return render_template('admin/add_menu_item.html')

@app.route('/admin/menu/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_menu_item(item_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    menu_item = MenuItem.query.get_or_404(item_id)
    
    if request.method == 'POST':
        # Process form data
        menu_item.name = request.form.get('name')
        menu_item.description = request.form.get('description')
        menu_item.price = float(request.form.get('price'))
        menu_item.category = request.form.get('category')
        menu_item.image_url = request.form.get('image_url')
        menu_item.dietary_info = ','.join(request.form.getlist('dietary_info'))
        menu_item.available = 'available' in request.form
        
        db.session.commit()
        
        flash('Menu item updated successfully')
        return redirect(url_for('admin_menu'))
    
    return render_template('admin/edit_menu_item.html', menu_item=menu_item)

@app.route('/admin/menu/delete/<int:item_id>')
@login_required
def admin_delete_menu_item(item_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    menu_item = MenuItem.query.get_or_404(item_id)
    db.session.delete(menu_item)
    db.session.commit()
    
    flash('Menu item deleted successfully')
    return redirect(url_for('admin_menu'))

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/order/<int:order_id>')
@login_required
def admin_order_detail(order_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
@login_required
def admin_update_order_status(order_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    order = Order.query.get_or_404(order_id)
    status = request.form.get('status')
    
    if status in ['received', 'cooking', 'ready', 'served', 'delivered']:
        order.order_status = status
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Invalid status'})

@app.route('/admin/customers')
@login_required
def admin_customers():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    customers = Customer.query.all()
    return render_template('admin/customers.html', customers=customers)

@app.route('/admin/reports')
@login_required
def admin_reports():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    return render_template('admin/reports.html')

@app.route('/api/reports/sales')
@login_required
def api_sales_report():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    # Get date range from query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Convert to datetime objects
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        # Default to 30 days ago
        start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date.replace(day=1)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        # Set to end of day
        end_date = end_date.replace(hour=23, minute=59, second=59)
    else:
        # Default to today
        end_date = datetime.utcnow().replace(hour=23, minute=59, second=59)
    
    # Query orders in date range
    orders = Order.query.filter(Order.order_date >= start_date, Order.order_date <= end_date).all()
    
    # Calculate total sales
    total_sales = sum(order.total_amount for order in orders)
    
    # Group by date
    sales_by_date = {}
    for order in orders:
        date_str = order.order_date.strftime('%Y-%m-%d')
        if date_str in sales_by_date:
            sales_by_date[date_str] += order.total_amount
        else:
            sales_by_date[date_str] = order.total_amount
    
    # Group by category
    sales_by_category = {}
    for order in orders:
        for item in order.order_items:
            category = item.menu_item.category
            if category in sales_by_category:
                sales_by_category[category] += item.price * item.quantity
            else:
                sales_by_category[category] = item.price * item.quantity
    
    return jsonify({
        'success': True,
        'total_sales': total_sales,
        'order_count': len(orders),
        'sales_by_date': sales_by_date,
        'sales_by_category': sales_by_category
    })

# Initialize database
@app.before_request
def create_tables():
    db.create_all()
    
    # Create admin user if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@resto.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Add sample menu items
        menu_items = [
            MenuItem(
                name='Butter Chicken',
                description='Tender chicken cooked in a rich, creamy tomato sauce with butter and spices',
                price=350,
                category='main',
                image_url='/static/images/butter_chicken.jpg',
                dietary_info='',
                available=True
            ),
            MenuItem(
                name='Paneer Tikka',
                description='Chunks of paneer marinated in spices and grilled in a tandoor',
                price=280,
                category='starter',
                image_url='/static/images/paneer_tikka.jpg',
                dietary_info='vegetarian',
                available=True
            ),
            MenuItem(
                name='Gulab Jamun',
                description='Soft, spongy milk-solid balls soaked in rose-flavored sugar syrup',
                price=120,
                category='dessert',
                image_url='/static/images/gulab_jamun.jpg',
                dietary_info='vegetarian',
                available=True
            ),
            MenuItem(
                name='Masala Chai',
                description='Traditional Indian spiced tea with milk',
                price=80,
                category='drink',
                image_url='/static/images/masala_chai.jpg',
                dietary_info='vegetarian',
                available=True
            ),
            MenuItem(
                name='Vegetable Biryani',
                description='Fragrant basmati rice cooked with mixed vegetables and aromatic spices',
                price=250,
                category='main',
                image_url='/static/images/veg_biryani.jpg',
                dietary_info='vegetarian',
                available=True
            ),
            MenuItem(
                name='Samosa',
                description='Crispy pastry filled with spiced potatoes and peas',
                price=100,
                category='starter',
                image_url='/static/images/samosa.jpg',
                dietary_info='vegetarian',
                available=True
            ),
            MenuItem(
                name='Rasmalai',
                description='Soft cottage cheese dumplings soaked in sweetened, thickened milk',
                price=150,
                category='dessert',
                image_url='/static/images/rasmalai.jpg',
                dietary_info='vegetarian',
                available=True
            ),
            MenuItem(
                name='Mango Lassi',
                description='Refreshing yogurt-based drink with mango pulp and spices',
                price=120,
                category='drink',
                image_url='/static/images/mango_lassi.jpg',
                dietary_info='vegetarian',
                available=True
            ),
            MenuItem(
                name='Chicken Biryani',
                description='Aromatic basmati rice cooked with tender chicken pieces and spices',
                price=320,
                category='main',
                image_url='/static/images/chicken_biryani.jpg',
                dietary_info='',
                available=True
            ),
            MenuItem(
                name='Dal Soup',
                description='Hearty lentil soup with Indian spices and herbs',
                price=150,
                category='starter',
                image_url='/static/images/dal_soup.jpg',
                dietary_info='vegetarian,vegan',
                available=True
            ),
            MenuItem(
                name='Kulfi',
                description='Traditional Indian ice cream with pistachios and cardamom',
                price=130,
                category='dessert',
                image_url='/static/images/kulfi.jpg',
                dietary_info='vegetarian',
                available=True
            )
        ]
        
        db.session.add_all(menu_items)
        db.session.commit()

# Create tables and initialize admin user
with app.app_context():
    db.create_all()
    # Check if admin user exists
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)