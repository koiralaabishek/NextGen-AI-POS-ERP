import base64
from apps.sales.models import Sale


class ThermalReceiptGenerator:
    """
    Thermal Receipt formatter and ESC/POS command byte generator
    supporting 58mm (32 columns) and 80mm (42-48 columns) rolls.
    """

    @classmethod
    def format_ascii_receipt(cls, sale: Sale, width: int = 42) -> str:
        org = sale.organization
        branch = sale.branch

        lines = []
        div = "=" * width
        sub_div = "-" * width

        def center(text: str) -> str:
            return text.center(width)[:width]

        def row(col1: str, col2: str) -> str:
            space = width - len(col1) - len(col2)
            if space < 1:
                col1 = col1[:width - len(col2) - 1]
                space = 1
            return f"{col1}{' ' * space}{col2}"

        # Header
        lines.append(div)
        lines.append(center(org.name.upper()))
        if branch.address:
            lines.append(center(branch.address))
        if org.tax_number:
            lines.append(center(f"PAN/VAT: {org.tax_number}"))
        if branch.phone:
            lines.append(center(f"Tel: {branch.phone}"))
        lines.append(center("TAX INVOICE"))
        lines.append(div)

        # Meta
        lines.append(row(f"Bill No: {sale.invoice_number}", ""))
        lines.append(row(f"Date: {sale.created_at.strftime('%Y-%m-%d %H:%M')}", f"Branch: {branch.code}"))
        if sale.cashier:
            lines.append(row(f"Cashier: {sale.cashier.first_name or sale.cashier.email.split('@')[0]}", ""))
        if sale.customer:
            lines.append(row(f"Customer: {sale.customer.name}", f"Phone: {sale.customer.phone or 'N/A'}"))
            if sale.customer.tax_number:
                lines.append(row(f"Buyer PAN: {sale.customer.tax_number}", ""))
        lines.append(sub_div)

        # Items Table
        lines.append(row("Item (Qty x Price)", "Subtotal"))
        lines.append(sub_div)

        for item in sale.items.select_related("variant", "variant__product"):
            prod_name = item.variant.product.name[:width - 15]
            lines.append(prod_name)
            detail = f"  {item.quantity} x {item.unit_price}"
            subtot_str = f"Rs. {item.subtotal}"
            lines.append(row(detail, subtot_str))

        lines.append(sub_div)

        # Financials
        lines.append(row("Gross Subtotal:", f"Rs. {sale.subtotal}"))
        if sale.discount_amount and sale.discount_amount > 0:
            lines.append(row("Discount:", f"-Rs. {sale.discount_amount}"))
        lines.append(row("Taxable Amount:", f"Rs. {sale.subtotal - sale.discount_amount}"))
        lines.append(row("VAT (13%):", f"Rs. {sale.tax_amount}"))
        lines.append(div)
        lines.append(row("NET PAYABLE:", f"Rs. {sale.total_amount}"))
        lines.append(div)

        # Payment Tender Details
        for pay in sale.payments.all():
            ref = f" ({pay.provider_reference})" if pay.provider_reference else ""
            lines.append(row(f"Paid via {pay.payment_method}{ref}:", f"Rs. {pay.amount}"))

        lines.append(sub_div)
        lines.append(center("Thank You For Shopping With Us!"))
        lines.append(center("Goods once sold are non-refundable"))
        lines.append(center(f"Powered by NextGen AI POS"))
        lines.append(div)

        return "\n".join(lines)

    @classmethod
    def generate_escpos_bytes(cls, sale: Sale, width: int = 42, open_drawer: bool = True) -> bytes:
        """
        Generates binary ESC/POS command stream ready to be piped to USB/Network thermal printer.
        """
        ESC = b"\x1b"
        GS = b"\x1d"

        commands = bytearray()
        # 1. Initialize printer
        commands += ESC + b"@"

        # 2. Open Cash Drawer pulse (Pin 2, 25ms on, 250ms off)
        if open_drawer:
            commands += ESC + b"p\x00\x19\xfa"

        # 3. Print ASCII text
        ascii_text = cls.format_ascii_receipt(sale, width=width)
        commands += ascii_text.encode("utf-8", errors="replace")

        # 4. Feed 4 lines
        commands += ESC + b"d\x04"

        # 5. Full Cut
        commands += GS + b"V\x41\x00"

        return bytes(commands)
