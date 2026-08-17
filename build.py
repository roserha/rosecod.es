#!/usr/bin/env python3
"""
Build script for rosecod.es.

This site has no other build step — the .html files in this repo ARE the
source. The only thing this script does is stitch the shared nav/footer
partials (in _includes/) into each page, and copy everything else as-is
into _site/, which is what actually gets published to GitHub Pages.

To preview the built site locally:
    python3 build.py
    cd _site && python3 -m http.server 8000

Runs automatically on every push via .github/workflows/deploy.yml — you
don't need to run this yourself before pushing, but it's here if you want
to check your changes before they go live.
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
INCLUDES = ROOT / "_includes"
OUT = ROOT / "_site"

# Paths that are never part of the built site.
EXCLUDE_DIRS = {"_includes", "_site", ".github", ".git", "node_modules"}
EXCLUDE_FILES = {"build.py", "README.md", ".gitignore"}

# Active-page hrefs, keyed by the "active" attribute used in each page's
# <!--#include nav active="..."--> marker.
NAV_ACTIVE_HREFS = {
    "home": "/",
    "projects": "/projects",
    "experience": "/experience",
    "hobbies": "/hobbies",
}

INCLUDE_RE = re.compile(r'<!--#include (\w+)(.*?)-->')
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')


def render_nav(active):
    nav = (INCLUDES / "nav.html").read_text(encoding="utf-8")
    href = NAV_ACTIVE_HREFS.get(active)
    if href is None:
        raise ValueError(f'unknown nav active="{active}"')
    # Add " active" to the <li> and <a> whose href matches the current page.
    # The href match must be exact (not a prefix) so "/" doesn't match every page.
    pattern = re.compile(
        r'<li class="([^"]*)">(\s*)<a href="' + re.escape(href) + r'" class="([^"]*)"'
    )
    def add_active(m):
        li_classes, whitespace, a_classes = m.groups()
        return f'<li class="{li_classes} active">{whitespace}<a href="{href}" class="{a_classes} active"'
    nav, n = pattern.subn(add_active, nav, count=1)
    if n == 0:
        raise ValueError(f'nav active="{active}" (href={href}) did not match any nav link')
    return nav


def render_footer():
    return (INCLUDES / "footer.html").read_text(encoding="utf-8")


def render_includes(text):
    def replace(m):
        name, attrs_str = m.group(1), m.group(2)
        attrs = dict(ATTR_RE.findall(attrs_str))
        if name == "nav":
            return render_nav(attrs.get("active"))
        if name == "footer":
            return render_footer()
        raise ValueError(f"unknown include: {name}")
    return INCLUDE_RE.sub(replace, text)


def should_skip(path: Path) -> bool:
    rel_parts = path.relative_to(ROOT).parts
    if any(part in EXCLUDE_DIRS for part in rel_parts):
        return True
    if path.is_file() and path.name in EXCLUDE_FILES:
        return True
    return False


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    html_count = 0
    copy_count = 0
    for path in ROOT.rglob("*"):
        if path.is_dir() or should_skip(path):
            continue
        rel = path.relative_to(ROOT)
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".html":
            text = path.read_text(encoding="utf-8")
            dest.write_text(render_includes(text), encoding="utf-8")
            html_count += 1
        else:
            shutil.copy2(path, dest)
            copy_count += 1

    print(f"built {html_count} html page(s), copied {copy_count} static file(s) -> {OUT}")


if __name__ == "__main__":
    build()
