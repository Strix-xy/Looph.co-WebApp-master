"""
ETERNO E-Commerce Platform - PDF Receipt Generator
Generates PDF receipts for sales and orders
"""
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import json
from datetime import datetime
from app.utils.helpers import format_datetime_sg

def generate_sale_receipt(sale):
    """
    Generate PDF receipt for POS sale
    
    Args:
        sale: Sale model instance
    
    Returns:
        BytesIO buffer containing PDF data
    """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Receipt header
    p.setFont("Helvetica-Bold", 20)
    p.drawString(220, 750, "Looph")
    p.setFont("Helvetica", 10)
    p.drawString(190, 730, "Looph POS Receipt")
    p.line(50, 720, 550, 720)
    
    # Sale information
    p.setFont("Helvetica", 12)
    p.drawString(50, 700, f"Sale ID: {sale.id}")
    p.drawString(50, 680, f"Date: {format_datetime_sg(sale.created_at)}")
    p.drawString(50, 660, "Customer: POS Walk-in")
    processed_by = getattr(sale.user, 'username', 'Admin')
    p.drawString(50, 640, f"Processed By: {processed_by}")
    p.drawString(50, 620, f"Payment: {sale.payment_method.upper()}")
    p.drawString(50, 600, f"Amount Paid: ₱{float(getattr(sale, 'amount_paid', 0) or 0):.2f}")
    p.drawString(50, 580, f"Change Due: ₱{float(getattr(sale, 'change_amount', 0) or 0):.2f}")
    
    if sale.discount_type:
        p.drawString(50, 560, f"Discount Type: {sale.discount_type.upper()}")
    else:
        p.drawString(50, 560, "Discount Type: NONE")
    
    p.line(50, 550, 550, 550)
    
    # Items table header
    try:
        items = json.loads(sale.items or '[]')
    except (TypeError, json.JSONDecodeError):
        items = []
    
    y_position = 570
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y_position, "Item")
    p.drawString(300, y_position, "Qty")
    p.drawString(380, y_position, "Price")
    p.drawString(480, y_position, "Total")
    
    y_position -= 20
    p.setFont("Helvetica", 10)
    
    subtotal = 0
    
    for item in items:
        name = (item.get('product_name') or item.get('name') or 'Item')[:35]
        quantity = int(item.get('quantity', 0))
        price = float(item.get('price', 0))
        line_total = price * quantity
        subtotal += line_total
        
        p.drawString(50, y_position, name)
        p.drawString(300, y_position, str(quantity))
        p.drawString(380, y_position, f"₱{price:.2f}")
        p.drawString(480, y_position, f"₱{line_total:.2f}")
        y_position -= 20
        
        # Check if we need a new page
        if y_position < 150:
            p.showPage()
            y_position = 750
    
    # Totals
    p.line(50, y_position, 550, y_position)
    y_position -= 20
    
    p.setFont("Helvetica", 10)
    p.drawString(380, y_position, "Subtotal:")
    p.drawString(480, y_position, f"₱{subtotal:.2f}")
    y_position -= 20
    
    discount_amount = float(sale.discount_amount or 0)
    if discount_amount > 0:
        p.drawString(380, y_position, "Discount:")
        p.drawString(480, y_position, f"-₱{discount_amount:.2f}")
        y_position -= 20
    
    p.setFont("Helvetica-Bold", 14)
    p.drawString(380, y_position, "TOTAL:")
    p.drawString(480, y_position, f"₱{sale.total_amount:.2f}")
    
    # Footer
    y_position -= 40
    p.setFont("Helvetica", 8)
    p.drawCentredString(300, y_position, "Thank you for your purchase!")
    p.drawCentredString(300, y_position - 15, "Looph")
    
    p.save()
    buffer.seek(0)
    return buffer

