"""
PDF Generator for Transcriptions
Creates professional-looking transcription PDFs
"""

import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether
)
from reportlab.pdfgen import canvas

from .transcription import TranscriptionResult, TranscriptionSegment

logger = logging.getLogger(__name__)


class TranscriptionPDFGenerator:
    """Generate professional PDF transcriptions"""
    
    def __init__(self, page_size=letter):
        """
        Initialize PDF generator
        
        Args:
            page_size: Page size (letter or A4)
        """
        self.page_size = page_size
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#4a4a4a'),
            spaceAfter=12,
            spaceBefore=12,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Speaker style
        self.styles.add(ParagraphStyle(
            name='Speaker',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=4,
            fontName='Helvetica-Bold'
        ))
        
        # Timestamp style
        self.styles.add(ParagraphStyle(
            name='Timestamp',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#808080'),
            spaceAfter=2,
            fontName='Helvetica-Oblique'
        ))
        
        # Transcription text style
        self.styles.add(ParagraphStyle(
            name='TranscriptText',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=16,
            spaceBefore=4,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        # Info style
        self.styles.add(ParagraphStyle(
            name='Info',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            spaceAfter=6,
            fontName='Helvetica'
        ))
    
    def generate_pdf(
        self,
        transcription: TranscriptionResult,
        output_path: Optional[Path] = None,
        speaker_filter: Optional[str] = None,
        title: str = "Transcription",
        include_timestamps: bool = True,
        include_metadata: bool = True
    ) -> bytes:
        """
        Generate PDF from transcription
        
        Args:
            transcription: TranscriptionResult object
            output_path: Optional path to save PDF
            speaker_filter: Optional speaker to filter (e.g., "Speaker 1")
            title: Document title
            include_timestamps: Whether to include timestamps
            include_metadata: Whether to include metadata header
            
        Returns:
            PDF bytes
        """
        
        # Create buffer
        buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
            title=title,
            author="TheConverter"
        )
        
        # Build content
        story = []
        
        # Add title
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Add metadata
        if include_metadata:
            story.extend(self._create_metadata_section(transcription, speaker_filter))
            story.append(Spacer(1, 0.3 * inch))
        
        # Add transcription content
        segments = transcription.segments
        if speaker_filter:
            segments = [s for s in segments if s.speaker == speaker_filter]
        
        story.extend(self._create_transcription_content(
            segments,
            include_timestamps
        ))
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_footer, onLaterPages=self._add_footer)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        # Save to file if path provided
        if output_path:
            output_path.write_bytes(pdf_bytes)
            logger.info(f"PDF saved to {output_path}")
        
        return pdf_bytes
    
    def _create_metadata_section(
        self,
        transcription: TranscriptionResult,
        speaker_filter: Optional[str]
    ) -> List:
        """Create metadata section"""
        
        elements = []
        
        # Create metadata table
        data = [
            ["Duration:", self._format_duration(transcription.duration)],
            ["Speakers:", ", ".join(transcription.speakers)],
            ["Language:", transcription.language.upper()],
            ["Model:", transcription.model_used],
            ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        ]
        
        if speaker_filter:
            data.append(["Filter:", f"Only {speaker_filter}"])
        
        table = Table(data, colWidths=[1.5*inch, 4*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4a4a4a')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1a1a1a')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_transcription_content(
        self,
        segments: List[TranscriptionSegment],
        include_timestamps: bool
    ) -> List:
        """Create transcription content"""
        
        elements = []
        
        # Add section header
        elements.append(Paragraph("Transcription", self.styles['CustomSubtitle']))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Add separator line
        elements.append(self._create_line())
        elements.append(Spacer(1, 0.2 * inch))
        
        # Group consecutive segments by speaker for cleaner output
        current_speaker = None
        current_text_parts = []
        current_start = None
        
        for i, segment in enumerate(segments):
            if segment.speaker != current_speaker:
                # Output previous speaker's content
                if current_speaker and current_text_parts:
                    elements.extend(self._create_speaker_block(
                        current_speaker,
                        " ".join(current_text_parts),
                        current_start,
                        segments[i-1].end_time,
                        include_timestamps
                    ))
                
                # Start new speaker block
                current_speaker = segment.speaker
                current_text_parts = [segment.text]
                current_start = segment.start_time
            else:
                # Continue current speaker
                current_text_parts.append(segment.text)
        
        # Output last speaker's content
        if current_speaker and current_text_parts:
            elements.extend(self._create_speaker_block(
                current_speaker,
                " ".join(current_text_parts),
                current_start,
                segments[-1].end_time,
                include_timestamps
            ))
        
        return elements
    
    def _create_speaker_block(
        self,
        speaker: str,
        text: str,
        start_time: float,
        end_time: float,
        include_timestamps: bool
    ) -> List:
        """Create a block for one speaker's continuous speech"""
        
        elements = []
        
        # Speaker name with color coding
        speaker_color = self._get_speaker_color(speaker)
        speaker_style = ParagraphStyle(
            'TempSpeaker',
            parent=self.styles['Speaker'],
            textColor=speaker_color
        )
        
        elements.append(Paragraph(f"<b>{speaker}</b>", speaker_style))
        
        # Timestamp if enabled
        if include_timestamps:
            timestamp_text = f"[{self._format_time(start_time)} - {self._format_time(end_time)}]"
            elements.append(Paragraph(timestamp_text, self.styles['Timestamp']))
        
        # Transcription text
        # Escape special characters for ReportLab
        safe_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        elements.append(Paragraph(safe_text, self.styles['TranscriptText']))
        
        return elements
    
    def _get_speaker_color(self, speaker: str) -> colors.Color:
        """Get color for speaker"""
        speaker_colors = {
            "Speaker 1": colors.HexColor('#2c5aa0'),
            "Speaker 2": colors.HexColor('#c7254e'),
            "Speaker 3": colors.HexColor('#18bc9c'),
            "Speaker 4": colors.HexColor('#f39c12'),
        }
        
        return speaker_colors.get(speaker, colors.HexColor('#666666'))
    
    def _create_line(self) -> Table:
        """Create a horizontal line"""
        line_table = Table([['']], colWidths=[6.5*inch])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#cccccc')),
        ]))
        return line_table
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def _format_time(self, seconds: float) -> str:
        """Format time as MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def _add_footer(self, canvas_obj, doc):
        """Add footer to page"""
        canvas_obj.saveState()
        
        # Page number
        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.setFillColor(colors.HexColor('#808080'))
        canvas_obj.drawCentredString(
            self.page_size[0] / 2.0,
            0.5 * inch,
            text
        )
        
        # Watermark
        canvas_obj.setFont('Helvetica-Oblique', 8)
        canvas_obj.drawRightString(
            self.page_size[0] - 72,
            0.5 * inch,
            "Generated by TheConverter"
        )
        
        canvas_obj.restoreState()


def generate_transcription_pdf(
    transcription: TranscriptionResult,
    output_path: Optional[Path] = None,
    speaker_filter: Optional[str] = None,
    title: str = "Interview Transcription",
    **kwargs
) -> bytes:
    """
    Helper function to generate transcription PDF
    
    Args:
        transcription: TranscriptionResult object
        output_path: Optional path to save PDF
        speaker_filter: Optional speaker filter
        title: PDF title
        **kwargs: Additional arguments for PDFGenerator
        
    Returns:
        PDF bytes
    """
    generator = TranscriptionPDFGenerator()
    return generator.generate_pdf(
        transcription=transcription,
        output_path=output_path,
        speaker_filter=speaker_filter,
        title=title,
        **kwargs
    )
