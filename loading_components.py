"""
Custom loading components for Streamlit app
Provides enhanced loading animations and progress indicators
"""

import streamlit as st
import time
import random
from typing import List, Optional


def show_loading_screen(title: str, message: str, progress: float = 0.0):
    """
    Display a custom loading screen with animation and progress
    
    Args:
        title: Main title for the loading screen
        message: Current status message (with cycling text and jokes)
        progress: Progress percentage (0.0 to 1.0)
    """
    st.markdown(f"""
    <div class="loading-container">
        <div class="loading-spinner"></div>
        <div class="loading-title">{title}</div>
        <div class="loading-message">{message}</div>
        <div class="loading-progress-bar">
            <div class="loading-progress-fill" style="width: {progress * 100}%"></div>
        </div>
    </div>
    <style>
    .loading-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: var(--spacing-lg);
        padding: var(--spacing-2xl);
        text-align: center;
        background: var(--color-surface);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-lg);
    }}
    .loading-spinner {{
        width: 60px;
        height: 60px;
        border: 4px solid var(--color-border);
        border-top-color: var(--color-primary);
        border-radius: var(--radius-full);
        animation: spin 1s linear infinite;
    }}
    @keyframes spin {{
        to {{ transform: rotate(360deg); }}
    }}
    .loading-title {{
        font-size: var(--font-size-2xl);
        font-weight: var(--font-weight-semibold);
        color: var(--color-text-primary);
        margin: 0;
    }}
    .loading-message {{
        font-size: var(--font-size-base);
        color: var(--color-text-secondary);
        margin: 0;
        max-width: 600px;
    }}
    .loading-progress-bar {{
        width: 100%;
        max-width: 400px;
        height: 8px;
        background-color: var(--color-surface-elevated);
        border-radius: var(--radius-full);
        overflow: hidden;
        margin-top: var(--spacing-sm);
    }}
    .loading-progress-fill {{
        height: 100%;
        background-color: var(--color-primary);
        border-radius: var(--radius-full);
        transition: width 0.3s ease;
    }}
    </style>
    """, unsafe_allow_html=True)


def get_cycling_message(step: str, progress: float, current: int = 0, total: int = 0) -> str:
    """
    Get cycling informative message with tech humor based on workflow step and progress
    
    Args:
        step: Current workflow step name
        progress: Progress percentage (0.0 to 1.0)
        current: Current item number (for steps with multiple items)
        total: Total items (for steps with multiple items)
    
    Returns:
        Informative message with optional tech humor
    """
    messages = {
        "analyzing": [
            "Reading job description... Did you know recruiters spend 6 seconds on average? We're taking longer because we actually read them!",
            "Extracting job requirements... Our AI is smarter than your average keyword matcher.",
            "Identifying certifications... Because 'or equivalent' shouldn't be a guessing game.",
            "Analyzing skill requirements... We're finding skills you didn't even know you needed.",
            "Finalizing extraction... Almost there! The AI is double-checking its work."
        ],
        "researching": [
            "Researching equivalent job titles... Because 'Senior Engineer' and 'Lead Developer' are basically the same thing.",
            "Mapping skill synonyms... Python, Python 3, and Python3 are all the same to us.",
            "Finding certification equivalents... CHST, OHST, STSC... alphabet soup, but we've got it sorted.",
            "Building synonym database... Making sure we don't miss candidates because of terminology differences."
        ],
        "parsing": [
            f"Processing resume {current} of {total}... Reading between the lines (literally).",
            f"Parsing resume {current} of {total}... Extracting candidate information with surgical precision.",
            f"Analyzing resume {current} of {total}... Our AI reads faster than you, but we're thorough.",
            f"Processing resume {current} of {total}... No PDF parsing errors here, we're professionals.",
            f"Extracting data from resume {current} of {total}... Because copy-paste is so 2020."
        ],
        "scoring": [
            f"Evaluating candidate {current} of {total}... Comparing apples to job descriptions.",
            f"Scoring candidate {current} of {total}... Our AI doesn't have unconscious bias, just conscious analysis.",
            f"Analyzing candidate {current} of {total}... Calculating fit score with mathematical precision.",
            f"Evaluating candidate {current} of {total}... We're thorough, not judgmental. Mostly.",
            f"Scoring candidate {current} of {total}... Because 'gut feeling' isn't a valid scoring metric."
        ],
        "ranking": [
            "Sorting candidates by fit score... From best to 'needs improvement'.",
            "Selecting top candidates... Separating the wheat from the chaff, algorithmically.",
            "Preparing ranking summary... Making sure the best candidates rise to the top.",
            "Ranking candidates... Because alphabetical order isn't helpful here.",
            "Finalizing rankings... The cream always rises to the top (with our help)."
        ],
        "generating": [
            "Compiling candidate data... Building your perfect report, one byte at a time.",
            "Creating visualizations... Because charts make everything better.",
            "Formatting PDF layout... Making it look professional, not like a ransom note.",
            "Finalizing report... Adding the finishing touches (and removing the typos).",
            "Generating PDF... Almost done! Your report is being crafted with care."
        ]
    }
    
    step_messages = messages.get(step, ["Processing... Please wait."])
    
    # Select message based on progress to create variety
    message_index = min(int(progress * len(step_messages)), len(step_messages) - 1)
    
    return step_messages[message_index]


def show_job_analysis_loading(progress: float = 0.3):
    """Show loading screen for job description analysis"""
    message = get_cycling_message("analyzing", progress)
    show_loading_screen(
        title="Analyzing Job Description",
        message=message,
        progress=progress
    )


def show_resume_parsing_loading(current: int, total: int, overall_progress: float = 0.0):
    """Show loading screen for resume parsing"""
    progress = (current / total) if total > 0 else 0.0
    message = get_cycling_message("parsing", progress, current, total)
    show_loading_screen(
        title="Parsing Resumes",
        message=message,
        progress=overall_progress
    )


def show_scoring_loading(current: int, total: int, overall_progress: float = 0.0):
    """Show loading screen for candidate scoring"""
    progress = (current / total) if total > 0 else 0.0
    message = get_cycling_message("scoring", progress, current, total)
    show_loading_screen(
        title="Evaluating Candidates",
        message=message,
        progress=overall_progress
    )


def show_report_generation_loading(progress: float = 0.9):
    """Show loading screen for PDF report generation"""
    message = get_cycling_message("generating", progress)
    show_loading_screen(
        title="Generating Report",
        message=message,
        progress=progress
    )


def show_full_workflow_loading(step: str, progress: float, current: int = 0, total: int = 0):
    """
    Show loading screen for full workflow processing
    
    Args:
        step: Current workflow step name
        progress: Overall progress percentage (0.0 to 1.0)
        current: Current item number (for steps with multiple items)
        total: Total items (for steps with multiple items)
    """
    workflow_titles = {
        "analyzing": "Analyzing Job Requirements",
        "researching": "Researching Equivalents",
        "parsing": "Parsing Resumes",
        "scoring": "Scoring Candidates",
        "ranking": "Ranking Candidates",
        "generating": "Generating PDF Report"
    }
    
    title = workflow_titles.get(step, "Processing")
    message = get_cycling_message(step, progress, current, total)
    
    show_loading_screen(
        title=title,
        message=message,
        progress=progress
    )

