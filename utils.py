"""
Utility functions for SEO Blog Optimizer
"""

import re
import html
from typing import List, Optional


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug
    - Lowercase
    - Replace spaces/special chars with hyphens
    - Remove consecutive hyphens
    """
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces and special characters with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    return text


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to max_length, adding suffix if truncated"""
    if len(text) <= max_length:
        return text
    
    # Truncate at word boundary
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.8:  # If space is reasonably close to end
        truncated = truncated[:last_space]
    
    return truncated + suffix


def extract_first_n_words(text: str, n: int = 100) -> str:
    """Extract first N words from text"""
    words = text.split()
    return ' '.join(words[:n])


def count_words(text: str) -> int:
    """Count words in text"""
    return len(text.split())


def contains_keyphrase(text: str, keyphrase: str, case_sensitive: bool = False) -> bool:
    """Check if text contains keyphrase"""
    if not case_sensitive:
        text = text.lower()
        keyphrase = keyphrase.lower()
    return keyphrase in text


def find_keyphrase_positions(text: str, keyphrase: str) -> List[int]:
    """Find all positions where keyphrase appears in text"""
    positions = []
    text_lower = text.lower()
    keyphrase_lower = keyphrase.lower()
    start = 0
    
    while True:
        pos = text_lower.find(keyphrase_lower, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + 1
    
    return positions


def clean_html(text: str) -> str:
    """Remove HTML tags from text"""
    # Simple regex-based removal (for basic HTML)
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = html.unescape(text)
    return text.strip()


def extract_text_from_html(html_content: str) -> str:
    """Extract plain text from HTML, preserving structure"""
    # Remove script and style tags
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Replace common HTML tags with newlines or spaces
    html_content = re.sub(r'<br[^>]*>', '\n', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'<p[^>]*>', '\n', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'</p>', '\n', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'<div[^>]*>', '\n', html_content, flags=re.IGNORECASE)
    
    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', html_content)
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Clean up whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newline
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single space
    
    return text.strip()


def format_meta_description(text: str, keyphrase: str, max_length: int = 160) -> str:
    """
    Format meta description with keyphrase
    Ensures keyphrase is included and description is within character limit
    """
    text = text.strip()
    
    # If already contains keyphrase and is short enough, return as-is
    if contains_keyphrase(text, keyphrase) and len(text) <= max_length:
        return text
    
    # Try to include keyphrase naturally
    if not contains_keyphrase(text, keyphrase):
        # Try adding keyphrase at the beginning
        candidate = f"{keyphrase}: {text}"
        if len(candidate) <= max_length:
            return candidate
        
        # Try adding at the end
        candidate = f"{text} {keyphrase}"
        if len(candidate) <= max_length:
            return candidate
    
    # Truncate to fit
    return truncate_text(text, max_length)


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text"""
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    # Replace multiple newlines (3+) with double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove trailing whitespace from lines
    lines = [line.rstrip() for line in text.split('\n')]
    return '\n'.join(lines)


def extract_headings_from_html(html_content: str) -> List[dict]:
    """
    Extract headings from HTML content
    Returns list of dicts with 'level', 'text', and 'tag' keys
    """
    headings = []
    
    # Pattern to match h1-h6 tags
    pattern = r'<h([1-6])[^>]*>(.*?)</h[1-6]>'
    
    for match in re.finditer(pattern, html_content, re.IGNORECASE | re.DOTALL):
        level = int(match.group(1))
        text = clean_html(match.group(2))
        headings.append({
            'level': level,
            'text': text,
            'tag': f'h{level}'
        })
    
    return headings


def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return pattern.match(url) is not None


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL"""
    match = re.match(r'https?://([^/]+)', url)
    return match.group(1) if match else None


