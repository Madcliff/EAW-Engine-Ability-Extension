#!/usr/bin/env python3
"""
StarWarsG.exe patch: up to 4 ability buttons per unit group (Forces of Corruption, 64-bit).

  python3 patch_starwarsg.py check     # report whether the exe is stock, patched or unknown
  python3 patch_starwarsg.py apply     # back up to StarWarsG.exe.orig, then patch
  python3 patch_starwarsg.py restore   # put the backup back
  python3 patch_starwarsg.py build OUT # write a patched copy to OUT (exe untouched)

How it works (details in ../exe_patch_4_ability_buttons_plan.md):
the engine's button routine 0x14030e660 sets up ability 0 on button b and runs a block for
ability 1 on button b+1. This patch runs that block again for abilities 2 and 3 on buttons
b+24 and b+25 (the second row of the modified i_tactical_controls.alo), and lets the
special-button loops cover 48 buttons instead of 24. Steam "verify files" or an update
replaces the exe; run `apply` again afterwards.
"""
import hashlib, os, shutil, struct, sys

EXE = os.path.expanduser("~/.local/share/Steam/steamapps/common/Star Wars Empire at War/corruption/StarWarsG.exe")
BACKUP = EXE + ".orig"
STOCK_SHA256 = "07daeeaec9d1e751383b1db3f5847b6c66f68785440a6c52c87b85f723d018a4"
STOCK_SIZE = 12428800

TEXT_VA, TEXT_RAW = 0x140001000, 0x400
def off(va): return va - TEXT_VA + TEXT_RAW

CAVE_VA = 0x1407fc4c0
CAVE_INIT, CAVE_ENTRY, CAVE_LOOP = 0x1407fc4c0, 0x1407fc4df, 0x1407fc4ef
# assembled from cave.s with GNU as/ld at 0x1407fc4c0 (calls/jumps already resolved)
CAVE = bytes.fromhex(
    "4531f64889442420c7456b01000000c74563a6010000c6456000e9c321b1ffc6456001488d86bb000000e9c024b1ff"
    "807d60000f84f50000008b456b83f8030f8de9000000ffc089456b8d88bb010000894d63488b7424304c8b7d4f488d"
    "86bb000000488d044041837cc710000f8ebb000000498b4cc708488b094885c90f84aa000000e867aeb9ff4885c00f"
    "849c0000004889c18b556be8f385b7ff85c00f8489000000894567c7457700000000488d86bb000000488d0440418b"
    "5cc7104d8b6cc70831ff4883ec3039df7d54498b4cfd004885c974468b5567e810c1b9ff84c0743ac7442420000000"
    "00c74424240000803f4c89f9498b54fd00448b45674c8d4c2420e8a6d2afff84c07410f30f10442424f30f5f4577f3"
    "0f114577ffc7eba84883c4304531f6e9ba23b1ff0f28bc24b0000000e9cd27b1ff")

