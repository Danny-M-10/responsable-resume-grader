"""
PDF Generator Module
Creates professional PDF reports with rankings and visualizations
"""

import os
from typing import List, Dict, Any
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas

from models import JobDetails, CandidateScore
from pathlib import Path


class PDFGenerator:
    """Generates professional PDF reports for candidate rankings"""

    # Fixed logo path - always use the same logo for consistency
    LOGO_PATH = Path(__file__).parent / "responsableLOGO-color-2048px.jpg"
    LOGO_WIDTH = 2.5 * inch
    LOGO_HEIGHT = 1.0 * inch

    def __init__(self, logo_path: str = None):
        """
        Initialize PDF Generator

        Args:
            logo_path: Deprecated - logo is now fixed. This parameter is ignored.
        """
        # Always use the fixed logo path
        self.logo_path = str(self.LOGO_PATH)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles with consistent font sizes"""
        # Title style - 20pt (standardized)
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Section header - 14pt (standardized)
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=colors.HexColor('#3498db'),
            borderPadding=5,
            backColor=colors.HexColor('#ecf0f1')
        ))

        # Body text - 10pt (keep)
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY
        ))

        # Candidate name - 11pt (standardized)
        self.styles.add(ParagraphStyle(
            name='CandidateName',
            parent=self.styles['Heading3'],
            fontSize=11,
            textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica-Bold',
            spaceAfter=6
        ))

        # Rationale style - 9pt (increased from 8pt for better readability)
        self.styles.add(ParagraphStyle(
            name='RationaleStyle',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=12,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#2c3e50'),
            wordWrap='LTR',
            splitLongWords=True
        ))

    def generate(self, job_details: JobDetails,
                top_candidates: List[CandidateScore],
                all_candidates_count: int,
                output_path: str):
        """
        Generate the complete PDF report

        Args:
            job_details: Job requirements and analysis
            top_candidates: Ranked list of top candidates
            all_candidates_count: Total candidates evaluated
            output_path: Path to save PDF
        """
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        # Build content
        story = []

        # Header with logo placeholder
        story.append(self._create_header())
        story.append(Spacer(1, 0.3*inch))

        # Title
        title = Paragraph("CANDIDATE RANKING REPORT", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.2*inch))

        # Metadata
        story.append(self._create_metadata(job_details))
        story.append(Spacer(1, 0.3*inch))

        # Section 1: Job Summary
        story.append(Paragraph("JOB SUMMARY", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.1*inch))
        story.append(self._create_job_summary(job_details))
        story.append(Spacer(1, 0.2*inch))

        # Section 2: Candidate Rankings
        story.append(Paragraph("CANDIDATE RANKINGS", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.1*inch))
        story.append(self._create_ranking_summary(top_candidates, all_candidates_count))
        story.append(Spacer(1, 0.2*inch))

        # Individual candidate details - ensure sorted (highest to lowest)
        sorted_candidates = sorted(top_candidates, key=lambda x: x.fit_score, reverse=True)
        for i, candidate in enumerate(sorted_candidates, 1):
            story.append(self._create_candidate_detail(i, candidate, job_details))
            story.append(Spacer(1, 0.15*inch))

        # Section 3: Ranking Visualization
        story.append(PageBreak())
        story.append(Paragraph("RANKING VISUALIZATION", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.1*inch))

        # Generate and add chart
        chart_image = self._create_ranking_chart(top_candidates, job_details)
        if chart_image:
            story.append(chart_image)
            story.append(Spacer(1, 0.2*inch))

        # Section 4: Overall Notes
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("OVERALL NOTES", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.1*inch))
        story.append(self._create_overall_notes(top_candidates, all_candidates_count))

        # Build PDF
        doc.build(story)

        print(f"  PDF report generated: {output_path}")

    def _create_header(self):
        """Create header with fixed company logo (left-justified, consistent size)"""
        # Always try to use the fixed logo file
        if os.path.exists(self.logo_path):
            try:
                # Get actual image dimensions to calculate aspect ratio
                try:
                    from PIL import Image as PILImage
                    pil_img = PILImage.open(self.logo_path)
                    img_width, img_height = pil_img.size
                    img_aspect = img_width / img_height if img_height > 0 else 1.0
                except ImportError:
                    # PIL not available, use default aspect ratio
                    img_aspect = 2.5  # Default aspect ratio (width/height)
                
                # Calculate dimensions maintaining aspect ratio
                max_width = self.LOGO_WIDTH
                max_height = self.LOGO_HEIGHT
                
                # Calculate scaled dimensions that fit within max bounds while maintaining aspect ratio
                if img_aspect > (max_width / max_height):
                    # Image is wider - constrain by width
                    scaled_width = max_width
                    scaled_height = max_width / img_aspect
                else:
                    # Image is taller - constrain by height
                    scaled_height = max_height
                    scaled_width = max_height * img_aspect
                
                # Create logo image with calculated dimensions
                logo = Image(self.logo_path, width=scaled_width, height=scaled_height)
                logo.hAlign = 'LEFT'
                
                return logo
            except Exception as e:
                print(f"  WARNING: Could not load logo from {self.logo_path}: {e}")
                # Fall back to text logo
                pass

        # Fallback: Create a simple text-based logo if image not found
        logo_text = Paragraph(
            "<b>ResponsAble Safety Staffing</b><br/>Safety Staffing On Demand",
            ParagraphStyle(
                'LogoStyle',
                parent=self.styles['Normal'],
                fontSize=12,  # Standardized (reduced from 14pt)
                textColor=colors.HexColor('#2c3e50'),
                fontName='Helvetica-Bold',
                alignment=TA_LEFT,
                spaceAfter=0.1*inch
            )
        )
        return logo_text

    def _create_metadata(self, job_details: JobDetails):
        """Create metadata table"""
        data = [
            ['Report Date:', datetime.now().strftime("%B %d, %Y")],
            ['Position:', job_details.job_title],
            ['Location:', job_details.location]
        ]

        table = Table(data, colWidths=[1.5*inch, 5*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),  # Standardized to 10pt
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        return table

    def _create_job_summary(self, job_details: JobDetails):
        """Create job summary section"""
        elements = []

        # Job title and equivalents
        equiv_text = ", ".join(job_details.equivalent_titles[:5])
        if len(job_details.equivalent_titles) > 5:
            equiv_text += f" (+{len(job_details.equivalent_titles) - 5} more)"

        elements.append(Paragraph(
            f"<b>Position:</b> {job_details.job_title}",
            self.styles['CustomBody']
        ))

        if job_details.equivalent_titles:
            elements.append(Spacer(1, 0.05*inch))
            elements.append(Paragraph(
                f"<b>Equivalent Titles:</b> {equiv_text}",
                self.styles['CustomBody']
            ))

        # Experience level
        if job_details.experience_level:
            elements.append(Spacer(1, 0.05*inch))
            elements.append(Paragraph(
                f"<b>Experience Level:</b> {job_details.experience_level}",
                self.styles['CustomBody']
            ))

        # Certifications - truncate long lists
        MAX_JOB_CERTS_DISPLAY = 8
        must_have_certs = [c.name for c in job_details.certifications if c.category == 'must-have']
        bonus_certs = [c.name for c in job_details.certifications if c.category == 'bonus']

        if must_have_certs:
            elements.append(Spacer(1, 0.05*inch))
            if len(must_have_certs) > MAX_JOB_CERTS_DISPLAY:
                cert_text = ', '.join(must_have_certs[:MAX_JOB_CERTS_DISPLAY]) + f" (+{len(must_have_certs) - MAX_JOB_CERTS_DISPLAY} more)"
            else:
                cert_text = ', '.join(must_have_certs)
            elements.append(Paragraph(
                f"<b>Must-Have Certifications:</b> {cert_text}",
                self.styles['CustomBody']
            ))

        if bonus_certs:
            elements.append(Spacer(1, 0.05*inch))
            if len(bonus_certs) > MAX_JOB_CERTS_DISPLAY:
                cert_text = ', '.join(bonus_certs[:MAX_JOB_CERTS_DISPLAY]) + f" (+{len(bonus_certs) - MAX_JOB_CERTS_DISPLAY} more)"
            else:
                cert_text = ', '.join(bonus_certs)
            elements.append(Paragraph(
                f"<b>Bonus Certifications:</b> {cert_text}",
                self.styles['CustomBody']
            ))

        # Required skills
        if job_details.required_skills:
            elements.append(Spacer(1, 0.05*inch))
            elements.append(Paragraph(
                f"<b>Required Skills:</b> {', '.join(job_details.required_skills[:10])}",
                self.styles['CustomBody']
            ))

        # Preferred skills
        if job_details.preferred_skills:
            elements.append(Spacer(1, 0.05*inch))
            elements.append(Paragraph(
                f"<b>Preferred Skills:</b> {', '.join(job_details.preferred_skills[:10])}",
                self.styles['CustomBody']
            ))

        # Location
        elements.append(Spacer(1, 0.05*inch))
        elements.append(Paragraph(
            f"<b>Location:</b> {job_details.location}",
            self.styles['CustomBody']
        ))

        return KeepTogether(elements)

    def _create_ranking_summary(self, top_candidates: List[CandidateScore],
                                all_candidates_count: int):
        """Create ranking summary paragraph"""
        text = f"Evaluated {all_candidates_count} candidate(s) total. "
        text += f"Presenting top {len(top_candidates)} candidate(s) ranked by fit score."

        return Paragraph(text, self.styles['CustomBody'])

    def _create_candidate_detail(self, rank: int, candidate: CandidateScore,
                                job_details: JobDetails):
        """Create detailed candidate section"""
        elements = []

        # Rank and name
        name_text = f"{rank}. {candidate.name} — Score: {candidate.fit_score:.2f}/10"
        elements.append(Paragraph(name_text, self.styles['CandidateName']))

        # Contact info
        contact_data = [
            ['Email:', candidate.email, 'Phone:', candidate.phone]
        ]

        # Calculate column widths to fit page (page width ~7.5 inches, margins ~1.5 inches total = 6 inches usable)
        # Use 0.7, 2.3, 0.7, 2.3 inches for better balance
        contact_table = Table(contact_data, colWidths=[0.7*inch, 2.3*inch, 0.7*inch, 2.3*inch])
        contact_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),  # Standardized to 10pt
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#34495e')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(contact_table)
        elements.append(Spacer(1, 0.05*inch))

        # Certifications - truncate long lists
        MAX_CERTS_DISPLAY = 8
        if candidate.certifications:
            if len(candidate.certifications) > MAX_CERTS_DISPLAY:
                cert_list = ', '.join(candidate.certifications[:MAX_CERTS_DISPLAY])
                cert_text = f"<b>Certifications:</b> {cert_list} (+{len(candidate.certifications) - MAX_CERTS_DISPLAY} more)"
            else:
                cert_text = f"<b>Certifications:</b> {', '.join(candidate.certifications)}"
        else:
            cert_text = "<b>Certifications:</b> None listed"

        elements.append(Paragraph(cert_text, self.styles['CustomBody']))
        elements.append(Spacer(1, 0.05*inch))

        # Rationale - clean and format properly
        cleaned_rationale = self._clean_rationale_text(candidate.rationale)

        # Truncate very long rationale text (allow 4-5 sentences, ~1500 chars)
        # Ensure truncation happens at sentence boundaries
        MAX_RATIONALE_CHARS = 1500
        if cleaned_rationale and len(cleaned_rationale) > MAX_RATIONALE_CHARS:
            # Truncate at the last complete sentence before the limit
            truncated = cleaned_rationale[:MAX_RATIONALE_CHARS]
            # Find the last sentence boundary (period, exclamation, question mark)
            last_period = truncated.rfind('.')
            last_exclamation = truncated.rfind('!')
            last_question = truncated.rfind('?')
            last_sentence_end = max(last_period, last_exclamation, last_question)
            
            # Only truncate at sentence boundary if we found one and it's reasonable (at least 1000 chars)
            if last_sentence_end > 1000:
                cleaned_rationale = truncated[:last_sentence_end + 1]
            else:
                # Fallback: truncate at word boundary if no sentence boundary found
                if ' ' in truncated:
                    truncated = truncated.rsplit(' ', 1)[0]
                cleaned_rationale = truncated + "..."

        # Wrap rationale in a table with proper formatting to prevent overflow
        rationale_width = 6.5 * inch  # Fit within page margins
        rationale_data = [[Paragraph(f"<b>Rationale:</b>", self.styles['CustomBody'])]]
        rationale_table = Table(rationale_data, colWidths=[rationale_width])
        rationale_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(rationale_table)

        # Add rationale content in a properly formatted table
        if cleaned_rationale:
            rationale_content_data = [[Paragraph(cleaned_rationale, self.styles['RationaleStyle'])]]
            rationale_content_table = Table(rationale_content_data, colWidths=[rationale_width])
            rationale_content_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(rationale_content_table)
        else:
            # Fallback if rationale is empty after cleaning
            elements.append(Paragraph("No detailed rationale available.", self.styles['RationaleStyle']))

        # Create border box
        return KeepTogether(elements)

    def _clean_rationale_text(self, rationale: str) -> str:
        """
        Clean rationale text to remove prompt headers and section markers
        
        Removes:
        - Section headers like "MUST-HAVE CERTIFICATIONS ANALYSIS:", "REQUIRED CERTIFICATION ANALYSIS"
        - Numbered sections like "1. **MUST-HAVE CERTIFICATIONS ANALYSIS**"
        - Prompt-like phrases such as "Component score (0-10): ___"
        - Question-format prompts ("Which required certifications...")
        - Instruction-format prompts ("Provide component scores...")
        - Markdown headers (###, ##, #)
        - Lines that are only section titles
        - COMPONENT_SCORES and WEIGHTED CALCULATION sections
        - All variations of "ANALYSIS" headers
        
        Args:
            rationale: Raw rationale text from AI
            
        Returns:
            Cleaned rationale text with only evaluation content
        """
        import re
        
        if not rationale:
            return ""
        
        lines = rationale.split('\n')
        cleaned_lines = []
        skip_until_content = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines at the start
            if not line_stripped and not cleaned_lines:
                continue
            
            # Remove numbered sections with bold headers (e.g., "1. **MUST-HAVE CERTIFICATIONS ANALYSIS**:")
            if re.match(r'^\d+\.\s*\*\*.*?\*\*:', line_stripped):
                skip_until_content = True
                continue
            
            # Remove markdown headers with "ANALYSIS" (e.g., "### MUST-HAVE CERTIFICATIONS ANALYSIS:")
            if re.match(r'^#{1,6}\s+.*ANALYSIS.*:', line_stripped, re.IGNORECASE):
                skip_until_content = True
                continue
            
            # Remove all-caps section headers with "ANALYSIS" (e.g., "MUST-HAVE CERTIFICATIONS ANALYSIS:")
            if re.match(r'^[A-Z\s]+ANALYSIS:', line_stripped):
                skip_until_content = True
                continue
            
            # Remove "REQUIRED CERTIFICATION" or "BONUS CERTIFICATION" (without "ANALYSIS")
            if re.match(r'^[A-Z\s]*(?:REQUIRED|BONUS|MUST-HAVE)\s+CERTIFICATION', line_stripped, re.IGNORECASE):
                skip_until_content = True
                continue
            
            # Remove "CERTIFICATION ANALYSIS" (any variation)
            if re.search(r'CERTIFICATION\s+ANALYSIS', line_stripped, re.IGNORECASE):
                skip_until_content = True
                continue
            
            # Remove "SKILLS ANALYSIS" (any variation)
            if re.search(r'SKILLS\s+ANALYSIS', line_stripped, re.IGNORECASE):
                skip_until_content = True
                continue
            
            # Remove "EXPERIENCE ANALYSIS" or "EXPERIENCE EVALUATION"
            if re.search(r'EXPERIENCE\s+(?:ANALYSIS|EVALUATION)', line_stripped, re.IGNORECASE):
                skip_until_content = True
                continue
            
            # Remove "JOB TITLE MATCH" or "TITLE MATCH ANALYSIS"
            if re.search(r'(?:JOB\s+)?TITLE\s+MATCH(?:\s+ANALYSIS)?', line_stripped, re.IGNORECASE):
                skip_until_content = True
                continue
            
            # Remove "LOCATION MATCH" or "LOCATION ANALYSIS"
            if re.search(r'LOCATION\s+(?:MATCH|ANALYSIS)', line_stripped, re.IGNORECASE):
                skip_until_content = True
                continue
            
            # Remove component score placeholders (e.g., "Component score (0-10): ___")
            if re.search(r'Component\s+score.*:', line_stripped, re.IGNORECASE):
                continue
            
            # Remove lines with score patterns like "X.X/10" or "Score (0-10)"
            if re.search(r'\d+\.?\d*\s*/\s*10|Score\s*\(0-10\)', line_stripped, re.IGNORECASE):
                if not re.search(r'\d+\.\d+/10', line_stripped):  # Keep actual scores in text
                    continue
            
            # Remove lines with colons followed by underscores or placeholders
            if re.search(r':\s*(?:___|___|\.\.\.|placeholder)', line_stripped, re.IGNORECASE):
                continue
            
            # Remove COMPONENT_SCORES section entirely
            if 'COMPONENT_SCORES:' in line_stripped.upper():
                skip_until_content = True
                continue
            
            # Remove WEIGHTED CALCULATION section
            if 'WEIGHTED CALCULATION' in line_stripped.upper() or re.search(r'WEIGHTED\s+CALCULATION', line_stripped, re.IGNORECASE):
                skip_until_content = True
                continue
            
            # Remove lines starting with question/instruction words
            question_starters = ['Which', 'Provide', 'Calculate', 'Evaluate', 'Determine', 'Identify', 'List']
            if any(line_stripped.startswith(word) for word in question_starters):
                # Check if it's a question/instruction (ends with ? or contains instruction words)
                if '?' in line_stripped or any(word in line_stripped for word in ['required certifications', 'missing', 'present', 'component score', 'match percentage']):
                    continue
            
            # Remove common prompt phrases
            prompt_phrases = [
                r'Which\s+required\s+certifications',
                r'Which\s+are\s+missing',
                r'Match\s+percentage',
                r'Component\s+score\s*\(0-10\)',
                r'Provide\s+component\s+scores',
                r'Calculate\s+weighted',
                r'Final\s+score\s*:',
                r'Overall\s+fit\s*:'
            ]
            for phrase in prompt_phrases:
                if re.search(phrase, line_stripped, re.IGNORECASE):
                    continue
            
            # Remove lines that are just section titles in various formats
            section_patterns = [
                r'^\d+\.\s+[A-Z\s]+ANALYSIS',
                r'^#{1,6}\s+[A-Z\s]+ANALYSIS',
                r'^\*\*[A-Z\s]+ANALYSIS\*\*',
                r'^[A-Z\s]+ANALYSIS\s*$',
                r'^[A-Z\s]+MATCH\s*$',
                r'^[A-Z\s]+EVALUATION\s*$',
                r'^OVERALL\s+ASSESSMENT\s*$',
                r'^RECOMMENDATIONS\s*$',
                r'^FINAL\s+SCORE\s*$',
                r'^REQUIRED\s+CERTIFICATION',
                r'^BONUS\s+CERTIFICATION',
                r'^MUST-HAVE\s+CERTIFICATION',
                r'^REQUIRED\s+SKILLS',
                r'^PREFERRED\s+SKILLS',
                r'^EXPERIENCE\s+LEVEL',
                r'^JOB\s+TITLE\s+MATCH',
                r'^LOCATION\s+MATCH'
            ]
            
            is_section_header = False
            for pattern in section_patterns:
                if re.match(pattern, line_stripped, re.IGNORECASE):
                    is_section_header = True
                    skip_until_content = True
                    break
            
            if is_section_header:
                continue
            
            # Skip lines that are just dashes or separators
            if re.match(r'^[-=]{3,}$', line_stripped):
                continue
            
            # If we're skipping until content, check if this line has actual content
            if skip_until_content:
                # Look for lines with substantial content (more than just a few words)
                # Exclude question/instruction formats
                if (len(line_stripped) > 20 and 
                    not any(line_stripped.startswith(word) for word in question_starters) and
                    not re.search(r'^\d+\.', line_stripped) and  # Not a numbered list item that's a header
                    ':' not in line_stripped[:30]):  # Not a label: value format that's a prompt
                    skip_until_content = False
                    cleaned_lines.append(line)
                continue
            
            # Include the line if it has content
            if line_stripped:
                cleaned_lines.append(line)
        
        cleaned_text = '\n'.join(cleaned_lines).strip()
        
        # Remove any remaining markdown headers
        cleaned_text = re.sub(r'^#{1,6}\s+', '', cleaned_text, flags=re.MULTILINE)
        
        # Remove any remaining all-caps section headers (standalone lines)
        cleaned_text = re.sub(r'^[A-Z\s]{10,}\s*$', '', cleaned_text, flags=re.MULTILINE)
        
        # Remove lines that are just evaluation instructions
        instruction_patterns = [
            r'^Which\s+.*\?',
            r'^Provide\s+.*',
            r'^Calculate\s+.*',
            r'^Evaluate\s+.*',
            r'^Determine\s+.*'
        ]
        for pattern in instruction_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Remove multiple consecutive blank lines
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        # Final cleanup: remove any remaining prompt-like patterns
        # Remove lines that are just "X:" or "X: ___" format (likely prompt labels)
        lines_final = cleaned_text.split('\n')
        cleaned_final = []
        for line in lines_final:
            line_stripped = line.strip()
            # Skip lines that look like prompt labels (short, ends with colon, no substantial content after)
            if re.match(r'^[A-Z\s]{2,30}:\s*(?:___|\.\.\.|$)', line_stripped):
                continue
            cleaned_final.append(line)
        
        cleaned_text = '\n'.join(cleaned_final).strip()
        
        return cleaned_text.strip()

    def _create_ranking_chart(self, top_candidates: List[CandidateScore],
                             job_details: JobDetails):
        """Create visual ranking chart with Y/N indicators"""
        if not top_candidates:
            return None

        # Limit to top 10 candidates to prevent overflow
        MAX_CHART_CANDIDATES = 10
        chart_candidates = top_candidates[:MAX_CHART_CANDIDATES]

        # Abbreviated criteria labels (no rotation needed)
        criteria = [
            'Must\nCerts',
            'Bonus\nCerts',
            'Req\nSkills',
            'Pref\nSkills',
            'Exp\nLevel',
            'Title\nMatch',
            'Location'
        ]

        # Create figure - adjust size based on number of candidates
        # Keep it smaller to fit on PDF page
        fig_height = min(5, 1.5 + len(chart_candidates) * 0.4)
        fig, ax = plt.subplots(figsize=(7.5, fig_height))

        # Prepare data - truncate names more aggressively
        candidate_names = [f"{c.name[:18]}..." if len(c.name) > 18 else c.name
                          for c in chart_candidates]

        # Matrix: rows = candidates, cols = criteria
        num_candidates = len(chart_candidates)
        num_criteria = len(criteria)

        # Create grid
        for i in range(num_candidates + 1):
            ax.axhline(i, color='gray', linewidth=0.5)

        for j in range(num_criteria + 2):  # +2 for name and score columns
            ax.axvline(j, color='gray', linewidth=0.5)

        # Headers - horizontal text, no rotation - standardized to 9pt
        ax.text(0.5, num_candidates + 0.5, 'Candidate', ha='center', va='center',
                fontweight='bold', fontsize=9)

        for j, criterion in enumerate(criteria, 1):
            ax.text(j + 0.5, num_candidates + 0.5, criterion, ha='center', va='center',
                    fontweight='bold', fontsize=9)  # Standardized to 9pt

        ax.text(num_criteria + 1.5, num_candidates + 0.5, 'Score', ha='center', va='center',
                fontweight='bold', fontsize=9)

        # Fill in data
        for i, candidate in enumerate(chart_candidates):
            row = num_candidates - i - 1  # Reverse order (top candidate at top)

            # Candidate name - standardized to 9pt
            ax.text(0.5, row + 0.5, candidate_names[i], ha='center', va='center',
                    fontsize=9)

            # Evaluation criteria
            evaluations = [
                candidate.certification_match['has_must_have'],
                candidate.certification_match['has_bonus'],
                candidate.skills_match['required_match_rate'] >= 0.7,
                candidate.skills_match['preferred_match_rate'] >= 0.5,
                candidate.experience_match['level_match'] >= 0.7,
                self._job_title_match(candidate.experience_match),
                candidate.location_match
            ]

            for j, is_match in enumerate(evaluations, 1):
                if is_match:
                    # Green Y for Yes
                    ax.text(j + 0.5, row + 0.5, 'Y', ha='center', va='center',
                           color='green', fontsize=12, fontweight='bold')
                else:
                    # Red N for No
                    ax.text(j + 0.5, row + 0.5, 'N', ha='center', va='center',
                           color='red', fontsize=12, fontweight='bold')

            # Score - standardized to 10pt
            score_color = 'darkgreen' if candidate.fit_score >= 8 else \
                         'green' if candidate.fit_score >= 6.5 else \
                         'orange' if candidate.fit_score >= 5 else 'red'

            ax.text(num_criteria + 1.5, row + 0.5, f"{candidate.fit_score:.1f}",
                   ha='center', va='center', fontsize=10, fontweight='bold',
                   color=score_color)

        # Set limits and remove axes
        ax.set_xlim(0, num_criteria + 2)
        ax.set_ylim(0, num_candidates + 1)
        ax.axis('off')

        # Legend - use Y/N instead of Unicode symbols
        legend_elements = [
            mpatches.Patch(color='green', label='Y = Meets Criteria'),
            mpatches.Patch(color='red', label='N = Does Not Meet')
        ]
        ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, -0.05),
                 ncol=2, fontsize=9)

        # Add title - standardized to 11pt
        plt.title('Candidate Ranking Matrix', fontsize=11, fontweight='bold', pad=20)

        plt.tight_layout()

        # Save to BytesIO
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()

        # Create Image for ReportLab with constrained dimensions
        # Maximum dimensions that fit on a letter-size page with margins
        max_width = 6.5 * inch
        max_height = 5.0 * inch

        img = Image(img_buffer, width=max_width, height=max_height)

        # Let ReportLab handle aspect ratio while respecting max dimensions
        img._restrictSize(max_width, max_height)

        return img

    def _job_title_match(self, experience_match: Dict[str, Any]) -> bool:
        """Check if job title matches"""
        # Simple heuristic: if there are job titles, assume match
        return len(experience_match.get('titles', [])) > 0

    def _create_overall_notes(self, top_candidates: List[CandidateScore],
                             all_candidates_count: int):
        """Create overall notes section"""
        elements = []

        # Summary statistics
        if top_candidates:
            avg_score = sum(c.fit_score for c in top_candidates) / len(top_candidates)
            max_score = max(c.fit_score for c in top_candidates)
            min_score = min(c.fit_score for c in top_candidates)

            elements.append(Paragraph(
                f"<b>Summary Statistics:</b> Average score: {avg_score:.2f}, "
                f"Highest: {max_score:.2f}, Lowest: {min_score:.2f}",
                self.styles['CustomBody']
            ))
            elements.append(Spacer(1, 0.1*inch))

        # Excluded candidates note
        excluded = all_candidates_count - len(top_candidates)
        if excluded > 0:
            elements.append(Paragraph(
                f"<b>Excluded Candidates:</b> {excluded} candidate(s) excluded from top list "
                f"due to low fit scores (below 5.0 threshold).",
                self.styles['CustomBody']
            ))
            elements.append(Spacer(1, 0.1*inch))

        # Trends
        if top_candidates:
            # Check certification gaps
            missing_certs = sum(1 for c in top_candidates
                              if not c.certification_match['has_must_have'])

            if missing_certs > 0:
                elements.append(Paragraph(
                    f"<b>Certification Gap:</b> {missing_certs} out of {len(top_candidates)} "
                    f"top candidate(s) missing required certifications. Consider candidates "
                    f"willing to obtain certifications.",
                    self.styles['CustomBody']
                ))
                elements.append(Spacer(1, 0.1*inch))

            # Skills analysis
            low_skills = sum(1 for c in top_candidates
                           if c.skills_match['required_match_rate'] < 0.7)

            if low_skills > 0:
                elements.append(Paragraph(
                    f"<b>Skills Gap:</b> {low_skills} candidate(s) show gaps in required skills. "
                    f"May require training or onboarding support.",
                    self.styles['CustomBody']
                ))
                elements.append(Spacer(1, 0.1*inch))

        # Recommendations
        elements.append(Paragraph(
            "<b>Recommendations:</b> Prioritize candidates with scores above 7.0 for initial "
            "interviews. Candidates scoring 5.0-7.0 may be viable with additional screening. "
            "Focus on must-have certifications and required skills during interview process.",
            self.styles['CustomBody']
        ))

        return KeepTogether(elements)
