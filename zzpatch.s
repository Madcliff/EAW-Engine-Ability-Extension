# Code for the extra .zzpatch section (VA 0x140cc0000): per-ability-type unit lists for
# abilities 3 and 4, so aimed abilities (Force Storm, Corruption Pulse, ...) can be
# ordered from buttons 3/4.
        .intel_syntax noprefix
        .text
        .set SEL_PASS_BODY,   0x14031c4ee   # after mov rcx,r15 / mov r14,r15 (pass for ability index ebx)
        .set SEL_PASS_HOOK,   0x14031c4e8   # hooked pass start (-> sel_entry)
        .set SEL_NEXT_CONT,   0x14031c642   # after mov r8,[rsp+0x48] (next unit)
        .set CLEAN_CONT,      0x1402e9f39   # after lea rax,[rsi+0xbb] (group-list removal)
        .set UNIT_TO_TYPE,    0x1403973b0
        .set TYPE_ABILITY,    0x140374b50
        .set LIST_REMOVE_AT,  0x1400475e0
        .set GET_COMPONENT,   0x140347b50
        .set SET_BONE_VISIBLE,0x14034ba10
        .set HIDE_CONT,       0x1402e791a   # after mov rdi,[rsp+0x40] in the hide-all routine 0x1402e77c0
        .set BLOCK_ENTRY,     0x14030e9a8
        .set EPILOGUE_CONT,   0x14030edc8
        .set HAS_ABILITY,     0x1403986b0
        .set RECHARGE_STATE,  0x1402f9870

        .globl sel_entry, sel_next, cave_clean, cave_loop6, cave_hide3

# selection routine 0x14031b590: the "add unit to its ability-2 type list" pass,
# re-run for ability indexes 2..7
sel_entry:                                  # replaces mov rcx,r15 / mov r14,r15 at 0x14031c4e8
        mov     eax, dword ptr [rip+pass_k]
        test    eax, eax
        jnz     1f
        mov     eax, 1                       # first (stock) pass: index 1
        mov     dword ptr [rip+pass_k], eax
1:      mov     ebx, eax                     # ability index for this pass
        mov     rcx, r15
        mov     r14, r15
        jmp     SEL_PASS_BODY

sel_next:                                   # replaces mov r8,[rsp+0x48] at 0x14031c63d
        mov     eax, dword ptr [rip+pass_k]
        test    eax, eax
        jz      3f                           # not in a pass (unit skipped earlier)
        cmp     eax, 15                      # ability indexes 1..15 (abilities 2-16)
        jge     2f
        inc     eax
        mov     dword ptr [rip+pass_k], eax
        xor     r13d, r13d                   # pass expects r13 = 0
        jmp     SEL_PASS_HOOK                # run the pass again for index 2 / 3
2:      mov     dword ptr [rip+pass_k], 0
3:      mov     r8, qword ptr [rsp+0x48]
        jmp     SEL_NEXT_CONT

# cleanup routine 0x1402e9d60 (unit rbp leaves the selection): also remove it from
# the type lists of its abilities 3 and 4
cave_clean:                                 # replaces lea rax,[rsi+0xbb] at 0x1402e9f32
        mov     qword ptr [rsp+0x20], rsi    # keep ability-2 type (slot is free until 0x1402e9f9c)
        mov     r14d, 2                      # r14 was saved by the routine; reloaded at 0x1402e9f84
clean_loop:
        mov     rcx, rbp
        call    UNIT_TO_TYPE
        test    rax, rax
        jz      clean_done
        mov     rcx, rax
        mov     edx, r14d
        call    TYPE_ABILITY
        test    eax, eax
        jz      clean_next
        movsxd  rax, eax
        add     rax, 0x108
        lea     rax, [rax+rax*2]
        lea     r9, [rbx+rax*8]              # type list
        mov     rcx, qword ptr [r9+0x8]
        test    rcx, rcx
        jz      clean_next
        mov     r8d, dword ptr [r9+0x10]     # count
        xor     edx, edx
