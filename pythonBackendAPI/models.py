from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# Определение модели User
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now(), nullable=False)

    cart = db.relationship("Cart", uselist=False, back_populates="user")

    def __repr__(self):
        return f'<User {self.id}>'


# Определение модели Product
class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now(), nullable=False)

    carts = db.relationship("CartItem", back_populates="product")

    def __repr__(self):
        return f'<Product {self.id}>'


# Определение модели Cart
class Cart(db.Model):
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now(), nullable=False)

    user = db.relationship("User", back_populates="cart")
    items = db.relationship("CartItem", back_populates="cart")

    def __init__(self):
        self.items = []

    def add_item(self, product, quantity):
        if isinstance(product, Product) and isinstance(quantity, int):
            item = CartItem(cart=self, product=product, quantity=quantity)
            self.items.append(item)
        else:
            raise ValueError('Invalid arguments')

    def total(self):
        return sum(item.product.price * item.quantity for item in self.items)


# Определение модели CartItem
class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer, default=1)

    cart = db.relationship("Cart", back_populates="items")
    product = db.relationship("Product")

    def __init__(self, cart, product, quantity=1):
        self.cart = cart
        self.product = product
        self.quantity = quantity