# extra section .zzpatch (assembled from zzpatch.s with GNU as/ld at 0x140cc0000):
# per-ability-type unit lists and the button loop for abilities 3-8 (rows 2-4), row 3/4 hiding,
# row 3/4 tooltips, unit-card hook for the swap buttons. Abilities 9/10 (row 5, ids 965+) need the DLL's
# enlarged component table: use the DLL, not the file patch (the file patch would read past the table).
ZZ_VA_RVA, ZZ_VSIZE, ZZ_RAWSIZE, ZZ_RAWPTR = 0xcc0000, 0x800, 0x800, STOCK_SIZE   # 0x800: DLL only (the DLL's own stubs start at zz+0x900)
ZZ_CHARS = 0xE0000020            # code | execute | read | write (holds one counter variable)
SEL_ENTRY, SEL_NEXT, CAVE_CLEAN, CAVE_LOOP6, CAVE_HIDE3 = 0x140cc0000, 0x140cc0022, 0x140cc0055, 0x140cc00cd, 0x140cc029b
TIP_A, TIP_B = 0x140cc02f2, 0x140cc0317
CARD_HOOK = 0x140cc033c
ZZ_CARD_FN = 0x140cc0388          # 8-byte pointer the DLL fills with its unit-card function (0 = no swap buttons)
ZZ_WIDE, GROUP_END = 0x140cc0390, 0x140cc03a0   # wide unit cards: flag the DLL sets, selection-bar group-end hook
SIZE_OF_IMAGE_OLD, SIZE_OF_IMAGE_NEW = 0xcc0000, 0xcc1000
ZZ_CODE = bytes.fromhex(
    "8b057a03000085c0750bb80100000089056b03000089c34c89f94d89fee9ccc465ff8b055803000085c0741f83f80f"
    "7d10ffc08905470300004531ede9a7c465ffc70535030000000000004c8b442448e9edc565ff488974242041be0200"
    "00004889e9e848736dff4885c0744f4889c14489f2e8d84a6bff85c074374863c0480508010000488d04404c8d0cc3"
    "498b49084885c9741d458b411031d24439c27d1248392cd17404ffc2ebf14c89c9e82d7538ff41ffc64183fe0f7ea4"
    "488b742420488d86bb000000e96c9e62ff807d60000f84b70100008b456b83f80f0f8dab010000ffc089456b8b5557"
    "8915ff0600008b0d8d020000890df7060000c705f10600000100000083fa14775c8d4a02d1e90fa30d6c020000724e"
    "8d4a03d1e90fa30d5e0200007240c705c60600000200000089c2c1ea0289c183e10383fa017217741d83fa02770881"
    "c1c5030000eb6081c1dd030000eb5881c1a5010000eb5081c1bd010000eb488d88bb01000083f8037e3d8d88c10300"
    "0083f8057e328d88d703000083f8077e278d88ed03000083f8097e1c8d880304000083f80b7e118d881904000083f8"
    "0d7e068d882f040000894d63488b7424304c8b7d4f488d86bb000000488d044041837cc710000f8ebb000000498b4c"
    "c708488b094885c90f84aa000000e8c7716dff4885c00f849c0000004889c18b556be853496bff85c00f8489000000"
    "894567c7457700000000488d86bb000000488d0440418b5cc7104d8b6cc70831ff4883ec3039df7d54498b4cfd0048"
    "85c974468b5567e870846dff84c0743ac744242000000000c74424240000803f4c89f9498b54fd00448b45674c8d4c"
    "2420e8069663ff84c07410f30f10442424f30f5f4577f30f114577ffc7eba84883c4304531f6e91ae764ff0f28bc24"
    "b0000000e92deb64ffc705df00000000000000bbc503000089d9e89f7868ff4885c074284889c74c8b00b2014889c1"
    "41ff50788b97a000000085d2780f488b8f880000004531c0e832b768ffffc381fb6c0400007ec2488b7c2440e92876"
    "62ff81f9c50300007c0c81f9540400000f8e2b2462ff81f9a50100000f8cdf0e62ffe9cc0e62ff81fbc50300007c0c"
    "81fb540400000f8e853462ff81fba50100000f8c7c3662ffe96a3462ff8b4424542d3901000083f8177709d1e80fab"
    "0531000000488b052e0000004885c0740d4889f94c89f2448b442454ffd0baff000000e92ec865ff662e0f1f840000"
    "00000000000000000000000000000000000000000000009066662e0f1f840000000000833de9ffffff007455c705dd"
    "ffffff0000000089f8d1e8ffc83b442448753f8d47023b4424687f36564883ec288db70901000089f1e8350000008d"
    "4e01e82d0000008d4e30e8250000008d4e31e81d0000004883c4285e83c702897c2440448b4424444c8b9de0000000"
    "e968cc65ff4883ec28e8387768ff4885c0740c4889c14c8b00b20141ff50784883c428c30000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000")
ZZ_HEADER = b".zzpatch" + struct.pack("<IIIIIIHHI", ZZ_VSIZE, ZZ_VA_RVA, ZZ_RAWSIZE, ZZ_RAWPTR, 0, 0, 0, 0, ZZ_CHARS)

def jmp(src, dst, length):
    rel = dst - (src + 5)
    return b"\xe9" + struct.pack("<i", rel) + b"\x90" * (length - 5)