clean_search:
        cmp     edx, r8d
        jge     clean_next
        cmp     qword ptr [rcx+rdx*8], rbp
        je      clean_found
        inc     edx
        jmp     clean_search
clean_found:
        mov     rcx, r9
        call    LIST_REMOVE_AT               # (list, index)
clean_next:
        inc     r14d
        cmp     r14d, 15                     # ability indexes 2..15 (abilities 3-16)
        jle     clean_loop
clean_done:
        mov     rsi, qword ptr [rsp+0x20]
        lea     rax, [rsi+0xbb]
        jmp     CLEAN_CONT

# button routine 0x14030e660: re-run the ability-1 block for abilities 3-8
cave_loop6:                                # replaces the jump at 0x14030edc0 (was cave_loop in .text)                                  # replaces movaps xmm7,[rsp+0xb0] at the epilogue
        cmp     byte ptr  [rbp+0x60], 0
        je      finish6
        mov     eax, dword ptr [rbp+0x6b]
        cmp     eax, 15
        jge     finish6
        inc     eax
        mov     dword ptr [rbp+0x6b], eax    # k = 2..15
        # Rows of 4 when the two button columns right of this group (b+2, b+3) are not under another unit
        # card this refresh (zz_used_cols, card column c covers button columns 2c and 2c+1) and fit (b <= 20):
        # ability k goes to row k/4, column b + k%4 (row 1 = special_button b.., row 2 = special_button
        # b+24.., row 3 = zz_button_r3_ b..). Otherwise rows of 2 (below). Abilities 0/1 sit on b, b+1 either way.
        mov     edx, dword ptr [rbp+0x57]    # b, the group's first button column
        mov     dword ptr [rip+zz_dbg_b], edx          # debug for the DLL log: b, the column bits seen, decision
        mov     ecx, dword ptr [rip+zz_used_cols]
        mov     dword ptr [rip+zz_dbg_cols], ecx
        mov     dword ptr [rip+zz_dbg_dec], 1          # 1 = rows of 2 unless the checks below pass
        cmp     edx, 20
        ja      narrow6
        lea     ecx, [rdx+2]
        shr     ecx, 1
        bt      dword ptr [rip+zz_used_cols], ecx
        jc      narrow6                      # a card sits under column b+2
        lea     ecx, [rdx+3]
        shr     ecx, 1
        bt      dword ptr [rip+zz_used_cols], ecx
        jc      narrow6                      # a card sits under column b+3
        mov     dword ptr [rip+zz_dbg_dec], 2          # 2 = rows of 4
        mov     edx, eax
        shr     edx, 2                       # row
        mov     ecx, eax
        and     ecx, 3                       # column within the row
        cmp     edx, 1
        jb      w_row1
        je      w_row2
        cmp     edx, 2
        ja      w_row4
        add     ecx, 0x3c5                   # row 3: zz_button_r3_ (965 + b + col)
        jmp     1f
w_row4: add     ecx, 0x3dd                   # row 4: zz_button_r4_ (989 + b + col), abilities 13-16 in rows of 4
        jmp     1f
w_row1: add     ecx, 0x1a5                   # row 1: special_button (0x1a5 + b + col)
        jmp     1f
w_row2: add     ecx, 0x1bd                   # row 2: special_button b+24.. (0x1bd + b + col)
        jmp     1f
