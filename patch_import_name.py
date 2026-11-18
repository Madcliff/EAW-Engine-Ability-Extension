"""Point StarWarsG.exe at the zz_mod_revrev engine DLL instead of powrprof.dll.

StarWarsG.exe (64-bit FoC) imports one function, CallNtPowerInformation, from POWRPROF.dll. The engine DLL
(dll/build.sh -> ZZ_SWFOC.dll) exports that same function (forwarded to ntdll) and installs all its patches
from DllMain. This script renames that import's DLL name string in place: POWRPROF.dll -> ZZ_SWFOC.dll
(same length, so nothing else in the exe moves). Wine/Windows then load ZZ_SWFOC.dll from the game folder;
no WINEDLLOVERRIDES launch option is needed.

usage: python3 -I patch_import_name.py [path/to/StarWarsG.exe] [--revert] [--check]
  default path: the Steam install's corruption/StarWarsG.exe
  --check   only report which DLL name the exe imports
  --revert  put POWRPROF.dll back
Steam's "Verify integrity" or a game update restores the original exe: run this again afterwards."""
import os, struct, sys

DEFAULT = os.path.expanduser('~/.local/share/Steam/steamapps/common/Star Wars Empire at War/corruption/StarWarsG.exe')
OLD, NEW = b'POWRPROF.dll', b'ZZ_SWFOC.dll'
assert len(OLD) == len(NEW)

args = [a for a in sys.argv[1:] if not a.startswith('--')]
path = args[0] if args else DEFAULT
revert, check = '--revert' in sys.argv, '--check' in sys.argv
src, dst = (NEW, OLD) if revert else (OLD, NEW)

b = bytearray(open(path, 'rb').read())
pe = struct.unpack_from('<I', b, 0x3c)[0]
assert b[pe:pe + 4] == b'PE\0\0', 'not a PE file'
opt = pe + 24
assert struct.unpack_from('<H', b, opt)[0] == 0x20b, 'not a 64-bit exe'
nsec = struct.unpack_from('<H', b, pe + 6)[0]
sec_tab = opt + struct.unpack_from('<H', b, pe + 20)[0]
secs = [struct.unpack_from('<IIII', b, sec_tab + 40 * i + 8) for i in range(nsec)]   # vsize, va, rawsize, rawptr
def off(rva):
    for vs, va, rs, rp in secs:
        if va <= rva < va + max(vs, rs):
            return rp + rva - va
    raise ValueError(hex(rva))
imp_rva = struct.unpack_from('<I', b, opt + 112 + 8)[0]          # data directory 1: import table
names = []
d = off(imp_rva)
while True:
    oft, ts, fwd, name_rva, ft = struct.unpack_from('<IIIII', b, d)
    if name_rva == 0:
        break
    n = off(name_rva)
    names.append((n, bytes(b[n:b.index(0, n)])))
    d += 20

hits = [(n, s) for n, s in names if s.upper() in (OLD.upper(), NEW.upper())]
assert len(hits) == 1, 'expected one POWRPROF/ZZ_SWFOC import, found %r' % [s for _, s in names]
n, cur = hits[0]
print('%s imports %s' % (os.path.basename(path), cur.decode()))
if check:
    sys.exit(0)
if cur.upper() == dst.upper():
    print('already patched; nothing to do')
    sys.exit(0)
b[n:n + len(dst)] = dst
open(path, 'wb').write(b)
print('patched: %s -> %s' % (cur.decode(), dst.decode()))
