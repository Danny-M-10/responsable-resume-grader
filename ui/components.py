"""
UI Components for ResponsAble
Reusable components using design tokens
"""

import streamlit as st
from typing import Optional, Dict, Any, List


def render_theme_toggle(current_theme: str = "light") -> None:
    """
    Render theme toggle using Streamlit button
    """
    is_dark = current_theme == "dark"
    toggle_label = "🌙 Dark Mode" if not is_dark else "☀️ Light Mode"
    
    if st.button(toggle_label, key="theme_toggle", use_container_width=True):
        new_theme = "dark" if not is_dark else "light"
        set_theme(new_theme)
        st.rerun()


def render_theme_script(current_theme: str = "light") -> str:
    """
    Render JavaScript to initialize theme and handle theme changes
    Returns HTML string with script
    """
    return f"""
    <script>
    (function() {{
        // Initialize theme from data-theme attribute or localStorage or OS preference
        const savedTheme = localStorage.getItem('responsable-theme');
        const osTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        const initialTheme = savedTheme || '{current_theme}' || osTheme;
        
        // Set initial theme
        if (initialTheme) {{
            document.documentElement.setAttribute('data-theme', initialTheme);
            localStorage.setItem('responsable-theme', initialTheme);
        }}
        
        // Listen for OS theme changes (if no saved preference)
        if (!savedTheme) {{
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {{
                const newTheme = e.matches ? 'dark' : 'light';
                document.documentElement.setAttribute('data-theme', newTheme);
            }});
        }}
    }})();
    </script>
    """


def get_initial_theme() -> str:
    """
    Get initial theme from session state, query params, or OS preference
    Returns 'light' or 'dark'
    """
    # Check session state first
    if 'theme' in st.session_state:
        return st.session_state['theme']
    
    # Check query params
    query_params = st.query_params
    if hasattr(query_params, 'get'):
        theme_param = query_params.get("theme")
        if theme_param:
            theme = theme_param[0] if isinstance(theme_param, list) else theme_param
            if theme in ['light', 'dark']:
                st.session_state['theme'] = theme
                return theme
    
    # Default to light (will be overridden by CSS media query if OS prefers dark)
    return 'light'


def set_theme(theme: str):
    """Set theme in session state and query params"""
    if theme not in ['light', 'dark']:
        return
    
    st.session_state['theme'] = theme
    # Update query params for persistence
    st.query_params['theme'] = theme


def inject_theme_css():
    """Inject theme CSS into the page"""
    css_path = "assets/theme.css"
    try:
        with open(css_path, 'r') as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # Fallback: use inline CSS from theme tokens
        from ui.theme import get_css_variables
        light_vars = get_css_variables("light")
        dark_vars = get_css_variables("dark")
        css_content = f"""
        <style>
        :root, :root[data-theme="light"] {{
        {light_vars}
        }}
        :root[data-theme="dark"] {{
        {dark_vars}
        }}
        </style>
        """
        st.markdown(css_content, unsafe_allow_html=True)


def render_badge(text: str, variant: str = "default", size: str = "md") -> str:
    """
    Render a badge component
    Variants: default, primary, success, warning, danger, info
    Sizes: sm, md, lg
    """
    variant_classes = {
        "default": "badge-default",
        "primary": "badge-primary",
        "success": "badge-success",
        "warning": "badge-warning",
        "danger": "badge-danger",
        "info": "badge-info",
    }
    size_classes = {
        "sm": "badge-sm",
        "md": "badge-md",
        "lg": "badge-lg",
    }
    
    badge_class = f"badge {variant_classes.get(variant, 'badge-default')} {size_classes.get(size, 'badge-md')}"
    
    return f"""
    <span class="{badge_class}">{text}</span>
    <style>
    .badge {{
        display: inline-flex;
        align-items: center;
        padding: var(--spacing-xs) var(--spacing-sm);
        border-radius: var(--radius-full);
        font-size: var(--font-size-xs);
        font-weight: var(--font-weight-medium);
        line-height: 1;
        white-space: nowrap;
    }}
    .badge-sm {{
        padding: 0.125rem 0.375rem;
        font-size: 0.625rem;
    }}
    .badge-md {{
        padding: var(--spacing-xs) var(--spacing-sm);
        font-size: var(--font-size-xs);
    }}
    .badge-lg {{
        padding: 0.375rem 0.75rem;
        font-size: var(--font-size-sm);
    }}
    .badge-default {{
        background: var(--color-surface-elevated);
        color: var(--color-text-primary);
        border: 1px solid var(--color-border);
    }}
    .badge-primary {{
        background: var(--color-primary);
        color: var(--color-text-inverse);
    }}
    .badge-success {{
        background: var(--color-success);
        color: var(--color-text-inverse);
    }}
    .badge-warning {{
        background: var(--color-warning);
        color: var(--color-text-inverse);
    }}
    .badge-danger {{
        background: var(--color-danger);
        color: var(--color-text-inverse);
    }}
    .badge-info {{
        background: var(--color-info);
        color: var(--color-text-inverse);
    }}
    </style>
    """


def render_card(title: Optional[str] = None, content: str = "", footer: Optional[str] = None, 
                variant: str = "default", key: Optional[str] = None) -> str:
    """
    Render a card component
    Variants: default, elevated, outlined
    """
    variant_classes = {
        "default": "card-default",
        "elevated": "card-elevated",
        "outlined": "card-outlined",
    }
    
    card_class = f"card {variant_classes.get(variant, 'card-default')}"
    card_id = f"card-{key}" if key else ""
    
    title_html = f'<div class="card-title">{title}</div>' if title else ""
    footer_html = f'<div class="card-footer">{footer}</div>' if footer else ""
    
    return f"""
    <div class="{card_class}" id="{card_id}">
        {title_html}
        <div class="card-content">{content}</div>
        {footer_html}
    </div>
    <style>
    .card {{
        background: var(--color-surface);
        border-radius: var(--radius-lg);
        padding: var(--spacing-lg);
        margin-bottom: var(--spacing-md);
        transition: all 0.2s ease;
    }}
    .card-elevated {{
        background: var(--color-surface-elevated);
        box-shadow: var(--shadow-md);
    }}
    .card-outlined {{
        border: 1px solid var(--color-border);
    }}
    .card:hover {{
        box-shadow: var(--shadow-lg);
    }}
    .card-title {{
        font-size: var(--font-size-lg);
        font-weight: var(--font-weight-semibold);
        color: var(--color-text-primary);
        margin-bottom: var(--spacing-md);
        padding-bottom: var(--spacing-sm);
        border-bottom: 1px solid var(--color-border);
    }}
    .card-content {{
        color: var(--color-text-primary);
        line-height: var(--line-height-relaxed);
    }}
    .card-footer {{
        margin-top: var(--spacing-md);
        padding-top: var(--spacing-md);
        border-top: 1px solid var(--color-border);
        color: var(--color-text-muted);
        font-size: var(--font-size-sm);
    }}
    </style>
    """


def render_skeleton(width: str = "100%", height: str = "1rem", variant: str = "text") -> str:
    """
    Render a skeleton loading placeholder
    Variants: text, circular, rectangular
    """
    variant_styles = {
        "text": "border-radius: var(--radius-sm);",
        "circular": "border-radius: var(--radius-full); width: " + height + "; height: " + height + ";",
        "rectangular": "border-radius: var(--radius-md);",
    }
    
    style = variant_styles.get(variant, variant_styles["text"])
    if variant != "circular":
        style += f" width: {width}; height: {height};"
    
    return f"""
    <div class="skeleton" style="{style}"></div>
    <style>
    .skeleton {{
        background: linear-gradient(
            90deg,
            var(--color-surface-elevated) 0%,
            var(--color-surface-hover) 50%,
            var(--color-surface-elevated) 100%
        );
        background-size: 200% 100%;
        animation: skeleton-loading 1.5s ease-in-out infinite;
    }}
    @keyframes skeleton-loading {{
        0% {{
            background-position: 200% 0;
        }}
        100% {{
            background-position: -200% 0;
        }}
    }}
    </style>
    """


def render_score_badge(score: float, show_label: bool = True) -> str:
    """
    Render a score badge with color coding
    """
    if score >= 8.0:
        variant = "success"
        label = "Excellent"
    elif score >= 6.0:
        variant = "warning"
        label = "Good"
    else:
        variant = "danger"
        label = "Needs Improvement"
    
    badge_text = f"{score:.2f}/10"
    if show_label:
        badge_text += f" ({label})"
    
    return render_badge(badge_text, variant=variant, size="md")