narrow6:
        lea     ecx, [rax+0x1bb]             # k=2 -> 0x1bd (b+24), k=3 -> 0x1be (b+25): special_button row 2
        cmp     eax, 3
        jle     1f
        # rows 3-6 are new components that exist only in the DLL's enlarged component table
        # (ids 965.., named zz_button_r3_00.. / r4 / r5 / r6, 24 per row)
        lea     ecx, [rax+0x3c1]             # k=4,5   -> 965+b, 966+b   (row 3)
        cmp     eax, 5
        jle     1f
        lea     ecx, [rax+0x3d7]             # k=6,7   -> 989+b, 990+b   (row 4)
        cmp     eax, 7
        jle     1f
        lea     ecx, [rax+0x3ed]             # k=8,9   -> 1013+b, 1014+b (row 5)
        cmp     eax, 9
        jle     1f
        lea     ecx, [rax+0x403]             # k=10,11 -> 1037+b, 1038+b (row 6)
        cmp     eax, 11
        jle     1f
        lea     ecx, [rax+0x419]             # k=12,13 -> 1061+b, 1062+b (row 7)
        cmp     eax, 13
        jle     1f
        lea     ecx, [rax+0x42f]             # k=14,15 -> 1085+b, 1086+b (row 8)
1:      mov     dword ptr [rbp+0x63], ecx
        mov     rsi, qword ptr [rsp+0x30]    # group's ability-0 type (stored by the block)
        mov     r15, qword ptr [rbp+0x4f]    # command bar
        lea     rax, [rsi+0xbb]
        lea     rax, [rax+rax*2]
        cmp     dword ptr [r15+rax*8+0x10], 0
        jle     finish6                       # empty group
        mov     rcx, qword ptr [r15+rax*8+0x8]
        mov     rcx, qword ptr [rcx]         # first unit
        test    rcx, rcx
        jz      finish6
        call    UNIT_TO_TYPE
        test    rax, rax
        jz      finish6
        mov     rcx, rax
        mov     edx, dword ptr [rbp+0x6b]
        call    TYPE_ABILITY                 # ability type k, 0 = none
        test    eax, eax
        jz      finish6
        mov     dword ptr [rbp+0x67], eax    # type the block displays
        # recharge dial for ability k (the block reads [rbp+0x77], which the caller
        # filled with ability 1's value): max recharge fraction over the group's units,
        # same rule as 0x1403108b0 (fraction while recharging, else 0)
        mov     dword ptr [rbp+0x77], 0
        # rsi (group type) and r15 (command bar) are callee-saved: still valid here
        lea     rax, [rsi+0xbb]
        lea     rax, [rax+rax*2]
        mov     ebx, dword ptr [r15+rax*8+0x10]   # unit count
        mov     r13, qword ptr [r15+rax*8+0x8]    # unit array
        xor     edi, edi
        sub     rsp, 0x30                    # shadow space + 8-byte result
frac_loop6:
        cmp     edi, ebx
        jge     frac_done6
        mov     rcx, qword ptr [r13+rdi*8]
        test    rcx, rcx
        jz      frac_next6
        mov     edx, dword ptr [rbp+0x67]
        call    HAS_ABILITY                  # unit has ability type?
        test    al, al
        jz      frac_next6
        mov     dword ptr [rsp+0x20], 0
        mov     dword ptr [rsp+0x24], 0x3f800000
        mov     rcx, r15
        mov     rdx, qword ptr [r13+rdi*8]
        mov     r8d, dword ptr [rbp+0x67]
        lea     r9, [rsp+0x20]
        call    RECHARGE_STATE               # al=1 + fraction at +4 while recharging
        test    al, al
        jz      frac_next6
        movss   xmm0, dword ptr [rsp+0x24]
        maxss   xmm0, dword ptr [rbp+0x77]
        movss   dword ptr [rbp+0x77], xmm0
frac_next6:
        inc     edi
        jmp     frac_loop6
frac_done6:
        add     rsp, 0x30
        xor     r14d, r14d                   # block expects r14 = 0 (rsi, r15 still valid)
        jmp     BLOCK_ENTRY                  # run the ability block again for ability k
finish6:
        movaps  xmm7, xmmword ptr [rsp+0xb0]
        jmp     EPILOGUE_CONT