def generate_order_receipt(order):
    """
    Generate PDF receipt for customer order
    
    Args:
        order: Order model instance
    
    Returns:
        BytesIO buffer containing PDF data
    """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Receipt header
    p.setFont("Helvetica-Bold", 20)
    p.drawString(220, 750, "Looph")
    p.setFont("Helvetica", 10)
    p.drawString(200, 730, "Order Receipt")
    p.line(50, 720, 550, 720)
    
    # Order information
    p.setFont("Helvetica", 12)
    p.drawString(50, 700, f"Order ID: {order.id}")
    p.drawString(50, 680, f"Date: {format_datetime_sg(order.created_at)}")
    p.drawString(50, 660, f"Customer: {order.customer_name}")
    p.drawString(50, 640, f"Email: {order.customer_email}")
    p.drawString(50, 620, f"Payment: {order.payment_method.upper()}")
    p.drawString(50, 600, f"Status: {order.status.upper()}")
    
    y_start = 580
    if order.customer_address:
        p.setFont("Helvetica", 10)
        p.drawString(50, y_start, f"Address: {order.customer_address[:60]}")
        y_start -= 20
    
    p.line(50, y_start, 550, y_start)
    
    # Items table header
    items = json.loads(order.items)
    y_position = y_start - 20
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y_position, "Item")
    p.drawString(300, y_position, "Qty")
    p.drawString(380, y_position, "Price")
    p.drawString(480, y_position, "Total")
    
    y_position -= 20
    p.setFont("Helvetica", 10)
    
    # List all items
    for item in items:
        name = item['product_name'][:35]
        p.drawString(50, y_position, name)
        p.drawString(300, y_position, str(item['quantity']))
        p.drawString(380, y_position, f"₱{item['price']:.2f}")
        p.drawString(480, y_position, f"₱{item['price'] * item['quantity']:.2f}")
        y_position -= 20
        
        # Check if we need a new page
        if y_position < 150:
            p.showPage()
            y_position = 750
    
    # Totals
    p.line(50, y_position, 550, y_position)
    y_position -= 20

    discount_amount = max(0, (order.subtotal + (order.shipping_fee or 0) - order.total_amount))
    if discount_amount > 0:
        p.setFont("Helvetica", 10)
        p.drawString(380, y_position, "Subtotal:")
        p.drawString(480, y_position, f"₱{order.subtotal:.2f}")
        y_position -= 20
        p.drawString(380, y_position, "Discount:")
        p.drawString(480, y_position, f"-₱{discount_amount:.2f}")
        y_position -= 20
    else:
        p.setFont("Helvetica", 10)
        p.drawString(380, y_position, "Subtotal:")
        p.drawString(480, y_position, f"₱{order.subtotal:.2f}")
        y_position -= 20

    p.drawString(380, y_position, "Delivery Fee:")
    p.drawString(480, y_position, f"₱{order.shipping_fee:.2f}")
    y_position -= 20

    p.setFont("Helvetica-Bold", 14)
    p.drawString(380, y_position, "TOTAL:")
    p.drawString(480, y_position, f"₱{order.total_amount:.2f}")
    
    # Footer
    y_position -= 40
    p.setFont("Helvetica", 8)
    p.drawCentredString(300, y_position, "Thank you for shopping with us!")
    p.drawCentredString(300, y_position - 15, "Looph")
    
    p.save()
    buffer.seek(0)
    return buffer


