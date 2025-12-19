# Unsplash API Integration Guide

## Overview

Your Unsplash API credentials have been securely added to this project. This guide shows you how to use the Unsplash API in your application.

## Credentials Stored

Your credentials are stored in the [.env](.env) file:
- **Application ID**: 808940
- **Access Key**: TvTR20TJm8upB1MaSb3lmtTE9NCftVsQhJQdLWZ2Ag
- **Secret Key**: MmAj2nEPvN_XvG3Z5TVG2v2Ik59beUzRVRT4jX88njg

**Important**: The `.env` file is automatically excluded from git commits (via [.gitignore](.gitignore)) to keep your API keys secure.

## Quick Start

### 1. Install Unsplash Library

```bash
source venv/bin/activate
pip install pyunsplash
```

### 2. Test Your Connection

```bash
python unsplash_example.py
```

### 3. Use in Your Code

```python
from config import UnsplashConfig
from pyunsplash import PyUnsplash

# Initialize API
api = PyUnsplash(api_key=UnsplashConfig.get_access_key())

# Search for photos
search = api.search(type_='photos', query='business professional')
photos = search.entries

# Get photo details
for photo in photos[:5]:
    print(f"Photo: {photo.id}")
    print(f"By: {photo.photographer_name}")
    print(f"URL: {photo.link_download}")
```

## Common Use Cases

### Search Photos

```python
from pyunsplash import PyUnsplash
from config import get_unsplash_access_key

api = PyUnsplash(api_key=get_unsplash_access_key())

# Search with specific query
search = api.search(type_='photos', query='office workspace', per_page=10)

for photo in search.entries:
    print(f"{photo.id}: {photo.link_html}")
```

### Get Random Photo

```python
# Get random photo with specific theme
photos = api.photos(type_='random', count=1, query='professional headshot')
photo = photos.entries[0]

print(f"Random photo URL: {photo.link_download}")
```

### Download Photo

```python
import requests

# Get photo
search = api.search(type_='photos', query='resume')
photo = search.entries[0]

# Download
response = requests.get(photo.link_download)
with open('downloaded_photo.jpg', 'wb') as f:
    f.write(response.content)
```

## Integration with Candidate Ranking App

Here are some ideas for integrating Unsplash into your candidate ranking application:

### 1. Professional Headers for PDFs

```python
# In pdf_generator.py
from config import UnsplashConfig
from pyunsplash import PyUnsplash

def get_header_image():
    """Get a professional header image for the PDF report."""
    if not UnsplashConfig.is_configured():
        return None

    api = PyUnsplash(api_key=UnsplashConfig.get_access_key())
    photos = api.photos(type_='random', count=1, query='business professional')
    return photos.entries[0].link_download if photos.entries else None
```

### 2. Company/Industry Images

```python
def get_industry_image(industry: str):
    """Get relevant image based on job industry."""
    api = PyUnsplash(api_key=UnsplashConfig.get_access_key())
    search = api.search(type_='photos', query=f'{industry} workplace', per_page=1)
    return search.entries[0].link_download if search.entries else None
```

### 3. Streamlit UI Enhancement

```python
# In app.py or app_enhanced.py
import streamlit as st
from pyunsplash import PyUnsplash
from config import UnsplashConfig

# Add background image to Streamlit app
if UnsplashConfig.is_configured():
    api = PyUnsplash(api_key=UnsplashConfig.get_access_key())
    photos = api.photos(type_='random', count=1, query='office minimalist')
    if photos.entries:
        st.image(photos.entries[0].link_download, use_container_width=True)
```

## API Limits

Unsplash has rate limits:
- **Demo/Development**: 50 requests per hour
- **Production**: 5000 requests per hour (requires approval)

Check your current usage at: https://unsplash.com/oauth/applications/808940

## Resources

- **Unsplash API Documentation**: https://unsplash.com/documentation
- **PyUnsplash Library**: https://github.com/salvoventura/pyunsplash
- **Your Application Dashboard**: https://unsplash.com/oauth/applications/808940

## Security Notes

1. Never commit the `.env` file to version control
2. Never share your Secret Key publicly
3. Use the Access Key for most operations
4. The Secret Key is only needed for OAuth flows
5. Rotate keys if they are ever exposed

## Configuration Module

The [config.py](config.py) module provides easy access to all API keys:

```python
from config import UnsplashConfig

# Check if configured
if UnsplashConfig.is_configured():
    access_key = UnsplashConfig.get_access_key()
    secret_key = UnsplashConfig.get_secret_key()
    app_id = UnsplashConfig.get_application_id()
```

## Example Files

- [config.py](config.py) - Configuration loader
- [unsplash_example.py](unsplash_example.py) - Example usage script
- [.env](.env) - Your API credentials (DO NOT COMMIT)
- [.gitignore](.gitignore) - Ensures .env is not committed

## Next Steps

1. Install pyunsplash: `pip install pyunsplash`
2. Run the example: `python unsplash_example.py`
3. Integrate images into your PDF reports
4. Add visual elements to your Streamlit interface
5. Apply for production rate limits if needed

---

**Questions or Issues?**
Check the [Unsplash API documentation](https://unsplash.com/documentation) or review the [PyUnsplash examples](https://github.com/salvoventura/pyunsplash/tree/master/examples).
