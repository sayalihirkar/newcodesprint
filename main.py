from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
import os
import time
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Replace with your actual DB credentials
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/studentdbms'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ----------------- MODELS -------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(1000))

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    name = db.Column(db.String(100))
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    photo_filename = db.Column(db.String(255))
    condition = db.Column(db.String(50))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    availability = db.Column(db.Enum('available', 'unavailable'), default='available')
    mode = db.Column(db.Enum('rent', 'sale', 'share'), nullable=False)
    date_added = db.Column(db.DateTime, default=db.func.current_timestamp())

class Rent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    renter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    rent_start_date = db.Column(db.Date, nullable=False)
    rent_end_date = db.Column(db.Date, nullable=False)
    rent_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    quantity = db.Column(db.Integer)
    total_price = db.Column(db.Float)
    status = db.Column(db.Enum('active', 'completed', 'cancelled'), default='active')

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    quantity = db.Column(db.Integer)
    sale_date = db.Column(db.DateTime, default=db.func.current_timestamp())

class Share(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    purpose = db.Column(db.String(255))
    share_date = db.Column(db.DateTime, default=db.func.current_timestamp())

# ----------------- USER MANAGEMENT -------------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('signup'))
        
        # Create new user
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:  # In production, use proper password hashing
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

# ----------------- ROUTES -------------------

# College-specific categories and conditions
COLLEGE_CATEGORIES = [
    'Lab Equipment',
    'Textbooks',
    'Lab Manuals',
    'Electronics Components',
    'Project Supplies',
    'Study Materials',
    'Lab Tools',
    'Technical Instruments',
    'Computing Devices',
    'Engineering Tools',
    'Research Equipment',
    'Workshop Materials'
]

ITEM_CONDITIONS = [
    'New',
    'Like New',
    'Excellent',
    'Good',
    'Fair',
    'Poor'
]

@app.route('/')
def index():
    search_query = request.args.get('q', '')
    category = request.args.get('category', '')
    mode = request.args.get('mode', '')
    
    query = Item.query
    
    if search_query:
        query = query.filter(
            db.or_(
                Item.name.ilike(f'%{search_query}%'),
                Item.description.ilike(f'%{search_query}%'),
                Item.category.ilike(f'%{search_query}%')
            )
        )
    
    if category:
        query = query.filter(Item.category == category)
    
    if mode:
        query = query.filter(Item.mode == mode)
    
    items = query.all()
    return render_template('index.html', items=items, categories=COLLEGE_CATEGORIES, search_query=search_query)

@app.route('/profile')
@login_required
def profile():
    # Get the current user's items
    user_items = Item.query.filter_by(owner_id=current_user.id).all()
    # Get user's rented items
    rented_items = Item.query.join(Rent).filter(Rent.renter_id == current_user.id).all()
    # Get user's shared items
    shared_items = Item.query.join(Share).filter(Share.user_id == current_user.id).all()
    # Get user's purchased items
    purchased_items = Item.query.join(Sale).filter(Sale.user_id == current_user.id).all()
    
    return render_template('profile.html', 
                           user=current_user,
                           owned_items=user_items,
                           rented_items=rented_items,
                           shared_items=shared_items,
                           purchased_items=purchased_items)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/rent_items')
def rent_items():
    search_query = request.args.get('q', '')
    category = request.args.get('category', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    condition = request.args.get('condition', '')
    
    query = Item.query.filter_by(mode='rent')
    
    if search_query:
        query = query.filter(
            db.or_(
                Item.name.ilike(f'%{search_query}%'),
                Item.description.ilike(f'%{search_query}%'),
                Item.category.ilike(f'%{search_query}%')
            )
        )
    
    if category:
        query = query.filter(Item.category == category)
    
    if min_price is not None:
        query = query.filter(Item.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Item.price <= max_price)
    
    if condition:
        query = query.filter(Item.condition == condition)
    
    items = query.all()
    return render_template('rent_items.html', 
                         items=items, 
                         categories=COLLEGE_CATEGORIES,
                         search_query=search_query,
                         selected_category=category,
                         min_price=min_price,
                         max_price=max_price,
                         condition=condition)

@app.route('/share_items')
def share_items():
    items = Item.query.filter_by(mode='share', availability='available').all()
    return render_template('share_items.html', items=items)

@app.route('/buy_items')
def buy_items():
    search_query = request.args.get('q', '')
    category = request.args.get('category', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    condition = request.args.get('condition', '')
    
    query = Item.query.filter_by(mode='sale')
    
    if search_query:
        query = query.filter(
            db.or_(
                Item.name.ilike(f'%{search_query}%'),
                Item.description.ilike(f'%{search_query}%'),
                Item.category.ilike(f'%{search_query}%')
            )
        )
    
    if category:
        query = query.filter(Item.category == category)
    
    if min_price is not None:
        query = query.filter(Item.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Item.price <= max_price)
    
    if condition:
        query = query.filter(Item.condition == condition)
    
    items = query.all()
    return render_template('buy_items.html', 
                         items=items, 
                         categories=COLLEGE_CATEGORIES,
                         search_query=search_query,
                         selected_category=category,
                         min_price=min_price,
                         max_price=max_price,
                         condition=condition)

@app.route('/sales')
def sales():
    records = Sale.query.all()
    return render_template('sales.html', records=records)

@app.route('/rentals')
@login_required
def rentals():
    rentals = Rent.query.filter_by(renter_id=current_user.id).all()
    return render_template('rentals.html', rentals=rentals)

@app.route('/shares')
def shares():
    records = Share.query.all()
    return render_template('shares.html', records=records)

@app.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        quantity = request.form['quantity']
        price = request.form['price']
        mode = request.form['mode']
        condition = request.form['condition']
        description = request.form.get('description', '')
        
        # Handle file upload
        photo = request.files.get('photo')
        photo_filename = ''
        if photo and allowed_file(photo.filename):
            # Secure the filename and save the file
            filename = secure_filename(photo.filename)
            # Add timestamp to filename to make it unique
            timestamp = str(int(time.time()))
            photo_filename = f"{timestamp}_{filename}"
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
        
        new_item = Item(
            owner_id=current_user.id,
            name=name,
            category=category,
            quantity=quantity,
            price=price,
            mode=mode,
            condition=condition,
            description=description,
            photo_filename=photo_filename
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        flash('Item added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_item.html', categories=COLLEGE_CATEGORIES, conditions=ITEM_CONDITIONS)

@app.route('/rent_item/<int:id>', methods=['GET', 'POST'])
@login_required
def rent_item(id):
    item = Item.query.get_or_404(id)
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        quantity = int(request.form['quantity'])
        
        if quantity <= 0:
            flash('Please enter a valid quantity!', 'danger')
            return render_template('rent_item.html', item=item)
        
        if quantity > item.quantity:
            flash('Not enough quantity available!', 'danger')
            return render_template('rent_item.html', item=item)
        
        # Check if dates are valid
        from datetime import datetime
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if start_date < datetime.now().date():
            flash('Start date cannot be in the past!', 'danger')
            return render_template('rent_item.html', item=item)
        
        if end_date < start_date:
            flash('End date must be after start date!', 'danger')
            return render_template('rent_item.html', item=item)
        
        # Calculate total price based on number of days
        days = (end_date - start_date).days + 1
        total_price = item.price * quantity * days
        
        # Create rental record
        rental = Rent(
            item_id=item.id,
            renter_id=current_user.id,
            rent_start_date=start_date,
            rent_end_date=end_date,
            quantity=quantity,
            total_price=total_price,
            status='active'
        )
        
        # Update item availability
        item.quantity -= quantity
        if item.quantity == 0:
            item.availability = 'unavailable'
        item.next_available_date = end_date
        item.current_rental_id = rental.id
        
        db.session.add(rental)
        db.session.commit()
        
        flash(f'Successfully rented {item.name}! Total cost: ₹{total_price:.2f}', 'success')
        return redirect(url_for('rent_items'))
    
    return render_template('rent_item.html', item=item)

@app.route('/buy_item/<int:id>', methods=['GET', 'POST'])
@login_required
def buy_item(id):
    item = Item.query.get_or_404(id)
    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        if item.quantity >= quantity:
            # Get payment method
            payment_method = request.form.get('paymentMethod')
            
            # Validate payment details based on method
            if payment_method == 'card':
                card_name = request.form.get('cardName')
                card_number = request.form.get('cardNumber')
                expiry_date = request.form.get('expiryDate')
                cvv = request.form.get('cvv')
                
                if not all([card_name, card_number, expiry_date, cvv]):
                    flash('Please provide all card payment details!', 'danger')
                    return render_template('buy_item.html', item=item)
            elif payment_method == 'upi':
                upi_id = request.form.get('upiId')
                upi_app = request.form.get('upiApp')
                
                if not all([upi_id, upi_app]):
                    flash('Please provide all UPI payment details!', 'danger')
                    return render_template('buy_item.html', item=item)
            else:
                flash('Please select a valid payment method!', 'danger')
                return render_template('buy_item.html', item=item)
            
            # In a real application, you would process the payment here
            # For demo purposes, we'll just create the sale
            sale = Sale(
                item_id=item.id,
                user_id=current_user.id,
                quantity=quantity
            )
            item.quantity -= quantity
            db.session.add(sale)
            db.session.commit()
            
            total_cost = quantity * item.price
            flash(f'Payment of ₹{total_cost:.2f} processed successfully! Item purchased.', 'success')
            return redirect(url_for('buy_items'))
        flash('Insufficient quantity available!', 'danger')
    return render_template('buy_item.html', item=item)

# ----------------- INIT DB -------------------

@app.cli.command("initdb")
def initdb_command():
    """Creates the database tables."""
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        
        # Create default user
        default_user = User(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        db.session.add(default_user)
        db.session.commit()
        print("Initialized the database with default user.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/edit_item/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_item(id):
    item = Item.query.get_or_404(id)
    if request.method == 'POST':
        item.name = request.form['name']
        item.category = request.form['category']
        item.quantity = int(request.form['quantity'])
        item.price = float(request.form['price'])
        item.mode = request.form['mode']
        item.description = request.form.get('description', '')
        db.session.commit()
        flash('Item updated successfully!', 'success')
        # Redirect based on the item's mode
        if item.mode == 'rent':
            return redirect(url_for('rent_items'))
        elif item.mode == 'share':
            return redirect(url_for('share_items'))
        else:  # mode == 'sale'
            return redirect(url_for('buy_items'))
    return render_template('edit_item.html', item=item)

@app.route('/delete_item/<int:id>')
@login_required
def delete_item(id):
    item = Item.query.get_or_404(id)
    mode = item.mode  # Store the mode before deleting
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully!', 'success')
    # Redirect based on the deleted item's mode
    if mode == 'rent':
        return redirect(url_for('rent_items'))
    elif mode == 'share':
        return redirect(url_for('share_items'))
    else:  # mode == 'sale'
        return redirect(url_for('buy_items'))

# ----------------- MAIN -------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Fixes RuntimeError
    app.run(debug=True)
