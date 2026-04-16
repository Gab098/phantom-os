#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantom_env import config_dir, opt_dir, user_state_dir


class ThemeManager:
    def __init__(self):
        self.themes_dir = opt_dir() / "themes"
        self.user_themes = user_state_dir() / "themes"
        self.bundled_themes = ROOT / "gui" / "themes"
        self.themes_dir.mkdir(parents=True, exist_ok=True)
        self.user_themes.mkdir(parents=True, exist_ok=True)
        
    def list_themes(self):
        themes = []
        for directory in [self.bundled_themes, self.themes_dir, self.user_themes]:
            if not directory.exists():
                continue
            for entry in directory.iterdir():
                if entry.is_dir() and (entry / "theme.json").exists():
                    themes.append(entry.name)
                elif entry.is_file() and entry.suffix == ".json":
                    themes.append(entry.stem)
        return sorted(set(themes))
        
    def apply_theme(self, name):
        sources = [
            self.bundled_themes / f"{name}.json",
            self.bundled_themes / name / "theme.json",
            self.themes_dir / f"{name}.json",
            self.themes_dir / name / "theme.json",
            self.user_themes / f"{name}.json",
            self.user_themes / name / "theme.json",
        ]
        source = next((path for path in sources if path.exists()), None)
        if source is None:
            return False, "Theme not found"
            
        with open(source) as f:
            theme = json.load(f)
            
        css_vars = self._generate_css(theme)
        
        theme_config_dir = config_dir() / "gui"
        theme_config_dir.mkdir(parents=True, exist_ok=True)
        (theme_config_dir / "theme.css").write_text(css_vars)
        
        return True, f"Applied: {name}"
        
    def _generate_css(self, theme):
        colors = theme.get("colors", {})
        return f""":root {{
  --bg-primary: {colors.get("bg_primary", "#2D2D2D")};
  --bg-secondary: {colors.get("bg_secondary", "#3D3D3D")};
  --fg-primary: {colors.get("fg_primary", "#F5F5F5")};
  --fg-secondary: {colors.get("fg_secondary", "#B0B0B0")};
  --accent: {colors.get("accent", "#26A269")};
  --accent-alt: {colors.get("accent_alt", "#2EC27E")};
  --warning: {colors.get("warning", "#F5C211")};
  --error: {colors.get("error", "#E01B24")};
  --success: {colors.get("success", "#26A269")};
}}

window, waybar, mako {{
  background: var(--bg-primary);
  color: var(--fg-primary);
  font-family: {theme.get("fonts", {}).get("ui", "Inter, sans-serif")};
}}

button, input {{
  border-radius: {theme.get("borders", {}).get("radius", "8px")};
  border: {theme.get("borders", {}).get("width", "1px")} solid var(--accent);
}}
"""
        
    def create_theme(self, name, colors):
        theme = {
            "name": name,
            "version": "0.1.0",
            "colors": colors,
            "fonts": {"ui": "Inter, sans-serif", "mono": "JetBrains Mono, monospace"},
            "borders": {"radius": "8px", "width": "1px"}
        }
        
        target = self.user_themes / name
        target.mkdir(parents=True, exist_ok=True)
        (target / "theme.json").write_text(json.dumps(theme, indent=2))
        
        print(f"Created theme: {name}")

if __name__ == "__main__":
    mgr = ThemeManager()
    print("Available themes:", mgr.list_themes())
