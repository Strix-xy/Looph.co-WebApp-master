"""
ETERNO E-Commerce Platform - Database Models
All SQLAlchemy models with optimized relationships and indexes
"""
from datetime import datetime
import json
from app import db
from app.utils.helpers import format_datetime_sg, isoformat_datetime_sg

class User(db.Model):
    """User model for customer, staff, cashier, and admin accounts"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')  # customer, staff, cashier, admin
    full_name = db.Column(db.String(120))
    address = db.Column(db.Text)
    phone_number = db.Column(db.String(30))
    default_payment_method = db.Column(db.String(50))
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    carts = db.relationship('Cart', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    sales = db.relationship('Sale', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    wishlist_items = db.relationship('WishlistItem', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_staff(self):
        return self.role in ('staff', 'cashier', 'admin')
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'full_name': self.full_name,
            'address': self.address,
            'phone_number': self.phone_number,
            'default_payment_method': self.default_payment_method,
            'created_at': isoformat_datetime_sg(self.created_at),
            'created_at_display': format_datetime_sg(self.created_at)
        }


class Product(db.Model):
    __tablename__ = 'product'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    sold_count = db.Column(db.Integer, nullable=False, default=0)
    is_pinned = db.Column(db.Boolean, default=False, index=True)
    badge = db.Column(db.String(20), index=True)
    tags = db.Column(db.String(100))
    category = db.Column(db.String(50), index=True)
    image_url = db.Column(db.String(500))
    image_urls = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    cart_items = db.relationship('Cart', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    wishlist_items = db.relationship('WishlistItem', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def is_in_stock(self, quantity=1):
        """Check if product has sufficient stock"""
        return self.stock >= quantity
    
    def reduce_stock(self, quantity):
        """Reduce product stock by quantity"""
        if self.is_in_stock(quantity):
            self.stock -= quantity
            return True
        return False
    
    def get_image_list(self):
        if self.image_urls:
            try:
                urls = json.loads(self.image_urls)
                if isinstance(urls, list) and urls:
                    return urls
            except (TypeError, json.JSONDecodeError):
                pass
        return [self.image_url] if self.image_url else []

    def get_tags_list(self):
        """Return normalized list of product tags."""
        allowed_tags = {"new", "limited", "sale"}
        raw = (self.tags or "").strip()
        if not raw:
            return []
        parsed = []
        for token in raw.split(","):
            normalized = token.strip().lower()
            if normalized in allowed_tags and normalized not in parsed:
                parsed.append(normalized)
        return parsed

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price else 0,
            'stock': self.stock,
            'sold_count': getattr(self, 'sold_count', 0) or 0,
            'is_pinned': getattr(self, 'is_pinned', False) or False,
            'category': self.category,
            'badge': self.badge,
            'tags': self.get_tags_list(),
            'image_url': self.image_url,
            'image_urls': self.get_image_list(),
            'created_at': isoformat_datetime_sg(self.created_at),
            'created_at_display': format_datetime_sg(self.created_at) if self.created_at else None
        }


class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user = db.relationship('User', backref=db.backref('reviews', lazy='dynamic'))


class WishlistItem(db.Model):
    __tablename__ = 'wishlist_item'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_user_wishlist_product'),)


class Sale(db.Model):
    """Sale model for admin POS transactions"""
    __tablename__ = 'sale'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), default='cash')  # cash, gcash, bank_transfer
    discount_type = db.Column(db.String(50))  # pwd, senior, voucher, none
    discount_amount = db.Column(db.Float, default=0)
    amount_paid = db.Column(db.Float, default=0)
    change_amount = db.Column(db.Float, default=0)
    items = db.Column(db.Text, nullable=False)  # JSON string of purchased items
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Sale {self.id}>'
    
    def to_dict(self):
        """Convert sale to dictionary"""
        try:
            items_data = json.loads(self.items or '[]')
        except (TypeError, json.JSONDecodeError):
            items_data = []
        
        subtotal = sum(
            float(item.get('price', 0)) * int(item.get('quantity', 0))
            for item in items_data
        )
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_amount': self.total_amount,
            'payment_method': self.payment_method,
            'discount_type': self.discount_type,
            'discount_amount': self.discount_amount,
            'amount_paid': getattr(self, 'amount_paid', 0) or 0,
            'change_amount': getattr(self, 'change_amount', 0) or 0,
            'items': self.items,
            'items_data': items_data,
            'subtotal': subtotal,
            'created_at': isoformat_datetime_sg(self.created_at),
            'created_at_display': format_datetime_sg(self.created_at)
        }


class Cart(db.Model):
    """Shopping cart for customer purchases"""
    __tablename__ = 'cart'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite unique constraint to prevent duplicate cart items
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='unique_user_product'),
    )
    
    def __repr__(self):
        return f'<Cart user:{self.user_id} product:{self.product_id}>'
    
    def get_subtotal(self):
        """Calculate subtotal for this cart item"""
        if self.product:
            return self.product.price * self.quantity
        return 0
    
    def to_dict(self):
        """Convert cart item to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'subtotal': self.get_subtotal()
        }


