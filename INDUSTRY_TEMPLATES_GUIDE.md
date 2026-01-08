# Industry Templates Guide

## Overview

The Universal Recruiting Tool includes pre-configured industry templates that optimize candidate scoring for different sectors. Each template adjusts the importance (weights) of various evaluation criteria based on industry best practices.

## Available Templates

### 1. General/Universal Template

**Best For**: Most industries and roles, balanced evaluation

**Scoring Weights**:
- Must-Have Certifications: 30%
- Bonus Certifications: 10%
- Required Skills: 25%
- Preferred Skills: 10%
- Experience Level: 10%
- Job Title Match: 10%
- Location: 5%

**Description**: A balanced scoring profile suitable for most industries. This is the default template and works well when industry-specific requirements aren't critical.

**Example Use Cases**:
- General office positions
- Administrative roles
- Mixed-industry recruiting
- When unsure which template to use

---

### 2. Healthcare Template

**Best For**: Medical, nursing, and healthcare roles

**Scoring Weights**:
- Must-Have Certifications: 40% (increased)
- Bonus Certifications: 10%
- Required Skills: 20%
- Preferred Skills: 5%
- Experience Level: 15% (increased)
- Job Title Match: 5%
- Location: 5%

**Description**: Emphasizes certifications, licenses, and experience. Ideal for roles where professional credentials are critical for patient safety and regulatory compliance.

**Key Features**:
- Recognizes medical terminology and licenses
- Common certifications: RN, LPN, BLS, ACLS, CPR, HIPAA, Medical License, Nursing License

**Example Use Cases**:
- Registered Nurse positions
- Medical Technicians
- Healthcare Administrators
- Clinical roles requiring licenses

---

### 3. Technology Template

**Best For**: Software engineering, IT, and tech roles

**Scoring Weights**:
- Must-Have Certifications: 15% (reduced)
- Bonus Certifications: 10%
- Required Skills: 35% (increased)
- Preferred Skills: 15% (increased)
- Experience Level: 15% (increased)
- Job Title Match: 5%
- Location: 5%

**Description**: Emphasizes technical skills and experience over certifications. Skills and hands-on experience are more important than credentials in tech roles.

**Key Features**:
- Recognizes programming languages and frameworks
- Common certifications: AWS Certified, Microsoft Certified, Google Cloud Certified, CISSP, PMP, Scrum Master

**Example Use Cases**:
- Software Engineers
- Data Scientists
- DevOps Engineers
- IT Administrators
- Technical roles where skills > certs

---

### 4. Construction Template

**Best For**: Construction, safety, and trade roles

**Scoring Weights**:
- Must-Have Certifications: 35% (increased)
- Bonus Certifications: 10%
- Required Skills: 20%
- Preferred Skills: 5%
- Experience Level: 20% (increased)
- Job Title Match: 5%
- Location: 5%

**Description**: Emphasizes safety certifications, licenses, and hands-on experience. Safety certifications are critical in construction and trade industries.

**Key Features**:
- Recognizes safety terminology and trade skills
- Common certifications: OSHA 10, OSHA 30, CDL, Crane Operator, Forklift, First Aid, CPR, Confined Space, Fall Protection

**Example Use Cases**:
- Safety Managers
- Construction Workers
- Electricians
- Heavy Equipment Operators
- Trade positions requiring safety certs

---

### 5. Finance Template

**Best For**: Accounting, banking, and finance roles

**Scoring Weights**:
- Must-Have Certifications: 30%
- Bonus Certifications: 10%
- Required Skills: 20%
- Preferred Skills: 10%
- Experience Level: 20% (increased)
- Job Title Match: 5%
- Location: 5%

**Description**: Emphasizes financial certifications, education, and experience. Financial credentials and regulatory knowledge are important.

**Key Features**:
- Recognizes financial terminology and compliance requirements
- Common certifications: CPA, CFA, CMA, Series 7, Series 63, FRM, CIA, CISA, CFP

**Example Use Cases**:
- Accountants
- Financial Analysts
- Bankers
- Compliance Officers
- Roles requiring financial credentials

---

### 6. Sales Template

**Best For**: Sales, account management, and business development roles

**Scoring Weights**:
- Must-Have Certifications: 10% (reduced)
- Bonus Certifications: 5% (reduced)
- Required Skills: 20%
- Preferred Skills: 10%
- Experience Level: 30% (increased)
- Job Title Match: 15% (increased)
- Location: 10% (increased)

