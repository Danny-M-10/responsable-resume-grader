# How to Get an Anthropic API Key

Follow these steps to get your Claude API key and enable AI-enhanced candidate evaluation.

## Step 1: Create an Anthropic Account

1. Go to [https://console.anthropic.com](https://console.anthropic.com)
2. Click "Sign Up" or "Get Started"
3. Create an account using:
   - Email and password, OR
   - Google account, OR
   - GitHub account

## Step 2: Access the API Console

1. After signing up, you'll be directed to the Anthropic Console
2. Navigate to **API Keys** in the left sidebar
3. Or go directly to: [https://console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

## Step 3: Create an API Key

1. Click the **"Create Key"** button
2. Give your key a descriptive name (e.g., "Candidate Ranking App")
3. Click **"Create Key"**
4. **IMPORTANT**: Copy the API key immediately - you won't be able to see it again!
   - The key will look like: `sk-ant-api03-...`

## Step 4: Add the Key to Your Application

### Option A: Add to .env File (Recommended)

1. Open the [.env](.env) file in your project directory
2. Find the line that says:
   ```
   # ANTHROPIC_API_KEY=your-anthropic-api-key-here
   ```
3. Replace it with your actual key (remove the `#`):
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-YOUR-ACTUAL-KEY-HERE
   ```
4. Save the file

### Option B: Set Environment Variable

**macOS/Linux:**
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-YOUR-ACTUAL-KEY-HERE"
```

**Windows (Command Prompt):**
```cmd
set ANTHROPIC_API_KEY=sk-ant-api03-YOUR-ACTUAL-KEY-HERE
```

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-api03-YOUR-ACTUAL-KEY-HERE"
```

## Step 5: Add Credits to Your Account

Anthropic requires you to add credits before using the API:

1. Go to [https://console.anthropic.com/settings/billing](https://console.anthropic.com/settings/billing)
2. Click **"Add Credits"**
3. Minimum purchase: **$5 USD**
4. Recommended starting amount: **$20-50** for testing
5. Enter payment information and complete purchase

### Pricing (as of 2025)

**Claude 3.5 Sonnet (Recommended for this app):**
- Input: $3 per million tokens (~$0.003 per 1,000 tokens)
- Output: $15 per million tokens (~$0.015 per 1,000 tokens)

**Estimated Cost Per Candidate Evaluation:**
- Approximately $0.01-0.05 per candidate
- Processing 10 candidates: ~$0.10-0.50
- Processing 100 candidates: ~$1-5

## Step 6: Verify Your Setup

Run this test script to verify your API key is working:

```bash
source venv/bin/activate
python -c "from config import AnthropicConfig; print('API Key configured:', AnthropicConfig.is_configured())"
```

Or run a full test:

```bash
python -c "
from anthropic import Anthropic
import os

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
message = client.messages.create(
    model='claude-3-5-sonnet-20241022',
    max_tokens=100,
    messages=[{'role': 'user', 'content': 'Say hello!'}]
)
print('✓ API Key is working!')
print('Response:', message.content[0].text)
"
```

## What AI Features Does This Enable?

Once your API key is configured, your Candidate Ranking Application can use:

### 1. **Smarter Resume Analysis**
- Natural language understanding of job descriptions
- Better skill extraction from resumes
- Context-aware matching

### 2. **Advanced Reasoning**
- Chain-of-thought candidate evaluation
- Nuanced assessment of qualifications
- Better handling of edge cases

### 3. **Improved Skill Matching**
- Semantic understanding of skills (e.g., "React" ≈ "React.js" ≈ "ReactJS")
- Recognition of related technologies
- Industry-specific knowledge

### 4. **Better Explanations**
- Detailed rationale for each candidate's score
- Specific recommendations for interviews
- Insights into candidate strengths/weaknesses

## Usage Monitoring

Monitor your API usage at: [https://console.anthropic.com/settings/usage](https://console.anthropic.com/settings/usage)

You can:
- View total credits used
- See request history
- Track spending over time
- Set up billing alerts

## Security Best Practices

1. **Never commit your API key to git**
   - The `.env` file is already in `.gitignore`
   - Never share your key publicly

2. **Rotate keys regularly**
   - Create new keys every few months
   - Delete old keys from the console

3. **Use different keys for different environments**
   - Development key for testing
   - Production key for live use

4. **Set up usage limits**
   - Monitor spending in the console
   - Set billing alerts to avoid surprises

## Troubleshooting

### "Authentication error" or "Invalid API key"
- Check that you copied the entire key
- Ensure no extra spaces in the `.env` file
- Verify the key starts with `sk-ant-api03-`

### "Insufficient credits"
- Add more credits at [console.anthropic.com/settings/billing](https://console.anthropic.com/settings/billing)

### "Rate limit exceeded"
- You're making too many requests too quickly
- Wait a few minutes and try again
- Consider upgrading your plan for higher limits

### "Model not found"
- Ensure you're using a valid model name
- Current models: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`, etc.

## Alternative: Using Without AI

If you don't want to use the AI features yet, the application works perfectly fine without them:
- Uses rule-based matching
- Keyword extraction
- Pattern matching
- Still very effective!

## Links

- **Anthropic Console**: [console.anthropic.com](https://console.anthropic.com)
- **API Documentation**: [docs.anthropic.com](https://docs.anthropic.com)
- **Pricing**: [anthropic.com/pricing](https://www.anthropic.com/pricing)
- **Status Page**: [status.anthropic.com](https://status.anthropic.com)

## Need Help?

- Check the [Anthropic Documentation](https://docs.anthropic.com)
- Review the [AI Integration Guide](AI_INTEGRATION_GUIDE.md) in this project
- Contact Anthropic support via the console

---

**Ready to enable AI features?** Just add your API key to the `.env` file and restart your application!
