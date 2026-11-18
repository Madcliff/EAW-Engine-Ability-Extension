#!/usr/bin/env python3
"""Writes docs/research/ENGINE_INDEX.md from the DLL source, so the reference can't drift from the code:

  1. config keys   every key each Data/zz_*.txt parser accepts, with the comment next to it in the source
  2. names         Mod_Multiplier / combat-mod names the aura keys mult= / mod= accept
  3. engine names  every named engine address (#define RVA_* / *_RVA) with its comment
  4. patch sites   the code-cave patches from patch_starwarsg.py (address, size, what)
  5. pages         memory the DLL allocates at fixed addresses (stubs, tables)
  6. address index every engine address (0x14xxxxxxx) the source mentions, by DLL function and line

usage: python3 -I tools/gen_engine_index.py          write the file
       python3 -I tools/gen_engine_index.py --check  exit 1 if the file is out of date (run before a release)
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _opt(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


SRC = _opt('--src', os.path.join(ROOT, 'dll', 'zz_ability_buttons.c'))         # --src / --out: index another copy
OUT = _opt('--out', os.path.join(ROOT, 'docs', 'research', 'ENGINE_INDEX.md'))  # of the source (e.g. a git revision)
IB = 0x140000000

PARSERS = [   # (file, parser function, how the line is split)
    ('zz_settings.txt', 'settings_line', 'name value'),
    ('zz_ability_types.txt', 'new_type_line', 'NEW_NAME key=value ...'),
    ('zz_auras.txt', 'aura_line', 'Name key=value ...'),
    ('zz_spell_books.txt', 'sb_line', 'UnitType pages'),
    ('zz_panel_buttons.txt', 'pcfg_line', 'UnitType SLOT ICON ACTION'),
    ('zz_unit_swap.txt', 'swap_line', 'FROM_TYPE TO_TYPE'),
    ('zz_wide_cards.txt', 'wide_line', 'UnitType'),
    ('zz_galactic_ranges.txt', 'grange_line', 'Name range'),
]


def md(s):
    return s.replace('|', '\\|').strip()


def func_body(src, name):
    m = re.search(r'^static \w+ %s\([^;{]*\)\s*\{' % re.escape(name), src, re.M)
    if not m:
        return None, 0
    i, depth = m.end(), 1
    while depth:
        c = src[i]
        depth += c == '{'
        depth -= c == '}'
        i += 1
    return src[m.start():i], src.count('\n', 0, m.start()) + 1


def line_comment(lines, i):
    """The /* ... */ comment on line i, continued over following comment-only lines."""
    m = re.search(r'/\*(.*?)(\*/|$)', lines[i])
    if not m:
        return ''
    text, closed = [m.group(1)], bool(m.group(2))
    j = i + 1
    while not closed and j < len(lines):
        t = lines[j].strip()
        closed = '*/' in t
        text.append(t.split('*/')[0])
        j += 1
    return ' '.join(' '.join(text).split())


def decl_comment(lines, target, struct_range, key):
    """Comment on the declaration of what a parser line assigns (a global g_X, or a field of the struct in
    struct_range), kept only when it names the key, so one comment shared by several fields isn't misattributed."""
    names = re.compile(r'\b%s\b' % re.escape(key), re.I)
    if target.startswith('g_'):
        cands = [i for i, l in enumerate(lines) if re.match(r'static\b[^(=;]*\b%s\b[^(;]*(=[^;]*)?;' % re.escape(target), l)]
    elif struct_range:
        cands = [i for i in range(*struct_range)
                 if re.search(r'\b%s\b' % re.escape(target), lines[i].split('/*')[0]) and ';' in lines[i].split('/*')[0]]
    else:
        cands = []
    for i in cands:
        c = line_comment(lines, i)
        if names.search(c):
            return c
    return ''


def struct_range(lines, name):
    for i, l in enumerate(lines):
        if re.match(r'\}\s*%s\s*;' % re.escape(name), l):
            j = i
            while j > 0 and not lines[j].startswith('typedef struct'):
                j -= 1
            return (j, i)
    return None


