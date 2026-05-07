"""
Gerador de Relatórios PDF Customizáveis v2.
Suporta seleção de colunas, múltiplas plataformas e filtros.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas
from datetime import datetime
import io
import statistics


# ==============================================================================
# CORES
# ==============================================================================
PRIMARY = HexColor("#0891b2")
PRIMARY_DARK = HexColor("#0e7490")
PRIMARY_LIGHT = HexColor("#22d3ee")
PRINT_BG = HexColor("#ffffff")
PRINT_TEXT = HexColor("#1e293b")
PRINT_TEXT_SEC = HexColor("#475569")
PRINT_BORDER = HexColor("#e2e8f0")
SUCCESS = HexColor("#22c55e")
ERROR = HexColor("#ef4444")


class ReportGeneratorV2:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        # Title
        self.styles.add(ParagraphStyle(
            name="ReportTitle",
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=PRINT_TEXT,
            alignment=TA_LEFT,
            spaceAfter=2 * mm,
        ))
        
        # Subtitle
        self.styles.add(ParagraphStyle(
            name="ReportSubtitle",
            fontName="Helvetica",
            fontSize=10,
            textColor=PRINT_TEXT_SEC,
            alignment=TA_LEFT,
            spaceAfter=6 * mm,
        ))
        
        # Section
        self.styles.add(ParagraphStyle(
            name="SectionTitle",
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=PRIMARY_DARK,
            spaceBefore=8 * mm,
            spaceAfter=3 * mm,
        ))
        
        # Table Header
        self.styles.add(ParagraphStyle(
            name="TableHeader",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=white,
            alignment=TA_CENTER,
        ))
        
        # Table Cell
        self.styles.add(ParagraphStyle(
            name="TableCell",
            fontName="Helvetica",
            fontSize=7.5,
            textColor=PRINT_TEXT,
            alignment=TA_CENTER,
        ))
        
        # Table Cell Left
        self.styles.add(ParagraphStyle(
            name="TableCellLeft",
            fontName="Helvetica",
            fontSize=7.5,
            textColor=PRINT_TEXT,
            alignment=TA_LEFT,
        ))
        
        # KPI Title
        self.styles.add(ParagraphStyle(
            name="KPITitle",
            fontName="Helvetica",
            fontSize=8,
            textColor=PRINT_TEXT_SEC,
        ))
        
        # KPI Value
        self.styles.add(ParagraphStyle(
            name="KPIValue",
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=PRIMARY_DARK,
        ))
        
        # Footer
        self.styles.add(ParagraphStyle(
            name="Footer",
            fontName="Helvetica",
            fontSize=7,
            textColor=PRINT_TEXT_SEC,
            alignment=TA_CENTER,
        ))
    
    def _header(self, canvas_obj, doc):
        canvas_obj.saveState()
        
        # Header bar
        canvas_obj.setFillColor(PRIMARY_DARK)
        canvas_obj.rect(0, A4[1] - 25 * mm, A4[0], 25 * mm, fill=1, stroke=0)
        
        # Logo
        logo_path = "backend/static/logo.png"
        try:
            canvas_obj.drawImage(logo_path, 15 * mm, A4[1] - 20 * mm, width=15 * mm, height=15 * mm, mask='auto')
        except:
            # Fallback if logo not found
            canvas_obj.setFillColor(white)
            canvas_obj.setFont("Helvetica-Bold", 14)
            canvas_obj.drawString(15 * mm, A4[1] - 15 * mm, "M+")
        
        # Title
        canvas_obj.setFillColor(white)
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.drawString(35 * mm, A4[1] - 13 * mm, "Melhora+")
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawString(35 * mm, A4[1] - 18 * mm, "Inteligência Genética Aplicada")
        
        # Date and Page
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawRightString(
            A4[0] - 15 * mm, A4[1] - 13 * mm,
            f"Gerado em: {datetime.now().strftime('%d/%m/%Y')}"
        )
        canvas_obj.drawRightString(
            A4[0] - 15 * mm, A4[1] - 18 * mm,
            f"Página {doc.page}"
        )
        
        # Footer bar
        canvas_obj.setFillColor(HexColor("#f1f5f9"))
        canvas_obj.rect(0, 0, A4[0], 12 * mm, fill=1, stroke=0)
        canvas_obj.setFillColor(PRINT_TEXT_SEC)
        canvas_obj.setFont("Helvetica-Oblique", 7)
        canvas_obj.drawCentredString(
            A4[0] / 2, 5 * mm,
            "Melhora+ • Sistema de Melhoramento Genético e Unificação de Dados • www.melhoramais.com.br"
        )
        
        canvas_obj.restoreState()
    
    def generate_custom_report(
        self,
        farm_name: str,
        animals: list,
        platforms: list,
        selected_columns: dict,
        include_genealogy: bool = False,
    ) -> bytes:
        """Gera o relatório PDF customizado."""
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=25 * mm,
            bottomMargin=15 * mm,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
        )
        
        story = []
        
        # Title
        story.append(Paragraph(f"Relatório Genético", self.styles["ReportTitle"]))
        story.append(Paragraph(
            f"Fazenda: {farm_name} | {len(animals)} animais | Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            self.styles["ReportSubtitle"]
        ))
        
        # KPI Section
        story.extend(self._build_kpis(animals, platforms, selected_columns))
        
        # Summary by Platform
        for platform in platforms:
            story.extend(self._build_platform_summary(platform, animals))
        
        # Animals Table
        story.append(PageBreak())
        story.append(Paragraph("Animais", self.styles["SectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm))
        
        story.extend(self._build_animals_table(animals, selected_columns, include_genealogy))
        
        doc.build(story, onFirstPage=self._header, onLaterPages=self._header)
        
        return buffer.getvalue()
    
    def _build_kpis(self, animals: list, platforms: list, selected_columns: dict) -> list:
        """Constrói seção de KPIs."""
        story = []
        story.append(Paragraph("Resumo", self.styles["SectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm))
        
        # Calcular estatísticas
        total = len(animals)
        
        sex_m = sum(1 for a in animals if a.sexo == "M")
        sex_f = sum(1 for a in animals if a.sexo == "F")
        
        # Médias de pesos
        p210_values = [a.p210_peso_desmama for a in animals if a.p210_peso_desmama]
        p365_values = [a.p365_peso_ano for a in animals if a.p365_peso_ano]
        p450_values = [a.p450_peso_sobreano for a in animals if a.p450_peso_sobreano]
        
        avg_p210 = statistics.mean(p210_values) if p210_values else 0
        avg_p365 = statistics.mean(p365_values) if p365_values else 0
        avg_p450 = statistics.mean(p450_values) if p450_values else 0
        
        kpi_data = [
            [
                Paragraph("Total", self.styles["KPITitle"]),
                Paragraph("Machos", self.styles["KPITitle"]),
                Paragraph("Fêmeas", self.styles["KPITitle"]),
                Paragraph("P210 Méd", self.styles["KPITitle"]),
                Paragraph("P365 Méd", self.styles["KPITitle"]),
                Paragraph("P450 Méd", self.styles["KPITitle"]),
            ],
            [
                Paragraph(str(total), self.styles["KPIValue"]),
                Paragraph(str(sex_m), self.styles["KPIValue"]),
                Paragraph(str(sex_f), self.styles["KPIValue"]),
                Paragraph(f"{avg_p210:.1f}" if avg_p210 else "—", self.styles["KPIValue"]),
                Paragraph(f"{avg_p365:.1f}" if avg_p365 else "—", self.styles["KPIValue"]),
                Paragraph(f"{avg_p450:.1f}" if avg_p450 else "—", self.styles["KPIValue"]),
            ],
        ]
        
        kpi_table = Table(kpi_data, colWidths=[25 * mm, 25 * mm, 25 * mm, 35 * mm, 35 * mm, 35 * mm])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, PRINT_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(kpi_table)
        
        story.append(Spacer(1, 6 * mm))
        
        return story
    
    def _build_platform_summary(self, platform: str, animals: list) -> list:
        """Constrói resumo por plataforma."""
        story = []
        
        # Map column names
        platform_cols = {
            "ANCP": "anc_mg",
            "GENEPLUS": "gen_iqg",
            "PMGZ": "pmg_iabc"
        }
        
        col_name = platform_cols.get(platform)
        if not col_name:
            return story
        
        values = []
        for animal in animals:
            val = getattr(animal, col_name, None)
            if val is not None:
                values.append(val)
        
        if not values:
            story.append(Paragraph(f"{platform}: Sem dados", self.styles["KPITitle"]))
            return story
        
        mean_val = statistics.mean(values)
        median_val = statistics.median(values)
        min_val = min(values)
        max_val = max(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0
        
        story.append(Paragraph(f"{platform} - Índice Principal", self.styles["KPITitle"]))
        
        data = [
            [
                Paragraph("Média", self.styles["TableCellLeft"]),
                Paragraph("Mediana", self.styles["TableCellLeft"]),
                Paragraph("Mín", self.styles["TableCellLeft"]),
                Paragraph("Máx", self.styles["TableCellLeft"]),
                Paragraph("StdDev", self.styles["TableCellLeft"]),
                Paragraph("N", self.styles["TableCellLeft"]),
            ],
            [
                Paragraph(f"{mean_val:.3f}", self.styles["TableCell"]),
                Paragraph(f"{median_val:.3f}", self.styles["TableCell"]),
                Paragraph(f"{min_val:.3f}", self.styles["TableCell"]),
                Paragraph(f"{max_val:.3f}", self.styles["TableCell"]),
                Paragraph(f"{std_val:.3f}", self.styles["TableCell"]),
                Paragraph(str(len(values)), self.styles["TableCell"]),
            ],
        ]
        
        table = Table(data, colWidths=[30 * mm, 30 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("BACKGROUND", (0, 1), (-1, -1), HexColor("#ffffff")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f8fafc")]),
            ("BOX", (0, 0), (-1, -1), 1, PRINT_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 6 * mm))
        
        return story
    
    def _build_animals_table(
        self,
        animals: list,
        selected_columns: dict,
        include_genealogy: bool,
    ) -> list:
        """Constrói tabela de animais."""
        story = []
        
        # Build header
        header = []
        
        # Basic columns
        basic_cols = selected_columns.get("basic", [])
        if "rgn_animal" in basic_cols:
            header.append(Paragraph("RGN", self.styles["TableHeader"]))
        if "nome_animal" in basic_cols:
            header.append(Paragraph("Nome", self.styles["TableHeader"]))
        if "sexo" in basic_cols:
            header.append(Paragraph("Sexo", self.styles["TableHeader"]))
        if "raca" in basic_cols:
            header.append(Paragraph("Raça", self.styles["TableHeader"]))
        if "p210_peso_desmama" in basic_cols:
            header.append(Paragraph("P210", self.styles["TableHeader"]))
        if "p365_peso_ano" in basic_cols:
            header.append(Paragraph("P365", self.styles["TableHeader"]))
        if "p450_peso_sobreano" in basic_cols:
            header.append(Paragraph("P450", self.styles["TableHeader"]))
        
        # Platform columns
        for platform, cols in selected_columns.get("platforms", {}).items():
            for col in cols[:3]:  # Max 3 columns per platform
                header.append(Paragraph(col[:8].upper(), self.styles["TableHeader"]))
        
        # Genealogy columns
        if include_genealogy:
            genealogy_cols = selected_columns.get("genealogy", [])
            if "mae_rgn" in genealogy_cols:
                header.append(Paragraph("Mãe", self.styles["TableHeader"]))
            if "pai_rgn" in genealogy_cols:
                header.append(Paragraph("Pai", self.styles["TableHeader"]))
        
        if not header:
            header = [
                Paragraph("RGN", self.styles["TableHeader"]),
                Paragraph("Nome", self.styles["TableHeader"]),
                Paragraph("Sexo", self.styles["TableHeader"]),
            ]
        
        rows = [header]
        
        # Limit rows
        for animal in animals[:200]:
            row = []
            
            basic_cols = selected_columns.get("basic", [])
            if "rgn_animal" in basic_cols:
                row.append(Paragraph(str(animal.rgn_animal or ""), self.styles["TableCellLeft"]))
            if "nome_animal" in basic_cols:
                row.append(Paragraph(str(animal.nome_animal or "")[:20], self.styles["TableCellLeft"]))
            if "sexo" in basic_cols:
                row.append(Paragraph(animal.sexo or "—", self.styles["TableCell"]))
            if "raca" in basic_cols:
                row.append(Paragraph(animal.raca or "—", self.styles["TableCell"]))
            if "p210_peso_desmama" in basic_cols:
                val = f"{animal.p210_peso_desmama:.1f}" if animal.p210_peso_desmama else "—"
                row.append(Paragraph(val, self.styles["TableCell"]))
            if "p365_peso_ano" in basic_cols:
                val = f"{animal.p365_peso_ano:.1f}" if animal.p365_peso_ano else "—"
                row.append(Paragraph(val, self.styles["TableCell"]))
            if "p450_peso_sobreano" in basic_cols:
                val = f"{animal.p450_peso_sobreano:.1f}" if animal.p450_peso_sobreano else "—"
                row.append(Paragraph(val, self.styles["TableCell"]))
            
            # Platform columns
            for platform, cols in selected_columns.get("platforms", {}).items():
                for col in cols[:3]:
                    val = getattr(animal, col, None)
                    row.append(Paragraph(f"{val:.2f}" if val else "—", self.styles["TableCell"]))
            
            # Genealogy
            if include_genealogy:
                genealogy_cols = selected_columns.get("genealogy", [])
                if "mae_rgn" in genealogy_cols:
                    row.append(Paragraph(animal.mae_rgn or "—", self.styles["TableCellLeft"]))
                if "pai_rgn" in genealogy_cols:
                    row.append(Paragraph(animal.pai_rgn or "—", self.styles["TableCellLeft"]))
            
            if not row[3:]:  # If no basic columns, at least show RGN
                row = [
                    Paragraph(str(animal.rgn_animal or ""), self.styles["TableCellLeft"]),
                    Paragraph(str(animal.nome_animal or "")[:20], self.styles["TableCellLeft"]),
                    Paragraph(animal.sexo or "—", self.styles["TableCell"]),
                ]
            
            rows.append(row)
        
        # Calculate column widths
        n_cols = len(header) if header else 3
        col_width = 190 * mm / max(n_cols, 1)
        
        table = Table(rows, colWidths=[col_width] * n_cols)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("BACKGROUND", (0, 1), (-1, -1), HexColor("#ffffff")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f8fafc")]),
            ("BOX", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, PRINT_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
        ]))
        
        story.append(table)
        
        if len(animals) > 200:
            story.append(Spacer(1, 3 * mm))
            story.append(Paragraph(
                f"* Mostrando 200 de {len(animals)} animais",
                self.styles["Footer"]
            ))
        
        return story