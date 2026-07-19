"""
Orders Utility Functions — invoice PDF generation, order number, pricing.
"""
import io
from decimal import Decimal
from django.conf import settings
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT


def generate_invoice_pdf(order) -> HttpResponse:
    """Generate a PDF invoice for an Order and return an HttpResponse."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    brand_color = colors.HexColor('#6c63ff')

    title_style = ParagraphStyle(
        'BrandTitle', parent=styles['Title'],
        textColor=brand_color, fontSize=28, spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        textColor=colors.grey, fontSize=10
    )
    heading_style = ParagraphStyle(
        'Heading', parent=styles['Heading2'],
        textColor=brand_color, fontSize=12, spaceBefore=8, spaceAfter=4
    )
    normal = styles['Normal']
    right_style = ParagraphStyle('Right', parent=normal, alignment=TA_RIGHT)

    story = []

    # ── Header ──────────────────────────────────────────────────────────────
    story.append(Paragraph('ShopSphere', title_style))
    story.append(Paragraph('Premium E-Commerce Platform', subtitle_style))
    story.append(HRFlowable(width='100%', color=brand_color, spaceAfter=6))

    story.append(Paragraph(f'INVOICE — {order.order_number}', heading_style))

    # ── Meta table ──────────────────────────────────────────────────────────
    meta_data = [
        ['Order Date:', order.created_at.strftime('%B %d, %Y')],
        ['Order Number:', order.order_number],
        ['Payment Status:', order.get_status_display().upper()],
        ['Customer:', f'{order.user.get_full_name() or order.user.username}'],
        ['Email:', order.user.email],
    ]
    meta_table = Table(meta_data, colWidths=[45 * mm, 100 * mm])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6 * mm))

    # ── Addresses ────────────────────────────────────────────────────────────
    addr_data = [
        [Paragraph('<b>Shipping Address</b>', normal), Paragraph('<b>Billing Address</b>', normal)],
        [
            Paragraph(
                f'{order.shipping_full_name}<br/>'
                f'{order.shipping_address_line1}<br/>'
                f'{order.shipping_city}, {order.shipping_state} {order.shipping_postal_code}<br/>'
                f'{order.shipping_country}', normal
            ),
            Paragraph(
                f'{order.billing_full_name}<br/>'
                f'{order.billing_address_line1}<br/>'
                f'{order.billing_city}, {order.billing_state} {order.billing_postal_code}<br/>'
                f'{order.billing_country}', normal
            ),
        ]
    ]
    addr_table = Table(addr_data, colWidths=[85 * mm, 85 * mm])
    addr_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f7ff')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(addr_table)
    story.append(Spacer(1, 6 * mm))

    # ── Line Items ────────────────────────────────────────────────────────────
    story.append(Paragraph('Order Items', heading_style))

    items_header = [['#', 'Product', 'SKU', 'Unit Price', 'Qty', 'Total']]
    items_data = []
    for idx, item in enumerate(order.items.all(), 1):
        items_data.append([
            str(idx),
            item.product_name,
            item.product_sku or '—',
            f'${item.price:.2f}',
            str(item.quantity),
            f'${item.get_total_price():.2f}',
        ])

    table_data = items_header + items_data
    col_widths = [10 * mm, 65 * mm, 25 * mm, 22 * mm, 12 * mm, 22 * mm]
    items_table = Table(table_data, colWidths=col_widths)
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), brand_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f7ff')]),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e0e0e0')),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 4 * mm))

    # ── Totals ────────────────────────────────────────────────────────────────
    totals_data = [
        ['Subtotal:', f'${order.subtotal:.2f}'],
        ['Shipping:', f'${order.shipping_cost:.2f}'],
        ['Tax (10%):', f'${order.tax_amount:.2f}'],
    ]
    if order.discount_amount > 0:
        totals_data.append(['Discount:', f'-${order.discount_amount:.2f}'])
    totals_data.append(['', ''])
    totals_data.append(['TOTAL:', f'${order.total_amount:.2f}'])

    totals_table = Table(totals_data, colWidths=[130 * mm, 30 * mm])
    totals_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('TEXTCOLOR', (0, -1), (-1, -1), brand_color),
        ('LINEABOVE', (0, -1), (-1, -1), 1, brand_color),
        ('TOPPADDING', (0, -1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 10 * mm))

    # ── Footer ───────────────────────────────────────────────────────────────
    story.append(HRFlowable(width='100%', color=colors.HexColor('#e0e0e0')))
    story.append(Paragraph(
        'Thank you for shopping with ShopSphere! For any queries, contact support@shopsphere.com',
        ParagraphStyle('Footer', parent=normal, textColor=colors.grey, fontSize=8, alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ShopSphere-Invoice-{order.order_number}.pdf"'
    return response


def calculate_order_totals(cart, coupon=None, shipping_address=None):
    """Return a dict with subtotal, shipping, tax, discount, and total."""
    from django.conf import settings as conf

    subtotal = cart.get_subtotal()
    tax_rate = Decimal(str(getattr(conf, 'TAX_RATE', 0.10)))
    free_threshold = Decimal(str(getattr(conf, 'FREE_SHIPPING_THRESHOLD', 100.00)))
    flat_shipping = Decimal(str(getattr(conf, 'SHIPPING_FEE', 5.00)))

    shipping_cost = Decimal('0') if subtotal >= free_threshold else flat_shipping
    discount_amount = Decimal('0')

    if coupon:
        valid, _ = coupon.is_valid()
        if valid:
            discount_amount = Decimal(str(coupon.calculate_discount(subtotal)))

    taxable = subtotal - discount_amount
    tax_amount = (taxable * tax_rate).quantize(Decimal('0.01'))
    total = taxable + shipping_cost + tax_amount

    return {
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'tax_amount': tax_amount,
        'discount_amount': discount_amount,
        'total': total,
    }
