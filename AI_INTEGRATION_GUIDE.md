# AI Integration Guide

## Overview

The candidate ranking tool now supports **AI-powered evaluation** using Claude API (Anthropic). This provides much more intelligent, context-aware candidate assessment compared to the rule-based approach.

---

## Comparison: Rule-Based vs AI-Powered

### Current Rule-Based Approach

**How it works:**
- Pattern matching with regex
- Hardcoded weights (30% certs, 25% skills, etc.)
- Exact string matching for skills
- Fixed synonym dictionary
- Simple percentage calculations

**Limitations:**
- ❌ Can't understand context or nuance
- ❌ Misses equivalent skills not in hardcoded list
- ❌ Can't assess quality of experience
- ❌ No understanding of career progression
- ❌ "Chain-of-thought" is just formatted text

**Advantages:**
- ✅ Fast (no API calls)
- ✅ Free (no API costs)
- ✅ Works offline
- ✅ Deterministic results

### AI-Powered Approach (NEW)

**How it works:**
- Uses Claude API (latest Sonnet model)
- Genuine chain-of-thought reasoning
- Contextual understanding of skills and experience
- Natural language evaluation
- Intelligent synonym detection

**Advantages:**
- ✅ **Understands context**: "5 years Python" vs "10 years programming including Python"
- ✅ **Recognizes equivalent skills**: Knows React experience helps with Vue
- ✅ **Assesses quality**: Junior role vs senior leadership experience
- ✅ **Nuanced evaluation**: Can identify transferable skills
- ✅ **Better reasoning**: Genuine AI-powered chain-of-thought
- ✅ **Adaptive**: No hardcoded rules, learns from job description

**Limitations:**
- ❌ Requires API key (costs money)
- ❌ Slower (API latency ~2-5 seconds per candidate)
- ❌ Requires internet connection
- ❌ Results may vary slightly between runs

---

## Setup Instructions

### 1. Install Anthropic SDK

Add to your requirements:

```bash
pip install anthropic
```

Or install from the updated requirements file:

```bash
cd "/Users/danny/Desktop/Claude Code Test"
source venv/bin/activate
pip install -r requirements_ai.txt
```

### 2. Get Anthropic API Key

1. Go to: https://console.anthropic.com/
2. Sign up or log in
3. Navigate to "API Keys"
4. Create a new API key
5. Copy the key (starts with `sk-ant-...`)

### 3. Set Environment Variable

**macOS/Linux:**
```bash
export ANTHROPIC_API_KEY='sk-ant-your-key-here'
```

**Or add to your shell profile (~/.zshrc or ~/.bashrc):**
```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

**Windows:**
```cmd
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 4. Enable AI Scoring

**Option A: Environment Variable (Recommended)**
```bash
export USE_AI_SCORING=true
```

**Option B: Code Configuration**

Modify `candidate_ranker.py`:

```python
# Change this line:
from scoring_engine import ScoringEngine

# To this:
from ai_scoring_engine import HybridScoringEngine as ScoringEngine
```

---

## Usage Examples

### Basic Usage (Hybrid Mode)

The hybrid engine automatically uses AI when available, falls back to rule-based:

```python
from ai_scoring_engine import HybridScoringEngine
from job_description_parser import JobDescriptionParser
from resume_parser import ResumeParser

# Initialize (will use AI if API key is set)
scoring_engine = HybridScoringEngine(use_ai=True)

# Parse job and resume
job_parser = JobDescriptionParser()
resume_parser = ResumeParser()

job_data = job_parser.parse('job_description.pdf')
candidate = resume_parser.parse('resume.pdf')

# Score with AI
score = scoring_engine.score_candidate(candidate, job_data)

print(f"Candidate: {score.candidate_name}")
print(f"Fit Score: {score.fit_score}/10")
print(f"\nAI Reasoning:\n{score.chain_of_thought}")
```

### Force AI-Only Mode

```python
from ai_scoring_engine import AIScoringEngine

# This will raise error if API key not set
scoring_engine = AIScoringEngine(api_key='sk-ant-...')

score = scoring_engine.score_candidate(candidate, job_data)
```

