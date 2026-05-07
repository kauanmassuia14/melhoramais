from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime
import os
import io


# ============================================
# Color Palette
# ============================================
PRIMARY = HexColor("#0891b2")       # cyan-600
PRIMARY_DARK = HexColor("#0e7490")  # cyan-700
PRIMARY_LIGHT = HexColor("#22d3ee") # cyan-400
ACCENT = HexColor("#06b6d4")        # cyan-500
BG_DARK = HexColor("#0f172a")       # slate-900
BG_CARD = HexColor("#1e293b")       # slate-800
TEXT_PRIMARY = HexColor("#f8fafc")  # slate-50
TEXT_SECONDARY = HexColor("#94a3b8") # slate-400
TEXT_MUTED = HexColor("#64748b")    # slate-500
BORDER = HexColor("#334155")        # slate-700
SUCCESS = HexColor("#22c55e")       # green-500
WARNING = HexColor("#eab308")       # yellow-500
ERROR = HexColor("#ef4444")         # red-500

# For print-friendly version
PRINT_BG = HexColor("#ffffff")
PRINT_TEXT = HexColor("#1e293b")
PRINT_TEXT_SEC = HexColor("#475569")
PRINT_BORDER = HexColor("#e2e8f0")


class ReportGenerator:
    def __init__(self):
        self.logo_path = os.path.join(
            os.path.dirname(__file__), "..", "frontend", "public", "assets", "images", "logomelhoramais.png"
        )
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        self.styles.add(ParagraphStyle(
            name="ReportTitle",
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=PRINT_TEXT,
            alignment=TA_LEFT,
            spaceAfter=4 * mm,
        ))
        self.styles.add(ParagraphStyle(
            name="ReportSubtitle",
            fontName="Helvetica",
            fontSize=11,
            textColor=PRINT_TEXT_SEC,
            alignment=TA_LEFT,
            spaceAfter=8 * mm,
        ))
        self.styles.add(ParagraphStyle(
            name="SectionTitle",
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=PRIMARY_DARK,
            spaceBefore=6 * mm,
            spaceAfter=4 * mm,
        ))
        self.styles.add(ParagraphStyle(
            name="CardTitle",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=PRINT_TEXT_SEC,
            alignment=TA_LEFT,
        ))
        self.styles.add(ParagraphStyle(
            name="CardValue",
            fontName="Helvetica-Bold",
            fontSize=24,
            textColor=PRIMARY_DARK,
            alignment=TA_LEFT,
        ))
        self.styles.add(ParagraphStyle(
            name="CardLabel",
            fontName="Helvetica",
            fontSize=8,
            textColor=TEXT_MUTED,
            alignment=TA_LEFT,
        ))
        self.styles.add(ParagraphStyle(
            name="TableHeader",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=white,
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            name="TableCell",
            fontName="Helvetica",
            fontSize=8.5,
            textColor=PRINT_TEXT,
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            name="TableCellLeft",
            fontName="Helvetica",
            fontSize=8.5,
            textColor=PRINT_TEXT,
            alignment=TA_LEFT,
        ))
        self.styles.add(ParagraphStyle(
            name="Footer",
            fontName="Helvetica",
            fontSize=7,
            textColor=TEXT_MUTED,
            alignment=TA_CENTER,
        ))

    def _header_footer(self, canvas_obj, doc):
        canvas_obj.saveState()

        # Header bar
        canvas_obj.setFillColor(PRIMARY_DARK)
        canvas_obj.rect(0, A4[1] - 25 * mm, A4[0], 25 * mm, fill=1, stroke=0)

        # Logo
        if os.path.exists(self.logo_path):
            canvas_obj.drawImage(
                self.logo_path,
                15 * mm, A4[1] - 20 * mm,
                width=14 * mm, height=14 * mm,
                mask="auto"
            )

        # Header text
        canvas_obj.setFillColor(white)
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.drawString(32 * mm, A4[1] - 14 * mm, "Melhora+")
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawString(32 * mm, A4[1] - 19 * mm, "Relatório do Dashboard Genético")

        # Date in header
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawRightString(
            A4[0] - 15 * mm, A4[1] - 14 * mm,
            datetime.now().strftime("%d/%m/%Y %H:%M")
        )

        # Footer
        canvas_obj.setFillColor(PRINT_BORDER)
        canvas_obj.rect(0, 0, A4[0], 12 * mm, fill=1, stroke=0)
        canvas_obj.setFillColor(TEXT_MUTED)
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawCentredString(
            A4[0] / 2, 5 * mm,
            f"Melhora+ Genética Platform • Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} • Página {doc.page}"
        )

        canvas_obj.restoreState()

    def _build_kpi_card(self, title: str, value: str, subtitle: str = ""):
        elements = []
        elements.append(Paragraph(title, self.styles["CardTitle"]))
        elements.append(Spacer(1, 2 * mm))
        elements.append(Paragraph(value, self.styles["CardValue"]))
        if subtitle:
            elements.append(Paragraph(subtitle, self.styles["CardLabel"]))
        return elements

    def _build_kpi_section(self, stats: dict):
        elements = []
        elements.append(Paragraph("Resumo Executivo", self.styles["SectionTitle"]))
        elements.append(HRFlowable(
            width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm
        ))

        # KPI cards in a table
        kpi_data = [
            [
                Paragraph("Total de Animais", self.styles["CardTitle"]),
                Paragraph("Fazendas Ativas", self.styles["CardTitle"]),
                Paragraph("Uploads (30 dias)", self.styles["CardTitle"]),
            ],
            [
                Paragraph(str(stats.get("total_animals", 0)), self.styles["CardValue"]),
                Paragraph(str(stats.get("total_farms", 0)), self.styles["CardValue"]),
                Paragraph(str(stats.get("recent_uploads", 0)), self.styles["CardValue"]),
            ],
        ]

        kpi_table = Table(kpi_data, colWidths=[60 * mm, 60 * mm, 60 * mm])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, PRINT_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 6 * mm))

        # Genetic averages
        avg_data = [
            [
                Paragraph("P210 (Desmama)", self.styles["CardTitle"]),
                Paragraph("P365 (Peso Ano)", self.styles["CardTitle"]),
                Paragraph("P450 (Sobreano)", self.styles["CardTitle"]),
            ],
            [
                Paragraph(
                    f"{stats.get('avg_p210', 0):.1f}%" if stats.get("avg_p210") else "N/A",
                    self.styles["CardValue"]
                ),
                Paragraph(
                    f"{stats.get('avg_p365', 0):.1f}%" if stats.get("avg_p365") else "N/A",
                    self.styles["CardValue"]
                ),
                Paragraph(
                    f"{stats.get('avg_p450', 0):.1f}%" if stats.get("avg_p450") else "N/A",
                    self.styles["CardValue"]
                ),
            ],
            [
                Paragraph("Média peso desmama", self.styles["CardLabel"]),
                Paragraph("Média peso ao ano", self.styles["CardLabel"]),
                Paragraph("Média peso sobreano", self.styles["CardLabel"]),
            ],
        ]

        avg_table = Table(avg_data, colWidths=[60 * mm, 60 * mm, 60 * mm])
        avg_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f0f9ff")),
            ("BOX", (0, 0), (-1, -1), 1, PRIMARY),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(avg_table)

        return elements

    def _build_distribution_section(self, stats: dict):
        elements = []
        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph("Distribuição do Rebanho", self.styles["SectionTitle"]))
        elements.append(HRFlowable(
            width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm
        ))

        # By source
        by_source = stats.get("animals_by_source", {})
        total = stats.get("total_animals", 1)

        if by_source:
            source_header = [
                Paragraph("Fonte", self.styles["TableHeader"]),
                Paragraph("Quantidade", self.styles["TableHeader"]),
                Paragraph("Percentual", self.styles["TableHeader"]),
            ]
            source_rows = [source_header]
            for source, count in sorted(by_source.items(), key=lambda x: -x[1]):
                pct = (count / total * 100) if total > 0 else 0
                source_rows.append([
                    Paragraph(source, self.styles["TableCellLeft"]),
                    Paragraph(str(count), self.styles["TableCell"]),
                    Paragraph(f"{pct:.1f}%", self.styles["TableCell"]),
                ])

            source_table = Table(source_rows, colWidths=[70 * mm, 50 * mm, 50 * mm])
            source_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("BACKGROUND", (0, 1), (-1, -1), HexColor("#ffffff")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f8fafc")]),
                ("BOX", (0, 0), (-1, -1), 1, PRINT_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            elements.append(source_table)

        # By sex
        elements.append(Spacer(1, 6 * mm))
        by_sex = stats.get("animals_by_sex", {})

        if by_sex:
            sex_header = [
                Paragraph("Sexo", self.styles["TableHeader"]),
                Paragraph("Quantidade", self.styles["TableHeader"]),
                Paragraph("Percentual", self.styles["TableHeader"]),
            ]
            sex_rows = [sex_header]
            sex_labels = {"M": "Macho", "F": "Fêmea"}
            for sex, count in sorted(by_sex.items()):
                pct = (count / total * 100) if total > 0 else 0
                label = sex_labels.get(sex, sex)
                sex_rows.append([
                    Paragraph(label, self.styles["TableCellLeft"]),
                    Paragraph(str(count), self.styles["TableCell"]),
                    Paragraph(f"{pct:.1f}%", self.styles["TableCell"]),
                ])

            sex_table = Table(sex_rows, colWidths=[70 * mm, 50 * mm, 50 * mm])
            sex_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("BACKGROUND", (0, 1), (-1, -1), HexColor("#ffffff")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f8fafc")]),
                ("BOX", (0, 0), (-1, -1), 1, PRINT_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            elements.append(sex_table)

        return elements

    def _build_animals_table(self, animals: list):
        elements = []
        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph("Animais do Rebanho", self.styles["SectionTitle"]))
        elements.append(HRFlowable(
            width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm
        ))

        if not animals:
            elements.append(Paragraph("Nenhum animal encontrado.", self.styles["CardLabel"]))
            return elements

        header = [
            Paragraph("RGN", self.styles["TableHeader"]),
            Paragraph("Nome", self.styles["TableHeader"]),
            Paragraph("Sexo", self.styles["TableHeader"]),
            Paragraph("Raça", self.styles["TableHeader"]),
            Paragraph("P210", self.styles["TableHeader"]),
            Paragraph("P365", self.styles["TableHeader"]),
            Paragraph("P450", self.styles["TableHeader"]),
            Paragraph("Fonte", self.styles["TableHeader"]),
        ]
        rows = [header]

        for animal in animals[:100]:  # Limit to 100 for PDF
            rows.append([
                Paragraph(str(animal.get("rgn_animal", "") or ""), self.styles["TableCellLeft"]),
                Paragraph(str(animal.get("nome_animal", "") or "—"), self.styles["TableCellLeft"]),
                Paragraph(str(animal.get("sexo", "") or "—"), self.styles["TableCell"]),
                Paragraph(str(animal.get("raca", "") or "—"), self.styles["TableCell"]),
                Paragraph(
                    f"{animal.get('p210_peso_desmama', 0):.1f}" if animal.get("p210_peso_desmama") else "—",
                    self.styles["TableCell"]
                ),
                Paragraph(
                    f"{animal.get('p365_peso_ano', 0):.1f}" if animal.get("p365_peso_ano") else "—",
                    self.styles["TableCell"]
                ),
                Paragraph(
                    f"{animal.get('p450_peso_sobreano', 0):.1f}" if animal.get("p450_peso_sobreano") else "—",
                    self.styles["TableCell"]
                ),
                Paragraph(str(animal.get("fonte_origem", "") or "—"), self.styles["TableCell"]),
            ])

        table = Table(rows, colWidths=[22 * mm, 28 * mm, 14 * mm, 22 * mm, 18 * mm, 18 * mm, 18 * mm, 22 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("BACKGROUND", (0, 1), (-1, -1), HexColor("#ffffff")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f8fafc")]),
            ("BOX", (0, 0), (-1, -1), 1, PRINT_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)

        if len(animals) > 100:
            elements.append(Spacer(1, 2 * mm))
            elements.append(Paragraph(
                f"* Mostrando 100 de {len(animals)} animais. Relatório completo disponível na plataforma.",
                self.styles["CardLabel"]
            ))

        return elements

    def _build_logs_table(self, logs: list):
        elements = []
        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph("Histórico de Processamentos", self.styles["SectionTitle"]))
        elements.append(HRFlowable(
            width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm
        ))

        if not logs:
            elements.append(Paragraph("Nenhum processamento encontrado.", self.styles["CardLabel"]))
            return elements

        header = [
            Paragraph("Data", self.styles["TableHeader"]),
            Paragraph("Sistema", self.styles["TableHeader"]),
            Paragraph("Arquivo", self.styles["TableHeader"]),
            Paragraph("Linhas", self.styles["TableHeader"]),
            Paragraph("Inseridos", self.styles["TableHeader"]),
            Paragraph("Status", self.styles["TableHeader"]),
        ]
        rows = [header]

        for log in logs[:20]:
            status_color = SUCCESS if log.get("status") == "completed" else ERROR
            status_text = "Concluído" if log.get("status") == "completed" else "Falhou"
            date_str = ""
            if log.get("started_at"):
                try:
                    dt = datetime.fromisoformat(log["started_at"].replace("Z", "+00:00"))
                    date_str = dt.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    date_str = log["started_at"][:16]

            rows.append([
                Paragraph(date_str, self.styles["TableCell"]),
                Paragraph(str(log.get("source_system", "") or ""), self.styles["TableCell"]),
                Paragraph(str(log.get("filename", "") or "—")[:25], self.styles["TableCellLeft"]),
                Paragraph(str(log.get("total_rows", 0)), self.styles["TableCell"]),
                Paragraph(str(log.get("rows_inserted", 0)), self.styles["TableCell"]),
                Paragraph(status_text, self.styles["TableCell"]),
            ])

        table = Table(rows, colWidths=[30 * mm, 22 * mm, 45 * mm, 22 * mm, 22 * mm, 25 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("BACKGROUND", (0, 1), (-1, -1), HexColor("#ffffff")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f8fafc")]),
            ("BOX", (0, 0), (-1, -1), 1, PRINT_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(table)

        return elements

    def generate_dashboard_report(
        self,
        stats: dict,
        animals: list = None,
        logs: list = None,
        farm_name: str = None,
    ) -> bytes:
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

        # Title
        title_text = "Relatório do Dashboard Genético"
        if farm_name:
            title_text += f" — {farm_name}"
        story.append(Paragraph(title_text, self.styles["ReportTitle"]))
        story.append(Paragraph(
            f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            self.styles["ReportSubtitle"]
        ))

        # KPI Section
        story.extend(self._build_kpi_section(stats))

        # Distribution Section
        story.extend(self._build_distribution_section(stats))

        # Animals Table
        if animals:
            story.append(PageBreak())
            story.extend(self._build_animals_table(animals))

        # Logs Table
        if logs:
            if not animals:
                story.append(PageBreak())
            story.extend(self._build_logs_table(logs))

        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)

        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _build_bar_chart_data(self, data: dict, title: str) -> Table:
        if not data:
            return Table([[Paragraph("Sem dados disponíveis", self.styles["CardLabel"])]])
        
        labels = list(data.keys())
        values = list(data.values())
        max_val = max(values) if values else 1
        
        rows = [[Paragraph(title, self.styles["TableHeader"])]]
        for label, value in zip(labels, values):
            pct = (value / max_val * 100) if max_val > 0 else 0
            bar_width = int(pct / 5)
            bar_str = "█" * bar_width + "░" * (20 - bar_width)
            rows.append([
                Paragraph(f"{label}: {value} ({pct:.1f}%)", self.styles["TableCellLeft"]),
            ])
        
        t = Table(rows, colWidths=[170 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("BACKGROUND", (0, 1), (-1, -1), HexColor("#ffffff")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f8fafc")]),
            ("BOX", (0, 0), (-1, -1), 1, PRINT_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        return t

    def generate_upload_report(
        self,
        log,
        animals: list,
        farm_name: str = None,
    ) -> bytes:
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
        
        title = f"Relatório de Upload — {log.source_system}"
        if farm_name:
            title += f" — {farm_name}"
        story.append(Paragraph(title, self.styles["ReportTitle"]))
        story.append(Paragraph(
            f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            self.styles["ReportSubtitle"]
        ))
        
        story.append(Paragraph("Informações do Processamento", self.styles["SectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm))
        
        info_data = [
            [Paragraph("Campo", self.styles["TableHeader"]), Paragraph("Valor", self.styles["TableHeader"])],
            [Paragraph("ID do Log", self.styles["TableCellLeft"]), Paragraph(str(log.id), self.styles["TableCell"])],
            [Paragraph("Sistema Fonte", self.styles["TableCellLeft"]), Paragraph(log.source_system or "—", self.styles["TableCell"])],
            [Paragraph("Nome do Arquivo", self.styles["TableCellLeft"]), Paragraph(log.filename or "—", self.styles["TableCell"])],
            [Paragraph("Data de Início", self.styles["TableCellLeft"]), Paragraph(log.started_at.strftime("%d/%m/%Y %H:%M") if log.started_at else "—", self.styles["TableCell"])],
            [Paragraph("Data de Conclusão", self.styles["TableCellLeft"]), Paragraph(log.completed_at.strftime("%d/%m/%Y %H:%M") if log.completed_at else "—", self.styles["TableCell"])],
            [Paragraph("Status", self.styles["TableCellLeft"]), Paragraph(log.status.upper(), self.styles["TableCell"])],
            [Paragraph("Total de Linhas", self.styles["TableCellLeft"]), Paragraph(str(log.total_rows or 0), self.styles["TableCell"])],
            [Paragraph("Linhas Inseridas", self.styles["TableCellLeft"]), Paragraph(str(log.rows_inserted or 0), self.styles["TableCell"])],
            [Paragraph("Linhas Atualizadas", self.styles["TableCellLeft"]), Paragraph(str(log.rows_updated or 0), self.styles["TableCell"])],
            [Paragraph("Linhas Falhas", self.styles["TableCellLeft"]), Paragraph(str(log.rows_failed or 0), self.styles["TableCell"])],
        ]
        
        if log.error_message:
            info_data.append([Paragraph("Mensagem de Erro", self.styles["TableCellLeft"]), Paragraph(log.error_message[:200], self.styles["TableCell"])])
        
        info_table = Table(info_data, colWidths=[60 * mm, 110 * mm])
        info_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("BACKGROUND", (0, 1), (-1, -1), HexColor("#ffffff")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f8fafc")]),
            ("BOX", (0, 0), (-1, -1), 1, PRINT_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(info_table)
        
        if animals:
            story.append(Spacer(1, 8 * mm))
            story.append(Paragraph("Distribuição por Sexo", self.styles["SectionTitle"]))
            story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm))
            
            sex_dist = {}
            for a in animals:
                sex = a.sexo or "Desconhecido"
                sex_dist[sex] = sex_dist.get(sex, 0) + 1
            
            story.append(self._build_bar_chart_data(sex_dist, "Sexo"))
            
            story.append(Spacer(1, 8 * mm))
            story.append(Paragraph("Distribuição por Raça", self.styles["SectionTitle"]))
            story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm))
            
            raca_dist = {}
            for a in animals:
                raca = a.raca or "Desconhecido"
                raca_dist[raca] = raca_dist.get(raca, 0) + 1
            raca_dist = dict(sorted(raca_dist.items(), key=lambda x: x[1], reverse=True)[:10])
            
            story.append(self._build_bar_chart_data(raca_dist, "Raça"))
            
            story.append(Spacer(1, 8 * mm))
            story.extend(self._build_animals_table(animals[:50]))
        
        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def generate_animal_report(
        self,
        animal,
        farm_name: str = None,
    ) -> bytes:
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
        
        title = f"Relatório do Animal — {animal.rgn_animal}"
        if farm_name:
            title += f" — {farm_name}"
        story.append(Paragraph(title, self.styles["ReportTitle"]))
        story.append(Paragraph(
            f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            self.styles["ReportSubtitle"]
        ))
        
        story.append(Paragraph("Dados Gerais", self.styles["SectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm))
        
        geral_data = [
            [Paragraph("Campo", self.styles["TableHeader"]), Paragraph("Valor", self.styles["TableHeader"])],
            [Paragraph("RGN", self.styles["TableCellLeft"]), Paragraph(animal.rgn_animal or "—", self.styles["TableCell"])],
            [Paragraph("Nome", self.styles["TableCellLeft"]), Paragraph(animal.nome_animal or "—", self.styles["TableCell"])],
            [Paragraph("Sexo", self.styles["TableCellLeft"]), Paragraph("Macho" if animal.sexo == "M" else "Fêmea" if animal.sexo == "F" else "—", self.styles["TableCell"])],
            [Paragraph("Raça", self.styles["TableCellLeft"]), Paragraph(animal.raca or "—", self.styles["TableCell"])],
            [Paragraph("Data de Nascimento", self.styles["TableCellLeft"]), Paragraph(animal.data_nascimento.strftime("%d/%m/%Y") if animal.data_nascimento else "—", self.styles["TableCell"])],
            [Paragraph("Mãe (RGN)", self.styles["TableCellLeft"]), Paragraph(animal.mae_rgn or "—", self.styles["TableCell"])],
            [Paragraph("Pai (RGN)", self.styles["TableCellLeft"]), Paragraph(animal.pai_rgn or "—", self.styles["TableCell"])],
            [Paragraph("Fonte de Origem", self.styles["TableCellLeft"]), Paragraph(animal.fonte_origem or "—", self.styles["TableCell"])],
        ]
        
        geral_table = Table(geral_data, colWidths=[60 * mm, 110 * mm])
        geral_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("BACKGROUND", (0, 1), (-1, -1), HexColor("#ffffff")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f8fafc")]),
            ("BOX", (0, 0), (-1, -1), 1, PRINT_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(geral_table)
        
        story.append(Spacer(1, 8 * mm))
        story.append(Paragraph("Pesos", self.styles["SectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm))
        
        pesos_data = [
            [Paragraph("Medida", self.styles["TableHeader"]), Paragraph("Valor (kg)", self.styles["TableHeader"]), Paragraph("Referência", self.styles["TableHeader"])],
            [Paragraph("P210 — Peso à Desmama", self.styles["TableCellLeft"]), Paragraph(f"{animal.p210_peso_desmama:.1f}" if animal.p210_peso_desmama else "—", self.styles["TableCell"]), Paragraph("~210 dias", self.styles["TableCell"])],
            [Paragraph("P365 — Peso ao Ano", self.styles["TableCellLeft"]), Paragraph(f"{animal.p365_peso_ano:.1f}" if animal.p365_peso_ano else "—", self.styles["TableCell"]), Paragraph("~365 dias", self.styles["TableCell"])],
            [Paragraph("P450 — Peso Sobreano", self.styles["TableCellLeft"]), Paragraph(f"{animal.p450_peso_sobreano:.1f}" if animal.p450_peso_sobreano else "—", self.styles["TableCell"]), Paragraph("~450 dias", self.styles["TableCell"])],
        ]
        
        pesos_table = Table(pesos_data, colWidths=[70 * mm, 50 * mm, 50 * mm])
        pesos_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("BACKGROUND", (0, 1), (-1, -1), HexColor("#ffffff")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f8fafc")]),
            ("BOX", (0, 0), (-1, -1), 1, PRINT_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(pesos_table)
        
        benchmark_data = []
        if animal.fonte_origem == "ANCP" and animal.anc_mg is not None:
            benchmark_data = [
                ["Média Genética (MG)", f"{animal.anc_mg:.3f}"],
                ["Tamanho (TE)", f"{animal.anc_te:.3f}"],
                ["Maternidade (M)", f"{animal.anc_m:.3f}"],
                ["Peso (P)", f"{animal.anc_p:.3f}"],
                ["Sobreano (SP)", f"{animal.anc_sp:.3f}"],
                ["Eficiência (E)", f"{animal.anc_e:.3f}"],
                ["Área Olho Lombo (SAO)", f"{animal.anc_sao:.3f}"],
                ["Legume (LEG)", f"{animal.anc_leg:.3f}"],
            ]
        elif animal.fonte_origem == "GENEPLUS" and animal.gen_iqg is not None:
            benchmark_data = [
                ["Índice Qualidade Genética (IQG)", f"{animal.gen_iqg:.3f}"],
                ["Peso Maternidade (PMM)", f"{animal.gen_pmm:.3f}"],
                ["Peso (P)", f"{animal.gen_p:.3f}"],
                ["Sobreano (SP)", f"{animal.gen_sp:.3f}"],
                ["Eficiência (E)", f"{animal.gen_e:.3f}"],
                ["Área Olho Lombo (SAO)", f"{animal.gen_sao:.3f}"],
            ]
        elif animal.fonte_origem == "PMGZ" and animal.pmg_iabc is not None:
            benchmark_data = [
                ["Índice ABCZ (iABCZ)", f"{animal.pmg_iabc:.3f}"],
                ["Zootecnia Peso Materno (ZPmm)", f"{animal.pmg_zpmm:.3f}"],
                ["Peso (P)", f"{animal.pmg_p:.3f}"],
                ["Sobreano (SP)", f"{animal.pmg_sp:.3f}"],
                ["Eficiência (E)", f"{animal.pmg_e:.3f}"],
                ["Área Olho Lombo (SAO)", f"{animal.pmg_sao:.3f}"],
            ]
        
        if benchmark_data:
            story.append(Spacer(1, 8 * mm))
            platform_label = animal.fonte_origem or "Benchmark"
            story.append(Paragraph(f"DEPs — {platform_label}", self.styles["SectionTitle"]))
            story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm))
            
            dep_rows = [[Paragraph("Característica", self.styles["TableHeader"]), Paragraph("DEP", self.styles["TableHeader"])]]
            for char, val in benchmark_data:
                dep_rows.append([Paragraph(char, self.styles["TableCellLeft"]), Paragraph(val, self.styles["TableCell"])])
            
            dep_table = Table(dep_rows, colWidths=[120 * mm, 50 * mm])
            dep_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("BACKGROUND", (0, 1), (-1, -1), HexColor("#ffffff")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f8fafc")]),
                ("BOX", (0, 0), (-1, -1), 1, PRINT_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(dep_table)
        
        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def generate_benchmark_report(
        self,
        platform_code: str,
        platform_name: str,
        characteristic: dict,
        evaluations: list = None,
        animals: list = None,
        farm_name: str = None,
    ) -> bytes:
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
        
        title = f"Relatório de Benchmark — {platform_name}"
        if farm_name:
            title += f" — {farm_name}"
        story.append(Paragraph(title, self.styles["ReportTitle"]))
        story.append(Paragraph(
            f"Característica: {characteristic['name']} | Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            self.styles["ReportSubtitle"]
        ))
        
        story.append(Paragraph("Resumo Estatístico", self.styles["SectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm))
        
        if evaluations:
            values = [getattr(e, characteristic["column"]) for e in evaluations if getattr(e, characteristic["column"]) is not None]
        elif animals:
            values = [getattr(a, characteristic["column"]) for a in animals if getattr(a, characteristic["column"]) is not None]
        else:
            values = []
        
        import statistics
        mean_val = statistics.mean(values) if values else 0
        median_val = statistics.median(values) if values else 0
        std_val = statistics.stdev(values) if len(values) > 1 else 0
        min_val = min(values) if values else 0
        max_val = max(values) if values else 0
        
        stats_data = [
            [Paragraph("Estatística", self.styles["TableHeader"]), Paragraph("Valor", self.styles["TableHeader"])],
            [Paragraph("Total de Animais", self.styles["TableCellLeft"]), Paragraph(str(len(values)), self.styles["TableCell"])],
            [Paragraph("Média", self.styles["TableCellLeft"]), Paragraph(f"{mean_val:.4f}", self.styles["TableCell"])],
            [Paragraph("Mediana", self.styles["TableCellLeft"]), Paragraph(f"{median_val:.4f}", self.styles["TableCell"])],
            [Paragraph("Desvio Padrão", self.styles["TableCellLeft"]), Paragraph(f"{std_val:.4f}", self.styles["TableCell"])],
            [Paragraph("Mínimo", self.styles["TableCellLeft"]), Paragraph(f"{min_val:.4f}", self.styles["TableCell"])],
            [Paragraph("Máximo", self.styles["TableCellLeft"]), Paragraph(f"{max_val:.4f}", self.styles["TableCell"])],
        ]
        
        stats_table = Table(stats_data, colWidths=[80 * mm, 90 * mm])
        stats_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("BACKGROUND", (0, 1), (-1, -1), HexColor("#ffffff")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f8fafc")]),
            ("BOX", (0, 0), (-1, -1), 1, PRINT_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(stats_table)
        
        data_source = evaluations if evaluations else animals
        
        if not data_source:
            data_source = []
        
        sex_dist = {}
        for item in data_source:
            sex = getattr(item, 'sexo', None) or "Desconhecido"
            val = getattr(item, characteristic["column"])
            if val is not None:
                if sex not in sex_dist:
                    sex_dist[sex] = []
                sex_dist[sex].append(val)
        
        if sex_dist:
            story.append(Spacer(1, 8 * mm))
            story.append(Paragraph("Distribuição por Sexo", self.styles["SectionTitle"]))
            story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm))
            
            sex_means = {k: statistics.mean(v) for k, v in sex_dist.items()}
            story.append(self._build_bar_chart_data(sex_means, "Sexo"))
        
        if len(data_source) > 0:
            story.append(Spacer(1, 8 * mm))
            story.append(Paragraph("Top 20 Avaliações", self.styles["SectionTitle"]))
            story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=4 * mm))
            
            sorted_animals = sorted(
                [(a, getattr(a, characteristic["column"])) for a in data_source if getattr(a, characteristic["column"]) is not None],
                key=lambda x: x[1],
                reverse=True
            )[:20]
            
            top_animals_data = [
                [Paragraph("ID", self.styles["TableHeader"]), Paragraph("Valor", self.styles["TableHeader"])]
            ]
            for a, val in sorted_animals:
                top_animals_data.append([
                    Paragraph(str(getattr(a, 'animal_id', '—'))[:8], self.styles["TableCellLeft"]),
                    Paragraph(f"{val:.4f}", self.styles["TableCell"]),
                ])
            
            top_table = Table(top_animals_data, colWidths=[80 * mm, 80 * mm])
            top_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("BACKGROUND", (0, 1), (-1, -1), HexColor("#ffffff")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f8fafc")]),
                ("BOX", (0, 0), (-1, -1), 1, PRINT_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, PRINT_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(top_table)
        
        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
