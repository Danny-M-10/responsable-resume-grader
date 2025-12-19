"""
Streamlit Web Interface for Candidate Ranker Application

Run with: streamlit run app.py
"""

import streamlit as st
import os
import tempfile
import csv
import io
from datetime import datetime
from pathlib import Path
from candidate_ranker import CandidateRankerApp
from config import OpenAIConfig
from ai_job_parser import AIJobParser
from loading_components import get_cycling_message


def init_session_state():
    """Initialize session state variables for result persistence"""
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'last_job_title' not in st.session_state:
        st.session_state.last_job_title = ""


def clear_results():
    """Clear stored results to start fresh"""
    st.session_state.results = None
    st.session_state.processing = False


def generate_csv_export(candidate_scores, job_title, location):
    """Generate CSV data from candidate scores"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        'Rank', 'Name', 'Email', 'Phone', 'Fit Score',
        'Certifications', 'Has Must-Have Certs', 'Location Match',
        'Rationale'
    ])

    # Sort candidates by score
    sorted_candidates = sorted(candidate_scores, key=lambda x: x.fit_score, reverse=True)

    # Data rows
    for i, candidate in enumerate(sorted_candidates, 1):
        writer.writerow([
            i,
            candidate.name,
            candidate.email,
            candidate.phone,
            f"{candidate.fit_score:.2f}",
            '; '.join(candidate.certifications) if candidate.certifications else 'None',
            'Yes' if candidate.certification_match.get('has_must_have', False) else 'No',
            'Yes' if candidate.location_match else 'No',
            candidate.rationale[:500] if candidate.rationale else ''
        ])

    return output.getvalue()


def get_score_color(score):
    """Return color class based on score"""
    if score >= 7.5:
        return "#27ae60"  # Green - Excellent
    elif score >= 5.5:
        return "#f39c12"  # Yellow/Orange - Good
    else:
        return "#e74c3c"  # Red - Needs improvement


def display_results(results):
    """Display stored results with sorting and filtering options"""
    st.markdown('<div class="section-header">Results</div>', unsafe_allow_html=True)

    candidate_scores = results['candidate_scores']
    pdf_path = results['pdf_path']
    pdf_data = results['pdf_data']
    job_details = results['job_details']
    processing_time = results.get('processing_time', 0)

    # Results header with clear button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Job:** {job_details['title']} | **Location:** {job_details['location']}")
    with col2:
        if st.button("Start New Analysis", type="secondary"):
            clear_results()
            st.rerun()

    # Summary metrics with color coding
    st.markdown("### Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Candidates", len(candidate_scores))

    with col2:
        viable_count = len([c for c in candidate_scores if c.fit_score >= 5.0])
        st.metric("Viable Candidates", viable_count)

    with col3:
        if candidate_scores:
            avg_score = sum(c.fit_score for c in candidate_scores) / len(candidate_scores)
            st.metric("Average Score", f"{avg_score:.2f}/10")

    with col4:
        if processing_time > 0:
            st.metric("Processing Time", f"{processing_time:.1f}s")

    # Sorting and filtering controls
    st.markdown("### Candidate Rankings")

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        sort_option = st.selectbox(
            "Sort by",
            ["Score (High to Low)", "Score (Low to High)", "Name (A-Z)", "Name (Z-A)"],
            key="sort_option"
        )

    with col2:
        min_score = st.slider(
            "Minimum Score Filter",
            min_value=0.0,
            max_value=10.0,
            value=0.0,
            step=0.5,
            key="min_score_filter"
        )

    with col3:
        show_details = st.checkbox("Expand All", value=False, key="expand_all")

    # Apply sorting
    sorted_candidates = list(candidate_scores)
    if sort_option == "Score (High to Low)":
        sorted_candidates.sort(key=lambda x: x.fit_score, reverse=True)
    elif sort_option == "Score (Low to High)":
        sorted_candidates.sort(key=lambda x: x.fit_score)
    elif sort_option == "Name (A-Z)":
        sorted_candidates.sort(key=lambda x: x.name.lower())
    elif sort_option == "Name (Z-A)":
        sorted_candidates.sort(key=lambda x: x.name.lower(), reverse=True)

    # Apply filtering
    filtered_candidates = [c for c in sorted_candidates if c.fit_score >= min_score]

    if len(filtered_candidates) < len(sorted_candidates):
        st.info(f"Showing {len(filtered_candidates)} of {len(sorted_candidates)} candidates (filtered by score >= {min_score})")

    # Display candidates with enhanced cards
    for i, candidate in enumerate(filtered_candidates, 1):
        score_color = get_score_color(candidate.fit_score)

        # Create score badge HTML
        score_badge = f"""
        <span style="
            background-color: {score_color};
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-weight: bold;
            font-size: 1rem;
        ">{candidate.fit_score:.1f}/10</span>
        """

        with st.expander(f"{i}. {candidate.name}", expanded=show_details):
            # Score and basic info row
            col1, col2, col3 = st.columns([1, 2, 2])

            with col1:
                st.markdown(f"**Score:** {score_badge}", unsafe_allow_html=True)

            with col2:
                st.markdown(f"**Email:** {candidate.email}")
                st.markdown(f"**Phone:** {candidate.phone}")

            with col3:
                # Certification match indicator
                has_must_have = candidate.certification_match.get('has_must_have', False)
                cert_icon = "Yes" if has_must_have else "No"
                st.markdown(f"**Must-Have Certs:** {cert_icon}")

                # Location match indicator
                loc_icon = "Yes" if candidate.location_match else "No"
                st.markdown(f"**Location Match:** {loc_icon}")

            # Certifications
            if candidate.certifications:
                st.markdown(f"**Certifications:** {', '.join(candidate.certifications)}")
            else:
                st.markdown("**Certifications:** None listed")

            # Rationale with better formatting
            st.markdown("---")
            st.markdown("**AI Assessment:**")
            st.markdown(f"<div style='background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; font-size: 0.9rem;'>{candidate.rationale}</div>", unsafe_allow_html=True)

    # Download section
    st.markdown('<div class="section-header">Download Reports</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label="Download PDF Report",
            data=pdf_data,
            file_name=os.path.basename(pdf_path),
            mime="application/pdf",
            use_container_width=True
        )

    with col2:
        # CSV Export
        csv_data = generate_csv_export(
            candidate_scores,
            job_details['title'],
            job_details['location']
        )
        st.download_button(
            label="Download CSV Data",
            data=csv_data,
            file_name=f"candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.info(f"PDF report saved locally at: {pdf_path}")


def main():
    # Initialize session state
    init_session_state()

    # Check for OpenAI API key at startup
    if not OpenAIConfig.is_configured():
        st.error("""
        **OpenAI API Key Not Configured**

        Please set the OPENAI_API_KEY environment variable to use this application.

        You can set it by:
        1. Adding it to your .env file: `OPENAI_API_KEY=your-key-here`
        2. Or exporting it: `export OPENAI_API_KEY=your-key-here`

        See OPENAI_API_SETUP.md for detailed instructions.
        """)
        st.stop()

    st.set_page_config(
        page_title="Recruitment Candidate Ranker",
        page_icon=None,
        layout="wide"
    )

    # Custom CSS with logo branding colors and enhanced styling
    st.markdown("""
        <style>
        /* Logo branding colors */
        :root {
            --brand-blue: #0066CC;
            --brand-green: #00A651;
            --brand-dark-gray: #4A4A4A;
            --score-excellent: #27ae60;
            --score-good: #f39c12;
            --score-poor: #e74c3c;
        }

        .header-container {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--brand-blue);
        }

        .logo-container {
            flex-shrink: 0;
        }

        .header-text {
            flex-grow: 1;
        }

        .main-header {
            font-size: 2.5rem;
            color: var(--brand-blue);
            font-weight: bold;
            margin-bottom: 0.3rem;
        }

        .main-header .green-text {
            color: var(--brand-green);
        }

        .sub-header {
            font-size: 1.2rem;
            color: var(--brand-dark-gray);
            margin-bottom: 0;
        }

        .section-header {
            font-size: 1.5rem;
            color: var(--brand-blue);
            font-weight: bold;
            margin-top: 2rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid var(--brand-green);
            padding-bottom: 0.5rem;
        }

        /* Style the Process Candidates button with brand green */
        div[data-testid="stButton"] > button[kind="primary"],
        button[kind="primary"] {
            background-color: var(--brand-green) !important;
            background: var(--brand-green) !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            font-size: 1.1rem !important;
            padding: 0.75rem 2rem !important;
            border-radius: 0.5rem !important;
            transition: all 0.3s ease !important;
        }

        div[data-testid="stButton"] > button[kind="primary"]:hover,
        button[kind="primary"]:hover {
            background-color: #008A42 !important;
            background: #008A42 !important;
            box-shadow: 0 4px 8px rgba(0, 166, 81, 0.4) !important;
            transform: translateY(-1px) !important;
        }

        /* Style download button with brand blue */
        div[data-testid="stDownloadButton"] > button,
        .stDownloadButton > button {
            background-color: var(--brand-blue) !important;
            background: var(--brand-blue) !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
        }

        div[data-testid="stDownloadButton"] > button:hover,
        .stDownloadButton > button:hover {
            background-color: #0052A3 !important;
            background: #0052A3 !important;
        }

        /* Additional Streamlit button styling */
        button[data-baseweb="button"][kind="primary"] {
            background-color: var(--brand-green) !important;
            background: var(--brand-green) !important;
        }

        /* Update success messages to use brand green */
        .stSuccess {
            background-color: #E8F5E9 !important;
            border-left: 4px solid var(--brand-green) !important;
        }

        /* Update info boxes to use brand blue */
        .stInfo {
            border-left: 4px solid var(--brand-blue) !important;
        }

        /* Update error boxes */
        .stError {
            border-left: 4px solid #DC3545 !important;
        }

        /* Style file uploaders with brand colors */
        .stFileUploader > div > div {
            border: 2px dashed var(--brand-blue) !important;
        }

        .stFileUploader > div > div:hover {
            border-color: var(--brand-green) !important;
        }

        /* Style text inputs with subtle brand colors */
        .stTextInput > div > div > input:focus {
            border-color: var(--brand-green) !important;
            box-shadow: 0 0 0 2px rgba(0, 166, 81, 0.2) !important;
        }

        /* Style selectboxes */
        .stSelectbox > div > div > select:focus {
            border-color: var(--brand-green) !important;
        }

        /* Style radio buttons */
        .stRadio > div > label {
            color: var(--brand-dark-gray) !important;
        }

        /* Style expanders */
        .streamlit-expanderHeader {
            color: var(--brand-blue) !important;
            font-weight: 600 !important;
        }

        /* Style metrics */
        [data-testid="stMetricValue"] {
            color: var(--brand-blue) !important;
        }

        /* Progress bar styling */
        .stProgress > div > div > div {
            background-color: var(--brand-green) !important;
        }

        /* Overall page styling */
        .main .block-container {
            padding-top: 2rem;
        }

        /* Score badge styling */
        .score-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-weight: bold;
            color: white;
        }

        .score-excellent { background-color: var(--score-excellent); }
        .score-good { background-color: var(--score-good); }
        .score-poor { background-color: var(--score-poor); }

        /* Processing status styling */
        .processing-status {
            background-color: #f0f7ff;
            border: 1px solid var(--brand-blue);
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
        }

        .processing-step {
            font-weight: bold;
            color: var(--brand-blue);
            margin-bottom: 0.5rem;
        }

        .processing-message {
            color: var(--brand-dark-gray);
            font-style: italic;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header with logo
    logo_path = Path(__file__).parent / "responsableLOGO-color-2048px.jpg"

    # Display full-width logo if it exists, otherwise show text header
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)
        st.markdown("""
            <div style="text-align: center; margin-top: -1rem; margin-bottom: 1rem;">
                <div style="font-size: 1.2rem; color: #4A4A4A; font-weight: 500;">
                    AI-Powered Candidate Screening and Ranking System
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        # Fallback text logo
        col1, col2 = st.columns([1, 4])

        with col1:
            st.markdown("""
                <div style="font-size: 1.5rem; font-weight: bold; color: #0066CC;">
                    RA
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
                <div class="header-text">
                    <div class="main-header">
                        <span style="color: #0066CC;">RESPONS</span><span class="green-text">ABLE</span>
                        <span style="color: #4A4A4A; font-size: 1.8rem;">Safety Staffing</span>
                    </div>
                    <div class="sub-header">AI-Powered Candidate Screening and Ranking System</div>
                </div>
            """, unsafe_allow_html=True)

    # If we have stored results, show them instead of the input form
    if st.session_state.results is not None:
        display_results(st.session_state.results)

        # Footer
        st.markdown("---")
        st.markdown(
            '<div style="text-align: center; color: #7f8c8d; padding: 1rem;">ResponsAble Safety Staffing | Recruitment Candidate Ranker</div>',
            unsafe_allow_html=True
        )
        return

    # Introduction
    with st.expander("How It Works", expanded=False):
        st.markdown("""
        This application analyzes job requirements and candidate resumes to provide intelligent rankings:

        1. **Job Analysis**: Extracts requirements from job description
        2. **Research**: Identifies equivalent skills and job titles
        3. **Resume Parsing**: Extracts structured data from resumes
        4. **Scoring**: Evaluates candidates with chain-of-thought reasoning
        5. **Ranking**: Selects top 4-10 candidates
        6. **Report**: Generates professional PDF with visualizations

        **Scoring Criteria**:
        - Must-have certifications: 30%
        - Bonus certifications: 10%
        - Required skills: 25%
        - Preferred skills: 10%
        - Experience level: 10%
        - Job title match: 10%
        - Location: 5%
        """)

    # Main input toggle
    st.markdown('<div class="section-header">Input Method</div>', unsafe_allow_html=True)

    input_mode = st.radio(
        "Choose how to provide job details:",
        ["Upload Job Description File (AI Extracts Everything)", "Manual Entry"],
        horizontal=True,
        help="File upload uses AI to automatically extract all job details"
    )

    job_title = ""
    location = ""
    certifications = []
    job_description = ""

    # MODE 1: File Upload (AI Auto-Extraction)
    if input_mode == "Upload Job Description File (AI Extracts Everything)":
        st.markdown('<div class="section-header">Upload Job Description</div>', unsafe_allow_html=True)

        job_desc_file = st.file_uploader(
            "Upload Job Description File",
            type=["txt", "pdf", "docx"],
            help="Upload job description - AI will automatically extract job title, location, certifications, and all requirements"
        )

        if job_desc_file:
            with st.spinner("AI is analyzing job description..."):
                try:
                    # Save to temp file for parser
                    temp_dir = tempfile.mkdtemp()
                    temp_path = os.path.join(temp_dir, job_desc_file.name)

                    try:
                        with open(temp_path, 'wb') as f:
                            f.write(job_desc_file.getbuffer())

                        # Parse the job description file using AI parser
                        parser = AIJobParser()  # Uses AI if API key available
                        job_data = parser.parse(temp_path)
                    finally:
                        # Cleanup temporary files
                        import shutil
                        try:
                            shutil.rmtree(temp_dir)
                        except Exception:
                            pass  # Ignore cleanup errors

                    job_description = job_data['full_description']
                    job_title = job_data.get('job_title', '')
                    location = job_data.get('location', '')
                    certifications = job_data.get('certifications', [])

                    # Show success with extracted info
                    st.success(f"Successfully processed: {job_desc_file.name}")

                    # Show extracted information in a nice format
                    st.markdown("### AI-Extracted Information")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Job Title", job_title if job_title else "Not found")
                        st.metric("Location", location if location else "Not found")
                    with col2:
                        st.metric("Certifications Found", len(certifications))
                        st.metric("Document Length", f"{len(job_description)} chars")

                    # Show certifications if found
                    if certifications:
                        with st.expander("View Extracted Certifications"):
                            for i, cert in enumerate(certifications, 1):
                                category_label = "[Required]" if cert.get('category') == 'must-have' else "[Preferred]"
                                st.write(f"{i}. {category_label} - **{cert.get('name')}**")

                    # Show preview
                    with st.expander("View Full Job Description"):
                        st.text_area("Content", job_description, height=300, disabled=True, key="jd_preview")

                except Exception as e:
                    st.error(f"Error processing file: {e}")
                    job_description = ""

    # MODE 2: Manual Entry
    else:
        st.markdown('<div class="section-header">Job Details</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            job_title = st.text_input(
                "Job Title",
                placeholder="e.g., Safety Specialist",
                help="Enter the exact job title"
            )

        with col2:
            location = st.text_input(
                "Location",
                placeholder="e.g., Houston, TX or Remote",
                help="Enter the job location"
            )

        # Simplified Certifications Entry
        st.markdown("**Certifications** (one per line, prefix with `*` for required)")
        st.caption("Example: `*OSHA 30` (required) or `First Aid` (preferred)")

        cert_text = st.text_area(
            "Certifications",
            height=100,
            placeholder="*OSHA 30\n*BCSP Certification\nFirst Aid\nCPR",
            help="Enter one certification per line. Prefix with * for must-have/required certifications.",
            label_visibility="collapsed"
        )

        # Parse certifications from text
        certifications = []
        if cert_text:
            for line in cert_text.strip().split('\n'):
                line = line.strip()
                if line:
                    if line.startswith('*'):
                        certifications.append({
                            "name": line[1:].strip(),
                            "category": "must-have"
                        })
                    else:
                        certifications.append({
                            "name": line,
                            "category": "bonus"
                        })

        if certifications:
            st.caption(f"Parsed: {len([c for c in certifications if c['category'] == 'must-have'])} required, {len([c for c in certifications if c['category'] == 'bonus'])} preferred")

        # Job Description
        st.markdown('<div class="section-header">Job Description</div>', unsafe_allow_html=True)

        job_description = st.text_area(
            "Full Job Description",
            height=300,
            placeholder="""Paste the complete job description including:
- Required skills and experience
- Preferred qualifications
- Responsibilities
- Technical requirements
- Any other relevant details

The AI will analyze this to extract skills and requirements.""",
            help="Provide as much detail as possible for accurate matching"
        )

    # Resume Upload
    st.markdown('<div class="section-header">Candidate Resumes</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload Resume Files",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="Upload candidate resumes in PDF, DOCX, or TXT format"
    )

    if uploaded_files:
        st.success(f"Uploaded {len(uploaded_files)} resume(s)")
        with st.expander("View uploaded files"):
            for file in uploaded_files:
                size_kb = file.size / 1024
                st.write(f"- {file.name} ({size_kb:.1f} KB)")

    # Process Button
    st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        # Use a custom styled button with brand green
        process_button = st.button(
            "Process Candidates",
            use_container_width=True,
            type="primary",
            key="process_btn"
        )

    # Process
    if process_button:
        # Validation
        errors = []

        if not job_title:
            errors.append("Job title is required")
        if not location:
            errors.append("Location is required")
        if not job_description:
            errors.append("Job description is required")
        if not uploaded_files:
            errors.append("At least one resume file is required")

        if errors:
            for error in errors:
                st.error(error)
        else:
            # Process the candidates with progress tracking
            start_time = datetime.now()

            # Create progress UI elements
            progress_container = st.container()

            with progress_container:
                st.markdown("### Processing Candidates")
                progress_bar = st.progress(0)
                status_text = st.empty()
                step_info = st.empty()

            # Progress callback function
            def update_progress(step, progress, current, total):
                progress_bar.progress(min(progress, 1.0))
                message = get_cycling_message(step, progress, current, total)

                step_titles = {
                    "analyzing": "Step 1/6: Analyzing Job Requirements",
                    "researching": "Step 2/6: Researching Equivalents",
                    "parsing": f"Step 3/6: Parsing Resumes ({current}/{total})",
                    "scoring": f"Step 4/6: Scoring Candidates ({current}/{total})",
                    "ranking": "Step 5/6: Ranking Candidates",
                    "generating": "Step 6/6: Generating PDF Report"
                }

                step_info.markdown(f"**{step_titles.get(step, 'Processing...')}**")
                status_text.markdown(f"*{message}*")

            try:
                # Save uploaded files temporarily
                temp_dir = tempfile.mkdtemp()
                resume_paths = []

                try:
                    for uploaded_file in uploaded_files:
                        file_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        resume_paths.append(file_path)

                    # Initialize app (logo is now fixed, no need to pass it)
                    app = CandidateRankerApp()

                    # Run processing with progress callback
                    pdf_path = app.run(
                        job_title=job_title,
                        certifications=certifications,
                        location=location,
                        job_description=job_description,
                        resume_files=resume_paths,
                        progress_callback=update_progress
                    )

                    # Read PDF data before cleanup
                    with open(pdf_path, "rb") as f:
                        pdf_data = f.read()

                finally:
                    # Cleanup temporary files
                    import shutil
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception:
                        pass  # Ignore cleanup errors

                # Calculate processing time
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()

                # Store results in session state
                st.session_state.results = {
                    'candidate_scores': app.candidate_scores,
                    'pdf_path': pdf_path,
                    'pdf_data': pdf_data,
                    'job_details': {
                        'title': job_title,
                        'location': location,
                        'certifications': certifications
                    },
                    'processing_time': processing_time,
                    'timestamp': datetime.now()
                }

                # Update progress to complete
                progress_bar.progress(1.0)
                status_text.markdown("*Processing complete!*")

                # Rerun to show results
                st.rerun()

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.exception(e)

    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #7f8c8d; padding: 1rem;">ResponsAble Safety Staffing | Recruitment Candidate Ranker</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
