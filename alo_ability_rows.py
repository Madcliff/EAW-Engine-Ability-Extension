"""Add ability-button rows to the tactical command bar model (i_tactical_controls.alo) for the DLL's extra rows.

usage: alo_ability_rows.py src.alo dst.alo FIRST_NEW_ROW COUNT
Row r (FIRST_NEW_ROW .. FIRST_NEW_ROW+COUNT-1) bone zz_button_r<r>_NN = a copy of zz_button_r<last>_NN (last = the
highest row already in the model), moved by (r - last) times that bone's own row step (row last minus row last-1, so
the spacing and any slant of the existing rows continue). Meshes attached to the copied bones are copied too.
Example: rows 7 and 8 from rows 5/6:  alo_ability_rows.py i_tactical_controls.alo out.alo 7 2"""
import struct, sys
src, dst, first, count = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
last = first - 1
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
assert top[0][0] == 0x200 and top[-1][0] == 0x600, [hex(c[0]) for c in top]
skel, conn = top[0], top[-1]
meshes = [c for c in top if c[0] == 0x400]
assert len(top) == 2 + len(meshes), 'unexpected top-level chunks: ' + str([hex(c[0]) for c in top])

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
# which bone each mesh is attached to (0x602: object index -> bone index)
ck = list(chunks(conn[2], conn[3])); assert ck[0][0] == 0x601
attached = {}
for cid, h, s, e in ck[1:]:
    if cid != 0x602: continue
    d = b[s:e]; obj = struct.unpack_from('<I', d, 2)[0]; bone = struct.unpack_from('<I', d, 8)[0]
    attached.setdefault(bone, []).append(obj)

T = (3, 7, 11)                                           # translation x, y, z in the 3x4 matrix after the 12-byte header
def trans(d): return [struct.unpack_from('<f', d, 12 + t * 4)[0] for t in T]
new_bones, new_meshes, new_links = [], [], []
for r in range(first, first + count):
    for k in range(24):
        tn, pn, name = f'zz_button_r{last}_{k:02d}', f'zz_button_r{last - 1}_{k:02d}', f'zz_button_r{r}_{k:02d}'
        assert name not in bidx, name + ' already present'
        assert tn in bidx and pn in bidx, 'template rows missing: ' + tn
        d = bytearray(bones[bidx[tn]][1])
        a, p = trans(bones[bidx[tn]][1]), trans(bones[bidx[pn]][1])
        for t, v, w in zip(T, a, p):
            struct.pack_into('<f', d, 12 + t * 4, v + (r - last) * (v - w))
        new_bones.append((name, bytes(d)))
        for obj in attached.get(bidx[tn], []):           # meshes on the template bone
            m = meshes[obj]
            mn, (nh, ne) = mesh_name(m)
            new_meshes.append(hdr(0x400, b[m[2]:nh] + hdr(0x401, name.encode() + b'\0', False) + b[ne:m[3]], True))
            new_links.append((len(meshes) + len(new_meshes) - 1, len(bones) + len(new_bones) - 1))

cnt = bytearray(b[kids[0][2]:kids[0][3]])
assert struct.unpack_from('<I', cnt, 0)[0] == len(bones)
struct.pack_into('<I', cnt, 0, len(bones) + len(new_bones))
bone_chunks = b''.join(hdr(0x202, hdr(0x203, n.encode() + b'\0', False) + hdr(0x206, d, False), True)
                       for n, d in new_bones)
new_skel = hdr(0x200, hdr(0x201, bytes(cnt), False) + b[kids[1][1]:skel[3]] + bone_chunks, True)

c601 = bytearray(b[ck[0][2]:ck[0][3]]); assert c601[0] == 1 and c601[1] == 4
assert struct.unpack_from('<I', c601, 2)[0] == len(meshes)
struct.pack_into('<I', c601, 2, len(meshes) + len(new_meshes))
links = b''.join(hdr(0x602, bytes([2, 4]) + struct.pack('<I', o) + bytes([3, 4]) + struct.pack('<I', bo), False)
                 for o, bo in new_links)
new_conn = hdr(0x600, hdr(0x601, bytes(c601), False) + b[ck[1][1]:conn[3]] + links, True)

out = new_skel + (b[meshes[0][1]:meshes[-1][3]] if meshes else b'') + b''.join(new_meshes) + new_conn
open(dst, 'wb').write(out)
k0 = new_bones[0]
print(f'{dst}: bones {len(bones)}->{len(bones) + len(new_bones)}, meshes {len(meshes)}->{len(meshes) + len(new_meshes)}')
for r in (last - 1, last):
    print(f'  r{r}_00 at', [round(v, 2) for v in trans(bones[bidx[f"zz_button_r{r}_00"]][1])])
for n, d in new_bones[::24]:
    print(f'  {n} at', [round(v, 2) for v in trans(d)])
