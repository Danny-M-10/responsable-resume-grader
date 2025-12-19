"""
Enhanced Streamlit Web Interface for Candidate Ranker Application
Now supports job description file upload for automatic extraction

Run with: streamlit run app_enhanced.py
"""

import streamlit as st
import os
import tempfile
from datetime import datetime
from pathlib import Path
from config import OpenAIConfig

# Import AIJobParser - handle import errors gracefully
try:
    from ai_job_parser import AIJobParser
except ImportError as e:
    st.error(f"Failed to import AIJobParser: {e}")
    st.stop()

from candidate_ranker import CandidateRankerApp
from loading_components import (
    show_job_analysis_loading,
    show_full_workflow_loading,
    show_resume_parsing_loading,
    show_scoring_loading,
    show_report_generation_loading
)


def main():
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

    # Custom CSS with logo branding colors
    st.markdown("""
        <style>
        /* Logo branding colors */
        :root {
            --brand-blue: #0066CC;
            --brand-green: #00A651;
            --brand-dark-gray: #4A4A4A;
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
        
        .success-box {
            padding: 1rem;
            background-color: #E8F5E9;
            border-left: 4px solid var(--brand-green);
            border-radius: 0.25rem;
            color: #155724;
            margin-bottom: 1rem;
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
        
        /* Overall page styling */
        .main .block-container {
            padding-top: 2rem;
        }
        
        /* Custom Loading Animation */
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .loading-container {
            background: linear-gradient(135deg, #f5f7fa 0%, #e8f5e9 100%);
            border: 2px solid var(--brand-green);
            border-radius: 1rem;
            padding: 2rem;
            margin: 2rem 0;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 166, 81, 0.1);
        }
        
        .loading-spinner {
            width: 60px;
            height: 60px;
            border: 6px solid #e0e0e0;
            border-top: 6px solid var(--brand-green);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1.5rem;
        }
        
        .loading-title {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--brand-blue);
            margin-bottom: 0.5rem;
            animation: slideIn 0.5s ease-out;
        }
        
        .loading-message {
            font-size: 1.1rem;
            color: var(--brand-dark-gray);
            margin-bottom: 1rem;
            animation: slideIn 0.7s ease-out;
        }
        
        .loading-progress-bar {
            width: 100%;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 1rem;
        }
        
        .loading-progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--brand-green), var(--brand-blue));
            border-radius: 4px;
            animation: pulse 2s ease-in-out infinite;
            transition: width 0.3s ease;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header with logo
    logo_path = Path(__file__).parent / "responsableLOGO-color-2048px.jpg"
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if logo_path.exists():
            st.image(str(logo_path), width=200)
        else:
            # Fallback text logo
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

    # Introduction
    with st.expander("How It Works", expanded=False):
        st.markdown("""
        This application analyzes job requirements and candidate resumes to provide intelligent rankings:

        1. **Job Analysis**: Extracts requirements from job description (automatically from uploaded file!)
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

    # Input Method Selection
    st.markdown('<div class="section-header">Job Information</div>', unsafe_allow_html=True)

    input_method = st.radio(
        "Choose how to provide job details:",
        ["Upload Job Description File (Recommended)", "Enter Details Manually"],
        help="Upload a job description file for automatic extraction, or enter details manually"
    )

    job_title = None
    location = None
    certifications = []
    job_description = None
    job_data_extracted = {}

    if input_method == "Upload Job Description File (Recommended)":
        st.info("Upload a job description file (PDF, DOCX, or TXT) and we'll automatically extract all the requirements.")

        job_file = st.file_uploader(
            "Upload Job Description",
            type=["pdf", "docx", "txt"],
            help="The system will automatically extract job title, location, certifications, and requirements"
        )

        if job_file:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(job_file.name).suffix) as tmp_file:
                tmp_file.write(job_file.getvalue())
                temp_job_path = tmp_file.name

            try:
                # Show custom loading screen
                loading_placeholder = st.empty()
                with loading_placeholder.container():
                    show_job_analysis_loading(progress=0.3)
                
                # Parse job description using AI
                parser = AIJobParser()
                job_data_extracted = parser.parse(temp_job_path)
                
                # Store in session state for later use
                st.session_state.job_data_extracted = job_data_extracted
                
                # Clear loading screen
                loading_placeholder.empty()

                # Extract job details
                job_title = job_data_extracted.get('job_title', '')
                location = job_data_extracted.get('location', '')
                certifications = job_data_extracted.get('certifications', [])
                job_description = job_data_extracted.get('full_description', '')

                # Display extracted information
                st.success("Job description analyzed successfully.")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Extracted Information:**")
                    st.write(f"**Job Title:** {job_title}")
                    st.write(f"**Location:** {location}")
                    st.write(f"**Experience:** {job_data_extracted.get('experience_requirements', 'Not specified')}")

                with col2:
                    st.markdown("**Certifications Found:**")
                    if certifications:
                        for cert in certifications:
                            badge = "[Required] Must-Have" if cert['category'] == 'must-have' else "[Preferred] Bonus"
                            st.write(f"{badge} {cert['name']}")
                    else:
                        st.write("No certifications found")

                # Allow editing
                with st.expander("Edit Extracted Information (Optional)", expanded=False):
                    col1, col2 = st.columns(2)

                    with col1:
                        job_title = st.text_input("Job Title", value=job_title, key="edit_title")
                        location = st.text_input("Location", value=location, key="edit_location")

                    with col2:
                        st.markdown("**Modify Certifications:**")
                        # Allow users to modify certifications
                        num_certs = st.number_input("Number of certifications",
                                                   min_value=0,
                                                   max_value=15,
                                                   value=len(certifications))

                        if num_certs != len(certifications):
                            # User wants to modify
                            certifications = []
                            for i in range(num_certs):
                                cert_name = st.text_input(f"Certification {i+1} Name", key=f"cert_edit_{i}")
                                cert_cat = st.selectbox(f"Certification {i+1} Category",
                                                       ["must-have", "bonus"],
                                                       key=f"cat_edit_{i}")
                                if cert_name:
                                    certifications.append({"name": cert_name, "category": cert_cat})

                # Cleanup temp file
                os.unlink(temp_job_path)

            except Exception as e:
                st.error(f"Error parsing job description: {e}")
                st.info("Please try manual entry or check your file format.")

    else:  # Manual entry
        col1, col2 = st.columns(2)

        with col1:
            job_title = st.text_input(
                "Job Title",
                placeholder="e.g., Data Scientist",
                help="Enter the exact job title"
            )

            location = st.text_input(
                "Location",
                placeholder="e.g., New York, NY",
                help="Enter the job location"
            )

        with col2:
            st.markdown("**Certifications**")
            num_certs = st.number_input("Number of certifications", min_value=0, max_value=10, value=2)

        # Certifications
        certifications = []
        if num_certs > 0:
            st.markdown("Enter certification details:")
            cert_cols = st.columns(2)

            for i in range(num_certs):
                with cert_cols[i % 2]:
                    with st.container():
                        cert_name = st.text_input(
                            f"Certification {i+1} Name",
                            key=f"cert_name_{i}",
                            placeholder="e.g., AWS Certified Machine Learning"
                        )
                        cert_category = st.selectbox(
                            f"Certification {i+1} Category",
                            key=f"cert_cat_{i}",
                            options=["must-have", "bonus"],
                            help="Must-have: Required (heavily weighted)\nBonus: Preferred (additional points)"
                        )

                        if cert_name:
                            certifications.append({
                                "name": cert_name,
                                "category": cert_category
                            })

        # Job Description
        st.markdown('<div class="section-header">Job Description</div>', unsafe_allow_html=True)

        job_description = st.text_area(
            "Full Job Description",
            height=300,
            placeholder="""Enter the complete job description including:
- Required skills
- Preferred skills
- Experience requirements
- Technical stack
- Responsibilities
- Industry context
- Any other relevant details

The system will automatically extract requirements from this description.""",
            help="Provide as much detail as possible for accurate matching"
        )

    # Resume Upload (common for both methods)
    st.markdown('<div class="section-header">Candidate Resumes</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload Resume Files",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="Upload candidate resumes in PDF, DOCX, or TXT format"
    )

    if uploaded_files:
        st.success(f"Uploaded {len(uploaded_files)} resume(s)")
        for file in uploaded_files:
            st.write(f"  {file.name} ({file.size:,} bytes)")

    # Process Button
    st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        process_button = st.button(
            "Process Candidates",
            use_container_width=True,
            type="primary"
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
            # Process the candidates
            loading_placeholder = st.empty()
            
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

                    # Initialize app
                    app = CandidateRankerApp()

                    # Extract AI-provided skills if available from session state
                    job_data_extracted = st.session_state.get('job_data_extracted', {})
                    required_skills = job_data_extracted.get('required_skills', []) if job_data_extracted else None
                    preferred_skills = job_data_extracted.get('preferred_skills', []) if job_data_extracted else None
                    
                    # Define progress callback to update loading screen
                    def update_progress(step: str, progress: float, current: int, total: int):
                        with loading_placeholder.container():
                            show_full_workflow_loading(step, progress, current, total)
                    
                    # Run processing with progress callback
                    pdf_path = app.run(
                        job_title=job_title,
                        certifications=certifications,
                        location=location,
                        job_description=job_description,
                        resume_files=resume_paths,
                        required_skills=required_skills,
                        preferred_skills=preferred_skills,
                        progress_callback=update_progress
                    )
                    
                    # Clear loading screen
                    loading_placeholder.empty()

                finally:
                    # Cleanup temporary files
                    import shutil
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception:
                        pass  # Ignore cleanup errors

                # Success
                st.success("Processing complete.")

                # Display results
                st.markdown('<div class="section-header">Results</div>', unsafe_allow_html=True)

                # Summary metrics
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Candidates", len(uploaded_files))

                with col2:
                    st.metric("Top Candidates", min(len(app.candidate_scores), 10))

                with col3:
                    if app.candidate_scores:
                        avg_score = sum(c.fit_score for c in app.candidate_scores) / len(app.candidate_scores)
                        st.metric("Average Score", f"{avg_score:.2f}")

                # Top candidates preview - use sorted top candidates
                st.markdown("**Top Candidates:**")
                
                # Get sorted top candidates (already sorted in _rank_candidates)
                top_candidates_sorted = sorted(
                    app.candidate_scores,
                    key=lambda x: x.fit_score,
                    reverse=True
                )[:10]

                for i, candidate in enumerate(top_candidates_sorted, 1):
                    # Status indicator based on score
                    if candidate.fit_score >= 8.0:
                        score_status = "[Excellent]"
                    elif candidate.fit_score >= 6.5:
                        score_status = "[Good]"
                    elif candidate.fit_score >= 5.0:
                        score_status = "[Fair]"
                    else:
                        score_status = "[Needs Review]"

                    with st.expander(f"{i}. {score_status} {candidate.name} - Score: {candidate.fit_score}/10"):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write(f"**Email:** {candidate.email}")
                            st.write(f"**Phone:** {candidate.phone}")

                        with col2:
                            st.write(f"**Fit Score:** {candidate.fit_score}/10")
                            cert_display = ', '.join(candidate.certifications) if candidate.certifications else 'None'
                            st.write(f"**Certifications:** {cert_display}")

                        st.write(f"**Rationale:** {candidate.rationale}")

                # Download button
                st.markdown('<div class="section-header">Download Report</div>', unsafe_allow_html=True)

                with open(pdf_path, "rb") as f:
                    pdf_data = f.read()

                st.download_button(
                    label="Download PDF Report",
                    data=pdf_data,
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf",
                    use_container_width=True
                )

                st.info(f"Report saved locally at: {pdf_path}")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                with st.expander("View Error Details"):
                    st.exception(e)

    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #7f8c8d; padding: 1rem;">ResponsAble Safety Staffing | Recruitment Candidate Ranker</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
