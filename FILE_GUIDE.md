# File Guide - Recruitment Candidate Ranker

## Complete File Listing

This document describes every file in the project.

---

## Documentation Files (Start Here)

### START_HERE.md (4.8 KB)
**Purpose**: First file to read when starting
**Contains**:
- Quick overview of the application
- 3-step quick start guide
- Key features summary
- File overview
- Troubleshooting basics

**Read this if**: You're new to the project

---

### QUICK_START.md (2.9 KB)
**Purpose**: Fast setup and running guide
**Contains**:
- Installation instructions
- Two usage options (Web vs Python)
- Output interpretation
- Tips for best results

**Read this if**: You want to start using the app immediately

---

### USER_MANUAL.md (13 KB)
**Purpose**: Comprehensive user guide
**Contains**:
- Detailed installation steps
- Complete usage instructions
- Input requirements
- Output format explanation
- Scoring methodology
- Best practices
- Troubleshooting section

**Read this if**: You want to understand everything in detail

---

### README.md (5.6 KB)
**Purpose**: Technical documentation
**Contains**:
- Feature list
- Installation guide
- Usage examples
- Architecture overview
- API documentation
- File format support

**Read this if**: You're a developer or need technical details

---

### PROJECT_SUMMARY.md (9.4 KB)
**Purpose**: Project overview and statistics
**Contains**:
- Complete feature list
- Technical implementation details
- Project structure
- Workflow process
- Best practices
- Extension possibilities

**Read this if**: You want a comprehensive project overview

---

### FILE_GUIDE.md (This File)
**Purpose**: Describes all files in the project
**Contains**:
- File-by-file description
- Purpose and contents of each file
- File categories and organization

**Read this if**: You want to understand the project structure

---

## Core Application Files

### candidate_ranker.py (11 KB)
**Purpose**: Main application orchestration
**Contains**:
- CandidateRankerApp class
- Workflow coordination
- Job detail parsing
- Resume processing pipeline
- Scoring coordination
- Report generation trigger

**Type**: Core Python module
**Used by**: app.py, example_usage.py

---

### resume_parser.py (11 KB)
**Purpose**: Extract structured data from resumes
**Contains**:
- ResumeParser class
- PDF/DOCX/TXT file reading
- Contact information extraction
- Skills extraction
- Certification detection
- Experience analysis
- Education extraction

**Type**: Core Python module
**Used by**: candidate_ranker.py

---

### scoring_engine.py (14 KB)
**Purpose**: Score candidates with chain-of-thought reasoning
**Contains**:
- ScoringEngine class
- Weighted scoring algorithm
- Chain-of-thought logic
- Certification evaluation
- Skills matching
- Experience evaluation
- Rationale generation

**Type**: Core Python module
**Used by**: candidate_ranker.py

---

### pdf_generator.py (18 KB)
**Purpose**: Create professional PDF reports
**Contains**:
- PDFGenerator class
- Report structure creation
- Job summary formatting
- Candidate detail formatting
- Ranking chart generation
- Visual matrix creation
- Overall notes section

**Type**: Core Python module
**Used by**: candidate_ranker.py

---

### skills_researcher.py (8.1 KB)
**Purpose**: Find equivalent terms and synonyms
**Contains**:
- SkillsResearcher class
- Job title equivalents database
- Skill synonyms mapping
- Certification equivalents
- Seniority variation generation

**Type**: Core Python module
**Used by**: candidate_ranker.py

---

### models.py (1.3 KB)
**Purpose**: Shared data structures
**Contains**:
- Certification dataclass
- JobDetails dataclass
- CandidateScore dataclass

**Type**: Data models module
**Used by**: All core modules

---

## User Interface Files

### app.py (9.3 KB)
**Purpose**: Web-based user interface
**Contains**:
- Streamlit web application
- Input forms (job details, certifications)
- File upload handling
- Results display
- PDF download functionality

**Type**: Streamlit web app
**Usage**: Run with `streamlit run app.py`

---

### example_usage.py (8.3 KB)
**Purpose**: Python API usage examples
**Contains**:
- Example workflow code
- Sample job configuration
- Resume file handling
- Error handling examples
- Sample resume generator

**Type**: Example script
**Usage**: Edit and run with `python example_usage.py`

---

## Configuration Files

### requirements.txt (87 Bytes)
**Purpose**: Python package dependencies
**Contains**:
- PyPDF2 (PDF parsing)
- python-docx (Word document parsing)
- reportlab (PDF generation)
- matplotlib (Charts)
- streamlit (Web interface)

