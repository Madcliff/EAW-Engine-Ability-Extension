#!/usr/bin/env python3
"""Installer for the ZZ_SWFOC engine patch (Star Wars: Empire at War - Forces of Corruption, 64-bit Steam build).

What it does:
  install    copies ZZ_SWFOC.dll into the game's corruption/ folder and renames StarWarsG.exe's one import
             POWRPROF.dll -> ZZ_SWFOC.dll (same length, nothing else in the exe changes). The untouched exe is
             backed up first as StarWarsG.exe.zz_original.
  uninstall  puts the POWRPROF.dll import back and removes ZZ_SWFOC.dll.
  status     shows what is installed.

The game folder is found through Steam (all libraries); pass --game-dir if it is somewhere else.
Steam's "Verify integrity of game files" and game updates restore the original exe: run install again afterwards.

usage: python3 install.py [install|uninstall|status] [--game-dir DIR] [--steam-root DIR] [--dll FILE] [--force]
"""
import argparse, hashlib, os, re, shutil, struct, sys, tempfile

DLL_NAME = 'ZZ_SWFOC.dll'
EXE_NAME = 'StarWarsG.exe'
OLD, NEW = b'POWRPROF.dll', b'ZZ_SWFOC.dll'
BACKUP_SUFFIX = '.zz_original'
GAME_FOLDER = 'Star Wars Empire at War'
# StarWarsG.exe 1.121.859328 (Steam, 64-bit), stock and with the import renamed
KNOWN_EXES = {
    '07daeeaec9d1e751383b1db3f5847b6c66f68785440a6c52c87b85f723d018a4': 'stock',
    'f3c1fa3af132afc17e4e606be2874bc3de9d42b4bff4fccdf0e16de2005fa917': 'patched',
}
HERE = os.path.dirname(os.path.abspath(__file__))


class Fail(Exception):
    pass


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ PE import table
def import_name_offset(b):
    """File offset and current text of the exe's POWRPROF.dll / ZZ_SWFOC.dll import name."""
    if b[:2] != b'MZ':
        raise Fail('not an exe file')
    pe = struct.unpack_from('<I', b, 0x3c)[0]
    if b[pe:pe + 4] != b'PE\0\0':
        raise Fail('not a PE file')
    opt = pe + 24
    if struct.unpack_from('<H', b, opt)[0] != 0x20b:
        raise Fail('not a 64-bit exe (this patch is for the 64-bit Steam build)')
    nsec = struct.unpack_from('<H', b, pe + 6)[0]
    sec_tab = opt + struct.unpack_from('<H', b, pe + 20)[0]
    secs = [struct.unpack_from('<IIII', b, sec_tab + 40 * i + 8) for i in range(nsec)]  # vsize, va, rawsize, rawptr

    def off(rva):
        for vs, va, rs, rp in secs:
            if va <= rva < va + max(vs, rs):
                return rp + rva - va
        raise Fail('import table points outside the exe (rva 0x%x)' % rva)

    d = off(struct.unpack_from('<I', b, opt + 112 + 8)[0])        # data directory 1: imports
    names = []
    while True:
        name_rva = struct.unpack_from('<I', b, d + 12)[0]
        if name_rva == 0:
            break
        n = off(name_rva)
        names.append((n, bytes(b[n:b.index(0, n)])))
        d += 20
    hits = [(n, s) for n, s in names if s.upper() in (OLD.upper(), NEW.upper())]
    if len(hits) != 1:
        raise Fail('expected one POWRPROF.dll import, found: %s' % ', '.join(s.decode('latin-1') for _, s in names))
    return hits[0]


