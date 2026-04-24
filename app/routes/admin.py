"""
ETERNO E-Commerce Platform - Admin Routes
Handles admin dashboard, POS, inventory management, and sales
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, send_file, current_app
from app import db
from app.models import User, Product, Sale, Order, ReportCheckpoint, Voucher, PaymentConfirmation
from app.utils.helpers import (
    calculate_discount, validate_product_data, 
    sanitize_string, validate_payment_method,
    get_period_range, get_period_label, normalize_period
)
from app.utils.export import export_to_excel
from app.utils.pdf import generate_sale_receipt, generate_sales_report_pdf, generate_dashboard_report_pdf
from app.utils.email import send_order_status_email
import json
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from uuid import uuid4

admin_bp = Blueprint('admin', __name__)


def _normalize_product_tags(raw_tags):
    """Normalize product tags to supported values."""
    allowed = {"new", "limited", "sale"}
    if not raw_tags:
        return ""
    if isinstance(raw_tags, str):
        candidates = [part.strip().lower() for part in raw_tags.split(",")]
    elif isinstance(raw_tags, list):
        candidates = [sanitize_string(part, max_length=20).lower() for part in raw_tags]
    else:
        candidates = []
    tags = []
    for tag in candidates:
        if tag in allowed and tag not in tags:
            tags.append(tag)
    return ",".join(tags)

# ==================== DASHBOARD ====================

@admin_bp.route('/dashboard')
def dashboard():
    if session.get('role') not in ('admin', 'staff', 'cashier'):
        return redirect(url_for('auth.login'))
    
    total_products = Product.query.count()
    total_customers = User.query.filter_by(role='customer').count()
    checkpoint = ReportCheckpoint.query.filter_by(period='overall').first()
    baseline = checkpoint.last_reset_at if checkpoint else None

    sale_query = Sale.query
    order_query = Order.query
    if baseline:
        sale_query = sale_query.filter(Sale.created_at >= baseline)
        order_query = order_query.filter(Order.created_at >= baseline)

    sales = sale_query.order_by(Sale.created_at.desc()).all()
    orders = order_query.order_by(Order.created_at.desc()).all()
    pos_revenue = sum(float(s.total_amount or 0) for s in sales)
    order_revenue = sum(float(o.total_amount or 0) for o in orders)
    total_revenue = pos_revenue + order_revenue
    total_orders = len(sales) + len(orders)
    avg_order_value = (total_revenue / total_orders) if total_orders else 0

    recent_orders = []
    for order in orders[:10]:
        recent_orders.append({
            'id': order.id,
            'reference': f"ORD-{order.id}",
            'customer_name': order.customer_name,
            'payment_method': order.payment_method,
            'status': order.status,
            'total_amount': float(order.total_amount or 0),
            'created_at_display': order.to_dict().get('created_at_display')
        })
    
    return render_template('admin_dashboard.html',
                         total_products=total_products,
                         total_customers=total_customers,
                         total_revenue=total_revenue,
                         total_orders=total_orders,
                         avg_order_value=avg_order_value,
                         recent_orders=recent_orders)


# ==================== POS SYSTEM ====================

@admin_bp.route('/pos')
def pos():
    if session.get('role') not in ('admin', 'cashier'):
        return redirect(url_for('auth.login'))
    
    # Get all products for POS listing (tiles can visually indicate stock state).
    products = Product.query.order_by(Product.name.asc()).all()
    products_payload = [product.to_dict() for product in products]
    
    return render_template('admin_pos.html', products=products, products_payload=products_payload)


@admin_bp.route('/sales/create', methods=['POST'])
def create_sale():
    if session.get('role') not in ('admin', 'cashier'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.json
        items = data.get('items', [])
        payment_method = data.get('payment_method', 'cash')
        discount_type = data.get('discount_type', 'none')
        voucher_code = (data.get('voucher_code') or '').strip().upper()
        
        # Validate items
        if not items:
            return jsonify({'error': 'No items in sale'}), 400
        
        # Validate payment method
        if not validate_payment_method(payment_method):
            return jsonify({'error': 'Invalid payment method'}), 400
        
        # Calculate subtotal and validate stock
        subtotal = 0
        for item in items:
            product = Product.query.get(item.get('product_id'))
            
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            
            quantity = item.get('quantity', 0)
            if not product.is_in_stock(quantity):
                return jsonify({'error': f'Insufficient stock for {product.name}'}), 400
            
            subtotal += product.price * quantity
        
        discount_amount = calculate_discount(subtotal, discount_type)
        manual_discount = float(data.get('manual_discount_amount', 0) or 0)
        if manual_discount > 0:
            discount_amount += manual_discount
        if voucher_code:
            voucher = Voucher.query.filter_by(code=voucher_code, is_active=True).first()
            if not voucher:
                return jsonify({'error': 'Invalid voucher code'}), 400
            if voucher.max_uses and (voucher.uses or 0) >= voucher.max_uses:
                return jsonify({'error': 'Voucher has reached maximum uses'}), 400
            now = datetime.utcnow()
            if voucher.start_at and now < voucher.start_at:
                return jsonify({'error': 'Voucher is not yet valid'}), 400
            if voucher.end_at and now > voucher.end_at:
                return jsonify({'error': 'Voucher has expired'}), 400
            if voucher.min_purchase and subtotal < float(voucher.min_purchase):
                return jsonify({'error': f'Minimum purchase ₱{float(voucher.min_purchase):,.2f} required'}), 400
            if voucher.voucher_type in ('product_discount', 'min_spend_discount', 'bogo'):
                discount_amount += min(float(voucher.discount_value), subtotal)
            elif voucher.voucher_type == 'free_delivery':
                discount_amount += 0
            voucher.uses = (voucher.uses or 0) + 1
        discount_amount = min(discount_amount, subtotal)
        final_total = subtotal - discount_amount
        
        amount_paid = float(data.get('amount_paid', final_total) or final_total)
        if amount_paid < final_total:
            return jsonify({'error': 'Amount paid must be equal to or greater than the total'}), 400
        change_amount = max(0, amount_paid - final_total)
        
        # Update product stock
        for item in items:
            product = Product.query.get(item['product_id'])
            product.reduce_stock(item['quantity'])
        
        # Create sale record
        new_sale = Sale(
            user_id=session.get('user_id'),
            total_amount=final_total,
            payment_method=payment_method,
            discount_type=discount_type if discount_type != 'none' else None,
            discount_amount=discount_amount,
            amount_paid=amount_paid,
            change_amount=change_amount,
            items=json.dumps(items)
        )
        
        db.session.add(new_sale)
        db.session.commit()
        
        # Export to Excel
        export_to_excel()
        
        return jsonify({
            'success': True,
            'sale_id': new_sale.id,
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'final_total': final_total,
            'amount_paid': amount_paid,
            'change_amount': change_amount
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create sale'}), 500


@admin_bp.route('/receipt/<int:sale_id>')
def generate_receipt(sale_id):
    if session.get('role') not in ('admin', 'cashier'):
        return redirect(url_for('auth.login'))
    
    sale = Sale.query.get_or_404(sale_id)
    buffer = generate_sale_receipt(sale)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'receipt_{sale_id}.pdf',
        mimetype='application/pdf'
    )


# ==================== INVENTORY MANAGEMENT ====================

@admin_bp.route('/inventory')
def inventory():
    if session.get('role') not in ('admin', 'staff'):
        return redirect(url_for('auth.login'))
    
    # Get all products
    products = Product.query.order_by(Product.name).all()
    
    # Prepare products data as JSON for JavaScript
    products_payload = [product.to_dict() for product in products]
    
    return render_template('admin_inventory.html', 
                         products=products, 
                         products_payload=products_payload)


@admin_bp.route('/products/add', methods=['POST'])
def add_product():
    if session.get('role') not in ('admin', 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.json
        
        # Validate product data
        is_valid, error_msg = validate_product_data(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        badge = sanitize_string(data.get('badge', ''), max_length=20).lower()
        if badge not in ('new', 'sale', 'limited'):
            badge = None
        image_urls_raw = data.get('image_urls')
        if isinstance(image_urls_raw, list):
            urls = [sanitize_string(u, max_length=500) for u in image_urls_raw[:20] if u]
        else:
            single = sanitize_string(data.get('image_url', ''), max_length=500)
            urls = [single] if single else []
        primary = urls[0] if urls else sanitize_string(data.get('image_url', ''), max_length=500)
        new_product = Product(
            name=sanitize_string(data['name'], max_length=100),
            description=sanitize_string(data.get('description', '')),
            price=float(data['price']),
            stock=int(data['stock']),
            category=sanitize_string(data.get('category', ''), max_length=50),
            badge=badge,
            tags=_normalize_product_tags(data.get('tags')),
            image_url=primary,
            image_urls=json.dumps(urls) if urls else None,
            is_pinned=bool(data.get('is_pinned', False))
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        # Export to Excel
        export_to_excel()
        
        return jsonify({
            'success': True,
            'product': new_product.to_dict()
        })
    
    except ValueError as e:
        return jsonify({'error': 'Invalid data format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to add product: {str(e)}'}), 500


@admin_bp.route('/products/update/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    if session.get('role') not in ('admin', 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        product = Product.query.get_or_404(product_id)
        data = request.json
        
        # Validate if updating critical fields
        if 'price' in data or 'stock' in data or 'name' in data:
            validation_payload = {
                'name': data.get('name', product.name),
                'price': data.get('price', product.price),
                'stock': data.get('stock', product.stock)
            }
            is_valid, error_msg = validate_product_data(validation_payload)
            if not is_valid:
                return jsonify({'error': error_msg}), 400
        
        # Update fields if provided
        if 'name' in data:
            product.name = sanitize_string(data['name'], max_length=100)
        
        if 'description' in data:
            product.description = sanitize_string(data['description'])
        
        if 'price' in data:
            product.price = float(data['price'])
        
        if 'stock' in data:
            product.stock = int(data['stock'])
        
        if 'category' in data:
            product.category = sanitize_string(data['category'], max_length=50)
        
        if 'image_urls' in data and isinstance(data['image_urls'], list):
            urls = [sanitize_string(u, max_length=500) for u in data['image_urls'][:20] if u]
            product.image_urls = json.dumps(urls) if urls else None
            product.image_url = urls[0] if urls else (product.image_url or '')
        elif 'image_url' in data:
            product.image_url = sanitize_string(data['image_url'], max_length=500)
        if 'badge' in data:
            badge = sanitize_string(data.get('badge', ''), max_length=20).lower()
            product.badge = badge if badge in ('new', 'sale', 'limited') else None
        if 'is_pinned' in data:
            product.is_pinned = bool(data['is_pinned'])
        if 'tags' in data:
            product.tags = _normalize_product_tags(data.get('tags'))
        db.session.commit()
        
        # Export to Excel
        export_to_excel()
        
        return jsonify({
            'success': True,
            'product': product.to_dict()
        })
    
    except ValueError as e:
        return jsonify({'error': 'Invalid data format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update product'}), 500


@admin_bp.route('/products/delete/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    if session.get('role') not in ('admin', 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        product = Product.query.get_or_404(product_id)
        
        db.session.delete(product)
        db.session.commit()
        
        # Export to Excel
        export_to_excel()
        
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete product'}), 500


# ==================== ORDER MANAGEMENT ====================

@admin_bp.route('/orders')
def get_orders():
    """Get all orders for admin dashboard with pagination support"""
    if session.get('role') not in ('admin', 'staff', 'cashier'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        limit = request.args.get('limit', None, type=int)
        
        checkpoint = ReportCheckpoint.query.filter_by(period='overall').first()
        baseline = checkpoint.last_reset_at if checkpoint else None
        
        orders_query = Order.query
        sales_query = Sale.query
        if baseline:
            orders_query = orders_query.filter(Order.created_at >= baseline)
            sales_query = sales_query.filter(Sale.created_at >= baseline)
        
        orders_query = orders_query.order_by(Order.created_at.desc())
        sales_query = sales_query.order_by(Sale.created_at.desc())
        
        total_customer_orders = orders_query.count()
        total_pos_sales = sales_query.count()
        
        orders = orders_query.limit(limit).all() if limit else orders_query.all()
        sales = sales_query.limit(limit).all() if limit else sales_query.all()
        
        transactions = []
        
        for order in orders:
            order_data = order.to_dict()
            discount_amount = order_data['subtotal'] + (order_data.get('shipping_fee') or 0) - order_data['total_amount']
            discount_amount = max(0, round(discount_amount, 2))
            transactions.append({
                'id': order.id,
                'record_type': 'customer_order',
                'reference': f"ORD-{order.id}",
                'created_at': order_data['created_at'],
                'created_at_display': order_data['created_at_display'],
                'customer_name': order_data['customer_name'],
                'customer_email': order_data['customer_email'],
                'customer_address': order_data['customer_address'],
                'payment_method': order_data['payment_method'],
                'status': order_data['status'],
                'subtotal': order_data['subtotal'],
                'shipping_fee': order_data['shipping_fee'],
                'discount_amount': discount_amount,
                'discount_type': 'voucher' if discount_amount else None,
                'total_amount': order_data['total_amount'],
                'items': order_data.get('items_data', []),
                'processed_by': 'Online Checkout'
            })
        
        for sale in sales:
            sale_data = sale.to_dict()
            transactions.append({
                'id': sale.id,
                'record_type': 'pos_sale',
                'reference': f"POS-{sale.id}",
                'created_at': sale_data['created_at'],
                'created_at_display': sale_data['created_at_display'],
                'customer_name': 'POS Walk-in',
                'customer_email': None,
                'customer_address': None,
                'payment_method': sale_data['payment_method'],
                'status': 'completed',
                'subtotal': sale_data['subtotal'],
                'shipping_fee': 0,
                'discount_amount': sale_data.get('discount_amount') or 0,
                'discount_type': sale_data['discount_type'],
                'total_amount': sale_data['total_amount'],
                'items': sale_data.get('items_data', []),
                'processed_by': sale.user.username if getattr(sale, 'user', None) else None
            })
        
        transactions.sort(key=lambda x: x['created_at'] or "", reverse=True)
        if limit:
            transactions = transactions[:limit]
        return jsonify({
            'success': True,
            'transactions': transactions,
            'totals': {
                'customer_orders': total_customer_orders,
                'pos_sales': total_pos_sales,
                'combined': total_customer_orders + total_pos_sales
            }
        })
    
    except Exception as e:
        return jsonify({'error': 'Failed to fetch orders'}), 500


@admin_bp.route('/orders/<int:order_id>')
def get_order_details(order_id):
    """Get detailed information about a specific order"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        order = Order.query.get(order_id)
        if order:
            order_data = order.to_dict()
            discount_amount = order_data['subtotal'] + (order_data.get('shipping_fee') or 0) - order_data['total_amount']
            discount_amount = max(0, round(discount_amount, 2))
            return jsonify({
                'success': True,
                'record_type': 'customer_order',
                'transaction': {
                    'id': order.id,
                    'reference': f"ORD-{order.id}",
                    'created_at': order_data['created_at'],
                    'created_at_display': order_data['created_at_display'],
                    'customer_name': order_data['customer_name'],
                    'customer_email': order_data['customer_email'],
                    'customer_address': order_data['customer_address'],
                    'payment_method': order_data['payment_method'],
                    'status': order_data['status'],
                    'subtotal': order_data['subtotal'],
                    'shipping_fee': order_data['shipping_fee'],
                    'discount_amount': discount_amount,
                    'discount_type': 'voucher' if discount_amount else None,
                    'total_amount': order_data['total_amount'],
                    'items': order_data.get('items_data', []),
                    'processed_by': 'Online Checkout'
                }
            })
        
        sale = Sale.query.get(order_id)
        if sale:
            sale_data = sale.to_dict()
            return jsonify({
                'success': True,
                'record_type': 'pos_sale',
                'transaction': {
                    'id': sale.id,
                    'reference': f"POS-{sale.id}",
                    'created_at': sale_data['created_at'],
                    'created_at_display': sale_data['created_at_display'],
                    'customer_name': 'POS Walk-in',
                    'customer_email': None,
                    'customer_address': None,
                    'payment_method': sale_data['payment_method'],
                    'status': 'completed',
                    'subtotal': sale_data['subtotal'],
                    'shipping_fee': 0,
                    'discount_amount': sale_data.get('discount_amount') or 0,
                    'discount_type': sale_data['discount_type'],
                    'total_amount': sale_data['total_amount'],
                    'items': sale_data.get('items_data', []),
                    'processed_by': sale.user.username if getattr(sale, 'user', None) else None
                }
            })
        return jsonify({'error': 'Transaction not found'}), 404
    
    except Exception as e:
        return jsonify({'error': 'Failed to fetch order details'}), 500


