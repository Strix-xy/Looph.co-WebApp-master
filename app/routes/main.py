"""
ETERNO E-Commerce Platform - Main Public Routes
Handles public pages accessible to all visitors
"""
from flask import Blueprint, render_template
from app.models import Product, Review
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page - show homepage with featured products"""
    # Keep homepage product data fully dynamic from admin inventory.
    featured_products = (
        Product.query
        .filter(Product.stock > 0)
        .order_by(Product.is_pinned.desc(), Product.created_at.desc())
        .limit(10)
        .all()
    )
    products = Product.query.filter(Product.stock > 0).order_by(Product.is_pinned.desc(), Product.created_at.desc()).all()
    products_payload = []
    for product in products:
        avg_rating = db.session.query(db.func.avg(Review.rating)).filter(Review.product_id == product.id).scalar()
        review_count = db.session.query(db.func.count(Review.id)).filter(Review.product_id == product.id).scalar() or 0
        images = product.get_image_list()
        first_image = images[0] if images else product.image_url
        if not first_image:
            continue
        products_payload.append({
            'id': product.id,
            'name': product.name,
            'cat': (product.category or 'Uncategorized').lower(),
            'category': product.category or 'Uncategorized',
            'price': float(product.price or 0),
            'badge': product.badge,
            'rating': round(float(avg_rating), 1) if review_count > 0 else 5.0,
            'reviews': int(review_count),
            'stock': int(product.stock or 0),
            'desc': product.description or '',
            'description': product.description or '',
            'imgs': [first_image] if first_image else [],
            'image_url': first_image
        })
    return render_template('landing.html', featured_products=featured_products, products_payload=products_payload)