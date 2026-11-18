"""Add the second-card control panel buttons to the tactical command bar model (i_tactical_controls.alo).

usage: alo_panel_buttons.py src.alo dst.alo
For every card column c (0..11) adds 8 bones zz_panel_CC_K (K = 0..7, a 2 x 4 grid filling the column's two card
slots, top row first), each a copy of zz_button_r8_00 (bone + attached mesh, a regular ability-button quad) moved to
its grid position. Column c's card slots are s_select_(2c) (top) and s_select_(2c+1) (bottom)."""
import struct, sys
src, dst = sys.argv[1], sys.argv[2]
b = open(src, 'rb').read()
TEMPLATE = 'special_button_00'   # stock button (mesh + collision as the engine made it); was zz_button_r8_00

def chunks(o, end):
    while o < end:
        cid, sz = struct.unpack_from('<II', b, o)
        sz &= 0x7fffffff
        yield cid, o, o + 8, o + 8 + sz
        o += 8 + sz
def hdr(cid, payload, container):
    return struct.pack('<II', cid, len(payload) | (0x80000000 if container else 0)) + payload

top = list(chunks(0, len(b)))
skel, conn = top[0], top[-1]
meshes = [c for c in top if c[0] == 0x400]
kids = list(chunks(skel[2], skel[3]))
bones = []
for cid, h, s, e in kids[1:]:
    name = data = None
    for c2, h2, s2, e2 in chunks(s, e):
        if c2 == 0x203: name = b[s2:e2].rstrip(b'\0').decode()
        if c2 == 0x206: data = b[s2:e2]
    bones.append((name, data))
bidx = {n: i for i, (n, _) in enumerate(bones)}
assert not any(n.startswith('zz_panel_') for n in bidx), 'panel bones already present'
def mesh_name(m):
    for c2, h2, s2, e2 in chunks(m[2], m[3]):
        if c2 == 0x401: return b[s2:e2].rstrip(b'\0').decode(), (h2, e2)
ck = list(chunks(conn[2], conn[3]))
attached = {}
for cid, h, s, e in ck[1:]:
    if cid != 0x602: continue
    d = b[s:e]; attached.setdefault(struct.unpack_from('<I', d, 8)[0], []).append(struct.unpack_from('<I', d, 2)[0])

T = (3, 7, 11)
def trans(d): return [struct.unpack_from('<f', d, 12 + t * 4)[0] for t in T]
tpl = bones[bidx[TEMPLATE]][1]
# depth: the engine's hit test takes the front-most collision mesh. The card buttons (s_select) sit at z 3.94 and the
# template at 2.11, i.e. behind the card, so the card took every click (and deselected the unit). Put the panel at the
# swap button's depth (4.86, in front of the card; the swap button's clicks work).
tz = trans(bones[bidx['zz_swap_00']][1])[2] if 'zz_swap_00' in bidx else trans(bones[bidx['s_select_00']][1])[2] + 1.0
new_bones, new_meshes, new_links = [], [], []
for c in range(12):
    cx = trans(bones[bidx['s_select_%02d' % (2 * c)]][1])[0]
    ytop = trans(bones[bidx['s_select_%02d' % (2 * c)]][1])[1]       # top card centre
    ybot = trans(bones[bidx['s_select_%02d' % (2 * c + 1)]][1])[1]   # bottom card centre
    step = (ytop - ybot) / 2.0                                       # one card = two button rows
    y0 = ytop + step / 2.0                                           # first (top) button row
    for k in range(8):
        name = 'zz_panel_%02d_%d' % (c, k)
        d = bytearray(tpl)
        x = cx + (-0.5 if k % 2 == 0 else 0.5) * step
        y = y0 - (k // 2) * step
        for t, v in zip(T, (x, y, tz)):
            struct.pack_into('<f', d, 12 + t * 4, v)
        new_bones.append((name, bytes(d)))
        for obj in attached.get(bidx[TEMPLATE], []):
            m = meshes[obj]
            mn, (nh, ne) = mesh_name(m)
            new_meshes.append(hdr(0x400, b[m[2]:nh] + hdr(0x401, name.encode() + b'\0', False) + b[ne:m[3]], True))
            new_links.append((len(meshes) + len(new_meshes) - 1, len(bones) + len(new_bones) - 1))

cnt = bytearray(b[kids[0][2]:kids[0][3]])
struct.pack_into('<I', cnt, 0, len(bones) + len(new_bones))
bone_chunks = b''.join(hdr(0x202, hdr(0x203, n.encode() + b'\0', False) + hdr(0x206, d, False), True) for n, d in new_bones)
new_skel = hdr(0x200, hdr(0x201, bytes(cnt), False) + b[kids[1][1]:skel[3]] + bone_chunks, True)
c601 = bytearray(b[ck[0][2]:ck[0][3]])
struct.pack_into('<I', c601, 2, len(meshes) + len(new_meshes))
links = b''.join(hdr(0x602, bytes([2, 4]) + struct.pack('<I', o) + bytes([3, 4]) + struct.pack('<I', bo), False) for o, bo in new_links)
new_conn = hdr(0x600, hdr(0x601, bytes(c601), False) + b[ck[1][1]:conn[3]] + links, True)
out = new_skel + b[meshes[0][1]:meshes[-1][3]] + b''.join(new_meshes) + new_conn
open(dst, 'wb').write(out)
print('%s: bones %d -> %d, meshes %d -> %d; button size step %.2f' % (dst, len(bones), len(bones) + len(new_bones),
      len(meshes), len(meshes) + len(new_meshes), step))
for n, d in (new_bones[0], new_bones[7], new_bones[-1]):
    print('  %s at %s' % (n, [round(v, 2) for v in trans(d)]))
