# Code Review: Bugs, Errors, and Potential Issues

## Critical Issues (Must Fix)

### 1. **Syntax Error in `ai_job_parser.py` (Line 37)**
**Location:** `ai_job_parser.py:37`
**Issue:** Incorrect indentation - `try` block is indented when it should be at the same level as the `if` statement
**Impact:** Code will not run - SyntaxError
**Fix:**
```python
# Current (WRONG):
        if not self.api_key:
            raise ValueError(...)
        
            try:  # <-- Wrong indentation
            self.client = OpenAI(api_key=self.api_key)

# Should be:
        if not self.api_key:
            raise ValueError(...)
        
        try:  # <-- Correct indentation
            self.client = OpenAI(api_key=self.api_key)
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
            print(f"AI job parsing enabled (using {self.model})")
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {e}")
```

### 2. **Missing Error Handling for JSON Parsing**
**Location:** Multiple files
**Issue:** `json.loads()` called without try/except blocks in several places
**Impact:** Application will crash if database contains malformed JSON
**Affected Locations:**
- `app.py:242` - `summary = json.loads(summary_json) if summary_json else {}`
- `app.py:344` - `certs_data = json.loads(certs_json)`
- `app.py:352` - `required_skills = json.loads(req_skills_json)`
- `app.py:359` - `preferred_skills = json.loads(pref_skills_json)`

**Fix:** Wrap all `json.loads()` calls in try/except:
```python
# Example fix for app.py:242
try:
    summary = json.loads(summary_json) if summary_json else {}
except (json.JSONDecodeError, TypeError):
    summary = {}
```

### 3. **Race Condition in Password Reset**
**Location:** `auth.py:reset_password_with_token()` and `reset_password_with_code()`
**Issue:** Window between checking token validity and marking as used allows potential double-use
**Impact:** Token could potentially be used twice if two requests happen simultaneously
**Fix:** Use database transaction with proper locking or check-and-update in single query:
```python
# Better approach - use UPDATE with WHERE to atomically check and mark
cur.execute(
    _prepare_query(conn, """
        UPDATE password_reset_tokens 
        SET used = TRUE 
        WHERE token = ? AND expires_at > ? AND used = FALSE
        RETURNING user_id
    """),
    (token, now_str),
)
row = cur.fetchone()
if not row:
    return False
user_id = row[0]
```

## High Priority Issues

### 4. **Timezone Handling Bug in Session Timeout**
**Location:** `auth.py:168-170`
**Issue:** Timezone conversion logic may fail for some datetime formats
**Impact:** Session timeout may not work correctly for some timezone formats
**Current Code:**
```python
last_activity = datetime.fromisoformat(last_activity_str.replace('Z', '+00:00'))
if last_activity.tzinfo:
    last_activity = last_activity.replace(tzinfo=None)
```
**Problem:** If `last_activity_str` doesn't contain 'Z', the replace does nothing, and timezone handling may be incorrect
**Fix:**
```python
try:
    # Handle ISO format with Z
    if last_activity_str.endswith('Z'):
        last_activity = datetime.fromisoformat(last_activity_str.replace('Z', '+00:00'))
    else:
        last_activity = datetime.fromisoformat(last_activity_str)
    
    # Convert to naive UTC datetime
    if last_activity.tzinfo:
        last_activity = last_activity.replace(tzinfo=None)
except (ValueError, TypeError) as e:
    # Log error for debugging
    print(f"Warning: Failed to parse last_activity_at: {last_activity_str}, error: {e}")
    pass
```

### 5. **Missing Transaction Rollback on Errors**
**Location:** Multiple database operations in `auth.py` and `app.py`
**Issue:** Database operations don't rollback on exceptions
**Impact:** Partial updates could leave database in inconsistent state
**Example:** `auth.py:reset_password_with_token()` - if password update succeeds but token marking fails, password is changed but token remains valid
**Fix:** Use proper transaction handling:
```python
with get_db() as conn:
    try:
        cur = conn.cursor()
        # ... operations ...
        conn.commit()
    except Exception:
        conn.rollback()
        raise
```

### 6. **Unsafe File Path Handling**
**Location:** `app.py:254` - `os.path.exists(pdf_path)`
**Issue:** No validation that `pdf_path` is within allowed directory
**Impact:** Potential path traversal vulnerability if `pdf_path` contains `../`
**Fix:** Validate paths:
```python
def is_safe_path(path: str, base_dir: str) -> bool:
    """Check if path is within base directory"""
    real_base = os.path.realpath(base_dir)
    real_path = os.path.realpath(path)
    return real_path.startswith(real_base)

# Usage:
if pdf_path and is_safe_path(pdf_path, ALLOWED_PDF_DIR):
    # ... safe to access
```

### 7. **Missing Input Validation for Password Reset Code**
**Location:** `app.py:127` - Code input
**Issue:** No validation that code is exactly 6 digits
**Impact:** Invalid codes could be accepted
**Fix:**
```python
entered_code = st.text_input("6-digit code", key="entered_code", max_chars=6)
if not entered_code.isdigit() or len(entered_code) != 6:
    st.error("Code must be exactly 6 digits")
    return
```

## Medium Priority Issues

### 8. **Potential Division by Zero**
**Location:** `app.py:398-400` - Average score calculation
**Issue:** No check if `viable_candidates` list is empty before division
**Current Code:**
```python
if viable_candidates:
    avg_score = sum(c.fit_score for c in viable_candidates) / len(viable_candidates)
```
**Status:** Actually handled correctly with `if` check, but could be more explicit