# ------------------------------------------------------------------ finding the game
def steam_roots(extra):
    roots = [extra] if extra else []
    if os.name == 'nt':
        try:
            import winreg
            for hive, key, val in ((winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam', 'SteamPath'),
                                   (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam', 'InstallPath'),
                                   (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Valve\Steam', 'InstallPath')):
                try:
                    with winreg.OpenKey(hive, key) as k:
                        roots.append(winreg.QueryValueEx(k, val)[0])
                except OSError:
                    pass
        except ImportError:
            pass
        for env in ('ProgramFiles(x86)', 'ProgramFiles'):
            if os.environ.get(env):
                roots.append(os.path.join(os.environ[env], 'Steam'))
    else:
        home = os.path.expanduser('~')
        roots += [os.path.join(home, p) for p in (
            '.local/share/Steam', '.steam/steam', '.steam/root',
            '.var/app/com.valvesoftware.Steam/.local/share/Steam',     # Flatpak
            'snap/steam/common/.local/share/Steam',                    # Snap
            'Library/Application Support/Steam')]                      # macOS (CrossOver/Whisky users pass --game-dir)
    return roots


def steam_libraries(roots):
    libs = []
    for r in roots:
        if not os.path.isdir(r):
            continue
        libs.append(r)
        vdf = os.path.join(r, 'steamapps', 'libraryfolders.vdf')
        try:
            text = open(vdf, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        libs += [p.replace('\\\\', '\\') for p in re.findall(r'"path"\s+"([^"]+)"', text)]
    seen, out = set(), []
    for lib in libs:
        key = os.path.normcase(os.path.realpath(lib))
        if key not in seen:
            seen.add(key)
            out.append(lib)
    return out


def corruption_dir(path):
    """The folder holding StarWarsG.exe, given the game folder or its corruption/ folder."""
    for d in (os.path.join(path, 'corruption'), path):
        if os.path.isfile(os.path.join(d, EXE_NAME)):
            return d
    return None


def find_game(args):
    if args.game_dir:
        d = corruption_dir(os.path.expanduser(args.game_dir))
        if not d:
            raise Fail('no corruption/%s under %s' % (EXE_NAME, args.game_dir))
        return d
    found = []
    for lib in steam_libraries(steam_roots(args.steam_root)):
        d = corruption_dir(os.path.join(lib, 'steamapps', 'common', GAME_FOLDER))
        if d and os.path.normcase(os.path.realpath(d)) not in [os.path.normcase(os.path.realpath(f)) for f in found]:
            found.append(d)
    if not found:
        raise Fail('could not find "%s" in any Steam library. Run again with --game-dir "<path to the game folder>"'
                   % GAME_FOLDER)
    if len(found) > 1:
        raise Fail('found more than one install, pick one with --game-dir:\n  ' + '\n  '.join(found))
    return found[0]


def find_dll(args):
    cands = [args.dll] if args.dll else [os.path.join(HERE, DLL_NAME), os.path.join(HERE, 'dll', DLL_NAME)]
    for c in cands:
        if c and os.path.isfile(c):
            return c
    raise Fail('%s not found next to the installer (looked for: %s)' % (DLL_NAME, ', '.join(cands)))


# ------------------------------------------------------------------ file helpers
def write_atomic(path, data, mode_from=None):
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(prefix='.zz_tmp_', dir=d)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        if mode_from and os.path.exists(mode_from):
            shutil.copymode(mode_from, tmp)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def exe_state(exe):
    b = bytearray(open(exe, 'rb').read())
    h = hashlib.sha256(b).hexdigest()
    n, cur = import_name_offset(b)
    return b, h, n, cur


def describe(h, cur):
    kind = KNOWN_EXES.get(h)
    name = cur.decode('latin-1')
    if kind == 'stock':
        return 'stock 1.121.859328 (imports %s)' % name
    if kind == 'patched':
        return 'patched 1.121.859328 (imports %s)' % name
    return 'unknown version (imports %s)' % name


# ------------------------------------------------------------------ commands
def cmd_status(args):
    game = find_game(args)
    exe = os.path.join(game, EXE_NAME)
    _, h, _, cur = exe_state(exe)
    dll = os.path.join(game, DLL_NAME)
    print('game folder: %s' % game)
    print('exe:         %s' % describe(h, cur))
    if os.path.isfile(dll):
        state = 'present'
        try:
            state += ', same as the bundled one' if sha256(dll) == sha256(find_dll(args)) else ', differs from the bundled one'
        except Fail:
            pass
        print('dll:         %s' % state)
    else:
        print('dll:         not installed')
    bak = exe + BACKUP_SUFFIX
    print('exe backup:  %s' % (os.path.basename(bak) if os.path.isfile(bak) else 'none'))
    installed = cur.upper() == NEW.upper() and os.path.isfile(dll)
    print('=> engine patch is %s' % ('INSTALLED' if installed else 'NOT installed'))
    return 0


def cmd_install(args):
    game = find_game(args)
    src_dll = find_dll(args)
    exe = os.path.join(game, EXE_NAME)
    b, h, n, cur = exe_state(exe)
    print('game folder: %s' % game)
    print('exe:         %s' % describe(h, cur))
    if h not in KNOWN_EXES:
        if not args.force:
            raise Fail('this StarWarsG.exe is not the Steam 64-bit version 1.121.859328 the patch was made for.\n'
                       'The DLL checks every site and turns off what does not match, but nothing is promised.\n'
                       'Run again with --force to install anyway.')
        print('warning: unknown exe version, installing anyway (--force)')

    # 1. the DLL (before the exe, so a patched exe never points at a missing DLL)
    dst_dll = os.path.join(game, DLL_NAME)
    if os.path.isfile(dst_dll) and sha256(dst_dll) == sha256(src_dll):
        print('dll:         already up to date')
    else:
        if os.path.isfile(dst_dll):
            shutil.copy2(dst_dll, dst_dll + '.prev')
            print('dll:         previous one kept as %s.prev' % DLL_NAME)
        write_atomic(dst_dll, open(src_dll, 'rb').read())
        print('dll:         copied %s' % DLL_NAME)

    # 2. the exe import
    if cur.upper() == NEW.upper():
        print('exe:         already points at %s' % DLL_NAME)
    else:
        bak = exe + BACKUP_SUFFIX          # the exe as it is now (unpatched) is the one to keep
        shutil.copy2(exe, bak)
        print('exe:         backed up as %s' % os.path.basename(bak))
        b[n:n + len(NEW)] = NEW
        write_atomic(exe, bytes(b), mode_from=exe)
        _, h2, _, cur2 = exe_state(exe)
        if cur2 != NEW or (h in KNOWN_EXES and KNOWN_EXES.get(h2) != 'patched'):
            raise Fail('the exe did not verify after patching; restore it from %s' % os.path.basename(bak))
        print('exe:         import renamed %s -> %s' % (cur.decode(), NEW.decode()))
    print('\nDone. Start the game as usual. The DLL log is %s' % os.path.join(game, 'zz_ability_buttons.log'))
    print('After a Steam update or "Verify integrity of game files", run this installer again.')
    return 0


def cmd_uninstall(args):
    game = find_game(args)
    exe = os.path.join(game, EXE_NAME)
    b, h, n, cur = exe_state(exe)
    print('game folder: %s' % game)
    print('exe:         %s' % describe(h, cur))
    if cur.upper() == NEW.upper():
        b[n:n + len(OLD)] = OLD
        write_atomic(exe, bytes(b), mode_from=exe)
        _, h2, _, cur2 = exe_state(exe)
        if cur2 != OLD:
            raise Fail('the exe did not verify after reverting')
        print('exe:         import restored to %s%s' % (OLD.decode(), ' (matches stock)' if KNOWN_EXES.get(h2) == 'stock' else ''))
    else:
        print('exe:         already imports %s' % cur.decode())
    for name in (DLL_NAME, DLL_NAME + '.prev'):
        p = os.path.join(game, name)
        if os.path.isfile(p):
            os.remove(p)
            print('dll:         removed %s' % name)
    bak = exe + BACKUP_SUFFIX
    if os.path.isfile(bak):
        print('exe backup %s left in place (delete it if you like)' % os.path.basename(bak))
    print('\nDone. The game runs without the engine patch now.')
    return 0


def main():
    ap = argparse.ArgumentParser(description='Install or remove the ZZ_SWFOC engine patch for Forces of Corruption.')
    ap.add_argument('command', nargs='?', default='install', choices=('install', 'uninstall', 'status'))
    ap.add_argument('--game-dir', help='game folder ("Star Wars Empire at War") or its corruption/ folder')
    ap.add_argument('--steam-root', help='extra Steam folder to search for libraries')
    ap.add_argument('--dll', help='DLL to install (default: %s next to this script)' % DLL_NAME)
    ap.add_argument('--force', action='store_true', help='install on an exe version the patch was not made for')
    args = ap.parse_args()
    sys.stdout.reconfigure(line_buffering=True)
    try:
        return {'install': cmd_install, 'uninstall': cmd_uninstall, 'status': cmd_status}[args.command](args)
    except Fail as e:
        print('error: %s' % e, file=sys.stderr)
        return 1
    except PermissionError as e:
        print('error: %s\nIs the game still running? If the game is under Program Files, run the installer as '
              'administrator.' % e, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