### Force Rule-Based Mode

```python
from scoring_engine import ScoringEngine

# Use original rule-based scoring
scoring_engine = ScoringEngine()

score = scoring_engine.score_candidate(candidate, job_data)
```

---

## Web Interface Integration

Update `app_enhanced.py` to use AI scoring:

```python
# Add toggle in sidebar
use_ai = st.sidebar.checkbox(
    "Use AI-Powered Scoring (requires API key)",
    value=os.environ.get('USE_AI_SCORING', '').lower() == 'true',
    help="Uses Claude API for intelligent evaluation"
)

# Initialize scoring engine based on selection
if use_ai:
    try:
        from ai_scoring_engine import AIScoringEngine
        scoring_engine = AIScoringEngine()
        st.sidebar.success("✓ AI scoring enabled")
    except Exception as e:
        st.sidebar.error(f"AI unavailable: {e}")
        from scoring_engine import ScoringEngine
        scoring_engine = ScoringEngine()
else:
    from scoring_engine import ScoringEngine
    scoring_engine = ScoringEngine()
```

---

## Cost Estimation

### Claude API Pricing (as of 2025)

**Claude Sonnet 4.5:**
- Input: $3 per million tokens
- Output: $15 per million tokens

**Typical Usage Per Candidate:**
- Input: ~2,000 tokens (job description + resume)
- Output: ~1,500 tokens (evaluation)
- **Cost per candidate: ~$0.03** (3 cents)

**For 100 candidates:**
- Total cost: ~$3.00

**For 1,000 candidates:**
- Total cost: ~$30.00

### Cost Optimization Tips

1. **Batch processing**: Process multiple candidates in one session
2. **Hybrid mode**: Use AI for top candidates only, rule-based for initial screening
3. **Cache job descriptions**: Reuse job analysis across candidates
4. **Use Claude Haiku**: Cheaper model for simpler evaluations ($0.25 per million input tokens)

---

## Example AI Output

Here's what AI-powered evaluation looks like:

```
1. **MUST-HAVE CERTIFICATIONS ANALYSIS**:

The candidate possesses OSHA 510, which is explicitly required. However,
they are missing COSS, CHST, ASP, and CUSP certifications. While OSHA 510
demonstrates safety training competency, the absence of the other four
certifications represents a significant gap for this safety-critical role.

2. **SKILLS MATCH ANALYSIS**:

Required skills present:
- Electrical utility distribution knowledge (10+ years experience)
- Safety protocol expertise (evidenced by OSHA 510 and safety-focused roles)
- Field operations experience (12 years in utility environments)

Required skills missing/unclear:
- Specific COSS certification knowledge
- Recent Construction Health & Safety Technician training

Transferable skills:
- The candidate's extensive lineman experience (12 years) directly translates
  to the electrical utility safety requirements
- Leadership experience managing 5-person crews aligns with the mentorship
  requirement

3. **EXPERIENCE EVALUATION**:

The candidate brings 12 years of highly relevant experience in electrical
utility distribution. Career progression shows growth from Lineman to Senior
Lineman to Crew Lead, demonstrating both technical competency and leadership
development. Industry alignment is excellent - utility sector throughout career.

4. **OVERALL FIT ASSESSMENT**:

Key strengths:
- Extensive hands-on electrical utility experience
- OSHA 510 certification (1 of 5 required certs)
- Proven leadership and mentorship capability
- Strong domain expertise in distribution systems

Notable gaps:
- Missing 4 critical safety certifications (COSS, CHST, ASP, CUSP)
- Certifications may be obtainable with training investment

Growth potential:
- Strong foundation for certification acquisition
- Already demonstrates safety-first mindset
- Leadership skills in place for team development role

5. **FINAL SCORE**: 6.5/10

This is a moderate-to-strong fit. The candidate has excellent relevant
experience and one required certification, but the missing certifications
represent a significant gap. However, given the strong experience base,
these certifications could likely be obtained with employer support.

6. **RECOMMENDATIONS**:

- **Interview**: Yes, qualified candidate worth interviewing
- **Focus questions on**:
  * Willingness to pursue additional certifications
  * Timeline for certification completion
  * Specific experience with energized systems and overhead line work
- **Considerations**:
  * May require 6-12 months to complete missing certifications
  * Strong enough experience base to justify certification investment
  * Consider conditional offer pending certification completion

FINAL_SCORE: 6.5/10
```

