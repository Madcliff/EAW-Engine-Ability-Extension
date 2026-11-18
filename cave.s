        .intel_syntax noprefix
        .text
        .set RET_INIT,     0x14030e6a2
        .set BLOCK_ENTRY,  0x14030e9a8
        .set BLOCK_AFTER,  0x14030e9af
        .set EPILOGUE_CONT,0x14030edc8
        .set UNIT_TO_TYPE, 0x1403973b0
        .set TYPE_ABILITY, 0x140374b50
        .set HAS_ABILITY,  0x1403986b0
        .set RECHARGE_STATE,0x1402f9870

        .globl cave_init, cave_entry, cave_loop
cave_init:                                  # replaces xor r14d,r14d / mov [rsp+0x20],rax
        xor     r14d, r14d
        mov     qword ptr [rsp+0x20], rax
        mov     dword ptr [rbp+0x6b], 1      # k = 1 (stock ability-1 pass)
        mov     dword ptr [rbp+0x63], 0x1a6  # button b+1
        mov     byte ptr  [rbp+0x60], 0      # block not entered yet
        jmp     RET_INIT

cave_entry:                                 # replaces lea rax,[rsi+0xbb] at block entry
        mov     byte ptr  [rbp+0x60], 1      # block entered
        lea     rax, [rsi+0xbb]
        jmp     BLOCK_AFTER

cave_loop:                                  # replaces movaps xmm7,[rsp+0xb0] at the epilogue
        cmp     byte ptr  [rbp+0x60], 0
        je      finish
        mov     eax, dword ptr [rbp+0x6b]
        cmp     eax, 3
        jge     finish
        inc     eax
        mov     dword ptr [rbp+0x6b], eax    # k = 2, then 3
        lea     ecx, [rax+0x1bb]             # k=2 -> 0x1bd (button b+24), k=3 -> 0x1be (button b+25)
        mov     dword ptr [rbp+0x63], ecx
        mov     rsi, qword ptr [rsp+0x30]    # group's ability-0 type (stored by the block)
        mov     r15, qword ptr [rbp+0x4f]    # command bar
        lea     rax, [rsi+0xbb]
        lea     rax, [rax+rax*2]
        cmp     dword ptr [r15+rax*8+0x10], 0
        jle     finish                       # empty group
        mov     rcx, qword ptr [r15+rax*8+0x8]
        mov     rcx, qword ptr [rcx]         # first unit
        test    rcx, rcx
        jz      finish
        call    UNIT_TO_TYPE
        test    rax, rax
        jz      finish
        mov     rcx, rax
        mov     edx, dword ptr [rbp+0x6b]
        call    TYPE_ABILITY                 # ability type k, 0 = none
        test    eax, eax
        jz      finish
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
frac_loop:
        cmp     edi, ebx
        jge     frac_done
        mov     rcx, qword ptr [r13+rdi*8]
        test    rcx, rcx
        jz      frac_next
        mov     edx, dword ptr [rbp+0x67]
        call    HAS_ABILITY                  # unit has ability type?
        test    al, al
        jz      frac_next
        mov     dword ptr [rsp+0x20], 0
        mov     dword ptr [rsp+0x24], 0x3f800000
        mov     rcx, r15
        mov     rdx, qword ptr [r13+rdi*8]
        mov     r8d, dword ptr [rbp+0x67]
        lea     r9, [rsp+0x20]
        call    RECHARGE_STATE               # al=1 + fraction at +4 while recharging
        test    al, al
        jz      frac_next
        movss   xmm0, dword ptr [rsp+0x24]
        maxss   xmm0, dword ptr [rbp+0x77]
        movss   dword ptr [rbp+0x77], xmm0
frac_next:
        inc     edi
        jmp     frac_loop
frac_done:
        add     rsp, 0x30
        xor     r14d, r14d                   # block expects r14 = 0 (rsi, r15 still valid)
        jmp     BLOCK_ENTRY                  # run the ability block again for ability k
finish:
        movaps  xmm7, xmmword ptr [rsp+0xb0]
        jmp     EPILOGUE_CONT
