#!/bin/bash
# API-based test script to complete a full candidate analysis workflow using curl
# This script tests the complete analysis workflow via API calls

set -e

BASE_URL="https://recruiting.crossroadcoach.com"
TEST_EMAIL="testuser2026@example.com"
TEST_PASSWORD="TestPassword123!"

SAMPLE_JOB_FILE="sample_job_descriptions/data_scientist_job.txt"
SAMPLE_RESUME_FILES=(
    "sample_resumes/jane_smith_resume.txt"
    "sample_resumes/john_doe_resume.txt"
    "sample_resumes/michael_chen_resume.txt"
)

echo "============================================================"
echo "FULL CANDIDATE ANALYSIS TEST (API-based)"
echo "============================================================"
echo ""

# Step 1: Login
echo "🔐 Step 1: Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('access_token', ''))" 2>/dev/null || echo "")

if [ -z "$TOKEN" ] || [ "$TOKEN" = "None" ] || [ "$TOKEN" = "" ]; then
    echo "❌ Login failed"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ Login successful"
echo ""

# Step 2: Upload job description
echo "📄 Step 2: Uploading job description..."
JOB_UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/jobs/upload" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@$SAMPLE_JOB_FILE")

JOB_ID=$(echo "$JOB_UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

if [ -z "$JOB_ID" ] || [ "$JOB_ID" = "None" ]; then
    echo "❌ Job upload failed"
    echo "Response: $JOB_UPLOAD_RESPONSE"
    exit 1
fi

JOB_TITLE=$(echo "$JOB_UPLOAD_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); pd=d.get('parsed_data', {}); print(pd.get('job_title', 'N/A'))" 2>/dev/null)
echo "✅ Job uploaded successfully"
echo "   Job ID: $JOB_ID"
echo "   Job Title: $JOB_TITLE"
echo ""

# Step 3: Upload resumes
echo "📄 Step 3: Uploading resume files..."
CURL_FILES=""
for resume_file in "${SAMPLE_RESUME_FILES[@]}"; do
    if [ -f "$resume_file" ]; then
        CURL_FILES="$CURL_FILES -F files=@$resume_file"
    fi
done

if [ -z "$CURL_FILES" ]; then
    echo "❌ No resume files found"
    exit 1
fi

RESUME_UPLOAD_RESPONSE=$(eval curl -s -X POST "$BASE_URL/api/resumes/upload" \
    -H "Authorization: Bearer $TOKEN" \
    $CURL_FILES)

CANDIDATE_IDS=$(echo "$RESUME_UPLOAD_RESPONSE" | python3 -c "
import sys, json
ids = json.load(sys.stdin).get('candidate_ids', [])
print(','.join(ids))
" 2>/dev/null)

if [ -z "$CANDIDATE_IDS" ]; then
    echo "❌ Resume upload failed"
    echo "Response: $RESUME_UPLOAD_RESPONSE"
    exit 1
fi

CANDIDATE_COUNT=$(echo "$CANDIDATE_IDS" | tr ',' '\n' | wc -l | tr -d ' ')
echo "✅ Resumes uploaded successfully"
echo "   Candidate IDs: $CANDIDATE_COUNT candidates"
echo ""

# Step 4: Start analysis
echo "🚀 Step 4: Starting analysis..."
CANDIDATE_IDS_ARRAY=$(echo "$CANDIDATE_IDS" | python3 -c "
import sys, json
ids = sys.stdin.read().strip().split(',')
print(json.dumps(ids))
")

ANALYSIS_CONFIG=$(python3 -c "
import json
config = {
    'job_id': '$JOB_ID',
    'candidate_ids': $CANDIDATE_IDS_ARRAY,
    'industry_template': 'technology',
    'bias_reduction_enabled': False
}
print(json.dumps(config))
")

ANALYSIS_RESPONSE=$(curl -s -X POST "$BASE_URL/api/analysis/start" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$ANALYSIS_CONFIG")

ANALYSIS_ID=$(echo "$ANALYSIS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

if [ -z "$ANALYSIS_ID" ] || [ "$ANALYSIS_ID" = "None" ]; then
    echo "❌ Analysis start failed"
    echo "Response: $ANALYSIS_RESPONSE"
    exit 1
fi

STATUS=$(echo "$ANALYSIS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
echo "✅ Analysis started successfully"
echo "   Analysis ID: $ANALYSIS_ID"
echo "   Status: $STATUS"
echo ""

# Step 5: Wait for completion
echo "⏳ Step 5: Waiting for analysis to complete (max 300 seconds)..."
MAX_WAIT=300
CHECK_INTERVAL=5
ELAPSED=0
LAST_STATUS=""

while [ $ELAPSED -lt $MAX_WAIT ]; do
    STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/analysis/$ANALYSIS_ID" \
        -H "Authorization: Bearer $TOKEN")
    
    CURRENT_STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
    
    if [ "$CURRENT_STATUS" != "$LAST_STATUS" ] && [ -n "$CURRENT_STATUS" ]; then
        echo "   Status: $CURRENT_STATUS"
        LAST_STATUS="$CURRENT_STATUS"
    fi
    
    if [ "$CURRENT_STATUS" = "completed" ]; then
        echo "✅ Analysis completed!"
        break
    elif [ "$CURRENT_STATUS" = "failed" ]; then
        echo "❌ Analysis failed"
        exit 1
    fi
    
    sleep $CHECK_INTERVAL
    ELAPSED=$((ELAPSED + CHECK_INTERVAL))
done

if [ "$CURRENT_STATUS" != "completed" ]; then
    echo "⏱️  Analysis did not complete within $MAX_WAIT seconds"
    echo "   Current status: $CURRENT_STATUS"
    exit 1
fi

echo ""

# Step 6: Get results
echo "📊 Step 6: Retrieving analysis results..."
FINAL_RESPONSE=$(curl -s -X GET "$BASE_URL/api/analysis/$ANALYSIS_ID" \
    -H "Authorization: Bearer $TOKEN")

HAS_RESULTS=$(echo "$FINAL_RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin).get('results', None); print('yes' if r else 'no')" 2>/dev/null)

if [ "$HAS_RESULTS" = "yes" ]; then
    echo "✅ Results retrieved successfully"
    echo ""
    echo "============================================================"
    echo "ANALYSIS RESULTS SUMMARY"
    echo "============================================================"
    echo ""
    
    # Display ranked candidates
    echo "$FINAL_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
results = data.get('results', {})
ranked = results.get('ranked_candidates', [])

print(f'📋 Ranked Candidates ({len(ranked)}):')
print('-' * 60)
for i, candidate in enumerate(ranked, 1):
    name = candidate.get('name', 'Unknown')
    score = candidate.get('total_score', 0)
    print(f'{i}. {name}: {score:.2f}%')
    summary = candidate.get('summary', '')
    if summary:
        print(f'   {summary[:100]}...')
    print()

summary_stats = results.get('summary', {})
if summary_stats:
    print('📈 Summary Statistics:')
    print('-' * 60)
    print(f\"Total Candidates: {summary_stats.get('total_candidates', 0)}\")
    print(f\"Qualified: {summary_stats.get('qualified_count', 0)}\")
    print()
" 2>/dev/null
    
    echo "============================================================"
    echo ""
    echo "✅ Full analysis test completed successfully!"
    echo "   Analysis ID: $ANALYSIS_ID"
    echo "   View results in the browser at: $BASE_URL/history"
else
    echo "⚠️  Analysis completed but no results found"
    echo "Response: $FINAL_RESPONSE"
    exit 1
fi