def generate_sales_report_pdf(period_label, start_date, end_date, metrics):
    """
    Generate PDF summary report for selected period.
    """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(300, 770, "Looph Sales Report")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, 740, f"Period: {period_label}")
    p.drawString(50, 720, f"Start: {format_datetime_sg(start_date)}")
    p.drawString(50, 700, f"End: {format_datetime_sg(end_date)}")
    p.line(50, 690, 550, 690)
    
    y_position = 670
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y_position, "Revenue Summary")
    y_position -= 25
    
    p.setFont("Helvetica", 11)
    p.drawString(60, y_position, f"Total Revenue: ₱{metrics.get('total_revenue', 0):,.2f}")
    y_position -= 18
    p.drawString(60, y_position, f"From Customer Orders: ₱{metrics.get('orders_revenue', 0):,.2f}")
    y_position -= 18
    p.drawString(60, y_position, f"From POS Sales: ₱{metrics.get('pos_revenue', 0):,.2f}")
    y_position -= 25
    
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y_position, "Transaction Counts")
    y_position -= 25
    
    p.setFont("Helvetica", 11)
    p.drawString(60, y_position, f"Customer Orders: {metrics.get('orders_count', 0)}")
    y_position -= 18
    p.drawString(60, y_position, f"POS Sales: {metrics.get('pos_count', 0)}")
    y_position -= 18
    total_transactions = metrics.get('orders_count', 0) + metrics.get('pos_count', 0)
    p.drawString(60, y_position, f"Total Transactions: {total_transactions}")
    y_position -= 25
    
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y_position, "Discounts Applied")
    y_position -= 25
    
    p.setFont("Helvetica", 11)
    p.drawString(60, y_position, f"Customer Order Discounts: ₱{metrics.get('discounts_orders', 0):,.2f}")
    y_position -= 18
    p.drawString(60, y_position, f"POS Discounts: ₱{metrics.get('discounts_pos', 0):,.2f}")
    y_position -= 18
    p.drawString(60, y_position, f"Total Discounts: ₱{metrics.get('combined_discounts', 0):,.2f}")
    y_position -= 40
    
    p.setFont("Helvetica", 9)
    p.drawCentredString(300, y_position, "Generated via Looph Admin Dashboard")
    
    p.save()
    buffer.seek(0)
    return buffer


def generate_dashboard_report_pdf(metrics, status_breakdown, recent_orders):
    """Generate PDF report for admin dashboard snapshot."""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(300, 770, "Looph Dashboard Report")
    p.setFont("Helvetica", 10)
    p.drawCentredString(300, 754, f"Generated: {format_datetime_sg(datetime.utcnow())}")
    p.line(50, 744, 550, 744)

    y = 724
    p.setFont("Helvetica-Bold", 13)
    p.drawString(50, y, "KPI Summary")
    y -= 22
    p.setFont("Helvetica", 11)
    p.drawString(60, y, f"Revenue: P{float(metrics.get('revenue', 0) or 0):,.2f}")
    y -= 18
    p.drawString(60, y, f"Orders: {int(metrics.get('orders', 0) or 0)}")
    y -= 18
    p.drawString(60, y, f"Customers: {int(metrics.get('customers', 0) or 0)}")
    y -= 18
    p.drawString(60, y, f"Average Order Value: P{float(metrics.get('avg_order_value', 0) or 0):,.2f}")
    y -= 26

    p.setFont("Helvetica-Bold", 13)
    p.drawString(50, y, "Order Status Breakdown")
    y -= 22
    p.setFont("Helvetica", 11)
    for key in ("processing", "shipped", "delivered", "completed", "cancelled"):
        p.drawString(60, y, f"{key.title()}: {int(status_breakdown.get(key, 0) or 0)}")
        y -= 16
    y -= 10

    p.setFont("Helvetica-Bold", 13)
    p.drawString(50, y, "Recent Orders")
    y -= 20
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "Reference")
    p.drawString(150, y, "Customer")
    p.drawString(315, y, "Status")
    p.drawString(400, y, "Total")
    p.drawString(485, y, "Date")
    y -= 14
    p.setFont("Helvetica", 9)

    for order in recent_orders[:12]:
        if y < 70:
            p.showPage()
            y = 760
            p.setFont("Helvetica-Bold", 10)
            p.drawString(50, y, "Reference")
            p.drawString(150, y, "Customer")
            p.drawString(315, y, "Status")
            p.drawString(400, y, "Total")
            p.drawString(485, y, "Date")
            y -= 14
            p.setFont("Helvetica", 9)
        p.drawString(50, y, str(order.get("reference", ""))[:14])
        p.drawString(150, y, str(order.get("customer_name", ""))[:28])
        p.drawString(315, y, str(order.get("status", ""))[:12].upper())
        p.drawRightString(470, y, f"P{float(order.get('total_amount', 0) or 0):,.2f}")
        p.drawString(485, y, str(order.get("created_at_display", ""))[:16])
        y -= 14

    p.save()
    buffer.seek(0)
    return buffer