---

## Testing AI Integration

Quick test script:

```bash
cd "/Users/danny/Desktop/Claude Code Test"
source venv/bin/activate

# Set API key
export ANTHROPIC_API_KEY='sk-ant-your-key-here'

# Test AI scoring
python -c "
from ai_scoring_engine import AIScoringEngine
from job_description_parser import JobDescriptionParser
from resume_parser import ResumeParser

engine = AIScoringEngine()
job_parser = JobDescriptionParser()
resume_parser = ResumeParser()

job_data = job_parser.parse('sample_job_descriptions/safety_lineman_job.txt')
candidate = resume_parser.parse('sample_resumes/jane_smith_resume.txt')

print('Testing AI-powered scoring...')
score = engine.score_candidate(candidate, job_data)
print(f'Score: {score.fit_score}/10')
print(f'Reasoning length: {len(score.chain_of_thought)} characters')
print('✓ AI integration working!')
"
```

---

## Hybrid Strategy (Best Practice)

For optimal cost/quality balance:

```python
# Use rule-based for initial screening
from scoring_engine import ScoringEngine
rule_engine = ScoringEngine()

# Use AI for top candidates
from ai_scoring_engine import AIScoringEngine
ai_engine = AIScoringEngine()

# Score all candidates with rule-based
all_scores = [rule_engine.score_candidate(c, job) for c in candidates]

# Get top 10
top_candidates = sorted(all_scores, key=lambda x: x.fit_score, reverse=True)[:10]

# Re-score top 10 with AI for detailed evaluation
ai_scores = [ai_engine.score_candidate(c, job) for c in top_candidates]
```

This approach:
- Costs ~$0.30 instead of $3.00 for 100 candidates
- Provides detailed AI evaluation where it matters most
- Fast initial screening with rule-based engine

---

## Next Steps

1. **Get API key** from https://console.anthropic.com/
2. **Install dependencies**: `pip install anthropic`
3. **Set environment variable**: `export ANTHROPIC_API_KEY='sk-ant-...'`
4. **Test with sample data** using the test script above
5. **Update web interface** with AI toggle option
6. **Monitor costs** using Anthropic dashboard

---

## Troubleshooting

### "API key not found"
```bash
# Check if environment variable is set
echo $ANTHROPIC_API_KEY

# If empty, set it:
export ANTHROPIC_API_KEY='sk-ant-your-key-here'
```

### "Module 'anthropic' not found"
```bash
pip install anthropic
```

### "Rate limit exceeded"
- You're making too many API calls too quickly
- Add delays between requests: `time.sleep(1)`
- Or use batch API (future feature)

### API costs too high
- Switch to Claude Haiku (cheaper model)
- Use hybrid strategy (AI for top candidates only)
- Cache job description analysis

---

## Benefits Summary

**Why Use AI-Powered Scoring:**

1. **Better Accuracy**: Understands context and nuance
2. **Intelligent Matching**: Recognizes equivalent skills and experience
3. **Genuine CoT**: Real chain-of-thought reasoning, not formatted text
4. **Adaptive**: No hardcoded rules to maintain
5. **Natural Language**: Easy to understand AI explanations
6. **Time Savings**: Better candidate selection = fewer wasted interviews

**Total Cost for Serious Recruitment:**
- 100 candidates @ $0.03 each = **$3.00**
- 1,000 candidates @ $0.03 each = **$30.00**

**ROI Calculation:**
- One wasted interview (wrong candidate) costs ~$500 in time
- AI screening prevents 1-2 bad interviews → **Pays for itself with 20 candidates**

---

**The tool now supports both approaches - choose based on your needs!**
