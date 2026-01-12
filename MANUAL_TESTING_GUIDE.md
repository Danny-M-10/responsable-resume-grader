# Manual Testing Guide for Live Application

## Application URL
**Production**: https://recruiting.crossroadcoach.com

## Testing Instructions

Since automated browser testing is not available, please follow this manual testing checklist in your web browser.

## 1. Initial Access Test

- [ ] Navigate to https://recruiting.crossroadcoach.com
- [ ] Verify page loads without errors
- [ ] Check that you're redirected to login page (if authentication is required)
- [ ] Verify HTTPS is working (secure connection)

## 2. Authentication Testing

### Registration (if available)
- [ ] Navigate to registration page
- [ ] Create a new test account
- [ ] Verify registration succeeds
- [ ] Check for confirmation message/email

### Login
- [ ] Navigate to login page
- [ ] Enter valid credentials
- [ ] Verify login succeeds
- [ ] Check that you're redirected to dashboard
- [ ] Verify session persists (refresh page, should stay logged in)

## 3. Dashboard Testing

- [ ] Verify dashboard loads after login
- [ ] Check that all navigation links are visible
- [ ] Verify no console errors in browser DevTools

## 4. Job Description Upload

- [ ] Navigate to job input section
- [ ] Upload a job description file (PDF, DOCX, or TXT)
- [ ] Verify file upload succeeds
- [ ] Check that job data is parsed and displayed
- [ ] Verify job title, location, certifications are extracted
- [ ] Test with multiple file formats

## 5. Resume Upload

- [ ] Navigate to resume upload section
- [ ] Upload a single resume file
- [ ] Verify upload succeeds
- [ ] Upload multiple resume files at once
- [ ] Verify all files are accepted
- [ ] Check that resume data is parsed and displayed

## 6. Vault Features Testing

### Save to Vault
- [ ] Navigate to Vault page
- [ ] Upload a resume to vault
- [ ] Verify resume is saved
- [ ] Check that resume appears in the list
- [ ] Verify resume metadata is parsed (name, skills, etc.)

### Search Functionality
- [ ] Enter a search query in the search box
- [ ] Verify results filter in real-time (with debounce)
- [ ] Test searching by candidate name
- [ ] Test searching by skills
- [ ] Test searching by tags
- [ ] Verify case-insensitive search works

### Filter by Tags
- [ ] Click on a tag filter chip
- [ ] Verify resumes are filtered (only those with that tag)
- [ ] Select multiple tags
- [ ] Verify ALL selected tags must match (AND logic)
- [ ] Clear tags and verify all resumes show again

### Filter by Skills
- [ ] Click on a skill filter chip
- [ ] Verify resumes are filtered (those with that skill)
- [ ] Select multiple skills
- [ ] Verify ANY selected skill can match (OR logic)
- [ ] Clear skills and verify all resumes show again

### Filter by Name
- [ ] Enter a name in the name filter field
- [ ] Verify only resumes matching that name are shown
- [ ] Test partial name matches
- [ ] Clear name filter

### Combined Filters
- [ ] Use search + tags + skills + name together
- [ ] Verify results match all criteria correctly
- [ ] Clear all filters
- [ ] Verify all resumes are shown again

## 7. Analysis Workflow

- [ ] Select a job (from upload or vault)
- [ ] Select resumes (from upload or vault)
- [ ] Configure scoring settings (if applicable)
- [ ] Start analysis
- [ ] Verify progress updates appear (if WebSocket is working)
- [ ] Wait for analysis to complete
- [ ] Verify results page loads
- [ ] Check that candidate rankings are displayed
- [ ] Verify scores and rationales are shown

## 8. History/Results Viewing

- [ ] Navigate to History page
- [ ] Verify past analyses are listed
- [ ] Click on a completed analysis
- [ ] Verify results page loads correctly
- [ ] Check that all candidate data is displayed

## 9. Error Handling

- [ ] Try uploading an invalid file format
- [ ] Verify appropriate error message appears
- [ ] Try submitting form with missing required fields
- [ ] Verify validation errors are shown
- [ ] Test with very large files (if applicable)
- [ ] Verify appropriate error handling

## 10. Performance Testing

- [ ] Test page load times
- [ ] Test search/filter responsiveness
- [ ] Test with large number of resumes in vault
- [ ] Verify no noticeable lag in UI interactions

## Expected Results

Based on our code review and deployment:

✅ All API endpoints should respond correctly
✅ File uploads should work (PDF, DOCX, TXT)
✅ Resume parsing should extract metadata automatically
✅ Search and filters should work as designed
✅ Analysis workflow should complete successfully
✅ No critical errors in browser console

## Reporting Issues

If you encounter any issues during testing:

1. Note the exact steps to reproduce
2. Check browser console for errors (F12 → Console)
3. Check Network tab for failed requests
4. Note the error message displayed
5. Check CloudWatch logs for backend errors

## CloudWatch Logs

To check logs for errors:
```bash
aws logs tail /ecs/internal_recruiting_candidate_ranker --since 1h --region us-east-2 --follow
```

## Quick Test Script

You can also use the automated smoke test:
```bash
./kck/smoke_test.sh https://recruiting.crossroadcoach.com us-east-2
```

This tests:
- Application accessibility
- Health check endpoint
- ECS service status
- Basic connectivity
