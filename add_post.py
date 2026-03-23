#!/usr/bin/env python3
"""
add_post.py — Add a new writing post to the site and push to GitHub.

Usage:
    python add_post.py my-essay.md

Markdown file format:
    ---
    title: My Essay Title
    category: personal          # or: professional
    eyebrow: Meditation         # label shown above title (optional, defaults to category)
    description: Short summary shown in the index listing.
    date: March 2026            # optional, defaults to current month/year
    ---

    Your essay content here. Blank lines between paragraphs.

    ## Section Heading

    More content.

    > A blockquote or pull quote.

Install markdown parser (recommended, one-time):
    pip install markdown
"""

import re
import sys
import os
import subprocess
from datetime import datetime

try:
    import markdown as md_lib
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False


def parse_frontmatter(text):
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not match:
        sys.exit("Error: No frontmatter found. File must start with ---")
    meta = {}
    for line in match.group(1).splitlines():
        if ':' in line:
            key, _, value = line.partition(':')
            meta[key.strip().lower()] = value.strip()
    body = text[match.end():]
    return meta, body


def md_to_html(text):
    if HAS_MARKDOWN:
        return md_lib.markdown(text, extensions=['extra'])
    # Basic fallback: paragraphs, ## headings, > blockquotes
    parts = []
    for para in re.split(r'\n{2,}', text.strip()):
        para = para.strip()
        if not para:
            continue
        if para.startswith('## '):
            parts.append(f'<h2>{para[3:].strip()}</h2>')
        elif para.startswith('# '):
            parts.append(f'<h2>{para[2:].strip()}</h2>')
        elif para.startswith('> '):
            parts.append(f'<blockquote>{para[2:].strip()}</blockquote>')
        else:
            parts.append(f'<p>\n          {para}\n        </p>')
    return '\n\n        '.join(parts)


def slug_from_title(title):
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    return re.sub(r'-+', '-', slug).strip('-')


def read_time(text):
    words = len(text.split())
    minutes = max(1, round(words / 200))
    return f'{minutes} min read'


def build_post_html(title, eyebrow, description, date_str, content_html):
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <meta name="description" content="{description}" />
    <link rel="stylesheet" href="../styles.css" />
  </head>
  <body>
    <main class="page page-sub">
      <nav class="nav">
        <a href="../index.html">Home</a>
        <a href="../personal/index.html">Personal</a>
        <a href="../professional/index.html">Professional</a>
      </nav>

      <header class="hero">
        <p class="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p class="lede">{description}</p>
        <p class="meta">{date_str}</p>
      </header>

      <article class="post">
        {content_html}
      </article>
    </main>
  </body>
</html>
"""


def update_index(index_path, filename, title, description):
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_item = (
        f'        <li>\n'
        f'          <a class="title" href="{filename}">{title}</a>\n'
        f'          <span class="meta">{description}</span>\n'
        f'        </li>\n'
    )

    marker = '<ul class="list">'
    if marker not in content:
        sys.exit(f'Error: Could not find <ul class="list"> in {index_path}')

    updated = content.replace(marker, marker + '\n' + new_item, 1)

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(updated)


def git_push(files, title):
    try:
        subprocess.run(['git', 'add'] + files, check=True)
        subprocess.run(['git', 'commit', '-m', f'Add post: {title}'], check=True)
        subprocess.run(['git', 'push'], check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(f'Git error: {e}')


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    md_file = sys.argv[1]
    if not os.path.exists(md_file):
        site_root = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(site_root, md_file),
            os.path.join(site_root, 'essay markdowns', md_file),
        ]
        found = next((p for p in candidates if os.path.exists(p)), None)
        if not found:
            sys.exit(f'Error: Could not find "{md_file}" in the site folder or "essay markdowns" folder.')
        md_file = found

    with open(md_file, 'r', encoding='utf-8') as f:
        raw = f.read()

    meta, body = parse_frontmatter(raw)

    title = meta.get('title') or sys.exit('Error: frontmatter missing "title"')
    category = meta.get('category', '').lower()
    if category not in ('personal', 'professional'):
        sys.exit('Error: frontmatter "category" must be "personal" or "professional"')

    eyebrow = meta.get('eyebrow', category.capitalize())
    description = meta.get('description', '')
    date_str = meta.get('date', datetime.now().strftime('%B %Y'))
    date_str = f'{date_str} · {read_time(body)}'

    content_html = md_to_html(body)
    slug = slug_from_title(title)
    filename = f'{slug}.html'

    site_root = os.path.dirname(os.path.abspath(__file__))
    post_path = os.path.join(site_root, category, filename)
    index_path = os.path.join(site_root, category, 'index.html')

    if os.path.exists(post_path):
        sys.exit(f'Error: {post_path} already exists. Rename the post or delete the file first.')

    post_html = build_post_html(title, eyebrow, description, date_str, content_html)
    with open(post_path, 'w', encoding='utf-8') as f:
        f.write(post_html)
    print(f'Created:  {category}/{filename}')

    update_index(index_path, filename, title, description)
    print(f'Updated:  {category}/index.html')

    git_push([os.path.join(category, filename), os.path.join(category, 'index.html')], title)
    print(f'Pushed to GitHub.')
    print(f'\nLive at: https://behramohabib.com/{category}/{filename}')


if __name__ == '__main__':
    main()
