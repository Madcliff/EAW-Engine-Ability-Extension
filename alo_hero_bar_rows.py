"""Add rows 3 and 4 to a hero bar model (I_MAIN_HERO_FRAME_REBEL.ALO / _EMPIRE.ALO, stock files from
GameData/Data/models.meg) for the DLL's hero_bar_rows 4 feature.

usage: alo_hero_bar_rows.py src.alo dst.alo good|evil
Slot/bar k (11..21) = a copy of slot/bar k-11 (bone matrix incl. the empire model's mirroring, and for slots the
mesh), moved down by two row spacings (2 x 39.2 = the distance row 1 -> row 2, doubled). So row 3 repeats row 1
(6 slots) and row 4 repeats row 2 (5 slots, half-step offset), like the stock pattern."""
import struct, sys
src, dst, side = sys.argv[1:4]
DY = -2 * 39.2
b = open(src, 'rb').read()

def chunks(o, end):
    while o < end:
        cid, sz = struct.unpack_from('<II', b, o)
        sz &= 0x7fffffff
        yield cid, o, o + 8, o + 8 + sz
        o += 8 + sz
def hdr(cid, payload, container):
    return struct.pack('<II', cid, len(payload) | (0x80000000 if container else 0)) + payload

top = list(chunks(0, len(b)))
assert top[0][0] == 0x200 and top[-1][0] == 0x600
skel, conn = top[0], top[-1]
meshes = [c for c in top if c[0] == 0x400]
assert len(top) == 2 + len(meshes), 'unexpected top-level chunks'

kids = list(chunks(skel[2], skel[3])); assert kids[0][0] == 0x201
bones = []
for cid, h, s, e in kids[1:]:
    assert cid == 0x202
    name = data = None
    for c2, h2, s2, e2 in chunks(s, e):
        if c2 == 0x203: name = b[s2:e2].rstrip(b'\0').decode()
        if c2 == 0x206: data = b[s2:e2]
    assert data is not None and len(data) >= 60, name
    bones.append((name, data))
bidx = {n: i for i, (n, _) in enumerate(bones)}

def mesh_name(m):
    for c2, h2, s2, e2 in chunks(m[2], m[3]):
        if c2 == 0x401: return b[s2:e2].rstrip(b'\0').decode(), (h2, e2)
midx = {mesh_name(m)[0]: i for i, m in enumerate(meshes)}

new_bones, new_meshes, new_links = [], [], []
for kind in ('hero_slot_', 'hero_hb_'):
    for k in range(11, 22):
        tname, name = f'{kind}{side}{k - 11:02d}', f'{kind}{side}{k:02d}'
        assert name not in bidx, name + ' already present'
        d = bytearray(bones[bidx[tname]][1])
        y = struct.unpack_from('<f', d, 12 + 7 * 4)[0]          # matrix row 2, column 4 = translation y
        struct.pack_into('<f', d, 12 + 7 * 4, y + DY)
        struct.pack_into('<I', d, 0, 0)                         # parent = Root, like every stock slot/bar bone
        new_bones.append((name, bytes(d)))
        if tname in midx:                                        # slots have a mesh, bars don't
            m = meshes[midx[tname]]
            _, (nh, ne) = mesh_name(m)
            new_meshes.append(hdr(0x400, b[m[2]:nh] + hdr(0x401, name.encode() + b'\0', False) + b[ne:m[3]], True))
            new_links.append((len(meshes) + len(new_meshes) - 1, len(bones) + len(new_bones) - 1))

cnt = bytearray(b[kids[0][2]:kids[0][3]])
assert struct.unpack_from('<I', cnt, 0)[0] == len(bones)
struct.pack_into('<I', cnt, 0, len(bones) + len(new_bones))
bone_chunks = b''.join(hdr(0x202, hdr(0x203, n.encode() + b'\0', False) + hdr(0x206, d, False), True)
                       for n, d in new_bones)
new_skel = hdr(0x200, hdr(0x201, bytes(cnt), False) + b[kids[1][1]:skel[3]] + bone_chunks, True)

ck = list(chunks(conn[2], conn[3])); assert ck[0][0] == 0x601
c601 = bytearray(b[ck[0][2]:ck[0][3]]); assert c601[0] == 1 and c601[1] == 4
assert struct.unpack_from('<I', c601, 2)[0] == len(meshes)
struct.pack_into('<I', c601, 2, len(meshes) + len(new_meshes))
links = b''.join(hdr(0x602, bytes([2, 4]) + struct.pack('<I', o) + bytes([3, 4]) + struct.pack('<I', bo), False)
                 for o, bo in new_links)
new_conn = hdr(0x600, hdr(0x601, bytes(c601), False) + b[ck[1][1]:conn[3]] + links, True)

out = new_skel + b[meshes[0][1]:meshes[-1][3]] + b''.join(new_meshes) + new_conn
open(dst, 'wb').write(out)
print(f'{dst}: bones {len(bones)}->{len(bones) + len(new_bones)}, meshes {len(meshes)}->{len(meshes) + len(new_meshes)}')