NOP = b"\x90"
PATCHES = [
    # (va, original bytes, new bytes, description)
    (0x14030e69a, "4533f648894424 20", jmp(0x14030e69a, CAVE_INIT, 8),  "hook: init loop at routine start"),
    (0x14030e9a8, "488d86bb000000",    jmp(0x14030e9a8, CAVE_ENTRY, 7), "hook: mark ability block entered"),
    (0x14030ea16, "ba01000000",        bytes.fromhex("8b556b") + NOP * 2, "ability index = loop counter"),
    (0x14030ec26, "81c1a6010000",      bytes.fromhex("034d63") + NOP * 3, "button = per-pass offset"),
    (0x14030ec45, "41b801000000",      bytes.fromhex("44 8b 45 6b".replace(" ", "")) + NOP * 2, "icon/tooltip: ability index = loop counter"),
    (0x14030ece7, "ba01000000488bcb448d4202", bytes.fromhex("8b556b488bcb41b803000000"), "button slot 3 (ability index used by click/cooldown) = loop counter"),
    (0x14030edc0, "0f28bc24b0000000",  jmp(0x14030edc0, CAVE_LOOP6, 8), "hook: loop for abilities 3-6 (in .zzpatch)"),
    (0x140346ecf, "4883f80175108d5003", bytes.fromhex("4883f80172106a045a"),
     "click handler: ability index >= 1 (not just == 1) uses the group key in slot 4"),
    (0x14031c4e8, "498bcf4d8bf7",   jmp(0x14031c4e8, SEL_ENTRY, 6),  "selection: type-list pass also for abilities 3/4 (entry)"),
    (0x14031c63d, "4c8b442448",     jmp(0x14031c63d, SEL_NEXT, 5),   "selection: type-list pass also for abilities 3/4 (loop)"),
    (0x1402e9f32, "488d86bb000000", jmp(0x1402e9f32, CAVE_CLEAN, 7), "cleanup: remove unit from ability 3/4 type lists"),
    (0x14031b5c5, "e826c50200",     bytes.fromhex("b817000000"),   "selection: slot limit pinned to 24 (last index 23) so s_select_24-47 stay ability buttons"),
    (0x1402e7915, "488b7c2440",     jmp(0x1402e7915, CAVE_HIDE3, 5), "hide-all: also hide the row 3/4 buttons s_select_24-47, s_health_24-47"),
    (0x1402e11db, "81f9a50100007c0e", jmp(0x1402e11db, TIP_A, 8), "tooltip (mouse-over path A): also rows 3/4 ids"),
    (0x1402e379a, "81fba50100000f8c0d020000", jmp(0x1402e379a, TIP_B, 12), "tooltip (path B): also rows 3/4 ids"),
    (0x14031cb9f, "baff000000",     jmp(0x14031cb9f, CARD_HOOK, 5),  "unit card filled: let the DLL show that card's unit-swap button"),
    (0x14031d06b, "448b4424444c8b9de0000000", jmp(0x14031d06b, GROUP_END, 12), "selection-bar group end: leave a column empty after a wide unit card"),
    (0x14030ee33, "4883f801750e8d5003", bytes.fromhex("4883f801720e6a045a"),
     "right-click autofire handler: ability index >= 1 uses the group key in slot 4 (same fix as the click handler)"),
    (0x1402dccfa, "8b05f0ac8400", bytes.fromhex("b830000000") + NOP, "button lookup loop: 48 buttons"),
    (0x1402dcd3a, "8b05b0ac8400", bytes.fromhex("b830000000") + NOP, "button lookup loop: 48 buttons"),
    (0x1402e78a2, "8b0548018400", bytes.fromhex("b830000000") + NOP, "hide-all loop: 48 buttons"),
    (0x1402e7904, "8b05e6008400", bytes.fromhex("b830000000") + NOP, "hide-all loop: 48 buttons"),
    (0x1402f59a5, "8b0545208300", bytes.fromhex("b830000000") + NOP, "find button by ability: 48 buttons"),
    (0x1402f59f1, "8b05f91f8300", bytes.fromhex("b830000000") + NOP, "find button by ability: 48 buttons"),
    (0x1402e11e3, "8d82a4010000", bytes.fromhex("b8d4010000") + NOP, "click range: buttons up to 47"),
    (0x1402e37a6, "8d81a4010000", bytes.fromhex("b8d4010000") + NOP, "click range: buttons up to 47"),
]
PATCHES = [(va, bytes.fromhex(o.replace(" ", "")), n, d) for va, o, n, d in PATCHES]

# component name table (.data, 72-byte entries from 0x140a174e0): s_select_24..47 get the
# special-button click handler, making them a third row of ability buttons (abilities 5/6).
# Only the +0x18 slot is changed: it already has a base-relocation entry, so ASLR stays correct.
DATA_VA, DATA_RAW = 0x1409cf000, 0x9cce00
def doff(va): return va - DATA_VA + DATA_RAW
COMP_TABLE, S_SELECT_24, S_SELECT_47 = 0x140a174e0, 0x121, 0x138
# Rows 3-6 and the swap buttons are new components in the DLL's enlarged table (ids 965..1084),
# so no entries of the stock table are changed any more (they used to be s_select/s_health 24..47).
DATA_PATCHES = []

# s_health_24..47 (ids 0x151..0x168) become the fourth row (abilities 7/8). Their +0x18 slot is empty
# (0) and has no base-relocation entry, so only the DLL injector (dll/) can set it: it writes the
# relocated handler address in memory. The file patch leaves row 4 unclickable.
S_HEALTH_24, S_HEALTH_47 = 0x151, 0x168
DLL_ONLY_DATA_PATCHES = []

for va, o, n, d in PATCHES:
    assert len(o) == len(n), (hex(va), d)

TEXT_VSIZE_OLD, TEXT_VSIZE_NEW = 0x7fb4b7, 0x7fb600   # map the spare bytes holding the new code