class Order(db.Model):
    """Order model for customer purchases with shipping details"""
    __tablename__ = 'order'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_address = db.Column(db.Text)
    subtotal = db.Column(db.Float, nullable=False)
    shipping_fee = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # cod, gcash, bank_transfer
    items = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='processing', index=True)
    voucher_code = db.Column(db.String(50), nullable=True)
    voucher_discount = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Order {self.id}>'
    
    def to_dict(self):
        """Convert order to dictionary"""
        try:
            items_data = json.loads(self.items or '[]')
        except (TypeError, json.JSONDecodeError):
            items_data = []
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_address': self.customer_address,
            'subtotal': self.subtotal,
            'shipping_fee': self.shipping_fee,
            'total_amount': self.total_amount,
            'payment_method': self.payment_method,
            'status': self.status,
            'items': self.items,
            'items_data': items_data,
            'voucher_code': self.voucher_code,
            'voucher_discount': getattr(self, 'voucher_discount', 0) or 0,
            'created_at': isoformat_datetime_sg(self.created_at),
            'created_at_display': format_datetime_sg(self.created_at)
        }


class OtpToken(db.Model):
    """One-time passcode tokens for password reset and payment confirmation"""
    __tablename__ = 'otp_token'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    code = db.Column(db.String(10), nullable=False, index=True)
    purpose = db.Column(db.String(50), nullable=False)  # reset, payment, other
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    used = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def is_valid(self, purpose):
        if self.used or self.purpose != purpose:
            return False
        return datetime.utcnow() <= self.expires_at


class Voucher(db.Model):
    __tablename__ = 'voucher'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    voucher_type = db.Column(db.String(50), nullable=False)  # free_delivery, product_discount, bogo, min_spend_discount
    discount_value = db.Column(db.Float, nullable=False, default=0)
    max_uses = db.Column(db.Integer, nullable=False, default=1)
    uses = db.Column(db.Integer, nullable=False, default=0)
    start_at = db.Column(db.DateTime, nullable=True)
    end_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    applies_to_product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    min_purchase = db.Column(db.Float, nullable=True, default=0)


class ReportCheckpoint(db.Model):
    """Track report reset timestamps per period"""
    __tablename__ = 'report_checkpoint'
    
    id = db.Column(db.Integer, primary_key=True)
    period = db.Column(db.String(20), unique=True, nullable=False)
    last_reset_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ReportCheckpoint {self.period}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'period': self.period,
            'last_reset_at': isoformat_datetime_sg(self.last_reset_at),
            'last_reset_at_display': format_datetime_sg(self.last_reset_at)
        }


class PaymentConfirmation(db.Model):
    """Payment confirmation model for proof of payment uploads"""
    __tablename__ = 'payment_confirmation'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    payment_method = db.Column(db.String(50), nullable=False)  # cod, gcash
    status = db.Column(db.String(50), default='pending', index=True)  # pending, approved, rejected
    customer_proof_image = db.Column(db.Text)  # File path or URL to uploaded proof
    admin_notes = db.Column(db.Text)  # Admin notes on verification
    admin_image = db.Column(db.Text)  # Admin uploaded image (e.g., delivery update)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PaymentConfirmation order:{self.order_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'payment_method': self.payment_method,
            'status': self.status,
            'customer_proof_image': self.customer_proof_image,
            'admin_notes': self.admin_notes,
            'admin_image': self.admin_image,
            'created_at': isoformat_datetime_sg(self.created_at),
            'created_at_display': format_datetime_sg(self.created_at),
            'updated_at': isoformat_datetime_sg(self.updated_at),
            'updated_at_display': format_datetime_sg(self.updated_at)
        }