def function_of(lines):
    """Enclosing top-level function (or the last one before) for every line."""
    starts = []
    for l in lines:
        m = re.match(r'(?:static\s+|__declspec\(\w+\)\s+)*[A-Za-z_][\w\s\*]*?\b(\w+)\s*\([^;]*$', l)
        ok = m and not l.startswith(('#', ' ', '\t', '/', '}')) and m.group(1) not in ('if', 'for', 'while', 'switch')
        starts.append(m.group(1) if ok else None)
    prev, cur = [], ''
    for n in starts:
        cur = n or cur
        prev.append(cur)
    nxt, cur = [''] * len(lines), ''
    for i in range(len(lines) - 1, -1, -1):
        cur = starts[i] or cur
        nxt[i] = cur
    out, in_top_comment = [], False      # a comment block at column 0 describes the function after it
    for i, l in enumerate(lines):
        if not in_top_comment and l.startswith('/*'):
            in_top_comment = True
        out.append(nxt[i] if in_top_comment else prev[i])
        if in_top_comment and '*/' in l:
            in_top_comment = False
    return out


def main():
    src = open(SRC, encoding='utf-8').read()
    lines = src.split('\n')
    func = function_of(lines)
    o = ['# Engine index (generated)', '',
         'Generated by `tools/gen_engine_index.py` from `dll/zz_ability_buttons.c` and `patch_starwarsg.py`. Do not edit',
         'by hand: change the source comments and rerun the script. The narrative reference is [ENGINE.md](ENGINE.md).',
         'Addresses are virtual addresses in StarWarsG.exe 1.121.859328 (image base 0x140000000); "line" is the line in',
         '`dll/zz_ability_buttons.c`.', '']

    # 1. config keys
    o += ['## 1. Config file keys', '']
    for fname, fn, shape in PARSERS:
        body, start = func_body(src, fn)
        if body is None:
            o += ['### `%s`' % fname, '', '*parser `%s` not found*' % fn, '']
            continue
        o += ['### `%s`' % fname, '', 'Line shape: `%s` (parser `%s`, line %d).' % (shape, fn, start), '']
        rows, seen = [], set()
        blines = body.split('\n')
        srange = struct_range(lines, 'aura_def') if fn == 'aura_line' else None
        for k, bl in enumerate(blines):
            for key in re.findall(r'eq_ci\((?:key|w\[0\])\s*,\s*"([^"]+)"\)', bl):
                if key in seen:
                    continue
                seen.add(key)
                c = line_comment(lines, start + k - 1)
                if not c:
                    t = re.search(r'(?:d->|\]\.)(\w+)\s*=|\b(g_\w+)\s*=', bl.split('eq_ci(', 1)[1])
                    if t:
                        c = decl_comment(lines, t.group(1) or t.group(2), srange, key)
                rows.append((key, start + k, c))
        if rows:
            o += ['| Key | Line | Source comment |', '|---|---|---|']
            o += ['| `%s` | %d | %s |' % (k, n, md(c)) for k, n, c in rows]
        else:
            o += ['Positional fields only (no keys); see [CONFIG.md](../CONFIG.md).']
        o.append('')

    # 2. names for mult= / mod=
    o += ['## 2. Names for `mult=` and `mod=`', '']
    for arr, what in (('MULT_NAMES', '`mult=NAME:value` (as XML `<Mod_Multiplier>`), index = engine multiplier id'),
                      ('MOD_NAMES', '`mod=NAME:value` (combat-mod dispatcher), index = COMBAT_MOD id')):
        m = re.search(r'%s\[\]\s*=\s*\{(.*?)\};' % arr, src, re.S)
        if m:
            names = re.findall(r'"([^"]+)"', m.group(1))
            o += ['%s:' % what, '', ', '.join('%d `%s`' % (i + 1, n) for i, n in enumerate(names)), '']

    # 3. named engine addresses
    o += ['## 3. Named engine addresses', '', '| Name | Address | Line | Comment |', '|---|---|---|---|']
    for i, l in enumerate(lines):
        m = re.match(r'#define\s+(\w*RVA\w*)\s+0x([0-9a-fA-F]+)u?\b', l)
        if m:
            o.append('| `%s` | 0x%x | %d | %s |' % (m.group(1), IB + int(m.group(2), 16), i + 1, md(line_comment(lines, i))))
    o.append('')

    # 4. code-cave patch sites
    o += ['## 4. Code patch sites (`patch_starwarsg.py`)', '']
    try:
        sys.path.insert(0, ROOT)
        import patch_starwarsg as p
        o += ['Applied in memory by the DLL (via `dll/patch_data.h`); every original byte is checked first.', '',
              '| Address | Bytes | What |', '|---|---|---|']
        o += ['| 0x%x | %d | %s |' % (va, len(ob), md(d)) for va, ob, nb, d in p.PATCHES]
        o += ['', 'Code cave at 0x%x, `.zzpatch` code at RVA 0x%x.' % (p.CAVE_VA, p.ZZ_VA_RVA), '']
    except Exception as e:    # keep the rest of the index usable
        o += ['*could not import patch_starwarsg.py: %s*' % e, '']

    # 6 (written before 5 so the long index stays last): pages the DLL allocates at fixed RVAs
    hdr = ''.join(open(os.path.join(ROOT, 'dll', h), encoding='utf-8').read() for h in ('patch_data.h',)
                  if os.path.exists(os.path.join(ROOT, 'dll', h)))
    defs = {m.group(1): int(m.group(2), 16) for m in re.finditer(r'#define\s+(\w+)\s+0x([0-9a-fA-F]+)u?\b', hdr + src)}
    pages = []
    for i, l in enumerate(lines):
        m = re.search(r'VirtualAlloc\(base \+ (\w+)u?,\s*(0x[0-9a-fA-F]+|\w+)', l)
        if m:
            a = m.group(1).rstrip('u')
            rva = int(a, 16) if a.startswith('0x') else defs.get(a)
            size = m.group(2)
            size = int(size, 16) if size.startswith('0x') else defs.get(size)
            if rva is not None:
                pages.append((rva, size, a, func[i], i + 1))
    o += ['## 5. DLL pages at fixed addresses', '',
          'Pages the DLL allocates right after the exe image (stubs must stay within 2 GB of the code they jump from).',
          'A new hook needs its own free 64 KB allocation unit: pick an address not listed here.', '',
          '| RVA | Address | Size | Name | Function | Line |', '|---|---|---|---|---|---|']
    o += ['| 0x%x | 0x%x | %s | `%s` | %s | %d |' % (r, IB + r, '0x%x' % z if z else '?', a, md(sc), n)
          for r, z, a, sc, n in sorted(pages)]
    o.append('')

    # 6. address index
    o += ['## 6. Address index', '',
          'Every engine address written in the source, in address order, with the DLL functions that mention it.', '',
          '| Address | Functions | Lines |', '|---|---|---|']
    idx = {}
    for i, l in enumerate(lines):
        for a in re.findall(r'\b0x(14[0-9a-fA-F]{7})\b', l):
            idx.setdefault(int(a, 16), []).append(i + 1)
    for a in sorted(idx):
        ls, fns = idx[a], []
        for n in ls:
            if func[n - 1] and func[n - 1] not in fns:
                fns.append(func[n - 1])
        o.append('| 0x%x | %s | %s |' % (a, ', '.join('`%s`' % f for f in fns[:5]) + (' …' if len(fns) > 5 else ''),
                                         ', '.join(map(str, ls[:8])) + (' …' if len(ls) > 8 else '')))
    o.append('')

    text = '\n'.join(o)
    if '--check' in sys.argv:
        cur = open(OUT, encoding='utf-8').read() if os.path.exists(OUT) else ''
        if cur != text:
            print('docs/research/ENGINE_INDEX.md is out of date: run python3 -I tools/gen_engine_index.py')
            return 1
        print('docs/research/ENGINE_INDEX.md is up to date')
        return 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w', encoding='utf-8').write(text)
    print('wrote %s (%d config keys, %d addresses)' % (os.path.relpath(OUT, ROOT),
          sum(1 for l in o if l.startswith('| `') and '|' in l[3:]), len(idx)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