# hide-all routine 0x1402e77c0: also hide the new buttons, ids 965..1132 (rows 3-8 and the swap buttons),
# exactly like the engine hides unused special buttons (component hidden + its model bone hidden)
cave_hide3:                                 # replaces mov rdi,[rsp+0x40] at 0x1402e7915
        mov     dword ptr [rip+zz_used_cols], 0   # new refresh: no card columns in use yet (card_hook marks them)
        mov     ebx, 0x3c5                   # zz_button_r3_00 .. zz_swap_23 (ids 965..1132)
hide3_loop:
        mov     ecx, ebx
        call    GET_COMPONENT
        test    rax, rax
        jz      hide3_next
        mov     rdi, rax                     # rdi is restored from [rsp+0x40] below
        mov     r8, qword ptr [rax]
        mov     dl, 1
        mov     rcx, rax
        call    qword ptr [r8+0x78]          # hide component
        mov     edx, dword ptr [rdi+0xa0]
        test    edx, edx
        js      hide3_next
        mov     rcx, qword ptr [rdi+0x88]
        xor     r8d, r8d
        call    SET_BONE_VISIBLE             # hide its mesh in the command-bar model
hide3_next:
        inc     ebx
        cmp     ebx, 0x46c
        jle     hide3_loop
        mov     rdi, qword ptr [rsp+0x40]
        jmp     HIDE_CONT

# Tooltips for rows 3-8. Two mouse-over paths only accept the ability-button ids 0x1a5..0x1d4 before
# calling the ability tooltip builder 0x1402f3e20; also send the new row ids 965..1108 there.
        .set TIPA_ORIG_LT,   0x1402e11f1   # id < 0x1a5 in path A (dispatcher 0x1402e0...)
        .set TIPA_ORIG_CONT, 0x1402e11e3   # upper-bound check in path A
        .set TIPA_HIT,       0x1402e2731   # path A: ability-button tooltip
        .set TIPB_ORIG_LT,   0x1402e39b3   # id < 0x1a5 in path B (routine 0x1402e32f0)
        .set TIPB_ORIG_CONT, 0x1402e37a6
        .set TIPB_HIT,       0x1402e37b0
        .globl tip_a, tip_b
tip_a:                                      # replaces cmp ecx,0x1a5 / jl 0x1402e11f1 at 0x1402e11db
        cmp     ecx, 0x3c5                 # rows 3-8: zz_button_r3_00 .. zz_button_r8_23 (965..1108)
        jl      1f
        cmp     ecx, 0x454
        jle     TIPA_HIT
1:      cmp     ecx, 0x1a5
        jl      TIPA_ORIG_LT
        jmp     TIPA_ORIG_CONT
tip_b:                                      # replaces cmp ebx,0x1a5 / jl 0x1402e39b3 at 0x1402e379a
        cmp     ebx, 0x3c5                 # rows 3-8: zz_button_r3_00 .. zz_button_r8_23 (965..1108)
        jl      1f
        cmp     ebx, 0x454
        jle     TIPB_HIT
1:      cmp     ebx, 0x1a5
        jl      TIPB_ORIG_LT
        jmp     TIPB_ORIG_CONT

# Unit-swap buttons (zz_swap_00..23, ids 1109..1132, one on each unit card). The selection bar
# fills unit card `slot` at 0x14031cb78..0x14031cb9a (rdi = card component, r14 = the card's unit,
# [rsp+0x54] = 0x139 + slot); after that, call the DLL's card function, which shows the swap button
# for that card if the unit has a swap target. The pointer is 0 without the DLL (nothing happens).
        .set CARD_CONT,      0x14031cba4   # after mov edx,0xff at 0x14031cb9f
        .globl card_hook, zz_card_fn
card_hook:                                  # replaces mov edx,0xff at 0x14031cb9f
        mov     eax, dword ptr [rsp+0x54]    # 0x139 + slot of the card being filled
        sub     eax, 0x139
        cmp     eax, 23
        ja      2f
        shr     eax, 1                       # card column (two card slots per column, top and bottom)
        bts     dword ptr [rip+zz_used_cols], eax
