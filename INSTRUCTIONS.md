# Publishing a New Post

## One-time setup

Install the Markdown parser (recommended):
```bash
pip install markdown
```

## Every time you publish

Create a `.md` file anywhere on your computer with this format at the top:

```markdown
---
title: Your Post Title
category: personal
eyebrow: Meditation
description: One line shown in the index listing.
date: March 2026
---

Your essay here. Blank line between paragraphs.

## A section heading

More writing.

> A pull quote if you want one.
```

**Fields:**
- `title` — required
- `category` — required, either `personal` or `professional`
- `eyebrow` — optional label shown above the title (defaults to the category name)
- `description` — short summary shown in the index listing
- `date` — optional, defaults to current month and year

Then run from the site folder:
```bash
python add_post.py path/to/your-essay.md
```

The script will:
1. Create the HTML post in the right folder
2. Add it to the top of the category index
3. Commit and push to GitHub

Your post will be live at `https://behramohabib.com/{category}/{post-title-as-slug}.html` within ~30 seconds.