**Description**: Emphasizes experience, soft skills, and achievements. Sales success is more about track record than certifications.

**Key Features**:
- Recognizes sales terminology and achievements
- Common certifications: Salesforce Certified, HubSpot Certified, SPIN Selling, Challenger Sale, Sandler Training

**Example Use Cases**:
- Sales Representatives
- Account Managers
- Business Development
- Territory Managers
- Roles where experience > credentials

---

## How to Use Templates

### In the Web Interface

1. **Navigate to "Scoring Configuration"** section
2. **Expand "Advanced Scoring Options"**
3. **Select an Industry Template** from the dropdown
4. **Review the template preview** showing weights
5. **Click "Apply Template"** to use those weights
6. **Optionally customize** individual weights using sliders
7. **Verify weights sum to 100%** before proceeding

### Programmatically

```python
from candidate_ranker import CandidateRankerApp

app = CandidateRankerApp()

pdf_path = app.run(
    job_title="Registered Nurse",
    certifications=[...],
    location="New York, NY",
    job_description="...",
    resume_files=["resume1.pdf", "resume2.pdf"],
    industry_template="healthcare",  # Use healthcare template
    custom_scoring_weights=None,  # Use template defaults
    dealbreakers=["Missing RN license"],  # Optional
    bias_reduction_enabled=False  # Optional
)
```

## Customizing Weights

You can customize weights even after selecting a template:

1. **Select a template** as a starting point
2. **Adjust individual sliders** to fine-tune weights
3. **Ensure total equals 100%** (system will warn if not)
4. **Custom weights override template** when set

## Dealbreakers

Dealbreakers automatically disqualify candidates (score = 0.0) if they meet the criteria:

**Examples**:
- "Missing required license"
- "No relevant experience"
- "Criminal record"
- "Missing OSHA 30 certification"

**How to Set**:
- Enter one dealbreaker per line in the "Dealbreakers" text area
- System checks resume text, skills, and certifications against dealbreakers
- Candidates matching any dealbreaker are automatically disqualified

## Bias Reduction

Enable "Bias Reduction (Blind Screening)" to:
- Remove names from evaluation
- Exclude photos
- Hide graduation dates
- Focus evaluation on qualifications only

This helps reduce unconscious bias in the screening process.

## Auto-Detection

The system automatically detects industry from job descriptions and suggests appropriate templates:

- **Healthcare keywords**: medical, hospital, nursing, clinical → suggests Healthcare template
- **Technology keywords**: software, programming, developer, IT → suggests Technology template
- **Construction keywords**: construction, safety, OSHA, trade → suggests Construction template
- **Finance keywords**: finance, accounting, banking, CPA → suggests Finance template
- **Sales keywords**: sales, account manager, business development → suggests Sales template

## Best Practices

1. **Start with a template** that matches your industry
2. **Customize only if needed** - templates are based on best practices
3. **Use dealbreakers sparingly** - only for truly disqualifying criteria
4. **Enable bias reduction** for fairer evaluations
5. **Test different templates** to see which works best for your roles
6. **Document your choices** for consistency across hiring

## Template Comparison

| Template | Certs Weight | Skills Weight | Experience Weight | Best For |
|----------|--------------|---------------|-------------------|----------|
| General | 30% | 25% | 10% | Most roles |
| Healthcare | 40% | 20% | 15% | Medical roles |
| Technology | 15% | 35% | 15% | Tech roles |
| Construction | 35% | 20% | 20% | Safety/trade roles |
| Finance | 30% | 20% | 20% | Financial roles |
| Sales | 10% | 20% | 30% | Sales roles |

## Troubleshooting

**Q: Weights don't sum to 100%**
- Adjust sliders until total equals 100%
- System will warn if weights are invalid

**Q: Template not applying**
- Click "Apply Template" button after selection
- Check that custom weights aren't overriding template

**Q: Dealbreakers not working**
- Ensure dealbreaker text matches resume content
- Check spelling and phrasing

**Q: Which template should I use?**
- Start with General for most roles
- Use industry-specific templates for specialized positions
- Customize if your needs don't match any template

## Support

For questions or issues with industry templates, consult the main README.md or contact support.

