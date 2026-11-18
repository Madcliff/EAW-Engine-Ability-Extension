#!/usr/bin/env python3
"""Builds the unified engine research PDF from the Markdown docs: pandoc (Markdown -> one HTML page) + headless
Chromium (HTML -> PDF). Links between the docs become links inside the PDF; links to CSV files become plain text.

usage: python3 -I tools/build_research_pdf.py [OUT.pdf] [--version X.Y.Z]
       default OUT: dist/EAW-Engine-Research.pdf
needs: pandoc, chromium (or google-chrome / chrome)"""
import datetime, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# (path, short id): the order is the order of the PDF
DOCS = [
    ('docs/research/ENGINE.md', 'engine'),
    ('docs/CONFIG.md', 'config'),
    ('docs/FEATURES.md', 'features'),
    ('docs/research/ability_type_map.md', 'ability-type-map'),
    ('docs/research/engine_ability_classes.md', 'engine-ability-classes'),
    ('ability_expansion/CENSUS.md', 'census'),
    ('docs/ability_id_checks.md', 'ability-id-checks'),
    ('docs/exe_patch_4_ability_buttons_plan.md', 'button-patch-plan'),
    ('docs/research/ENGINE_INDEX.md', 'engine-index'),
]
CSS = """
@page { size: A4; margin: 16mm 14mm 18mm 14mm;
        @bottom-center { content: counter(page); font-size: 8pt; color: #666; } }
body { font-family: 'Noto Sans', 'DejaVu Sans', sans-serif; font-size: 9.5pt; line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 18pt; border-bottom: 2px solid #333; padding-bottom: 4px; page-break-before: always; margin-top: 0; }
h1.title { page-break-before: avoid; border: none; font-size: 26pt; margin-top: 30mm; }
.doc-start { page-break-before: always; }
h2 { font-size: 13pt; margin-top: 18px; border-bottom: 1px solid #bbb; }
h3 { font-size: 11pt; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.3pt; background: #f2f2f2; padding: 0 2px; }
pre { background: #f5f5f5; padding: 6px 8px; font-size: 8pt; white-space: pre-wrap; word-break: break-all; }
pre code { background: none; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 8pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th, td { border: 1px solid #ccc; padding: 2px 4px; vertical-align: top; overflow-wrap: break-word; }
td code { white-space: nowrap; }
td { max-width: 60%; }
th { background: #eee; }
a { color: #1a4d8f; text-decoration: none; }
nav#TOC { page-break-after: always; }
nav#TOC ul { list-style: none; padding-left: 14px; }
nav#TOC > ul > li { margin-top: 4px; font-weight: bold; }
nav#TOC > ul > li li { font-weight: normal; }
.subtitle, .date { color: #555; }
"""


def find_browser():
    for b in ('chromium', 'chromium-browser', 'google-chrome-stable', 'google-chrome', 'chrome'):
        if shutil.which(b):
            return shutil.which(b)
    sys.exit('needs chromium or google-chrome for the PDF step')


def rewrite(text, here, ids):
    """Point links to other included docs at their place in the PDF; CSV and other files become plain text."""
    def repl(m):
        label, target = m.group(1), m.group(2)
        if re.match(r'[a-z]+://', target) or target.startswith('#'):
            return m.group(0)
        path, _, frag = target.partition('#')
        full = os.path.normpath(os.path.join(ROOT, os.path.dirname(here), path))
        rel = os.path.relpath(full, ROOT)
        if rel in ids:
            return '[%s](#%s)' % (label, frag if frag else 'doc-' + ids[rel])
        return '%s (`%s`)' % (label, rel) if label.strip('`') != os.path.basename(rel) else '`%s`' % rel
    return re.sub(r'\[([^\]]*)\]\(([^)\s]+)\)', repl, text)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out = os.path.abspath(args[0]) if args else os.path.join(ROOT, 'dist', 'EAW-Engine-Research.pdf')
    ver = sys.argv[sys.argv.index('--version') + 1] if '--version' in sys.argv else None
    if ver in args:
        args.remove(ver)
        out = os.path.abspath(args[0]) if args else os.path.join(ROOT, 'dist', 'EAW-Engine-Research.pdf')
    if not shutil.which('pandoc'):
        sys.exit('needs pandoc')
    ids = {p: i for p, i in DOCS}
    parts = []
    for path, did in DOCS:
        full = os.path.join(ROOT, path)
        if not os.path.exists(full):
            print('skipped (missing): %s' % path)
            continue
        text = open(full, encoding='utf-8').read()
        # the doc's first heading becomes a chapter (h1) with a stable id; everything else keeps its level
        text = re.sub(r'\A\s*# (.+)', lambda m: '# %s {#doc-%s .doc-start}' % (m.group(1), did), text, count=1)
        # XML tags written bare in headings would be swallowed as HTML: show them as code
        text = re.sub(r'^(#+ .*)$', lambda m: re.sub(r'(?<!`)(</?[A-Za-z_][^<>`]*>)(?!`)', r'`\1`', m.group(1)),
                      text, flags=re.M)
        parts.append(rewrite(text, path, ids))
    sub = 'Star Wars: Empire at War – Forces of Corruption, StarWarsG.exe 1.121.859328 (64-bit Steam)'
    date = datetime.date.today().isoformat() + (' · extension v%s' % ver if ver else '')
    md = '\n\n'.join(parts)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src, css, html = (os.path.join(tmp, n) for n in ('all.md', 'style.css', 'all.html'))
        open(src, 'w', encoding='utf-8').write(md)
        open(css, 'w', encoding='utf-8').write(CSS)
        subprocess.run(['pandoc', src, '-f', 'gfm+attributes', '-t', 'html5', '-s', '--toc', '--toc-depth=2',
                        '--embed-resources', '--css', css,
                        '-M', 'title=EAW Engine Ability Extension: Engine Research',
                        '-M', 'subtitle=' + sub, '-M', 'date=' + date, '-o', html], check=True)
        r = subprocess.run([find_browser(), '--headless', '--disable-gpu', '--no-pdf-header-footer',
                            '--print-to-pdf=' + out, 'file://' + html], capture_output=True, text=True)
        if r.returncode or not os.path.exists(out):
            sys.exit('chromium failed:\n' + r.stderr[-2000:])
    print('wrote %s (%d KB)' % (os.path.relpath(out, ROOT), os.path.getsize(out) // 1024))


if __name__ == '__main__':
    main()