@admin_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        order = Order.query.get_or_404(order_id)
        data = request.json
        raw_status = (data.get('status') or '').strip().lower()
        legacy_map = {
            'pending': 'processing',
            'out_for_delivery': 'shipped'
        }
        new_status = legacy_map.get(raw_status, raw_status)

        valid_statuses = ['processing', 'shipped', 'delivered', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({'error': 'Invalid status'}), 400
        
        old_status = order.status
        order.status = new_status
        db.session.commit()
        export_to_excel()
        try:
            send_order_status_email(order, old_status, new_status)
        except Exception:
            pass
        
        return jsonify({
            'success': True,
            'order': order.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update order status'}), 500


@admin_bp.route('/customers')
def get_customers():
    """Get customer accounts for admin management."""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        customers = User.query.filter_by(role='customer').order_by(User.created_at.desc()).all()
        return jsonify({
            'success': True,
            'customers': [{
                'id': c.id,
                'username': c.username,
                'email': c.email,
                'full_name': c.full_name,
                'created_at_display': c.to_dict().get('created_at_display')
            } for c in customers]
        })
    except Exception:
        return jsonify({'error': 'Failed to fetch customers'}), 500


@admin_bp.route('/customers/<int:user_id>', methods=['DELETE'])
def delete_customer(user_id):
    """Delete customer account and related records."""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        customer = User.query.get_or_404(user_id)
        if customer.role != 'customer':
            return jsonify({'error': 'Only customer accounts can be deleted'}), 400
        if session.get('user_id') == customer.id:
            return jsonify({'error': 'You cannot delete your own active account'}), 400
        db.session.delete(customer)
        db.session.commit()
        export_to_excel()
        return jsonify({'success': True})
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete customer'}), 500


@admin_bp.route('/products/list')
def get_products_list():
    """Get all products for admin dashboard"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        products = Product.query.order_by(Product.name).all()
        products_list = [product.to_dict() for product in products]
        
        return jsonify({
            'success': True,
            'products': products_list
        })
    
    except Exception as e:
        return jsonify({'error': 'Failed to fetch products'}), 500


@admin_bp.route('/products/<int:product_id>/orders')
def get_product_orders(product_id):
    """Get order IDs that contain a specific product"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Get all orders
        orders = Order.query.all()
        order_ids = []
        
        # Check each order's items for the product
        for order in orders:
            try:
                items = json.loads(order.items)
                for item in items:
                    if item.get('product_id') == product_id:
                        order_ids.append(order.id)
                        break  # Only add order ID once
            except:
                continue
        
        return jsonify({
            'success': True,
            'order_ids': sorted(order_ids, reverse=True)  # Most recent first
        })
    
    except Exception as e:
        return jsonify({'error': 'Failed to fetch product orders'}), 500


@admin_bp.route('/revenue')
def get_revenue_breakdown():
    """Get revenue breakdown for admin dashboard"""
    if session.get('role') not in ('admin', 'staff', 'cashier'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        checkpoint = ReportCheckpoint.query.filter_by(period='overall').first()
        baseline = checkpoint.last_reset_at if checkpoint else None
        
        # Calculate revenue from orders
        orders_query = Order.query
        if baseline:
            orders_query = orders_query.filter(Order.created_at >= baseline)
        orders = orders_query.all()
        orders_revenue = sum(order.total_amount for order in orders)
        orders_count = len(orders)
        
        # Calculate revenue from POS sales
        sales_query = Sale.query
        if baseline:
            sales_query = sales_query.filter(Sale.created_at >= baseline)
        sales = sales_query.all()
        pos_revenue = sum(sale.total_amount for sale in sales)
        pos_count = len(sales)
        
        total_revenue = orders_revenue + pos_revenue
        avg_order_value = total_revenue / (orders_count + pos_count) if (orders_count + pos_count) > 0 else 0
        
        return jsonify({
            'success': True,
            'revenue': {
                'total': total_revenue,
                'from_orders': orders_revenue,
                'from_pos': pos_revenue,
                'orders_count': orders_count,
                'pos_count': pos_count,
                'avg_order_value': avg_order_value
            }
        })
    
    except Exception as e:
        return jsonify({'error': 'Failed to fetch revenue'}), 500


@admin_bp.route('/revenue/history')
def get_revenue_history():
    """Get revenue breakdown by month for history view."""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        months = int(request.args.get('months', 12))
        months = min(max(1, months), 24)
        end = datetime.utcnow()
        history = []
        for i in range(months):
            start = end - timedelta(days=30)
            orders = Order.query.filter(
                Order.created_at >= start,
                Order.created_at < end
            ).all()
            sales = Sale.query.filter(
                Sale.created_at >= start,
                Sale.created_at < end
            ).all()
            from_orders = sum(o.total_amount for o in orders)
            from_pos = sum(s.total_amount for s in sales)
            total = from_orders + from_pos
            label = start.strftime('%b %Y') if start else ''
            history.append({
                'period_label': label,
                'total': total,
                'from_orders': from_orders,
                'from_pos': from_pos,
                'orders_count': len(orders),
                'pos_count': len(sales)
            })
            end = start
        history.reverse()
        return jsonify({'success': True, 'history': history})
    except Exception:
        return jsonify({'error': 'Failed to fetch revenue history'}), 500


@admin_bp.route('/reports/checkpoints')
def get_report_checkpoints():
    """Get last reset timestamps for report periods"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        checkpoints = ReportCheckpoint.query.all()
        return jsonify({
            'success': True,
            'checkpoints': {checkpoint.period: checkpoint.to_dict() for checkpoint in checkpoints}
        })
    except Exception:
        return jsonify({'error': 'Failed to fetch report checkpoints'}), 500


@admin_bp.route('/reports/reset', methods=['POST'])
def reset_reports():
    """Reset report baseline timestamp for a given period"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.json or {}
        period = data.get('period')
        period_key = normalize_period(period)
        
        if not period_key:
            return jsonify({'error': 'Invalid period'}), 400
        
        now = datetime.utcnow()
        checkpoint = ReportCheckpoint.query.filter_by(period=period_key).first()
        
        if checkpoint:
            checkpoint.last_reset_at = now
        else:
            checkpoint = ReportCheckpoint(period=period_key, last_reset_at=now)
            db.session.add(checkpoint)
        
        overall_checkpoint = ReportCheckpoint.query.filter_by(period='overall').first()
        if overall_checkpoint:
            overall_checkpoint.last_reset_at = now
        else:
            overall_checkpoint = ReportCheckpoint(period='overall', last_reset_at=now)
            db.session.add(overall_checkpoint)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'checkpoint': checkpoint.to_dict(),
            'message': f'{get_period_label(period_key)} reports reset.'
        })
    
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to reset reports'}), 500


@admin_bp.route('/reports/pdf')
def download_report_pdf():
    """Generate PDF sales report for the selected period"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        period = request.args.get('period', 'weekly')
        period_key = normalize_period(period)
        
        if not period_key:
            return jsonify({'error': 'Invalid period'}), 400
        
        checkpoint = ReportCheckpoint.query.filter_by(period=period_key).first()
        last_reset = checkpoint.last_reset_at if checkpoint else None
        start_date, end_date = get_period_range(period_key, last_reset)
        
        orders = Order.query.filter(
            Order.created_at >= start_date,
            Order.created_at <= end_date
        ).all()
        sales = Sale.query.filter(
            Sale.created_at >= start_date,
            Sale.created_at <= end_date
        ).all()
        
        orders_revenue = sum(order.total_amount for order in orders)
        pos_revenue = sum(sale.total_amount for sale in sales)
        orders_count = len(orders)
        pos_count = len(sales)
        total_revenue = orders_revenue + pos_revenue
        discounts_orders = sum(
            max(0, round(order.subtotal + (order.shipping_fee or 0) - order.total_amount, 2))
            for order in orders
        )
        discounts_pos = sum(max(0, sale.discount_amount or 0) for sale in sales)
        
        metrics = {
            'orders_revenue': orders_revenue,
            'pos_revenue': pos_revenue,
            'total_revenue': total_revenue,
            'orders_count': orders_count,
            'pos_count': pos_count,
            'discounts_orders': discounts_orders,
            'discounts_pos': discounts_pos,
            'combined_discounts': discounts_orders + discounts_pos
        }
        
        report_buffer = generate_sales_report_pdf(
            get_period_label(period_key),
            start_date,
            end_date,
            metrics
        )
        
        filename = f"sales_report_{period_key}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            report_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    
    except ValueError:
        return jsonify({'error': 'Invalid period'}), 400
    except Exception:
        return jsonify({'error': 'Failed to generate report'}), 500


@admin_bp.route('/dashboard/report/pdf')
def download_dashboard_report_pdf():
    """Generate PDF report for dashboard metrics and latest orders."""
    if session.get('role') not in ('admin', 'staff', 'cashier'):
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        checkpoint = ReportCheckpoint.query.filter_by(period='overall').first()
        baseline = checkpoint.last_reset_at if checkpoint else None

        orders_query = Order.query
        sales_query = Sale.query
        if baseline:
            orders_query = orders_query.filter(Order.created_at >= baseline)
            sales_query = sales_query.filter(Sale.created_at >= baseline)

        orders = orders_query.order_by(Order.created_at.desc()).all()
        sales = sales_query.order_by(Sale.created_at.desc()).all()
        orders_revenue = sum(float(o.total_amount or 0) for o in orders)
        pos_revenue = sum(float(s.total_amount or 0) for s in sales)
        total_revenue = orders_revenue + pos_revenue
        total_orders = len(orders) + len(sales)
        avg_order_value = (total_revenue / total_orders) if total_orders else 0

        customers = {
            (o.customer_email or o.customer_name or '').strip().lower()
            for o in orders if (o.customer_email or o.customer_name)
        }
        status_breakdown = {'processing': 0, 'shipped': 0, 'delivered': 0, 'completed': 0, 'cancelled': 0}
        for order in orders:
            status = (order.status or 'processing').strip().lower()
            if status not in status_breakdown:
                status = 'processing'
            status_breakdown[status] += 1

        recent_orders = [{
            'reference': f"ORD-{o.id}",
            'customer_name': o.customer_name,
            'status': o.status or 'processing',
            'total_amount': float(o.total_amount or 0),
            'created_at_display': o.to_dict().get('created_at_display') or ''
        } for o in orders[:20]]

        report_buffer = generate_dashboard_report_pdf(
            {
                'revenue': total_revenue,
                'orders': total_orders,
                'customers': len(customers),
                'avg_order_value': avg_order_value
            },
            status_breakdown,
            recent_orders
        )
        filename = f"dashboard_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        return send_file(report_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
    except Exception:
        return jsonify({'error': 'Failed to generate dashboard report'}), 500


# ==================== IMAGE UPLOAD ====================

@admin_bp.route('/products/upload-image', methods=['POST'])
def upload_product_image():
    """Upload product image file"""
    if session.get('role') not in ('admin', 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if running on Vercel (serverless environment)
    if os.environ.get('VERCEL'):
        return jsonify({
            'error': 'File upload not available in serverless environment. Please use direct image URLs instead.',
            'use_url_upload': True
        }), 400
    
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file is an image
        if not file.content_type.startswith('image/'):
            return jsonify({'error': 'File must be an image'}), 400
        
        # Save to the active Flask static directory (supports external theme static path).
        upload_folder = os.path.join(current_app.static_folder, 'images', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Generate secure filename with timestamp
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = f"{timestamp}{uuid4().hex[:8]}_{filename}"
        
        # Save file
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Return URL path
        image_url = url_for('static', filename=f'images/uploads/{filename}')
        
        return jsonify({
            'success': True,
            'image_url': image_url
        })
    
    except Exception as e:
        return jsonify({'error': 'Failed to upload image'}), 500


# ==================== VOUCHERS ====================

@admin_bp.route('/vouchers')
def vouchers():
    if session.get('role') not in ('admin', 'staff'):
        return redirect(url_for('auth.login'))
    vouchers_list = Voucher.query.order_by(Voucher.id.desc()).all()
    return render_template('admin_vouchers.html', vouchers=vouchers_list)


@admin_bp.route('/vouchers/create', methods=['POST'])
def create_voucher():
    if session.get('role') not in ('admin', 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        data = request.get_json() or request.form
        code = (data.get('code') or '').strip().upper()
        if not code:
            return jsonify({'error': 'Voucher code is required'}), 400
        if Voucher.query.filter_by(code=code).first():
            return jsonify({'error': 'Voucher code already exists'}), 400
        voucher_type = data.get('voucher_type') or 'min_spend_discount'
        discount_value = float(data.get('discount_value', 0))
        max_uses = int(data.get('max_uses', 1))
        min_purchase = float(data.get('min_purchase') or 0) or None
        start_at = data.get('start_at')
        end_at = data.get('end_at')
        if start_at:
            try:
                start_at = datetime.fromisoformat(start_at.replace('Z', '+00:00'))
            except Exception:
                start_at = None
        if end_at:
            try:
                end_at = datetime.fromisoformat(end_at.replace('Z', '+00:00'))
            except Exception:
                end_at = None
        v = Voucher(
            code=code,
            voucher_type=voucher_type,
            discount_value=discount_value,
            max_uses=max_uses,
            min_purchase=min_purchase,
            start_at=start_at,
            end_at=end_at,
            is_active=True
        )
        db.session.add(v)
        db.session.commit()
        return jsonify({
            'success': True,
            'id': v.id,
            'voucher': {
                'id': v.id,
                'code': v.code,
                'voucher_type': v.voucher_type,
                'discount_value': float(v.discount_value or 0),
                'uses': int(v.uses or 0),
                'max_uses': int(v.max_uses or 0),
                'end_at': v.end_at.isoformat() if v.end_at else '',
                'is_active': bool(v.is_active)
            }
        })
    except (ValueError, TypeError) as e:
        return jsonify({'error': 'Invalid data'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create voucher: {str(e)}'}), 500


@admin_bp.route('/vouchers/<int:voucher_id>/update', methods=['PUT'])
def update_voucher(voucher_id):
    if session.get('role') not in ('admin', 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403
    v = Voucher.query.get_or_404(voucher_id)
    try:
        data = request.get_json()
        if data.get('is_active') is not None:
            v.is_active = bool(data['is_active'])
        if 'discount_value' in data:
            v.discount_value = float(data['discount_value'])
        if 'max_uses' in data:
            v.max_uses = int(data['max_uses'])
        if 'min_purchase' in data:
            v.min_purchase = float(data['min_purchase']) or None
        db.session.commit()
        return jsonify({'success': True})
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid data'}), 400
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to update'}), 500


# ==================== PAYMENT CONFIRMATIONS ====================

@admin_bp.route('/payments/pending')
def get_pending_payments():
    """Get all pending payment confirmations"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        pending = PaymentConfirmation.query.filter_by(status='pending').all()
        payments_data = []
        
        for pc in pending:
            order = Order.query.get(pc.order_id)
            user = User.query.get(pc.user_id)
            
            if order and user:
                payments_data.append({
                    'id': pc.id,
                    'order_id': pc.order_id,
                    'order_reference': f"ORD-{pc.order_id}",
                    'customer_name': user.full_name or user.username,
                    'customer_email': user.email,
                    'payment_method': pc.payment_method,
                    'amount': float(order.total_amount or 0),
                    'customer_proof_image': pc.customer_proof_image,
                    'created_at': pc.created_at.isoformat() if pc.created_at else None,
                    'created_at_display': pc.created_at.strftime('%Y-%m-%d %H:%M') if pc.created_at else None
                })
        
        return jsonify({
            'success': True,
            'payments': payments_data
        })
    except Exception as e:
        return jsonify({'error': f'Failed to fetch payments: {str(e)}'}), 500


@admin_bp.route('/payments/<int:payment_id>/approve', methods=['PUT'])
def approve_payment(payment_id):
    """Approve a payment confirmation"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        pc = PaymentConfirmation.query.get_or_404(payment_id)
        data = request.get_json() or {}
        
        pc.status = 'approved'
        pc.admin_id = session.get('user_id')
        pc.admin_notes = sanitize_string(data.get('notes', ''), max_length=500)
        pc.updated_at = datetime.utcnow()
        
        # Update order status to processing
        order = Order.query.get(pc.order_id)
        if order:
            order.status = 'processing'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment approved successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to approve: {str(e)}'}), 500


@admin_bp.route('/payments/<int:payment_id>/reject', methods=['PUT'])
def reject_payment(payment_id):
    """Reject a payment confirmation"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        pc = PaymentConfirmation.query.get_or_404(payment_id)
        data = request.get_json() or {}
        
        pc.status = 'rejected'
        pc.admin_id = session.get('user_id')
        pc.admin_notes = sanitize_string(data.get('reason', ''), max_length=500)
        pc.updated_at = datetime.utcnow()
        
        # Update order status back to pending_payment for user to resubmit
        order = Order.query.get(pc.order_id)
        if order:
            order.status = 'pending_payment'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment rejected. Customer can resubmit proof.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to reject: {str(e)}'}), 500


@admin_bp.route('/payments/<int:payment_id>/upload-image', methods=['POST'])
def upload_admin_payment_image(payment_id):
    """Admin uploads image (delivery update, etc) for payment confirmation"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        pc = PaymentConfirmation.query.get_or_404(payment_id)
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not file.filename.split('.')[-1].lower() in allowed_extensions:
            return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF'}), 400
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads', 'admin-updates')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        unique_filename = f"{payment_id}_{uuid4().hex}_{secure_filename(file.filename)}"
        file_path = os.path.join(upload_dir, unique_filename)
        relative_path = f"/static/uploads/admin-updates/{unique_filename}"
        
        # Save file
        file.save(file_path)
        
        pc.admin_image = relative_path
        pc.admin_id = session.get('user_id')
        pc.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'image_url': relative_path,
            'message': 'Image uploaded successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500