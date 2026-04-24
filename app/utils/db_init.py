"""
ETERNO E-Commerce Platform - Database Initialization
Creates database tables and default admin account
"""
from app import db
from app.models import User, Product
from werkzeug.security import generate_password_hash
import json

def _add_missing_columns():
    """Add columns that were added to models after the table was first created."""
    if db.engine.url.drivername != "sqlite":
        return
    with db.engine.connect() as conn:
        # Add missing product columns
        result = conn.execute(db.text("PRAGMA table_info(product)"))
        product_columns = [row[1] for row in result.fetchall()]
        if "image_urls" not in product_columns:
            conn.execute(db.text("ALTER TABLE product ADD COLUMN image_urls TEXT"))
        if "badge" not in product_columns:
            conn.execute(db.text("ALTER TABLE product ADD COLUMN badge VARCHAR(20)"))
        if "tags" not in product_columns:
            conn.execute(db.text("ALTER TABLE product ADD COLUMN tags VARCHAR(100)"))
        conn.commit()

        # Add missing sale columns
        result = conn.execute(db.text("PRAGMA table_info(sale)"))
        sale_columns = [row[1] for row in result.fetchall()]
        if "amount_paid" not in sale_columns:
            conn.execute(db.text("ALTER TABLE sale ADD COLUMN amount_paid FLOAT DEFAULT 0"))
        if "change_amount" not in sale_columns:
            conn.execute(db.text("ALTER TABLE sale ADD COLUMN change_amount FLOAT DEFAULT 0"))
        conn.commit()

        # Add missing voucher columns
        result = conn.execute(db.text("PRAGMA table_info(voucher)"))
        voucher_columns = [row[1] for row in result.fetchall()]
        if "voucher_type" not in voucher_columns:
            conn.execute(db.text("ALTER TABLE voucher ADD COLUMN voucher_type VARCHAR(50) DEFAULT 'min_spend_discount'"))
        if "discount_value" not in voucher_columns:
            conn.execute(db.text("ALTER TABLE voucher ADD COLUMN discount_value FLOAT DEFAULT 0"))
        if "max_uses" not in voucher_columns:
            conn.execute(db.text("ALTER TABLE voucher ADD COLUMN max_uses INTEGER DEFAULT 1"))
        if "uses" not in voucher_columns:
            conn.execute(db.text("ALTER TABLE voucher ADD COLUMN uses INTEGER DEFAULT 0"))
        if "start_at" not in voucher_columns:
            conn.execute(db.text("ALTER TABLE voucher ADD COLUMN start_at DATETIME"))
        if "end_at" not in voucher_columns:
            conn.execute(db.text("ALTER TABLE voucher ADD COLUMN end_at DATETIME"))
        if "is_active" not in voucher_columns:
            conn.execute(db.text("ALTER TABLE voucher ADD COLUMN is_active BOOLEAN DEFAULT 1"))
        if "applies_to_product_id" not in voucher_columns:
            conn.execute(db.text("ALTER TABLE voucher ADD COLUMN applies_to_product_id INTEGER"))
        if "min_purchase" not in voucher_columns:
            conn.execute(db.text("ALTER TABLE voucher ADD COLUMN min_purchase FLOAT DEFAULT 0"))
        conn.commit()

        # Add missing user columns
        result = conn.execute(db.text("PRAGMA table_info(user)"))
        user_columns = [row[1] for row in result.fetchall()]
        if "is_verified" not in user_columns:
            conn.execute(db.text("ALTER TABLE user ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT 0"))
        conn.commit()


def init_database():
    """
    Initialize database tables and create default admin account
    This function is called automatically when the app starts
    """
    db.create_all()
    _add_missing_columns()

    # Check if default admin exists
    admin = User.query.filter_by(username='admin').first()
    
    if not admin:
        # Create default admin account
        admin = User(
            username='admin',
            email='admin@eterno.com',
            password=generate_password_hash('admin123'),
            role='admin',
            is_verified=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("[OK] Default admin account created:")
        print("  Username: admin")
        print("  Password: admin123")
        print("  Email: admin@eterno.com")
    
    # Seed sample products if none exist
    if Product.query.count() == 0:
        sample_products = [
            {
                'name': 'Premium Cotton T-Shirt',
                'description': '100% premium cotton, comfortable and breathable for everyday wear.',
                'price': 899.00,
                'stock': 15,
                'category': 'Shirts',
                'badge': 'new',
                'image_url': '/static/images/cover2.jpg',
                'tags': 'new'
            },
            {
                'name': 'Classic Denim Jacket',
                'description': 'Timeless denim jacket perfect for layering. Durable and versatile.',
                'price': 2499.00,
                'stock': 8,
                'category': 'Jackets',
                'badge': None,
                'image_url': '/static/images/cover2.jpg',
                'tags': ''
            },
            {
                'name': 'Comfortable Joggers',
                'description': 'Soft joggers perfect for relaxing or casual outings.',
                'price': 1299.00,
                'stock': 12,
                'category': 'Pants',
                'badge': 'sale',
                'image_url': '/static/images/cover2.jpg',
                'tags': 'sale'
            },
            {
                'name': 'Leather Crossbody Bag',
                'description': 'Premium leather bag for everyday essentials.',
                'price': 3999.00,
                'stock': 5,
                'category': 'Accessories',
                'badge': None,
                'image_url': '/static/images/cover2.jpg',
                'tags': ''
            },
            {
                'name': 'Limited Edition Hoodie',
                'description': 'Limited edition hoodie with exclusive design.',
                'price': 1799.00,
                'stock': 3,
                'category': 'Shirts',
                'badge': 'limited',
                'image_url': '/static/images/cover2.jpg',
                'tags': 'limited'
            },
            {
                'name': 'Summer Collection Shorts',
                'description': 'Breathable shorts perfect for summer.',
                'price': 799.00,
                'stock': 20,
                'category': 'Pants',
                'badge': 'new',
                'image_url': '/static/images/cover2.jpg',
                'tags': 'new'
            }
        ]
        
        for product_data in sample_products:
            product = Product(**product_data)
            db.session.add(product)
        
        db.session.commit()
        print(f"[OK] {len(sample_products)} sample products created for initial setup")
    
    print("[OK] Database initialized successfully")

def seed_sample_data():
    """
    Sample seeding intentionally disabled.
    """
    print("[INFO] Sample data seeding is disabled. Add products manually via admin inventory.")