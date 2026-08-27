"""
presentation_module.py - 5.6 Product Catalog Presentation Module
Generates and manages the official Product Zone International (PZI) Metal Candle Holder Collection
and export specification PDF catalog attachments for international campaigns.
"""

import os
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Tuple

try:
    from reportlab.lib.pagesizes import letter  # type: ignore
    from reportlab.lib import colors  # type: ignore
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable  # type: ignore
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class PresentationModule:
    """
    Handles PDF presentation catalog asset verification, generation, and MIME packaging.
    """

    DEFAULT_ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
    DEFAULT_FILENAME = "Candle_Holders.pdf"

    def __init__(self, asset_path: Optional[str] = None):
        if asset_path:
            self.presentation_path = os.path.abspath(asset_path)
        else:
            os.makedirs(self.DEFAULT_ASSET_DIR, exist_ok=True)
            self.presentation_path = os.path.join(self.DEFAULT_ASSET_DIR, self.DEFAULT_FILENAME)

    def ensure_presentation_exists(self) -> str:
        """
        Ensures the presentation PDF exists on disk; if missing, generates the PZI Export Catalog PDF.
        """
        if not os.path.exists(self.presentation_path):
            os.makedirs(os.path.dirname(self.presentation_path), exist_ok=True)
            self.generate_sample_catalog_pdf(self.presentation_path)
        return self.presentation_path

    def get_mime_attachment(self) -> Tuple[Optional[MIMEBase], Optional[str]]:
        """
        Reads the presentation PDF and returns a ready-to-attach MIMEBase object and filename.
        """
        filepath = self.ensure_presentation_exists()
        if not os.path.exists(filepath):
            return None, None

        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            mime_part = MIMEBase("application", "pdf")
            mime_part.set_payload(f.read())

        encoders.encode_base64(mime_part)
        mime_part.add_header(
            "Content-Disposition",
            f"attachment; filename=\"{filename}\""
        )
        return mime_part, filename

    def generate_sample_catalog_pdf(self, output_path: str):
        """
        Generates a 2-page Product Zone International (PZI) Metal Candle Holder Export Catalog using reportlab.
        """
        if not REPORTLAB_AVAILABLE:
            with open(output_path, "wb") as f:
                f.write(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF")
            return

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        styles = getSampleStyleSheet()

        brand_style = ParagraphStyle(
            'BrandStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor("#c2410c"),
            fontName='Helvetica-Bold',
            spaceAfter=4
        )
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor("#0f172a"),
            fontName='Helvetica-Bold',
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'SubTitleStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor("#475569"),
            spaceAfter=14
        )
        h2_style = ParagraphStyle(
            'H2Style',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor("#0f766e"),
            fontName='Helvetica-Bold',
            spaceBefore=10,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor("#334155"),
            leading=13,
            spaceAfter=8
        )

        elements = []

        # Header Block
        elements.append(Paragraph("PRODUCT ZONE INTERNATIONAL", brand_style))
        elements.append(Paragraph("Warm the Room: Metal Candle Holder Collection", title_style))
        elements.append(Paragraph(
            "<i>Handcrafted metal pieces that turn a single flame into an atmosphere — designed for everyday essentials and premium retail gifts.</i>",
            subtitle_style
        ))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        # Collection Overview
        elements.append(Paragraph("1. Collection Overview & Finishes", h2_style))
        elements.append(Paragraph(
            "Product Zone International specializes in high-grade architectural metal candle holders, hurricane lanterns, graduated pyramid trios, and multi-arm candelabras. "
            "Available in four signature finishes: <b>Matte Black</b>, <b>Antique Brass</b>, <b>Polished Nickel</b>, and <b>Warm Heritage Bronze</b>. All products are finished with heat-resistant protective coatings suited for dining tables, hearths, and hospitality settings.",
            body_style
        ))

        # Catalog Table
        elements.append(Paragraph("2. Core Product Line & Export Specifications", h2_style))
        
        table_data = [
            ["SKU #", "Description & Silhouette", "Material / Finish", "Dimensions", "MOQ", "Export FOB (USD)"],
            ["#PZI-429", "Square-Based Architectural Lantern with Tapered Crown", "Iron Frame + Open Glass", "8\" x 8\" x 16\"", "20 pcs", "$18.50"],
            ["#PZI-421", "Slim Taper Candle Holders with Spiral Stem (Pair)", "Solid Brass / Polished Silver", "3.5\" base x 12\" H", "30 pairs", "$12.80 / pair"],
            ["#PZI-424", "Hexagonal Pyramid Nesting Holders (Set of 3)", "Faceted Glass + Fine Metal", "Small, Med, Large", "15 sets", "$24.50 / set"],
            ["#PZI-425 ABC", "Angular Pyramid Centerpiece Trio with Glass Body", "Textured Cast Iron / Matte", "14\", 18\", 22\" H", "15 sets", "$29.00 / set"],
            ["#PZI-426", "Compact Geometric Cage Votive Holders (Set of 4)", "Interlocking Metal Wire", "4\" x 4\" x 3.5\"", "50 sets", "$8.90 / set"],
            ["#PZI-417", "Tall Ornate Lantern with Decorative Crown Finial", "Antique Pewter / Scrollwork", "7\" x 7\" x 20\"", "20 pcs", "$21.00"],
            ["#PZI-410", "Pillar Hurricane Holder with Sturdy Metal Base", "Clear Glass Cylinder + Steel", "6\" dia x 14\" H", "25 pcs", "$16.50"],
            ["#PZI-400", "5-Light Multi-Arm Candelabra Centerpiece", "Warm Antique Brass Tone", "16\" span x 18\" H", "10 pcs", "$34.00"],
            ["#PZI-397", "Classic Glass-and-Metal Wind-Resistant Hurricane", "Polished Nickel + Glass", "5\" dia x 11\" H", "30 pcs", "$14.20"]
        ]

        table = Table(table_data, colWidths=[65, 175, 115, 85, 45, 55])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f766e")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (4, 0), (5, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('FONTSIZE', (0, 1), (-1, -1), 7.5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 8))

        # Packaging & Logistics
        elements.append(Paragraph("3. Export Logistics, Private Labeling & Logistics (USA & Canada)", h2_style))
        elements.append(Paragraph(
            "• <b>Custom Retail Packaging:</b> Drop-tested, double-walled foam cushioned master cartons with barcode labeling & retail hangtags.<br/>"
            "• <b>Private Label & OEM:</b> Custom laser engraving, custom Pantone metal coatings, and buyer brand packaging available.<br/>"
            "• <b>Door-to-Door Logistics:</b> DDP / FOB air cargo (DHL/FedEx door-to-door, 4-6 business days) or sea container freight to US & Canadian ports.",
            body_style
        ))

        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceAfter=8))
        elements.append(Paragraph("<b>Direct Export Inquiries:</b> sales@productzoneintl.com | WhatsApp / Phone: +1 (555) 019-2834 | Website: https://www.productzoneintl.com", body_style))

        doc.build(elements)
