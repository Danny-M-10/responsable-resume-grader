# How to Get an OpenAI API Key

Follow these steps to get your OpenAI API key and enable AI-powered candidate evaluation.

## Step 1: Create an OpenAI Account

1. Go to [https://platform.openai.com](https://platform.openai.com)
2. Click "Sign Up" or "Log In" if you already have an account
3. Complete the registration process

## Step 2: Get Your API Key

1. After signing up, you'll be directed to the OpenAI Dashboard
2. Click on your profile icon (top right)
3. Select "API Keys" from the dropdown menu
4. Or go directly to: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
5. Click "Create new secret key"
6. Give it a name (e.g., "Candidate Ranking App")
7. Copy the key immediately - you won't be able to see it again!

## Step 3: Set Environment Variable

### macOS/Linux (Terminal):

```bash
# Add to your ~/.zshrc or ~/.bashrc for permanent setup
export OPENAI_API_KEY='sk-your-actual-key-here'

# Or set for current session only
export OPENAI_API_KEY='sk-your-actual-key-here'
```

### Windows (Command Prompt):

```cmd
set OPENAI_API_KEY=sk-your-actual-key-here
```

### Windows (PowerShell):

```powershell
$env:OPENAI_API_KEY="sk-your-actual-key-here"
```

## Step 4: Add Credits to Your Account

OpenAI requires you to add credits before using the API:

1. Go to [https://platform.openai.com/account/billing](https://platform.openai.com/account/billing)
2. Click "Add payment method"
3. Add credits (minimum $5 recommended for testing)

**GPT-4 Turbo Pricing (as of 2025):**
- Input: $10.00 per 1M tokens
- Output: $30.00 per 1M tokens
- Typical cost per candidate evaluation: ~$0.01-0.03

## Step 5: Verify Setup

Test that your API key is configured:

```bash
python -c "import os; print('API Key configured:', bool(os.getenv('OPENAI_API_KEY')))"
```

Or test the configuration module:

```python
from config import OpenAIConfig
print('OpenAI configured:', OpenAIConfig.is_configured())
```

## Troubleshooting

### "API key not found"
- Make sure you've set the environment variable correctly
- Restart your terminal/IDE after setting the variable
- Check that the variable name is exactly `OPENAI_API_KEY` (case-sensitive)

### "Insufficient credits"
- Add credits at [platform.openai.com/account/billing](https://platform.openai.com/account/billing)
- Check your usage at [platform.openai.com/usage](https://platform.openai.com/usage)

### "Rate limit exceeded"
- You've hit OpenAI's rate limits
- Wait a few minutes and try again
- Consider upgrading your account tier

## Model Information

**Default Model**: `gpt-4-turbo-preview` (GPT-4 Turbo)

You can change the model by setting the `OPENAI_MODEL` environment variable:
- `gpt-4-turbo-preview` - Latest GPT-4 Turbo (recommended)
- `gpt-4-0125-preview` - GPT-4 Turbo snapshot
- `gpt-3.5-turbo` - Faster, lower cost (less capable)

## Cost Management

Monitor your API usage:
- Dashboard: [platform.openai.com/usage](https://platform.openai.com/usage)
- Set usage limits: [platform.openai.com/account/billing/limits](https://platform.openai.com/account/billing/limits)

## Additional Resources

- **OpenAI Platform**: [platform.openai.com](https://platform.openai.com)
- **API Documentation**: [platform.openai.com/docs](https://platform.openai.com/docs)
- **Pricing**: [openai.com/pricing](https://openai.com/pricing)
- **Status Page**: [status.openai.com](https://status.openai.com)

## Need Help?

- Check the [OpenAI Documentation](https://platform.openai.com/docs)
- Visit the [OpenAI Community Forum](https://community.openai.com)
- Contact OpenAI support via the platform dashboard

