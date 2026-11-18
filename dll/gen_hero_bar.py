"""Generate hero_bar_data.h: byte patches that move the hero bar (top-right hero portraits, galactic + tactical)
from its stock component ids 0x27d..0x2aa (2 rows, 11 slots per side) to a new block of ids at the end of the
DLL's enlarged component table with 22 slots per side (4 rows).

Stock id layout (component table 0x140a174e0):            new layout (G = HERO_BAR_FIRST_SLOT):
  0x27d       good_hero_frame                               G-1         good_hero_frame
  0x27e-0x288 hero_slot_good00..10                          G..G+21     hero_slot_good00..21
  0x289-0x293 hero_hb_good00..10                            G+22..G+43  hero_hb_good00..21
  0x294       evil_hero_frame                               G+44        evil_hero_frame
  0x295-0x29f hero_slot_evil00..10                          G+45..G+66  hero_slot_evil00..21
  0x2a0-0x2aa hero_hb_evil00..10                            G+67..G+88  hero_hb_evil00..21

Every site's original instruction bytes are read from the stock exe here and checked again by the DLL at runtime.
usage: gen_hero_bar.py [path/to/StarWarsG.exe]   (default: the Steam install)"""
import os, struct, sys

EXE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    '~/.local/share/Steam/steamapps/common/Star Wars Empire at War/corruption/StarWarsG.exe')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hero_bar_data.h')

FIRST_NEW = 1229                 # first free id after the ability rows, swap buttons and panel (965 + 6*24 + 24 + 96)
G = FIRST_NEW + 1                # hero_slot_good00
SLOTS = 22
ID_MAP = {0x27d: G - 1, 0x27e: G, 0x288: G + SLOTS - 1, 0x289: G + SLOTS, 0x293: G + 2 * SLOTS - 1,
          0x294: G + 2 * SLOTS, 0x295: G + 2 * SLOTS + 1, 0x29f: G + 3 * SLOTS, 0x2a0: G + 3 * SLOTS + 1,
          0x2aa: G + 4 * SLOTS}
TOTAL_NEW = 4 * SLOTS + 2        # 90 entries: G-1 .. G+88

# (va, instruction length, offset of the constant, size of the constant, stock value (signed), new value, note)
S = []
def imm(va, ln, off, old, note, size=4):            # id immediate / disp32 that is an id
    S.append((va, ln, off, size, old, ID_MAP[old], note))
def neg(va, ln, off, old, new, note, size=4):       # negative displacement
    S.append((va, ln, off, size, old, new, note))