**Type**: pip requirements file
**Usage**: `pip install -r requirements.txt`

---

## Setup Scripts

### setup.sh (1.9 KB)
**Purpose**: Automated setup for macOS/Linux
**Contains**:
- Python version check
- Dependency installation
- Verification steps
- Usage instructions

**Type**: Bash script
**Usage**: `./setup.sh`
**Platform**: macOS, Linux, Unix

---

### setup.bat (1.5 KB)
**Purpose**: Automated setup for Windows
**Contains**:
- Python version check
- Dependency installation
- Verification steps
- Usage instructions

**Type**: Windows batch script
**Usage**: `setup.bat`
**Platform**: Windows

---

## File Organization

### By Purpose

**Getting Started**
- START_HERE.md - First file to read
- QUICK_START.md - Fast setup
- setup.sh / setup.bat - Installation

**Documentation**
- USER_MANUAL.md - Complete guide
- README.md - Technical docs
- PROJECT_SUMMARY.md - Overview
- FILE_GUIDE.md - This file

**Core Application**
- candidate_ranker.py - Main app
- resume_parser.py - Resume parsing
- scoring_engine.py - Scoring
- pdf_generator.py - PDF reports
- skills_researcher.py - Synonyms
- models.py - Data structures

**User Interfaces**
- app.py - Web interface
- example_usage.py - Python examples

**Configuration**
- requirements.txt - Dependencies

### By Type

**Documentation** (6 files)
- START_HERE.md
- QUICK_START.md
- USER_MANUAL.md
- README.md
- PROJECT_SUMMARY.md
- FILE_GUIDE.md

**Python Code** (8 files)
- candidate_ranker.py
- resume_parser.py
- scoring_engine.py
- pdf_generator.py
- skills_researcher.py
- models.py
- app.py
- example_usage.py

**Configuration** (3 files)
- requirements.txt
- setup.sh
- setup.bat

### By Size

**Large** (10+ KB)
- pdf_generator.py (18 KB)
- scoring_engine.py (14 KB)
- USER_MANUAL.md (13 KB)
- candidate_ranker.py (11 KB)
- resume_parser.py (11 KB)

**Medium** (5-10 KB)
- PROJECT_SUMMARY.md (9.4 KB)
- app.py (9.3 KB)
- example_usage.py (8.3 KB)
- skills_researcher.py (8.1 KB)
- README.md (5.6 KB)

**Small** (< 5 KB)
- START_HERE.md (4.8 KB)
- QUICK_START.md (2.9 KB)
- setup.sh (1.9 KB)
- setup.bat (1.5 KB)
- models.py (1.3 KB)
- requirements.txt (87 bytes)

---

## File Dependencies

### Import Hierarchy

```
app.py
  └── candidate_ranker.py
       ├── models.py
       ├── resume_parser.py
       │    └── (PyPDF2, docx)
       ├── scoring_engine.py
       │    └── models.py
       ├── pdf_generator.py
       │    └── models.py
       │    └── (reportlab, matplotlib)
       └── skills_researcher.py
```

### Usage Flow

```
User Input
  ↓
app.py (Web) OR example_usage.py (Python)
  ↓
candidate_ranker.py
  ↓
[resume_parser.py] → [scoring_engine.py] → [pdf_generator.py]
  ↓
PDF Report Output
```

---

## Recommended Reading Order

### For End Users (Non-Programmers)

1. START_HERE.md (5 min)
2. QUICK_START.md (5 min)
3. Run: `./setup.sh` or `setup.bat`
4. Run: `streamlit run app.py`
5. USER_MANUAL.md (as needed for reference)

### For Developers

1. START_HERE.md (5 min)
2. README.md (10 min)
3. PROJECT_SUMMARY.md (10 min)
4. Review: candidate_ranker.py
5. Review: scoring_engine.py
6. Modify: example_usage.py

### For System Administrators

1. QUICK_START.md (5 min)
2. requirements.txt (verify dependencies)
3. setup.sh or setup.bat (review installation)
4. USER_MANUAL.md (troubleshooting section)

---

## Summary

**Total Files**: 17
**Total Size**: ~110 KB
**Documentation**: 6 files (35 KB)
**Code**: 8 files (71 KB)
**Config**: 3 files (4 KB)

**All files are included** - no external downloads needed except Python packages (via requirements.txt).

---

**Project Status**: Production Ready
**Version**: 1.0
**Last Updated**: December 2024