### 9. **Missing Error Handling for File Operations**
**Location:** `app.py:254-259` - PDF file reading
**Issue:** Generic `except Exception: pass` hides errors
**Impact:** Silent failures make debugging difficult
**Fix:** At minimum, log the error:
```python
except Exception as e:
    print(f"Warning: Failed to load PDF from {pdf_path}: {e}")
    # Or use proper logging
    import logging
    logging.warning(f"Failed to load PDF from {pdf_path}: {e}")
```

### 10. **Inconsistent Error Messages**
**Location:** Various authentication functions
**Issue:** Some functions return `False` on error, others raise exceptions
**Impact:** Inconsistent error handling makes code harder to maintain
**Recommendation:** Standardize on either exceptions or return values

### 11. **Missing Validation for User ID in Database Queries**
**Location:** `app.py:load_analysis_data()` and `load_user_analyses()`
**Issue:** No validation that `user_id` is a valid UUID format
**Impact:** Could allow SQL injection if user_id is manipulated (though parameterized queries help)
**Fix:** Validate UUID format:
```python
import uuid

def is_valid_uuid(uuid_string: str) -> bool:
    try:
        uuid.UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False

# Usage:
if not is_valid_uuid(user_id):
    raise ValueError("Invalid user ID format")
```

### 12. **Potential Memory Issue with Large PDFs**
**Location:** `app.py:256` - Reading entire PDF into memory
**Issue:** Large PDF files could cause memory issues
**Impact:** Application could crash or become slow with very large PDFs
**Fix:** Consider streaming or size limits:
```python
MAX_PDF_SIZE = 50 * 1024 * 1024  # 50MB
if os.path.getsize(pdf_path) > MAX_PDF_SIZE:
    st.error("PDF file too large")
    return None
```

## Low Priority / Code Quality Issues

### 13. **Duplicate Query Preparation Functions**
**Location:** `app.py` has `_prepare_query_wrapper()` and `auth.py` has `_prepare_query()`
**Issue:** Code duplication
**Recommendation:** Move to shared utility module

### 14. **Magic Numbers**
**Location:** Various files
**Issue:** Hard-coded values like `2 * 60 * 60` for timeout
**Recommendation:** Use named constants:
```python
INACTIVITY_TIMEOUT_SECONDS = 2 * 60 * 60  # 2 hours
```

### 15. **Missing Type Hints**
**Location:** Some functions
**Issue:** Incomplete type annotations
**Recommendation:** Add complete type hints for better IDE support and documentation

### 16. **Inconsistent Date Formatting**
**Location:** `app.py:display_analysis_history()`
**Issue:** Date formatting assumes ISO format but doesn't handle all cases
**Fix:** Use proper date parsing:
```python
from datetime import datetime
try:
    dt = datetime.fromisoformat(analysis['created_at'].replace('Z', '+00:00'))
    date_str = dt.strftime('%Y-%m-%d')
    time_str = dt.strftime('%H:%M:%S')
except (ValueError, AttributeError):
    date_str = analysis['created_at'][:10] if len(analysis['created_at']) >= 10 else 'Unknown'
    time_str = ''
```

### 17. **Missing Indexes on Database Tables**
**Location:** `db.py` - Table creation
**Issue:** No indexes on frequently queried columns
**Impact:** Performance degradation as data grows
**Recommendation:** Add indexes:
```sql
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_candidate_scores_report_id ON candidate_scores(report_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
```

## Security Considerations

### 18. **Password Reset Code Displayed in UI**
**Location:** `app.py:125`
**Issue:** Reset code is displayed in UI for testing
**Impact:** Security risk in production
**Status:** Documented as "for testing" but should be removed or gated behind debug mode
**Fix:** Only show in development:
```python
if os.getenv('ENVIRONMENT') == 'development':
    st.success(f"Reset code generated: **{code}** (Development mode)")
else:
    st.success("Reset code has been sent to your email.")
```

### 19. **Session Token in Session State**
**Location:** `app.py` - Session tokens stored in Streamlit session state
**Issue:** Session state is client-side accessible
**Impact:** Tokens could be exposed if session state is compromised
**Note:** This is a limitation of Streamlit - consider server-side session storage for production

### 20. **No Rate Limiting on Password Reset**
**Location:** `auth.py:request_password_reset()`
**Issue:** No limit on password reset requests
**Impact:** Could be abused for DoS or email spam
**Recommendation:** Add rate limiting:
```python
# Check recent reset requests
cur.execute(
    _prepare_query(conn, """
        SELECT COUNT(*) FROM password_reset_tokens
        WHERE user_id = ? AND created_at > ?
    """),
    (user_id, (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z")
)
if cur.fetchone()[0] >= 5:  # Max 5 per hour
    raise ValueError("Too many reset requests. Please wait before trying again.")
```

## Summary

**Critical:** 3 issues (syntax error, missing error handling, race condition)
**High Priority:** 4 issues (timezone, transactions, path validation, input validation)
**Medium Priority:** 5 issues (error handling, validation, memory)
**Low Priority:** 4 issues (code quality, performance)
**Security:** 3 considerations

**Total:** 19 issues identified

## Recommended Fix Order

1. Fix syntax error in `ai_job_parser.py` (blocks execution)
2. Add error handling for all `json.loads()` calls
3. Fix race condition in password reset
4. Fix timezone handling in session timeout
5. Add transaction rollback handling
6. Add input validation for password reset codes
7. Add path validation for file operations
8. Add database indexes for performance
9. Add rate limiting for password reset
10. Address remaining code quality issues