# mouse-over router: hero_slot_good range check
neg(0x1402e1044, 6, 2, -0x27e, -G, 'tooltip: lea eax,[rcx-good00]')
neg(0x1402e104a, 3, 2, 0xa, SLOTS - 1, 'tooltip: cmp eax,slots-1', size=1)
# init: one effect object per slot (count = group size of hero_slot_good00 / evil00)
imm(0x1402fa8d6, 5, 1, 0x27e, 'init: group count good')
imm(0x1402fa9bd, 5, 1, 0x295, 'init: group count evil')
# frame colour
imm(0x1402fcc25, 5, 1, 0x27d, 'frame colour: good frame')
imm(0x1402fcc6c, 5, 1, 0x294, 'frame colour: evil frame')
# clear-all loop
imm(0x140306c2d, 5, 1, 0x27e, 'clear: first good')
imm(0x140306c4e, 6, 2, 0x288, 'clear: last good')
imm(0x140306c56, 5, 1, 0x295, 'clear: first evil')
imm(0x140306c7c, 6, 2, 0x29f, 'clear: last evil')
# timer list mode (0x140311xxx)
imm(0x140311615, 5, 1, 0x289, 'timer: first good bar')
imm(0x140311635, 6, 2, 0x293, 'timer: last good bar')
imm(0x14031163d, 5, 1, 0x2a0, 'timer: first evil bar')
imm(0x140311657, 6, 2, 0x2aa, 'timer: last evil bar')
imm(0x14031165f, 5, 1, 0x27d, 'timer: good frame')
imm(0x1403116cb, 5, 1, 0x27e, 'timer: first good')
neg(0x140311800, 8, 4, -0x13f0, -8 * G, 'timer: effect index [id*8-good00*8]')
imm(0x140311813, 6, 2, 0x288, 'timer: last good')
imm(0x14031189f, 6, 2, 0x288, 'timer: last good (hide rest)')
neg(0x1403118aa, 8, 4, -0x13f0, -8 * G, 'timer: effect index (hide rest)')
imm(0x1403118ee, 6, 2, 0x288, 'timer: last good (hide loop)')
imm(0x1403118f6, 5, 1, 0x295, 'timer: first evil')
imm(0x14031193c, 6, 2, 0x29f, 'timer: last evil')
imm(0x140311954, 5, 1, 0x27e, 'timer off: first good')
imm(0x14031199c, 6, 2, 0x288, 'timer off: last good')
imm(0x1403119a4, 5, 1, 0x295, 'timer off: first evil')
imm(0x1403119ec, 6, 2, 0x29f, 'timer off: last evil')
# hero list fill (0x14031af30)
imm(0x14031af55, 5, 1, 0x27e, 'fill: first good')
imm(0x14031af72, 6, 2, 0x295, 'fill: first evil')
neg(0x14031af7f, 3, 2, 0x22, 3 * SLOTS + 1, 'fill: evil bar = good00 + x', size=1)
neg(0x14031af86, 4, 3, 0xb, SLOTS, 'fill: good bar = good00 + x', size=1)
neg(0x14031afb2, 3, 2, 0x16, 2 * SLOTS, 'fill: evil frame = good00 + x', size=1)
imm(0x14031b022, 6, 2, 0x288, 'fill (no list): last good')
imm(0x14031b05d, 7, 3, 0x29f, 'fill (no list): last evil')
imm(0x14031b0f6, 6, 2, 0x288, 'fill: good slots full')
imm(0x14031b11b, 6, 2, 0x29f, 'fill: evil slots full')
imm(0x14031b3d9, 5, 1, 0x27e, 'fill: next hero')
neg(0x14031b3f8, 7, 3, -0x27e, -G, 'cleanup: good count')
neg(0x14031b3ff, 7, 3, -0x295, -(G + 2 * SLOTS + 1), 'cleanup: evil count')
imm(0x14031b440, 7, 3, 0x288, 'cleanup: last good')
neg(0x14031b44c, 8, 4, -0x13f0, -8 * G, 'cleanup: good effect index')
imm(0x14031b47f, 6, 2, 0x288, 'cleanup: last good (loop)')
imm(0x14031b487, 7, 3, 0x293, 'cleanup: last good bar')
imm(0x14031b4a7, 7, 3, 0x293, 'cleanup: last good bar (loop)')
imm(0x14031b4f4, 7, 3, 0x29f, 'cleanup: last evil')
neg(0x14031b500, 8, 4, -0x14a8, -8 * (G + 2 * SLOTS + 1), 'cleanup: evil effect index')
imm(0x14031b533, 6, 2, 0x29f, 'cleanup: last evil (loop)')
imm(0x14031b53b, 6, 2, 0x2aa, 'cleanup: last evil bar')
imm(0x14031b558, 6, 2, 0x2aa, 'cleanup: last evil bar (loop)')

D = open(EXE, 'rb').read()
pe = struct.unpack_from('<I', D, 0x3c)[0]
nsec = struct.unpack_from('<H', D, pe + 6)[0]; opt = struct.unpack_from('<H', D, pe + 20)[0]
secs = [struct.unpack_from('<IIII', D, pe + 24 + opt + 40 * i + 8) for i in range(nsec)]  # vsize, va, rsize, raw
def foff(rva):
    for vs, va, rs, raw in secs:
        if va <= rva < va + max(vs, rs): return rva - va + raw
    raise SystemExit('rva not in a section: %x' % rva)

lines = []
for va, ln, off, size, old, new, note in S:
    rva = va - 0x140000000
    b = D[foff(rva):foff(rva) + ln]
    fmt = '<i' if size == 4 else '<b'
    got = struct.unpack_from(fmt, b, off)[0]
    if got != old:
        raise SystemExit('site %x (%s): expected %x, found %x' % (va, note, old, got))
    nb = bytearray(b); struct.pack_into(fmt, nb, off, new)
    lines.append('    { 0x%xu, %d, {%s}, {%s} }, /* %s: %#x -> %#x */' % (
        rva, ln, ','.join('0x%02x' % x for x in b), ','.join('0x%02x' % x for x in nb), note, old, new))

with open(OUT, 'w') as f:
    f.write('/* generated by gen_hero_bar.py from the stock StarWarsG.exe - do not edit */\n')
    f.write('#define HERO_BAR_FIRST_ID   %du  /* good_hero_frame; hero_slot_good00 = +1 */\n' % FIRST_NEW)
    f.write('#define HERO_BAR_COUNT      %du  /* new table entries */\n' % TOTAL_NEW)
    f.write('#define HERO_BAR_SLOTS      %du  /* slots per side (stock 11) */\n' % SLOTS)
    f.write('#define HERO_BAR_STOCK_FIRST 0x27du /* stock good_hero_frame .. 0x2aa */\n')
    f.write('typedef struct { unsigned rva; unsigned char len, orig[8], new_[8]; } hero_bar_patch;\n')
    f.write('static const hero_bar_patch HERO_BAR_PATCHES[] = {\n' + '\n'.join(lines) + '\n};\n')
print('wrote', OUT, len(S), 'sites')
