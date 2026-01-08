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
from ui.theme import LIGHT_TOKENS, BRAND_COLORS


class PDFGenerator:
    """Generates professional PDF reports for candidate rankings"""

    # Fixed logo path - CROSSROADS Professional Services logo
    LOGO_PATH = Path(__file__).parent / "Services Logo Full Color3840px copy.png"
    LOGO_WIDTH = 2.5 * inch
    LOGO_HEIGHT = 1.0 * inch
    
    # CROSSROADS Brand Colors (from design tokens)
    BRAND_BLUE = colors.HexColor(BRAND_COLORS['blue'])
    BRAND_BROWN = colors.HexColor(BRAND_COLORS['brown'])
    BRAND_BLACK = colors.HexColor(BRAND_COLORS['black'])
    
    # Typography from design tokens (converted to ReportLab units)
    # Spacing: convert rem to points (assuming 1rem = 12pt base)
    SPACING_XS = 3  # 0.25rem * 12
    SPACING_SM = 6  # 0.5rem * 12
    SPACING_MD = 12  # 1rem * 12
    SPACING_LG = 18  # 1.5rem * 12
    SPACING_XL = 24  # 2rem * 12
    
    # Font sizes from tokens
    FONT_SIZE_XS = 9   # 0.75rem * 12
    FONT_SIZE_SM = 10.5  # 0.875rem * 12
    FONT_SIZE_BASE = 12  # 1rem * 12
    FONT_SIZE_LG = 13.5  # 1.125rem * 12
    FONT_SIZE_XL = 15   # 1.25rem * 12
    FONT_SIZE_2XL = 18  # 1.5rem * 12
    FONT_SIZE_3XL = 22.5  # 1.875rem * 12

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
        """Setup custom paragraph styles with CROSSROADS branding using design tokens"""
        # Title style - using FONT_SIZE_3XL from tokens
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=self.FONT_SIZE_3XL,
            textColor=self.BRAND_BROWN,
            spaceAfter=self.SPACING_XL,
            alignment=TA_CENTER,
            fontName='Times-Bold',
            leading=self.FONT_SIZE_3XL * 1.25  # line-height-tight
        ))

        # Section header - using FONT_SIZE_XL from tokens
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=self.FONT_SIZE_XL,
            textColor=self.BRAND_BROWN,
            spaceAfter=self.SPACING_MD,
            spaceBefore=self.SPACING_LG,
            fontName='Times-Bold',
            leading=self.FONT_SIZE_XL * 1.25,
            borderWidth=1,
            borderColor=self.BRAND_BLUE,
            borderPadding=self.SPACING_SM,
            backColor=colors.HexColor(LIGHT_TOKENS['colors']['surface_elevated'])
        ))

        # Body text - using FONT_SIZE_SM from tokens
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=self.FONT_SIZE_SM,
            leading=self.FONT_SIZE_SM * 1.5,  # line-height-normal
            alignment=TA_JUSTIFY,
            fontName='Times-Roman',
            textColor=colors.HexColor(LIGHT_TOKENS['colors']['text_primary'])
        ))

        # Candidate name - using FONT_SIZE_LG from tokens
        self.styles.add(ParagraphStyle(
            name='CandidateName',
            parent=self.styles['Heading3'],
            fontSize=self.FONT_SIZE_LG,
            textColor=self.BRAND_BROWN,  # Brown for emphasis
            fontName='Times-Bold',  # Serif bold
            spaceAfter=6
        ))

        # Rationale style - 9pt with serif
        self.styles.add(ParagraphStyle(
            name='RationaleStyle',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=12,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#333333'),
            fontName='Times-Roman',  # Serif font
            wordWrap='LTR',
            splitLongWords=True
        ))
        
        # Bullet point style - optimized for scannability with serif
        self.styles.add(ParagraphStyle(
            name='BulletStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#333333'),
            fontName='Times-Roman',  # Serif font
            leftIndent=0,
            bulletIndent=0,
            spaceBefore=2,
            spaceAfter=2
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

        # Title - CROSSROADS branded
        title = Paragraph("CANDIDATE RANKING REPORT", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.1*inch))
        
        # Add CROSSROADS branding subtitle
        subtitle = Paragraph(
            "<i>CROSSROADS Professional Services</i>",
            ParagraphStyle(
                'SubtitleStyle',
                parent=self.styles['Normal'],
                fontSize=12,
                textColor=self.BRAND_BLUE,  # CROSSROADS blue
                alignment=TA_CENTER,
                fontName='Times-Italic',  # Serif italic
                spaceAfter=10
            )
        )
        story.append(subtitle)
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
        story.append(self._create_overall_notes(top_candidates, all_candidates_count, job_details))

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
            "<b>CROSSROADS</b><br/><i>Professional Services</i>",
            ParagraphStyle(
                'LogoStyle',
                parent=self.styles['Normal'],
                fontSize=14,
                textColor=self.BRAND_BROWN,  # Brown for CROSSROADS
                fontName='Times-Bold',  # Serif font
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
            ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),  # Serif bold
            ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),  # Serif
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.BRAND_BROWN),  # Brown for labels
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#333333')),  # Dark gray for values
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        return table

    def _create_job_summary(self, job_details: JobDetails):
        """Create job summary section with scannable bullet points"""
        elements = []

        bullets = []
        
        # Job title
        bullets.append(f"• <b>Position:</b> {job_details.job_title}")
        
        # Equivalent titles
        if job_details.equivalent_titles:
            equiv_text = ", ".join(job_details.equivalent_titles[:5])
            if len(job_details.equivalent_titles) > 5:
                equiv_text += f" (+{len(job_details.equivalent_titles) - 5} more)"
            bullets.append(f"• <b>Equivalent Titles:</b> {equiv_text}")

        # Experience level
        if job_details.experience_level:
            bullets.append(f"• <b>Experience Level:</b> {job_details.experience_level}")

        # Certifications - truncate long lists
        MAX_JOB_CERTS_DISPLAY = 6
        must_have_certs = [c.name for c in job_details.certifications if c.category == 'must-have']
        bonus_certs = [c.name for c in job_details.certifications if c.category == 'bonus']

        if must_have_certs:
            if len(must_have_certs) > MAX_JOB_CERTS_DISPLAY:
                cert_text = ', '.join(must_have_certs[:MAX_JOB_CERTS_DISPLAY]) + f" (+{len(must_have_certs) - MAX_JOB_CERTS_DISPLAY} more)"
            else:
                cert_text = ', '.join(must_have_certs)
            bullets.append(f"• <b>Must-Have Certifications:</b> {cert_text}")

        if bonus_certs:
            if len(bonus_certs) > MAX_JOB_CERTS_DISPLAY:
                cert_text = ', '.join(bonus_certs[:MAX_JOB_CERTS_DISPLAY]) + f" (+{len(bonus_certs) - MAX_JOB_CERTS_DISPLAY} more)"
            else:
                cert_text = ', '.join(bonus_certs)
            bullets.append(f"• <b>Bonus Certifications:</b> {cert_text}")

        # Required skills
        if job_details.required_skills:
            skills_text = ', '.join(job_details.required_skills[:8])
            if len(job_details.required_skills) > 8:
                skills_text += f" (+{len(job_details.required_skills) - 8} more)"
            bullets.append(f"• <b>Required Skills:</b> {skills_text}")

        # Preferred skills
        if job_details.preferred_skills:
            skills_text = ', '.join(job_details.preferred_skills[:8])
            if len(job_details.preferred_skills) > 8:
                skills_text += f" (+{len(job_details.preferred_skills) - 8} more)"
            bullets.append(f"• <b>Preferred Skills:</b> {skills_text}")

        # Location
        bullets.append(f"• <b>Location:</b> {job_details.location}")
        
        # Industry template if used
        if job_details.industry_template and job_details.industry_template != "general":
            bullets.append(f"• <b>Scoring Profile:</b> {job_details.industry_template.title()} template")

        # Add all bullets from earlier
        for bullet in bullets:
            elements.append(Paragraph(bullet, self.styles['CustomBody']))
            elements.append(Spacer(1, 0.04*inch))
        
        # Scoring weights/profile - show the weighting system being used
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("<b>Scoring Weights (Universal Standard):</b>", self.styles['CustomBody']))
        elements.append(Spacer(1, 0.05*inch))
        
        # Get scoring weights (default to universal standard if not set)
        from industry_templates import get_default_weights
        weights = job_details.scoring_profile if job_details.scoring_profile else get_default_weights()
        
        # Sort weights by importance (highest first)
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        
        weight_bullets = []
        for key, weight in sorted_weights:
            weight_pct = weight * 100
            # Format the key name nicely (NEW PRIORITY ORDER)
            key_name = key.replace('_', ' ').title()
            if key == 'experience_level':
                key_name = 'Experience Level'
            elif key == 'job_title_match':
                key_name = 'Job Title Match'
            elif key == 'required_skills':
                key_name = 'Required Skills'
            elif key == 'transferrable_skills':
                key_name = 'Transferrable Skills'
            elif key == 'location':
                key_name = 'Location'
            elif key == 'preferred_skills':
                key_name = 'Preferred Skills'
            elif key == 'certifications_education':
                key_name = 'Certifications/Education'
            # Legacy support for old weight keys
            elif key == 'must_have_certs':
                key_name = 'Must-Have Certifications (Legacy)'
            elif key == 'bonus_certs':
                key_name = 'Bonus Certifications (Legacy)'
            
            # Highlight top 3 most important criteria
            if len(weight_bullets) < 3:
                weight_bullets.append(f"• <b>{key_name}:</b> {weight_pct:.0f}% (High Priority)")
            else:
                weight_bullets.append(f"• {key_name}: {weight_pct:.0f}%")
        
        for bullet in weight_bullets:
            elements.append(Paragraph(bullet, self.styles['CustomBody']))
            elements.append(Spacer(1, 0.03*inch))

        return KeepTogether(elements)

    def _create_ranking_summary(self, top_candidates: List[CandidateScore],
                                all_candidates_count: int):
        """Create ranking summary paragraph"""
        text = f"Evaluated {all_candidates_count} candidate(s) total. "
        text += f"Presenting top {len(top_candidates)} candidate(s) ranked by fit score."

        return Paragraph(text, self.styles['CustomBody'])

    def _create_candidate_detail(self, rank: int, candidate: CandidateScore,
                                job_details: JobDetails):
        """Create detailed candidate section with scannable bullet points, prioritized by scoring weights"""
        elements = []

        # Rank and name with score - ALWAYS displayed
        name_text = f"{rank}. {candidate.name} — Score: {candidate.fit_score:.2f}/10"
        elements.append(Paragraph(name_text, self.styles['CandidateName']))
        elements.append(Spacer(1, 0.08*inch))

        # Contact info - ALWAYS displayed (show "Not provided" if missing)
        contact_info = []
        email_display = candidate.email if candidate.email else "Not provided"
        phone_display = candidate.phone if candidate.phone else "Not provided"
        
        contact_info.append(f"<b>Email:</b> {email_display}")
        contact_info.append(f"<b>Phone:</b> {phone_display}")
        
        contact_text = " • ".join(contact_info)
        elements.append(Paragraph(contact_text, self.styles['CustomBody']))
        elements.append(Spacer(1, 0.1*inch))

        # Get scoring weights to prioritize information
        from industry_templates import get_default_weights
        weights = job_details.scoring_profile if job_details.scoring_profile else get_default_weights()
        
        # Key Qualifications as bullet points - ordered by weight importance
        elements.append(Paragraph("<b>Key Qualifications (by importance):</b>", self.styles['CustomBody']))
        elements.append(Spacer(1, 0.05*inch))
        
        # Build qualification items with their weights (NEW PRIORITY ORDER)
        qual_items = []
        
        # 1. Experience Level (HIGHEST PRIORITY)
        exp_weight = weights.get('experience_level', 0.25)
        exp_years = candidate.experience_match.get('years', 0)
        if exp_years > 0:
            qual_items.append((exp_weight, f"• <b>Experience:</b> {exp_years} years"))
        else:
            qual_items.append((exp_weight, f"• <b>Experience:</b> Not specified"))
        
        # 2. Job Title Match (SECOND PRIORITY)
        title_weight = weights.get('job_title_match', 0.20)
        titles = candidate.experience_match.get('titles', [])
        if titles:
            title_list = ', '.join(titles[:3])
            if len(titles) > 3:
                title_list += f" (+{len(titles) - 3} more)"
            qual_items.append((title_weight, f"• <b>Job Title Match:</b> {title_list}"))
        else:
            qual_items.append((title_weight, f"• <b>Job Title Match:</b> No relevant titles"))
        
        # 3. Required Skills (THIRD PRIORITY)
        req_skills_weight = weights.get('required_skills', 0.18)
        req_skills_list = candidate.skills_match.get('candidate_skills', [])
        required_skills = job_details.required_skills or []
        matched_skills = [s for s in req_skills_list if any(req.lower() in s.lower() or s.lower() in req.lower() for req in required_skills)]
        if matched_skills:
            skills_display = ', '.join(matched_skills[:5])
            if len(matched_skills) > 5:
                skills_display += f" (+{len(matched_skills) - 5} more)"
            qual_items.append((req_skills_weight, f"• <b>Required Skills:</b> {skills_display}"))
        else:
            qual_items.append((req_skills_weight, f"• <b>Required Skills:</b> Limited match"))
        
        # 4. Transferrable Skills (FOURTH PRIORITY - NEW)
        transferrable_weight = weights.get('transferrable_skills', 0.15)
        transferrable_skills_list = candidate.transferrable_skills_match.get('transferrable_skills', [])
        if transferrable_skills_list:
            skills_display = ', '.join(transferrable_skills_list[:5])
            if len(transferrable_skills_list) > 5:
                skills_display += f" (+{len(transferrable_skills_list) - 5} more)"
            qual_items.append((transferrable_weight, f"• <b>Transferrable Skills:</b> {skills_display}"))
        else:
            qual_items.append((transferrable_weight, f"• <b>Transferrable Skills:</b> Limited transferrable skills"))
        
        # 5. Location (FIFTH PRIORITY)
        location_weight = weights.get('location', 0.10)
        if candidate.location_match:
            qual_items.append((location_weight, f"• <b>Location:</b> ✓ Matches job location"))
        else:
            qual_items.append((location_weight, f"• <b>Location:</b> ✗ Does not match job location"))
        
        # 6. Preferred Skills (SIXTH PRIORITY)
        pref_skills_weight = weights.get('preferred_skills', 0.07)
        pref_skills_list = candidate.skills_match.get('candidate_skills', [])
        preferred_skills = job_details.preferred_skills or []
        matched_pref_skills = [s for s in pref_skills_list if any(pref.lower() in s.lower() or s.lower() in pref.lower() for pref in preferred_skills)]
        if matched_pref_skills:
            skills_display = ', '.join(matched_pref_skills[:5])
            if len(matched_pref_skills) > 5:
                skills_display += f" (+{len(matched_pref_skills) - 5} more)"
            qual_items.append((pref_skills_weight, f"• <b>Preferred Skills:</b> {skills_display}"))
        else:
            qual_items.append((pref_skills_weight, f"• <b>Preferred Skills:</b> Limited match"))
        
        # 7. Certifications/Education (LOWEST PRIORITY - COMBINED)
        cert_ed_weight = weights.get('certifications_education', 0.05)
        if candidate.certifications:
            MAX_CERTS_DISPLAY = 3
            if len(candidate.certifications) > MAX_CERTS_DISPLAY:
                cert_list = ', '.join(candidate.certifications[:MAX_CERTS_DISPLAY])
                qual_items.append((cert_ed_weight, f"• <b>Certifications/Education:</b> {cert_list} (+{len(candidate.certifications) - MAX_CERTS_DISPLAY} more)"))
            else:
                qual_items.append((cert_ed_weight, f"• <b>Certifications/Education:</b> {', '.join(candidate.certifications)}"))
        else:
            qual_items.append((cert_ed_weight, f"• <b>Certifications/Education:</b> None listed"))
        
        # Sort by weight (highest first) and display
        qual_items.sort(key=lambda x: x[0], reverse=True)
        for _, bullet in qual_items:
            elements.append(Paragraph(bullet, self.styles['CustomBody']))
            elements.append(Spacer(1, 0.03*inch))
        
        elements.append(Spacer(1, 0.08*inch))
        
        # Summary - concise 1-2 sentence fit assessment
        elements.append(Paragraph("<b>Summary:</b>", self.styles['CustomBody']))
        elements.append(Spacer(1, 0.05*inch))
        
        # Generate concise 1-2 sentence summary
        summary_text = self._generate_concise_summary(candidate, job_details)
        elements.append(Paragraph(summary_text, self.styles['RationaleStyle']))
        elements.append(Spacer(1, 0.05*inch))

        # Create border box
        return KeepTogether(elements)

    def _generate_concise_summary(self, candidate: CandidateScore, job_details: JobDetails) -> str:
        """
        Generate a concise 1-2 sentence summary about the candidate's fit for the role.
        
        Args:
            candidate: CandidateScore object with evaluation data
            job_details: JobDetails object with job requirements
            
        Returns:
            Concise 1-2 sentence summary string
        """
        import re
        
        # Clean the rationale first
        cleaned_rationale = self._clean_rationale_text(candidate.rationale)
        
        # Extract key information from candidate data
        score = candidate.fit_score
        exp_years = candidate.experience_match.get('years', 0)
        has_must_have_certs = candidate.certification_match.get('has_must_have', False)
        required_skills_match = candidate.skills_match.get('required_match_rate', 0.0)
        location_match = candidate.location_match
        job_titles = candidate.experience_match.get('titles', [])
        
        # Build summary based on score and key qualifications
        summary_parts = []
        
        # Overall assessment based on score
        if score >= 8.0:
            assessment = "excellent fit"
        elif score >= 6.5:
            assessment = "strong candidate"
        elif score >= 5.0:
            assessment = "viable candidate"
        else:
            assessment = "limited fit"
        
        # First sentence: Overall fit with key strengths
        strengths = []
        if exp_years > 0:
            strengths.append(f"{exp_years} years of experience")
        if job_titles:
            strengths.append("relevant job titles")
        if has_must_have_certs:
            strengths.append("required certifications")
        if required_skills_match >= 0.7:
            strengths.append("strong skills match")
        elif required_skills_match >= 0.5:
            strengths.append("adequate skills match")
        
        if strengths:
            strength_text = ", ".join(strengths[:2])  # Limit to 2 key strengths
            first_sentence = f"{candidate.name} presents an {assessment} for the {job_details.job_title} position with {strength_text}."
        else:
            first_sentence = f"{candidate.name} presents an {assessment} for the {job_details.job_title} position."
        
        summary_parts.append(first_sentence)
        
        # Second sentence: Key gaps or additional qualifications (if needed)
        gaps = []
        if not has_must_have_certs and any(c.category == 'must-have' for c in job_details.certifications):
            gaps.append("missing required certifications")
        if required_skills_match < 0.5 and job_details.required_skills:
            gaps.append("limited required skills match")
        if not location_match:
            gaps.append("location mismatch")
        
        # Additional qualifications
        bonuses = []
        if len(candidate.certifications) > 0 and not has_must_have_certs:
            bonuses.append("additional certifications")
        transferrable_skills = candidate.transferrable_skills_match.get('transferrable_skills', [])
        if transferrable_skills and len(transferrable_skills) >= 3:
            bonuses.append("strong transferrable skills")
        
        # Build second sentence if there are notable gaps or bonuses
        if gaps and score < 7.0:
            # Mention gaps for lower-scoring candidates
            gap_text = gaps[0]  # Focus on primary gap
            second_sentence = f"Primary consideration: {gap_text}."
            summary_parts.append(second_sentence)
        elif bonuses and score >= 6.5:
            # Mention bonuses for stronger candidates
            bonus_text = bonuses[0]
            second_sentence = f"Additional qualifications include {bonus_text}."
            summary_parts.append(second_sentence)
        elif score < 5.0:
            # For low scores, provide context
            second_sentence = "Significant gaps in key requirements limit overall fit."
            summary_parts.append(second_sentence)
        
        # If we couldn't build a good summary from structured data, extract from rationale
        if len(summary_parts) < 2 and cleaned_rationale:
            # Extract first 1-2 meaningful sentences from cleaned rationale
            sentences = re.split(r'(?<=[.!?])\s+', cleaned_rationale.strip())
            meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 30 and len(s.strip()) < 200]
            
            # Look for overall assessment sentences
            for sentence in meaningful_sentences[:2]:
                # Skip if it's a detail sentence (too specific)
                if any(word in sentence.lower() for word in ['component', 'score', 'calculation', 'weighted', 'breakdown']):
                    continue
                # Prefer sentences with overall assessment words
                if any(word in sentence.lower() for word in ['fit', 'candidate', 'recommend', 'suitable', 'qualified', 'strong', 'excellent', 'good', 'viable']):
                    if len(summary_parts) == 1:
                        summary_parts.append(sentence)
                        break
        
        # Ensure we have at least one sentence
        if not summary_parts:
            summary_parts.append(f"{candidate.name} scored {score:.1f}/10 for the {job_details.job_title} position.")
        
        # Join sentences (limit to 2 sentences max)
        summary = " ".join(summary_parts[:2])
        
        # Ensure summary ends with proper punctuation
        if not summary.rstrip().endswith(('.', '!', '?')):
            summary = summary.rstrip() + "."
        
        return summary

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
        content_found = False  # Track if we've found any actual content
        
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
            # But be more careful - only remove if it's clearly a prompt/calculation line
            if re.search(r'Score\s*\(0-10\)', line_stripped, re.IGNORECASE):
                continue
            # Remove lines that are just score calculations (e.g., "8.0 × 0.15 = 1.2")
            if re.search(r'^\s*\d+\.?\d*\s*[×x*]\s*\d+\.?\d*\s*=\s*\d+\.?\d*\s*$', line_stripped):
                continue
            # Remove lines with "FINAL_SCORE" or "Final Score" patterns
            if re.search(r'FINAL[_\s]?SCORE\s*:?\s*\d+\.?\d*/10', line_stripped, re.IGNORECASE):
                continue
            if re.search(r'\*\*FINAL[_\s]?SCORE\*\*', line_stripped, re.IGNORECASE):
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
            
            # Remove "Score Breakdown" or "Score Calculation" sections
            if re.search(r'Score\s+(?:Breakdown|Calculation|Breakdown and Calculation)', line_stripped, re.IGNORECASE):
                skip_until_content = True
                continue
            
            # Remove lines that are score calculations (e.g., "Transferrable skills: 8.0 × 0.15 = 1.2")
            if re.search(r'^\s*\w+.*?:\s*\d+\.?\d*\s*[×x*]\s*\d+\.?\d*\s*=\s*\d+\.?\d*\s*$', line_stripped, re.IGNORECASE):
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
                # Made less restrictive: reduced from 20 to 10 chars, allow colons if line is longer
                if (len(line_stripped) > 10 and 
                    not any(line_stripped.startswith(word) for word in question_starters) and
                    not re.search(r'^\d+\.\s*[A-Z\s]+ANALYSIS', line_stripped, re.IGNORECASE) and  # Not a numbered analysis header
                    not (':' in line_stripped[:20] and len(line_stripped) < 50)):  # Not a short label: value format
                    skip_until_content = False
                    content_found = True
                    cleaned_lines.append(line)
                continue
            
            # Include the line if it has content
            if line_stripped:
                # Mark that we've found content
                if len(line_stripped) > 10:
                    content_found = True
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
        
        # SAFEGUARD: If cleaning removed everything, return original rationale
        # (but still remove FINAL_SCORE line and obvious prompt headers)
        if not cleaned_text or (not content_found and len(cleaned_text) < 50):
            # Fallback: return original but remove only the most obvious prompt elements
            fallback = rationale
            # Remove FINAL_SCORE line (all variations including markdown)
            fallback = re.sub(r'\*\*?FINAL[_\s]?SCORE\*\*?\s*:?\s*\d+\.?\d*/10.*', '', fallback, flags=re.IGNORECASE | re.MULTILINE)
            fallback = re.sub(r'FINAL[_\s]?SCORE\s*:?\s*\d+\.?\d*/10.*', '', fallback, flags=re.IGNORECASE | re.MULTILINE)
            # Remove "Score Breakdown and Calculation" sections
            fallback = re.sub(r'Score\s+Breakdown\s+and\s+Calculation:.*?(?=FINAL_SCORE|Summary|\Z)', '', fallback, flags=re.DOTALL | re.IGNORECASE)
            # Remove weighted calculation lines (e.g., "Transferrable skills: 8.0 × 0.15 = 1.2")
            fallback = re.sub(r'^\s*\w+.*?:\s*\d+\.?\d*\s*[×x*]\s*\d+\.?\d*\s*=\s*\d+\.?\d*\s*$', '', fallback, flags=re.MULTILINE | re.IGNORECASE)
            # Remove COMPONENT_SCORES section
            fallback = re.sub(r'COMPONENT_SCORES:.*?(?=WEIGHTED CALCULATION|FINAL_SCORE|Score Breakdown|\Z)', '', fallback, flags=re.DOTALL | re.IGNORECASE)
            # Remove WEIGHTED CALCULATION section
            fallback = re.sub(r'WEIGHTED\s+CALCULATION:.*?(?=FINAL_SCORE|Score Breakdown|\Z)', '', fallback, flags=re.DOTALL | re.IGNORECASE)
            # Remove obvious section headers (all caps lines ending with colon)
            fallback = re.sub(r'^[A-Z\s]{15,}:\s*$', '', fallback, flags=re.MULTILINE)
            # Clean up multiple blank lines
            fallback = re.sub(r'\n{3,}', '\n\n', fallback)
            cleaned_text = fallback.strip()
        
        return cleaned_text.strip()

    def _create_ranking_chart(self, top_candidates: List[CandidateScore],
                             job_details: JobDetails):
        """Create visual ranking chart with Y/N indicators"""
        if not top_candidates:
            return None

        # Limit to top 10 candidates to prevent overflow
        MAX_CHART_CANDIDATES = 10
        chart_candidates = top_candidates[:MAX_CHART_CANDIDATES]

        # Abbreviated criteria labels (NEW PRIORITY ORDER)
        criteria = [
            'Exp\nLevel',
            'Title\nMatch',
            'Req\nSkills',
            'Transfer\nSkills',
            'Location',
            'Pref\nSkills',
            'Certs/\nEdu'
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

            # Evaluation criteria (NEW PRIORITY ORDER)
            # Get certifications/education score
            cert_ed_score = candidate.component_scores.get('certifications_education', 0.0) if candidate.component_scores else 0.0
            if cert_ed_score == 0.0:
                # Fallback: derive from certification_match
                has_must_have = candidate.certification_match.get('has_must_have', False)
                has_certs = len(candidate.certifications) > 0
                cert_ed_score = 8.0 if (has_must_have and has_certs) else (6.0 if has_certs else 2.0)
            
            evaluations = [
                candidate.experience_match['level_match'] >= 0.7,  # 1. Experience Level
                self._job_title_match(candidate.experience_match),  # 2. Job Title Match
                candidate.skills_match['required_match_rate'] >= 0.7,  # 3. Required Skills
                candidate.transferrable_skills_match.get('match_rate', 0.0) >= 0.6,  # 4. Transferrable Skills
                candidate.location_match,  # 5. Location
                candidate.skills_match['preferred_match_rate'] >= 0.5,  # 6. Preferred Skills
                cert_ed_score >= 6.0  # 7. Certifications/Education
            ]

            for j, is_match in enumerate(evaluations, 1):
                if is_match:
                    # CROSSROADS blue Y for Yes
                    ax.text(j + 0.5, row + 0.5, 'Y', ha='center', va='center',
                           color='#00A8CC', fontsize=12, fontweight='bold')
                else:
                    # Brown-tinted red N for No
                    ax.text(j + 0.5, row + 0.5, 'N', ha='center', va='center',
                           color='#C85A3A', fontsize=12, fontweight='bold')

            # Score - use CROSSROADS blue for high scores, brown for medium, orange/red for low
            if candidate.fit_score >= 8:
                score_color = '#00A8CC'  # CROSSROADS blue for excellent
            elif candidate.fit_score >= 6.5:
                score_color = '#4A90E2'  # Lighter blue for good
            elif candidate.fit_score >= 5:
                score_color = '#D4A574'  # Brown-tinted orange for viable
            else:
                score_color = '#C85A3A'  # Brown-tinted red for poor

            ax.text(num_criteria + 1.5, row + 0.5, f"{candidate.fit_score:.1f}",
                   ha='center', va='center', fontsize=10, fontweight='bold',
                   color=score_color)

        # Set limits and remove axes
        ax.set_xlim(0, num_criteria + 2)
        ax.set_ylim(0, num_candidates + 1)
        ax.axis('off')

        # Legend - use Y/N with CROSSROADS colors
        legend_elements = [
            mpatches.Patch(color='#00A8CC', label='Y = Meets Criteria'),  # CROSSROADS blue
            mpatches.Patch(color='#C85A3A', label='N = Does Not Meet')  # Brown-tinted red
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
                             all_candidates_count: int, job_details: JobDetails = None):
        """Create overall notes section with scannable bullet points, weight-aware"""
        elements = []

        bullets = []

        # Summary statistics
        if top_candidates:
            avg_score = sum(c.fit_score for c in top_candidates) / len(top_candidates)
            max_score = max(c.fit_score for c in top_candidates)
            min_score = min(c.fit_score for c in top_candidates)

            bullets.append(f"• <b>Average Score:</b> {avg_score:.2f}/10")
            bullets.append(f"• <b>Score Range:</b> {min_score:.2f} - {max_score:.2f}/10")
            
            # Score interpretation based on universal standard
            excellent = sum(1 for c in top_candidates if c.fit_score >= 8.0)
            good = sum(1 for c in top_candidates if 6.5 <= c.fit_score < 8.0)
            viable = sum(1 for c in top_candidates if 5.0 <= c.fit_score < 6.5)
            
            if excellent > 0:
                bullets.append(f"• <b>Excellent Fit (8.0+):</b> {excellent} candidate(s) - highly recommended")
            if good > 0:
                bullets.append(f"• <b>Good Fit (6.5-7.9):</b> {good} candidate(s) - minor gaps")
            if viable > 0:
                bullets.append(f"• <b>Viable (5.0-6.4):</b> {viable} candidate(s) - may need additional screening")

        # Excluded candidates note
        excluded = all_candidates_count - len(top_candidates)
        if excluded > 0:
            bullets.append(f"• <b>Excluded:</b> {excluded} candidate(s) below 5.0 threshold")

        # Add statistics bullets
        for bullet in bullets:
            elements.append(Paragraph(bullet, self.styles['CustomBody']))
            elements.append(Spacer(1, 0.05*inch))

        # Key Insights - weight-aware
        if top_candidates and job_details:
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph("<b>Key Insights (by scoring weights):</b>", self.styles['CustomBody']))
            elements.append(Spacer(1, 0.05*inch))
            
            from industry_templates import get_default_weights
            weights = job_details.scoring_profile if job_details.scoring_profile else get_default_weights()
            
            insight_bullets = []
            
            # Check highest-weighted criteria first (NEW PRIORITY ORDER)
            exp_weight = weights.get('experience_level', 0.25)
            if exp_weight >= 0.20:  # Highest priority
                low_exp = sum(1 for c in top_candidates
                            if c.experience_match.get('level_match', 0.0) < 0.7)
                if low_exp > 0:
                    insight_bullets.append(
                        f"• <b>Experience Level ({exp_weight*100:.0f}% weight):</b> {low_exp} candidate(s) below optimal experience level (highest priority)"
                    )
            
            title_weight = weights.get('job_title_match', 0.20)
            if title_weight >= 0.15:  # Second priority
                low_titles = sum(1 for c in top_candidates
                               if not self._job_title_match(c.experience_match))
                if low_titles > 0:
                    insight_bullets.append(
                        f"• <b>Job Title Match ({title_weight*100:.0f}% weight):</b> {low_titles} candidate(s) with limited title relevance (high priority)"
                    )
            
            req_skills_weight = weights.get('required_skills', 0.18)
            if req_skills_weight >= 0.15:  # Third priority
                low_skills = sum(1 for c in top_candidates
                               if c.skills_match['required_match_rate'] < 0.7)
                if low_skills > 0:
                    insight_bullets.append(
                        f"• <b>Required Skills ({req_skills_weight*100:.0f}% weight):</b> {low_skills} candidate(s) below 70% match (high priority)"
                    )
            
            transferrable_weight = weights.get('transferrable_skills', 0.15)
            if transferrable_weight >= 0.10:  # Fourth priority
                low_transferrable = sum(1 for c in top_candidates
                                      if c.transferrable_skills_match.get('match_rate', 0.0) < 0.6)
                if low_transferrable > 0:
                    insight_bullets.append(
                        f"• <b>Transferrable Skills ({transferrable_weight*100:.0f}% weight):</b> {low_transferrable} candidate(s) with limited transferrable skills"
                    )
            
            cert_ed_weight = weights.get('certifications_education', 0.05)
            if cert_ed_weight >= 0.05:  # Lowest priority but still check
                missing_certs = sum(1 for c in top_candidates
                                  if not c.certification_match['has_must_have'])
                if missing_certs > 0:
                    insight_bullets.append(
                        f"• <b>Certifications/Education ({cert_ed_weight*100:.0f}% weight):</b> {missing_certs} of {len(top_candidates)} missing must-have certifications (lower priority)"
                    )
            
            # High performers
            high_scores = sum(1 for c in top_candidates if c.fit_score >= 7.0)
            if high_scores > 0:
                insight_bullets.append(
                    f"• <b>Strong Candidates:</b> {high_scores} candidate(s) scored 7.0+ (excellent fit)"
                )
            
            if not insight_bullets:
                insight_bullets.append("• All top candidates meet key requirements based on scoring weights")
            
            for bullet in insight_bullets:
                elements.append(Paragraph(bullet, self.styles['CustomBody']))
                elements.append(Spacer(1, 0.05*inch))

        # Recommendations - weight-aware
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("<b>Recommendations:</b>", self.styles['CustomBody']))
        elements.append(Spacer(1, 0.05*inch))
        
        rec_bullets = [
            "• Prioritize candidates with scores ≥7.0 for initial interviews (excellent fit)",
            "• Candidates scoring 5.0-7.0 may be viable with additional screening",
        ]
        
        if job_details:
            from industry_templates import get_default_weights
            weights = job_details.scoring_profile if job_details.scoring_profile else get_default_weights()
            
            # Get top 3 most important criteria (NEW PRIORITY ORDER)
            sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
            top_criteria = [w[0] for w in sorted_weights[:3]]
            
            focus_areas = []
            if 'experience_level' in top_criteria:
                focus_areas.append("experience level")
            if 'job_title_match' in top_criteria:
                focus_areas.append("job title relevance")
            if 'required_skills' in top_criteria:
                focus_areas.append("required skills")
            if 'transferrable_skills' in top_criteria:
                focus_areas.append("transferrable skills")
            
            if focus_areas:
                rec_bullets.append(f"• Focus interview questions on: {', '.join(focus_areas)} (highest weighted criteria)")
            else:
                rec_bullets.append("• Focus on highest-weighted criteria during interviews")
        else:
            rec_bullets.append("• Focus on experience level, job title match, and required skills during interviews")
        
        for bullet in rec_bullets:
            elements.append(Paragraph(bullet, self.styles['CustomBody']))
            elements.append(Spacer(1, 0.05*inch))

        return KeepTogether(elements)
