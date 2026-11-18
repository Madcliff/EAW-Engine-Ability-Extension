#!/bin/sh
# Builds ZZ_SWFOC.dll (the zz_mod_revrev engine DLL; StarWarsG.exe loads it after patch_import_name.py) with clang + lld-link, no C runtime.
# patch_data.h is regenerated from ../patch_starwarsg.py on every build.
set -e
cd "$(dirname "$0")"
python3 -I gen_patch_data.py
python3 -I gen_hero_bar.py
llvm-dlltool -m i386:x86-64 -d kernel32.def -l kernel32.lib
llvm-dlltool -m i386:x86-64 -d user32.def -l user32.lib
clang --target=x86_64-pc-windows-msvc -O2 -ffreestanding -fno-builtin -fno-stack-protector \
      -mno-stack-arg-probe -Wall -Wextra -c zz_ability_buttons.c -o zz_ability_buttons.obj
lld-link /dll /nodefaultlib /entry:DllMain /subsystem:windows /machine:x64 \
      /out:ZZ_SWFOC.dll zz_ability_buttons.obj kernel32.lib user32.lib
echo built "$(pwd)/ZZ_SWFOC.dll"