def text_vsize_offset(data):
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    sh = pe + 24 + opt
    for i in range(nsec):
        if data[sh + 40 * i: sh + 40 * i + 8].rstrip(b"\0") == b".text":
            return sh + 40 * i + 8
    raise SystemExit(".text section not found")

def pe_info(data):
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    return pe, pe + 24, pe + 24 + opt          # PE header, optional header, section table

def zz_present(data):
    pe, opt, sh = pe_info(data)
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    return (nsec == 8 and data[sh + 40 * 7: sh + 40 * 8] == ZZ_HEADER
            and struct.unpack_from("<I", data, opt + 56)[0] == SIZE_OF_IMAGE_NEW
            and data[ZZ_RAWPTR: ZZ_RAWPTR + len(ZZ_CODE)] == ZZ_CODE and len(data) == ZZ_RAWPTR + ZZ_RAWSIZE)

def add_section(out):
    pe, opt, sh = pe_info(out)
    assert struct.unpack_from("<H", out, pe + 6)[0] == 7 and set(out[sh + 280: sh + 320]) == {0}
    assert struct.unpack_from("<I", out, opt + 56)[0] == SIZE_OF_IMAGE_OLD and len(out) == ZZ_RAWPTR
    struct.pack_into("<H", out, pe + 6, 8)
    out[sh + 280: sh + 320] = ZZ_HEADER
    struct.pack_into("<I", out, opt + 56, SIZE_OF_IMAGE_NEW)
    out += ZZ_CODE + b"\0" * (ZZ_RAWSIZE - len(ZZ_CODE))

def state(data):
    vs = struct.unpack_from("<I", data, text_vsize_offset(data))[0]
    orig = all(data[off(va): off(va) + len(o)] == o for va, o, n, d in PATCHES) and \
           all(data[doff(va): doff(va) + 8] == o for va, o, n in DATA_PATCHES)
    new = all(data[off(va): off(va) + len(n)] == n for va, o, n, d in PATCHES) and \
          all(data[doff(va): doff(va) + 8] == n for va, o, n in DATA_PATCHES)
    cave_ok = data[off(CAVE_VA): off(CAVE_VA) + len(CAVE)] == CAVE
    cave_zero = set(data[off(CAVE_VA): off(CAVE_VA) + len(CAVE)]) == {0}
    if orig and cave_zero and vs == TEXT_VSIZE_OLD and len(data) == STOCK_SIZE:
        return "stock"
    if new and cave_ok and vs == TEXT_VSIZE_NEW and zz_present(data):
        return "patched"
    return "unknown"

def patched_bytes(data):
    if hashlib.sha256(data).hexdigest() != STOCK_SHA256 or len(data) != STOCK_SIZE:
        raise SystemExit("exe is not the known stock 1.121.859328 build; refusing to patch")
    out = bytearray(data)
    for va, o, n, d in PATCHES:
        out[off(va): off(va) + len(n)] = n
    for va, o, n in DATA_PATCHES:
        out[doff(va): doff(va) + 8] = n
    out[off(CAVE_VA): off(CAVE_VA) + len(CAVE)] = CAVE
    struct.pack_into("<I", out, text_vsize_offset(out), TEXT_VSIZE_NEW)
    add_section(out)
    assert state(bytes(out)) == "patched"
    return bytes(out)

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    data = open(EXE, "rb").read()
    st = state(data)
    if cmd == "check":
        print("StarWarsG.exe:", st, "| backup present:", os.path.exists(BACKUP))
    elif cmd == "build":
        open(sys.argv[2], "wb").write(patched_bytes(data)); print("wrote", sys.argv[2])
    elif cmd == "apply":
        if st == "patched":
            print("already patched"); return
        source = data
        if st != "stock":
            # e.g. an older version of this patch: rebuild from the stock backup
            if not os.path.exists(BACKUP):
                raise SystemExit("exe is not stock and there is no backup; refusing to patch")
            source = open(BACKUP, "rb").read()
            print("exe is not stock (older patch?); rebuilding from", BACKUP)
        new = patched_bytes(source)
        if not os.path.exists(BACKUP):
            shutil.copy2(EXE, BACKUP)
        open(EXE, "wb").write(new)
        print("patched; stock exe saved as", BACKUP)
    elif cmd == "restore":
        if not os.path.exists(BACKUP):
            raise SystemExit("no backup found")
        b = open(BACKUP, "rb").read()
        if hashlib.sha256(b).hexdigest() != STOCK_SHA256:
            raise SystemExit("backup is not the stock exe; not restoring")
        shutil.copy2(BACKUP, EXE); print("stock exe restored")
    else:
        raise SystemExit(__doc__)

if __name__ == "__main__":
    main()