2:
        mov     rax, qword ptr [rip+zz_card_fn]
        test    rax, rax
        jz      1f
        mov     rcx, rdi                     # card component
        mov     rdx, r14                     # unit shown on the card
        mov     r8d, dword ptr [rsp+0x54]    # 0x139 + slot
        call    rax                          # rsp is 16-aligned here (same as the routine's own calls)
1:      mov     edx, 0xff
        jmp     CARD_CONT

        .p2align 4
pass_k: .long 0                              # ability index of the running pass (0 = none)
zz_used_cols: .long 0                        # bit c = card column c holds a unit card this refresh (cleared in cave_hide3)
        .p2align 3
zz_card_fn: .quad 0                          # filled in by the DLL: void card_fn(card, unit, 0x139 + slot)

# Wide unit cards. The selection bar (0x14031b590) lays cards out per unit-type group, each group starting on
# a fresh card column (two card slots per column, top/bottom); [rsp+0x40] = slots used so far, [rsp+0x48] =
# the group's first column, [rsp+0x68] = slot limit. The group's ability buttons go above it and use rows of 4
# when the next card column holds no card (zz_used_cols). The DLL's card function sets zz_wide when a card shows a
# unit listed in zz_wide_cards.txt; at the end of a one-column group the next column is then left empty
# (its two card slots hidden), so the next group moves one column right and this group gets rows of 4.
        .set GROUP_END_CONT, 0x14031d077   # after mov r8d,[rsp+0x44] / mov r11,[rbp+0xe0]
        .globl zz_wide, group_end
        .p2align 3
zz_wide: .long 0                            # set by the DLL's card function, cleared at each group end
        .p2align 4
group_end:                                  # replaces mov r8d,[rsp+0x44] / mov r11,[rbp+0xe0] at 0x14031d06b
        cmp     dword ptr [rip+zz_wide], 0
        je      9f
        mov     dword ptr [rip+zz_wide], 0
        mov     eax, edi                     # slots used (even here: the group's last column is complete)
        shr     eax, 1
        dec     eax                          # the group's last column
        cmp     eax, dword ptr [rsp+0x48]
        jne     9f                           # wider than one column: rows of 4 can't fit anyway
        lea     eax, [rdi+2]
        cmp     eax, dword ptr [rsp+0x68]
        jg      9f
        push    rsi
        sub     rsp, 0x28                    # body rsp is 16-aligned: 8 + 0x28 keeps calls 16-aligned
        lea     esi, [rdi+0x109]             # empty column's slots s = edi, edi+1: components 0x109+s and 0x139+s
        mov     ecx, esi
        call    hide_comp
        lea     ecx, [rsi+1]
        call    hide_comp
        lea     ecx, [rsi+0x30]
        call    hide_comp
        lea     ecx, [rsi+0x31]
        call    hide_comp
        add     rsp, 0x28
        pop     rsi
        add     edi, 2
        mov     dword ptr [rsp+0x40], edi
9:      mov     r8d, dword ptr [rsp+0x44]
        mov     r11, qword ptr [rbp+0xe0]
        jmp     GROUP_END_CONT

hide_comp:                                  # ecx = component id; hides it (vtable+0x78, dl = 1)
        sub     rsp, 0x28
        call    GET_COMPONENT
        test    rax, rax
        jz      1f
        mov     rcx, rax
        mov     r8, qword ptr [rax]
        mov     dl, 1
        call    qword ptr [r8+0x78]
1:      add     rsp, 0x28
        ret

# debug words read by the DLL (fixed address 0x140cc07f0): last rows-of-4 check in cave_loop6
        .org    0x7f0
zz_dbg_b:    .long 0                         # the group's first button column b
zz_dbg_cols: .long 0                         # zz_used_cols at the check
zz_dbg_dec:  .long 0                         # 1 = rows of 2, 2 = rows of 4
