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
    PageBreak, HRFlowable, Image, KeepTogether
)
from reportlab.pdfgen import canvas
from datetime import datetime, timezone, timedelta
import io
import os
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.abspath(os.path.join(
            current_dir, "..", "frontend", "public", "assets", "images", "logomelhoramais.png"
        ))
        try:
            canvas_obj.drawImage(logo_path, 15 * mm, A4[1] - 20 * mm, width=15 * mm, height=15 * mm, mask='auto')
        except Exception:
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
            f"Gerado em: {datetime.now(timezone(timedelta(hours=-3))).strftime('%d/%m/%Y')}"
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
            f"Fazenda: {farm_name} | {len(animals)} animais | Gerado em {datetime.now(timezone(timedelta(hours=-3))).strftime('%d/%m/%Y às %H:%M')}",
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

    def generate_dashboard_report(
        self,
        stats: dict,
        animals: list = None,
        logs: list = None,
        farm_name: str = None,
    ) -> bytes:
        """Gera o relatório do Dashboard Genético com Matplotlib Charts e tabelas."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=30 * mm,
            bottomMargin=18 * mm,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
        )
        
        story = []
        
        # Titulo Principal
        title_text = "Relatório do Dashboard Genético"
        if farm_name:
            title_text += f" — {farm_name}"
        story.append(Paragraph(title_text, self.styles["ReportTitle"]))
        story.append(Paragraph(
            f"Gerado em {datetime.now(timezone(timedelta(hours=-3))).strftime('%d/%m/%Y às %H:%M')}",
            self.styles["ReportSubtitle"]
        ))
        
        # Resumo Executivo & KPIs
        story.append(Paragraph("Resumo Executivo", self.styles["SectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm))
        
        total_anim = stats.get("total_animals", 0)
        recent_ups = stats.get("recent_uploads", 0)
        
        # KPI Averages Weights
        avg_p210 = stats.get("avg_p210")
        avg_p365 = stats.get("avg_p365")
        avg_p450 = stats.get("avg_p450")
        
        kpi_data = [
            [
                Paragraph("Total de Animais", self.styles["KPITitle"]),
                Paragraph("Uploads (30 dias)", self.styles["KPITitle"]),
                Paragraph("P210 Méd (Desmama)", self.styles["KPITitle"]),
                Paragraph("P365 Méd (Ano)", self.styles["KPITitle"]),
                Paragraph("P450 Méd (Sobreano)", self.styles["KPITitle"]),
            ],
            [
                Paragraph(str(total_anim), self.styles["KPIValue"]),
                Paragraph(str(recent_ups), self.styles["KPIValue"]),
                Paragraph(f"{avg_p210:.2f} kg" if avg_p210 else "—", self.styles["KPIValue"]),
                Paragraph(f"{avg_p365:.2f} kg" if avg_p365 else "—", self.styles["KPIValue"]),
                Paragraph(f"{avg_p450:.2f} kg" if avg_p450 else "—", self.styles["KPIValue"]),
            ]
        ]
        
        kpi_table = Table(kpi_data, colWidths=[35 * mm, 35 * mm, 38 * mm, 36 * mm, 36 * mm])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, PRINT_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 6 * mm))
        
        # ----------------------------------------------------
        # Seção de Gráficos e Distribuição (Visual Dashboards)
        # ----------------------------------------------------
        story.append(Paragraph("Distribuição e Análise Visual", self.styles["SectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm))
        
        charts_flowables = []
        
        # 1. Sex distribution chart
        sex_counts = stats.get("animals_by_sex") or {}
        if sex_counts:
            try:
                sex_chart_buf = self._generate_sex_distribution_chart(sex_counts)
                sex_chart_flowable = Image(sex_chart_buf, width=82 * mm, height=38 * mm)
                charts_flowables.append(sex_chart_flowable)
            except Exception as e:
                charts_flowables.append(Paragraph(f"Erro ao gerar gráfico de sexo: {str(e)}", self.styles["TableCell"]))
        
        # 2. ANCP vs PMGZ Metrics Comparison Chart
        pmgz_evals = []
        ancp_evals = []
        for anim in (animals or []):
            fo = anim.get("fonte_origem")
            metrics = anim.get("metrics") or {}
            if not metrics:
                continue
            if fo == "PMGZ":
                pmgz_evals.append(metrics)
            elif fo == "ANCP":
                ancp_evals.append(metrics)
                
        pmgz_avgs = {}
        ancp_avgs = {}
        
        def get_avg_dep(evals_list, pmgz_key, ancp_key):
            values = []
            for ev in evals_list:
                m = ev.get(pmgz_key) or ev.get(ancp_key)
                if m and m.get("dep") is not None:
                    try:
                        values.append(float(m["dep"]))
                    except Exception:
                        pass
            return statistics.mean(values) if values else 0.0
            
        if pmgz_evals:
            pmgz_avgs['pd'] = get_avg_dep(pmgz_evals, 'PD-EDg', 'DP210')
            pmgz_avgs['ps'] = get_avg_dep(pmgz_evals, 'PS-EDg', 'DP450')
            pmgz_avgs['pm'] = get_avg_dep(pmgz_evals, 'PM-EMg', 'DIPM')
            pmgz_avgs['pe'] = get_avg_dep(pmgz_evals, 'PE-365g', 'DPE')
            pmgz_avgs['aol'] = get_avg_dep(pmgz_evals, 'AOLg', 'DAOL')
            
        if ancp_evals:
            ancp_avgs['pd'] = get_avg_dep(ancp_evals, 'PD-EDg', 'DP210')
            ancp_avgs['ps'] = get_avg_dep(ancp_evals, 'PS-EDg', 'DP450')
            ancp_avgs['pm'] = get_avg_dep(ancp_evals, 'PM-EMg', 'DIPM')
            ancp_avgs['pe'] = get_avg_dep(ancp_evals, 'PE-365g', 'DPE')
            ancp_avgs['aol'] = get_avg_dep(ancp_evals, 'AOLg', 'DAOL')
            
        if pmgz_evals or ancp_evals:
            try:
                comp_chart_buf = self._generate_comparison_chart(pmgz_avgs, ancp_avgs, has_pmgz=bool(pmgz_evals), has_ancp=bool(ancp_evals))
                comp_chart_flowable = Image(comp_chart_buf, width=98 * mm, height=38 * mm)
                charts_flowables.append(comp_chart_flowable)
            except Exception as e:
                charts_flowables.append(Paragraph(f"Erro ao gerar gráfico de métricas: {str(e)}", self.styles["TableCell"]))
                
        # Layout double charts side-by-side inside a table
        if len(charts_flowables) >= 2:
            charts_table = Table([[charts_flowables[0], charts_flowables[1]]], colWidths=[85 * mm, 100 * mm])
            charts_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(charts_table)
        elif len(charts_flowables) == 1:
            story.append(charts_flowables[0])
            
        story.append(Spacer(1, 4 * mm))
        
        # 3. Source platforms text summary
        source_counts = stats.get("animals_by_source") or {}
        if source_counts:
            source_rows = [
                [
                    Paragraph("Plataforma Origem", self.styles["TableHeader"]),
                    Paragraph("Quantidade", self.styles["TableHeader"]),
                    Paragraph("Proporção", self.styles["TableHeader"]),
                ]
            ]
            for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
                pct = (count / total_anim * 100) if total_anim > 0 else 0.0
                source_rows.append([
                    Paragraph(str(source), self.styles["TableCellLeft"]),
                    Paragraph(str(count), self.styles["TableCell"]),
                    Paragraph(f"{pct:.1f}%", self.styles["TableCell"]),
                ])
                
            source_table = Table(source_rows, colWidths=[70 * mm, 50 * mm, 60 * mm])
            source_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("BACKGROUND", (0, 1), (-1, -1), white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#f8fafc")]),
                ("BOX", (0, 0), (-1, -1), 1, PRINT_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(source_table)
            
        # Animals Table (PageBreak if list is populated)
        if animals:
            story.append(PageBreak())
            story.append(Paragraph("Animais do Rebanho", self.styles["SectionTitle"]))
            story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm))
            
            # Draw a beautiful table of V2 animals
            selected_cols = {
                "basic": ["rgn_animal", "nome_animal", "sexo", "raca", "p210_peso_desmama", "p365_peso_ano", "p450_peso_sobreano"],
                "platforms": {}
            }
            story.extend(self._build_animals_table_v2(animals, selected_cols))
            
        doc.build(story, onFirstPage=self._header, onLaterPages=self._header)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
        
    def _generate_sex_distribution_chart(self, sex_counts: dict) -> io.BytesIO:
        """Desenha um gráfico de pizza da distribuição por sexo em Matplotlib."""
        labels = []
        values = []
        for s, count in sex_counts.items():
            label = 'Machos' if s in ['M', 'Macho'] else 'Fêmeas' if s in ['F', 'Fêmea'] else str(s or 'Indefinido')
            labels.append(label)
            values.append(count)
            
        fig, ax = plt.subplots(figsize=(4.0, 1.8), dpi=300)
        
        colors = ['#0891b2', '#ec4899', '#94a3b8']
        
        wedges, texts, autotexts = ax.pie(
            values, 
            labels=labels, 
            autopct='%1.1f%%', 
            startangle=90, 
            colors=colors[:len(values)],
            textprops={'fontsize': 7, 'color': '#1e293b'},
            wedgeprops={'edgecolor': 'white', 'linewidth': 1, 'antialiased': True}
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_weight('bold')
            autotext.set_size(6.5)
            
        ax.axis('equal')
        ax.set_title('Distribuição por Sexo', fontsize=8, pad=8, weight='bold', color='#0f172a')
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, transparent=True)
        buf.seek(0)
        plt.close(fig)
        return buf
        
    def _generate_comparison_chart(self, pmgz_data: dict, ancp_data: dict, has_pmgz: bool, has_ancp: bool) -> io.BytesIO:
        """Desenha o gráfico comparativo de métricas PMGZ vs ANCP em Matplotlib."""
        labels = ['Desmama', 'Sobreano', 'Maternal', 'PE', 'AOL']
        keys = ['pd', 'ps', 'pm', 'pe', 'aol']
        
        pmgz_vals = [pmgz_data.get(k, 0.0) for k in keys]
        ancp_vals = [ancp_data.get(k, 0.0) for k in keys]
        
        x = range(len(labels))
        width = 0.3
        
        fig, ax = plt.subplots(figsize=(4.8, 1.8), dpi=300)
        
        if has_pmgz and has_ancp:
            ax.bar([i - width/2 for i in x], pmgz_vals, width, label='PMGZ', color='#7c3aed', edgecolor='none')
            ax.bar([i + width/2 for i in x], ancp_vals, width, label='ANCP', color='#0891b2', edgecolor='none')
            ax.set_title('Comparativo Genético: PMGZ vs ANCP', fontsize=8, pad=8, weight='bold', color='#0f172a')
            ax.legend(fontsize=6, loc='upper right', frameon=True, facecolor='white', edgecolor='none')
        elif has_pmgz:
            ax.bar(x, pmgz_vals, width*1.5, label='PMGZ', color='#7c3aed')
            ax.set_title('Métricas Genéticas Médias: PMGZ', fontsize=8, pad=8, weight='bold', color='#0f172a')
        else:
            ax.bar(x, ancp_vals, width*1.5, label='ANCP', color='#0891b2')
            ax.set_title('Métricas Genéticas Médias: ANCP', fontsize=8, pad=8, weight='bold', color='#0f172a')
            
        ax.set_ylabel('DEP Média', fontsize=7, color='#475569')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=6.5, color='#475569')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cbd5e1')
        ax.spines['bottom'].set_color('#cbd5e1')
        ax.tick_params(colors='#475569', labelsize=6.5)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, transparent=True)
        buf.seek(0)
        plt.close(fig)
        return buf
        
    def _build_animals_table_v2(
        self,
        animals: list,
        selected_columns: dict,
    ) -> list:
        """Constrói tabela de animais específica para o dashboard v2."""
        story = []
        
        header = [
            Paragraph("RGN", self.styles["TableHeader"]),
            Paragraph("Nome", self.styles["TableHeader"]),
            Paragraph("Sexo", self.styles["TableHeader"]),
            Paragraph("Série/Raça", self.styles["TableHeader"]),
            Paragraph("PD (Desmama)", self.styles["TableHeader"]),
            Paragraph("PA (Ano)", self.styles["TableHeader"]),
            Paragraph("PS (Sobreano)", self.styles["TableHeader"]),
            Paragraph("Origem", self.styles["TableHeader"]),
        ]
        
        rows = [header]
        
        for animal in animals[:100]:
            rgn = animal.get("rgn_animal") or "—"
            nome = animal.get("nome_animal") or "—"
            sexo = animal.get("sexo") or "—"
            raca = animal.get("raca") or "—"
            
            p210 = animal.get("p210_peso_desmama")
            p365 = animal.get("p365_peso_ano")
            p450 = animal.get("p450_peso_sobreano")
            
            p210_str = f"{p210:.2f}" if p210 is not None else "—"
            p365_str = f"{p365:.2f}" if p365 is not None else "—"
            p450_str = f"{p450:.2f}" if p450 is not None else "—"
            
            origem = animal.get("fonte_origem") or "—"
            
            rows.append([
                Paragraph(str(rgn), self.styles["TableCellLeft"]),
                Paragraph(str(nome)[:22], self.styles["TableCellLeft"]),
                Paragraph(str(sexo), self.styles["TableCell"]),
                Paragraph(str(raca)[:15], self.styles["TableCell"]),
                Paragraph(p210_str, self.styles["TableCell"]),
                Paragraph(p365_str, self.styles["TableCell"]),
                Paragraph(p450_str, self.styles["TableCell"]),
                Paragraph(str(origem), self.styles["TableCell"]),
            ])
            
        table = Table(rows, colWidths=[20*mm, 35*mm, 15*mm, 25*mm, 25*mm, 25*mm, 25*mm, 20*mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("BACKGROUND", (0, 1), (-1, -1), white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#f8fafc")]),
            ("BOX", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, PRINT_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
        ]))
        
        story.append(table)
        
        if len(animals) > 100:
            story.append(Spacer(1, 3 * mm))
            story.append(Paragraph(
                f"* Mostrando 100 de {len(animals)} animais cadastrados.",
                self.styles["Footer"]
            ))
            
        return story

    def _generate_radar_chart_oo(self, animals: list) -> io.BytesIO:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        import numpy as np

        categories = ['Desmama (PD)', 'Sobreano (PS)', 'Maternal (PM)', 'PE', 'AOL']
        N = len(categories)
        
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]

        fig = Figure(figsize=(4.8, 4.8), dpi=300)
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111, polar=True)

        colors = ['#2d6a4f', '#8b5a2b', '#52b788', '#402218', '#74c69d']

        for idx, a in enumerate(animals):
            values = [
                a.get("pd") or 0.0,
                a.get("ps") or 0.0,
                a.get("pm") or 0.0,
                a.get("pe") or 0.0,
                a.get("aol") or 0.0
            ]
            values += values[:1]
            
            color = colors[idx % len(colors)]
            nome = a.get("nome_animal") or a.get("rgn_animal") or f"Animal {idx+1}"
            
            ax.plot(angles, values, color=color, linewidth=1.5, label=nome[:15])
            ax.fill(angles, values, color=color, alpha=0.1)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=8, color='#16261d', weight='bold')
        
        ax.tick_params(axis='y', labelsize=6, colors='#528266')
        ax.grid(color='#d0e5da', linestyle='--', linewidth=0.5)
        ax.spines['polar'].set_color('#a3c9b4')
        
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=6, frameon=True, facecolor='white', edgecolor='none')
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', transparent=True)
        buf.seek(0)
        return buf

    def _generate_benchmark_evolution_chart(self, farms_data: list, system_avg: float, safra_years: list) -> io.BytesIO:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        import numpy as np

        fig = Figure(figsize=(6, 2.8), dpi=300)
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)

        x = np.arange(len(safra_years))
        width = 0.6 / max(len(farms_data), 1)

        colors = ['#2d6a4f', '#8b5a2b', '#52b788', '#402218']

        for idx, f in enumerate(farms_data):
            farm_name = f.get("farm_name") or f"Fazenda {idx+1}"
            y_vals = f.get("values") or [0.0] * len(safra_years)
            offset = (idx - len(farms_data)/2 + 0.5) * width
            
            ax.bar(x + offset, y_vals, width, label=farm_name[:20], color=colors[idx % len(colors)])

        ax.axhline(system_avg, color='#9c1c1c', linestyle='--', linewidth=1, label=f'Média Geral ({system_avg:.2f})')

        ax.set_title('Evolução do Índice Genético Médio (Últimas 3 Safras)', fontsize=8, pad=8, weight='bold', color='#16261d')
        ax.set_ylabel('Índice Médio', fontsize=7, color='#2b4737')
        ax.set_xticks(x)
        ax.set_xticklabels([str(yr) for yr in safra_years], fontsize=7, color='#2b4737')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#c1d6cc')
        ax.spines['bottom'].set_color('#c1d6cc')
        ax.tick_params(colors='#2b4737', labelsize=7)
        ax.grid(axis='y', linestyle='--', alpha=0.3, color='#c1d6cc')
        ax.legend(fontsize=6, loc='upper left', frameon=True, facecolor='white', edgecolor='none')

        fig.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', transparent=True)
        buf.seek(0)
        return buf

    def generate_animal_comparison_report(
        self,
        farm_name: str,
        animals: list,
    ) -> bytes:
        """Gera o relatório comparativo de animais."""
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
        
        story.append(Paragraph("Relatório Comparativo de Animais", self.styles["ReportTitle"]))
        story.append(Paragraph(
            f"Fazenda: {farm_name} | Comparação de {len(animals)} animais | Gerado em {datetime.now(timezone(timedelta(hours=-3))).strftime('%d/%m/%Y às %H:%M')}",
            self.styles["ReportSubtitle"]
        ))
        
        story.append(Paragraph("Análise de Equilíbrio Genético", self.styles["SectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#2d6a4f"), spaceAfter=4 * mm))
        
        try:
            radar_buf = self._generate_radar_chart_oo(animals)
            radar_image = Image(radar_buf, width=90 * mm, height=90 * mm)
            
            radar_table = Table([[radar_image]], colWidths=[180 * mm])
            radar_table.setStyle(TableStyle([
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ]))
            
            story.append(KeepTogether([radar_table, Spacer(1, 4 * mm)]))
        except Exception as e:
            story.append(Paragraph(f"Erro ao gerar gráfico de radar: {str(e)}", self.styles["TableCell"]))
            
        story.append(PageBreak())
        
        story.append(Paragraph("Tabela Comparativa de DEPs", self.styles["SectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#2d6a4f"), spaceAfter=4 * mm))
        
        story.append(KeepTogether([self._build_comparison_table(animals)]))
        
        doc.build(story, onFirstPage=self._header, onLaterPages=self._header)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _build_comparison_table(self, animals: list) -> Table:
        header = [Paragraph("<b>Característica</b>", self.styles["TableHeader"])]
        for a in animals:
            name = a.get("nome_animal") or a.get("rgn_animal") or "Animal"
            header.append(Paragraph(f"<b>{name[:20]}</b><br/>RGN: {a.get('rgn_animal')}", self.styles["TableHeader"]))
            
        rows = [header]
        
        traits = [
            {"key": "pd", "label": "Desmama (PD)"},
            {"key": "ps", "label": "Sobreano (PS)"},
            {"key": "pm", "label": "Maternal (PM)"},
            {"key": "pe", "label": "Perímetro Escrotal (PE)"},
            {"key": "aol", "label": "Área Olho Lombo (AOL)"},
        ]
        
        style_label = ParagraphStyle(
            name="CompLabel",
            parent=self.styles["TableCellLeft"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
        )
        
        style_normal = self.styles["TableCell"]
        
        style_best = ParagraphStyle(
            name="CompBest",
            parent=self.styles["TableCell"],
            fontName="Helvetica-Bold",
            textColor=HexColor("#2d6a4f"),
        )
        
        for t in traits:
            row = [Paragraph(t["label"], style_label)]
            
            vals = []
            for a in animals:
                val = a.get(t["key"])
                if val is not None:
                    try:
                        vals.append(float(val))
                    except ValueError:
                        pass
            
            best_val = max(vals) if vals else None
            
            for a in animals:
                val = a.get(t["key"])
                if val is not None:
                    try:
                        f_val = float(val)
                        is_best = (f_val == best_val)
                        txt = f"{f_val:.2f}"
                        style = style_best if is_best else style_normal
                    except ValueError:
                        txt = str(val)
                        style = style_normal
                else:
                    txt = "—"
                    style = style_normal
                
                row.append(Paragraph(txt, style))
            rows.append(row)
            
        n_cols = len(animals) + 1
        col_width = 180 * mm / n_cols
        
        table = Table(rows, colWidths=[col_width] * n_cols)
        
        table_styles = [
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2d6a4f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#c1d6cc")),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, HexColor("#c1d6cc")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        
        for row_idx in range(1, len(traits) + 1):
            t = traits[row_idx - 1]
            vals = []
            for a in animals:
                val = a.get(t["key"])
                if val is not None:
                    try:
                        vals.append(float(val))
                    except ValueError:
                        pass
            best_val = max(vals) if vals else None
            
            for col_idx in range(1, len(animals) + 1):
                val = animals[col_idx - 1].get(t["key"])
                if val is not None:
                    try:
                        if float(val) == best_val:
                            table_styles.append(("BACKGROUND", (col_idx, row_idx), (col_idx, row_idx), HexColor("#eef5f1")))
                    except ValueError:
                        pass
                        
        table.setStyle(TableStyle(table_styles))
        return table

    def generate_farm_benchmark_report(
        self,
        farms_data: list,
        system_avg: float,
        safra: int,
        safra_years: list,
    ) -> bytes:
        """Gera o relatório de benchmark entre fazendas."""
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
        
        story.append(Paragraph("Relatório Benchmark de Fazendas", self.styles["ReportTitle"]))
        story.append(Paragraph(
            f"Comparação de Desempenho | Safra Ref: {safra} | Gerado em {datetime.now(timezone(timedelta(hours=-3))).strftime('%d/%m/%Y às %H:%M')}",
            self.styles["ReportSubtitle"]
        ))
        
        story.append(Paragraph("Análise Comparativa de Índices", self.styles["SectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#2d6a4f"), spaceAfter=4 * mm))
        
        try:
            chart_buf = self._generate_benchmark_evolution_chart(farms_data, system_avg, safra_years)
            chart_img = Image(chart_buf, width=160 * mm, height=75 * mm)
            chart_table = Table([[chart_img]], colWidths=[180 * mm])
            chart_table.setStyle(TableStyle([
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ]))
            story.append(KeepTogether([chart_table, Spacer(1, 4 * mm)]))
        except Exception as e:
            story.append(Paragraph(f"Erro ao gerar gráfico de evolução: {str(e)}", self.styles["TableCell"]))
            
        story.append(Spacer(1, 2 * mm))
        
        story.append(Paragraph(f"Tabela de Comparação de Médias - Safra {safra}", self.styles["SectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#2d6a4f"), spaceAfter=4 * mm))
        
        table_rows = [
            [
                Paragraph("<b>Fazenda</b>", self.styles["TableHeader"]),
                Paragraph("<b>Total Animais</b>", self.styles["TableHeader"]),
                Paragraph("<b>Índice Médio</b>", self.styles["TableHeader"]),
                Paragraph("<b>Média P210 (Desmama)</b>", self.styles["TableHeader"]),
                Paragraph("<b>Média P450 (Sobreano)</b>", self.styles["TableHeader"]),
            ]
        ]
        
        for f in farms_data:
            table_rows.append([
                Paragraph(f.get("farm_name") or "Fazenda", self.styles["TableCellLeft"]),
                Paragraph(str(f.get("total_animals") or 0), self.styles["TableCell"]),
                Paragraph(f"{f.get('avg_index'):.2f}" if f.get('avg_index') is not None else "—", self.styles["TableCell"]),
                Paragraph(f"{f.get('avg_p210'):.2f} kg" if f.get('avg_p210') is not None else "—", self.styles["TableCell"]),
                Paragraph(f"{f.get('avg_p450'):.2f} kg" if f.get('avg_p450') is not None else "—", self.styles["TableCell"]),
            ])
            
        table_rows.append([
            Paragraph("<b>Média Geral do Sistema (Benchmark)</b>", self.styles["TableCellLeft"]),
            Paragraph("—", self.styles["TableCell"]),
            Paragraph(f"<b>{system_avg:.2f}</b>", self.styles["TableCell"]),
            Paragraph("—", self.styles["TableCell"]),
            Paragraph("—", self.styles["TableCell"]),
        ])
        
        bench_table = Table(table_rows, colWidths=[65 * mm, 25 * mm, 30 * mm, 30 * mm, 30 * mm])
        bench_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2d6a4f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("BACKGROUND", (0, 1), (-1, -2), white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [white, HexColor("#eef5f1")]),
            ("BACKGROUND", (0, -1), (-1, -1), HexColor("#d0e5da")),
            ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#c1d6cc")),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, HexColor("#c1d6cc")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        
        story.append(KeepTogether([bench_table]))
        
        doc.build(story, onFirstPage=self._header, onLaterPages=self._header)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def generate_individual_animal_report(
        self,
        farm_name: str,
        animal: dict,
        pedigree: dict,
    ) -> bytes:
        """Gera o relatório da ficha individual do animal (página única)."""
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
        
        story.append(Paragraph(f"Ficha Técnica Individual de Leilão", self.styles["ReportTitle"]))
        story.append(Paragraph(
            f"Fazenda: {farm_name} | Data de Emissão: {datetime.now(timezone(timedelta(hours=-3))).strftime('%d/%m/%Y às %H:%M')}",
            self.styles["ReportSubtitle"]
        ))
        
        story.append(Paragraph("Identificação do Animal", self.styles["SectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#2d6a4f"), spaceAfter=3 * mm))
        
        percentil = animal.get("percentil_principal")
        badge_bg = "#52b788"
        badge_text_color = "#16261d"
        badge_label = "N/A"
        
        if percentil is not None:
            try:
                p_val = float(percentil)
                if p_val <= 1.0:
                    badge_bg = "#1b4332"
                    badge_text_color = "#ffffff"
                    badge_label = f"TOP {p_val:.1f}%"
                elif p_val <= 5.0:
                    badge_bg = "#2d6a4f"
                    badge_text_color = "#ffffff"
                    badge_label = f"TOP {p_val:.1f}%"
                elif p_val <= 10.0:
                    badge_bg = "#52b788"
                    badge_text_color = "#16261d"
                    badge_label = f"TOP {p_val:.1f}%"
                else:
                    badge_bg = "#d0e5da"
                    badge_text_color = "#2b4737"
                    badge_label = f"TOP {p_val:.1f}%"
            except ValueError:
                pass
                
        style_badge = ParagraphStyle(
            name="BadgeText",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=HexColor(badge_text_color),
            alignment=TA_CENTER,
        )
        
        badge_para = Paragraph(f"<b>{badge_label}</b>", style_badge)
        
        info_data = [
            [
                Paragraph("<b>Nome do Animal:</b>", self.styles["TableCellLeft"]),
                Paragraph(animal.get("nome") or "—", self.styles["TableCellLeft"]),
                Paragraph("<b>Classificação:</b>", self.styles["TableCellLeft"]),
                badge_para
            ],
            [
                Paragraph("<b>RGN:</b>", self.styles["TableCellLeft"]),
                Paragraph(animal.get("rgn") or "—", self.styles["TableCellLeft"]),
                Paragraph("<b>Sexo:</b>", self.styles["TableCellLeft"]),
                Paragraph("Macho" if animal.get("sexo") == "M" else "Fêmea" if animal.get("sexo") == "F" else "—", self.styles["TableCellLeft"]),
            ],
            [
                Paragraph("<b>Raça / Série:</b>", self.styles["TableCellLeft"]),
                Paragraph(animal.get("raca") or animal.get("serie") or "—", self.styles["TableCellLeft"]),
                Paragraph("<b>Nascimento:</b>", self.styles["TableCellLeft"]),
                Paragraph(animal.get("nascimento") or "—", self.styles["TableCellLeft"]),
            ],
            [
                Paragraph("<b>Genotipado:</b>", self.styles["TableCellLeft"]),
                Paragraph("Sim" if animal.get("genotipado") else "Não", self.styles["TableCellLeft"]),
                Paragraph("<b>CSG:</b>", self.styles["TableCellLeft"]),
                Paragraph("Sim" if animal.get("csg") else "Não", self.styles["TableCellLeft"]),
            ]
        ]
        
        info_table = Table(info_data, colWidths=[35 * mm, 55 * mm, 35 * mm, 55 * mm])
        info_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#c1d6cc")),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, HexColor("#c1d6cc")),
            ("BACKGROUND", (0, 0), (-1, -1), white),
            ("BACKGROUND", (3, 0), (3, 0), HexColor(badge_bg)),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 6 * mm))
        
        story.append(Paragraph("Árvore Genealógica (Pedigree)", self.styles["SectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#2d6a4f"), spaceAfter=3 * mm))
        
        style_ped_bold = ParagraphStyle(
            name="PedBold",
            parent=self.styles["TableCell"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
        )
        
        style_ped = ParagraphStyle(
            name="PedNormal",
            parent=self.styles["TableCell"],
            fontSize=7.0,
            leading=9,
        )
        
        def format_anc(anc):
            if not anc:
                return "—"
            return f"<b>{anc.get('nome') or 'Sem Nome'}</b><br/>RGN: {anc.get('rgn') or '—'}"
            
        ped_data = [
            [
                Paragraph(f"<b>{animal.get('nome') or 'Animal'}</b><br/>RGN: {animal.get('rgn')}", style_ped_bold), 
                Paragraph(format_anc(pedigree.get("sire")), style_ped), 
                Paragraph(format_anc(pedigree.get("sire_sire")), style_ped)
            ],
            [
                "", 
                "", 
                Paragraph(format_anc(pedigree.get("sire_dam")), style_ped)
            ],
            [
                "", 
                Paragraph(format_anc(pedigree.get("dam")), style_ped), 
                Paragraph(format_anc(pedigree.get("dam_sire")), style_ped)
            ],
            [
                "", 
                "", 
                Paragraph(format_anc(pedigree.get("dam_dam")), style_ped)
            ],
        ]
        
        ped_table = Table(ped_data, colWidths=[60 * mm, 60 * mm, 60 * mm], rowHeights=[14 * mm] * 4)
        ped_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (0, 3)),
            ('SPAN', (1, 0), (1, 1)),
            ('SPAN', (1, 2), (1, 3)),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#c1d6cc")),
            ('BACKGROUND', (0, 0), (0, 3), HexColor("#eef5f1")),
            ('BACKGROUND', (1, 0), (1, 1), HexColor("#fafbfc")),
            ('BACKGROUND', (1, 2), (1, 3), HexColor("#fafbfc")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        
        story.append(ped_table)
        story.append(Spacer(1, 6 * mm))
        
        story.append(Paragraph("Desempenho Genético", self.styles["SectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#2d6a4f"), spaceAfter=3 * mm))
        
        eval_data = [
            [
                Paragraph("<b>Plataforma Origem:</b>", self.styles["TableCellLeft"]),
                Paragraph(animal.get("fonte_origem") or "—", self.styles["TableCellLeft"]),
                Paragraph("<b>Safra Avaliação:</b>", self.styles["TableCellLeft"]),
                Paragraph(str(animal.get("safra") or "—"), self.styles["TableCellLeft"]),
            ],
            [
                Paragraph("<b>Índice Principal:</b>", self.styles["TableCellLeft"]),
                Paragraph(f"{animal.get('indice_principal'):.2f}" if animal.get('indice_principal') is not None else "—", self.styles["TableCellLeft"]),
                Paragraph("<b>Percentil / Rank:</b>", self.styles["TableCellLeft"]),
                Paragraph(f"{animal.get('percentil_principal'):.2f}%" if animal.get('percentil_principal') is not None else "—", self.styles["TableCellLeft"]),
            ]
        ]
        
        eval_table = Table(eval_data, colWidths=[40 * mm, 50 * mm, 40 * mm, 50 * mm])
        eval_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#c1d6cc")),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, HexColor("#c1d6cc")),
            ("BACKGROUND", (0, 0), (-1, -1), white),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        
        story.append(eval_table)
        
        doc.build(story, onFirstPage=self._header, onLaterPages=self._header)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes