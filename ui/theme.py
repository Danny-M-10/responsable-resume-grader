"""
Design tokens for CROSSROADS Professional Services UI
Provides consistent design system for light and dark modes
"""

from typing import Dict, Any

# Brand colors (unchanged from existing)
BRAND_COLORS = {
    "blue": "#00A8CC",  # Primary brand blue
    "green": "#00A651",  # Success/accent green
    "brown": "#6B4423",  # Primary text color
    "black": "#000000",  # Black background
    "dark_gray": "#4A4A4A",  # Dark gray
}

# Light mode design tokens
LIGHT_TOKENS: Dict[str, Any] = {
    # Colors
    "colors": {
        "primary": BRAND_COLORS["blue"],
        "accent": BRAND_COLORS["green"],
        "success": BRAND_COLORS["green"],
        "warning": "#F39C12",
        "danger": "#E74C3C",
        "info": BRAND_COLORS["blue"],
        
        # Surfaces
        "surface": "#FFFFFF",
        "surface_elevated": "#F8FAFC",
        "surface_hover": "#F1F5F9",
        
        # Borders
        "border": "#E5E7EB",
        "border_hover": BRAND_COLORS["green"],
        "border_focus": BRAND_COLORS["blue"],
        
        # Text
        "text_primary": BRAND_COLORS["brown"],
        "text_secondary": "#4A4A4A",
        "text_muted": "#64748B",
        "text_inverse": "#FFFFFF",
        
        # Overlays
        "overlay": "rgba(0, 0, 0, 0.5)",
        "overlay_light": "rgba(0, 0, 0, 0.1)",
        
        # Focus ring
        "focus_ring": f"{BRAND_COLORS['blue']}40",  # 40 = 25% opacity in hex
    },
    
    # Spacing scale (rem units)
    "spacing": {
        "xs": "0.25rem",   # 4px
        "sm": "0.5rem",    # 8px
        "md": "1rem",      # 16px
        "lg": "1.5rem",    # 24px
        "xl": "2rem",      # 32px
        "2xl": "3rem",     # 48px
        "3xl": "4rem",     # 64px
    },
    
    # Typography
    "typography": {
        "font_family_serif": "'Times New Roman', 'Times', serif",
        "font_family_sans": "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
        "font_size_xs": "0.75rem",    # 12px
        "font_size_sm": "0.875rem",   # 14px
        "font_size_base": "1rem",     # 16px
        "font_size_lg": "1.125rem",   # 18px
        "font_size_xl": "1.25rem",    # 20px
        "font_size_2xl": "1.5rem",    # 24px
        "font_size_3xl": "1.875rem",  # 30px
        "font_size_4xl": "2.25rem",   # 36px
        "font_weight_normal": "400",
        "font_weight_medium": "500",
        "font_weight_semibold": "600",
        "font_weight_bold": "700",
        "line_height_tight": "1.25",
        "line_height_normal": "1.5",
        "line_height_relaxed": "1.75",
    },
    
    # Border radius
    "radius": {
        "none": "0",
        "sm": "0.25rem",   # 4px
        "md": "0.5rem",    # 8px
        "lg": "0.75rem",   # 12px
        "xl": "1rem",      # 16px
        "full": "9999px",
    },
    
    # Shadows
    "shadows": {
        "none": "none",
        "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
        "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
        "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
    },
    
    # Z-index scale
    "z_index": {
        "base": "0",
        "dropdown": "1000",
        "sticky": "1020",
        "fixed": "1030",
        "modal_backdrop": "1040",
        "modal": "1050",
        "popover": "1060",
        "tooltip": "1070",
    },
}

# Dark mode design tokens
DARK_TOKENS: Dict[str, Any] = {
    # Colors (dark mode optimized)
    "colors": {
        "primary": BRAND_COLORS["blue"],
        "accent": BRAND_COLORS["green"],
        "success": "#4ADE80",  # Lighter green for dark mode
        "warning": "#FBBF24",  # Lighter orange for dark mode
        "danger": "#F87171",   # Lighter red for dark mode
        "info": "#60A5FA",     # Lighter blue for dark mode
        
        # Surfaces (dark gray, not pure black)
        "surface": "#0F1115",      # Very dark gray
        "surface_elevated": "#151821",  # Slightly lighter
        "surface_hover": "#1A1D26",     # Hover state
        
        # Borders
        "border": "#2A2F3A",       # Medium dark gray
        "border_hover": BRAND_COLORS["green"],
        "border_focus": BRAND_COLORS["blue"],
        
        # Text (desaturated for readability)
        "text_primary": "#E6EAF2",     # Light gray
        "text_secondary": "#CBD5E1",   # Medium light gray
        "text_muted": "#A2A8B5",       # Muted light gray
        "text_inverse": "#0F1115",     # Dark for light backgrounds
        
        # Overlays
        "overlay": "rgba(0, 0, 0, 0.7)",
        "overlay_light": "rgba(0, 0, 0, 0.3)",
        
        # Focus ring
        "focus_ring": f"{BRAND_COLORS['blue']}60",  # 60 = 37.5% opacity
    },
    
    # Spacing, typography, radius, shadows, z-index same as light mode
    "spacing": LIGHT_TOKENS["spacing"],
    "typography": LIGHT_TOKENS["typography"],
    "radius": LIGHT_TOKENS["radius"],
    "shadows": {
        "none": "none",
        "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.3)",
        "md": "0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3)",
        "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3)",
        "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 10px 10px -5px rgba(0, 0, 0, 0.3)",
    },
    "z_index": LIGHT_TOKENS["z_index"],
}

# Score colors (semantic)
SCORE_COLORS = {
    "excellent": LIGHT_TOKENS["colors"]["success"],
    "good": LIGHT_TOKENS["colors"]["warning"],
    "poor": LIGHT_TOKENS["colors"]["danger"],
}

def get_tokens(theme: str = "light") -> Dict[str, Any]:
    """Get design tokens for specified theme"""
    return DARK_TOKENS if theme == "dark" else LIGHT_TOKENS

def get_css_variables(theme: str = "light") -> str:
    """Generate CSS variable declarations for specified theme"""
    tokens = get_tokens(theme)
    css_vars = []
    
    # Colors
    for key, value in tokens["colors"].items():
        css_key = key.replace("_", "-")
        css_vars.append(f"  --color-{css_key}: {value};")
    
    # Spacing
    for key, value in tokens["spacing"].items():
        css_vars.append(f"  --spacing-{key}: {value};")
    
    # Typography
    for key, value in tokens["typography"].items():
        css_key = key.replace("_", "-")
        css_vars.append(f"  --font-{css_key}: {value};")
    
    # Radius
    for key, value in tokens["radius"].items():
        css_vars.append(f"  --radius-{key}: {value};")
    
    # Shadows
    for key, value in tokens["shadows"].items():
        css_vars.append(f"  --shadow-{key}: {value};")
    
    # Z-index
    for key, value in tokens["z_index"].items():
        css_key = key.replace("_", "-")
        css_vars.append(f"  --z-{css_key}: {value};")
    
    # Brand colors (always available)
    for key, value in BRAND_COLORS.items():
        css_key = key.replace("_", "-")
        css_vars.append(f"  --brand-{css_key}: {value};")
    
    # Score colors
    for key, value in SCORE_COLORS.items():
        css_vars.append(f"  --score-{key}: {value};")
    
    return "\n".join(css_vars)

