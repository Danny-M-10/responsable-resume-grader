# Storage Architecture Explanation

## Why Analyses Show Up Even When S3 Bucket is Empty

The analyses you see in the History page are **stored in the database**, not in S3. Here's how the storage works:

## Storage Locations

### 1. Database (PostgreSQL/SQLite) - Analysis Records
**Table**: `analyses`
- **Stores**: Analysis metadata, status, configuration, results JSON
- **Includes**: Analysis ID, user ID, job ID, status (completed/failed), created_at, updated_at
- **This is what you see in the History page**

### 2. S3 Bucket - File Storage Only
**Bucket**: `responsable-recruitment-ai-uploads-us-east-2-774305585062`
- **Stores**: 
  - Uploaded resume files
  - Uploaded job description files
  - Generated PDF reports
- **Does NOT store**: Analysis records or metadata

## What This Means

When you see analyses in the History page:
- ✅ The analysis **record** exists in the database
- ✅ The analysis **metadata** (status, date, job info) is in the database
- ❓ The **PDF report file** may or may not be in S3 (depending on when it was generated)
- ❓ The **uploaded files** may or may not be in S3 (if they were cleaned up)

## Current Situation

Your S3 bucket is **empty**, which means:
- No resume files stored
- No job description files stored  
- No PDF report files stored

But your **database still contains**:
- Analysis records (what you see in History)
- Analysis metadata and results JSON
- Job descriptions (metadata)
- Candidate profiles (metadata)

## If You Want to Clear the Analyses

If you want to remove the analyses from the History page, you would need to:

1. **Clear the database** (not S3):
   - Delete records from `analyses` table
   - Optionally delete related records from `reports`, `candidates`, `jobs` tables

2. **S3 bucket** is already empty, so no action needed there

## Summary

- **S3 Bucket**: Empty ✅ (files only)
- **Database**: Contains analysis records (this is why History shows analyses)

The History page reads from the database `analyses` table, which is why you see analyses even though S3 is empty.
