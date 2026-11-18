"""Forward trace of an ability-id register from each id check: records memory operands whose address is
   base_reg + id*S + B (S = entry size, B = offset of id 0). Linear, no branch merging (follows fallthrough and
   stops at ret/indirect jmp or after N instructions)."""
import re,collections,sys,json
import os
SP=os.environ.get('IDTRACE_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 're'))   # text.dis (objdump of the exe) + ability_type_sites.txt
L=open(SP+'/text.dis').read().splitlines()
pos={}
for i,l in enumerate(L):
    m=re.match(r'\s*([0-9a-f]+):',l)
    if m: pos[int(m.group(1),16)]=i
R64={'eax':'rax','ebx':'rbx','ecx':'rcx','edx':'rdx','esi':'rsi','edi':'rdi','ebp':'rbp','esp':'rsp'}
for k in range(8,16): R64['r%dd'%k]='r%d'%k
def r64(r): return R64.get(r,r)
def parse_int(s):
    s=s.strip()
    neg=s.startswith('-'); s=s.lstrip('+-')
    v=int(s,16) if s.startswith('0x') else int(s)
    return -v if neg else v
DEPTH=[0]; SEEN=set()
def trace(start_line, reg, limit=60, seed=None):
    # state: reg -> (mul, add) meaning value = id*mul + add  (only for id-derived regs)
    st=dict(seed) if seed else {r64(reg):(1,0)}
    out=[]
    for x in L[start_line:start_line+limit]:
        ins=x.split('\t')[-1].strip(); a=x.split(':')[0].strip()
        if not ins or ins.startswith('int3'): break
        m=re.match(r'(\w+) +(.*)',ins)
        if not m: continue
        op,args=m.group(1),m.group(2)
        if op=='call':
            mc=re.match(r'0x([0-9a-f]+)$',args.strip())
            if mc and DEPTH[0]<2:
                tgt=int(mc.group(1),16)
                for argr in ('rcx','rdx','r8','r9'):
                    if argr in st and st[argr]==(1,0) and tgt in pos and (tgt,argr) not in SEEN:
                        SEEN.add((tgt,argr)); DEPTH[0]+=1
                        for t in trace(pos[tgt],argr,80): out.append(t[:5]+(t[5]+'   [in 0x%x]'%tgt,))
                        DEPTH[0]-=1
            for r in ('rax','rcx','rdx','r8','r9','r10','r11'): st.pop(r,None)
            continue
        # memory operands
        for mm in re.finditer(r'\[([^\]]+)\]',args):
            expr=mm.group(1)
            parts=re.findall(r'([+-]?)\s*([a-z0-9]+(?:\*\d)?|0x[0-9a-f]+)',expr)
            base=None; idxv=None; disp=0
            for sgn,p in parts:
                if '*' in p:
                    r,sc=p.split('*'); r=r64(r)
                    if r in st: idxv=(st[r][0]*int(sc), st[r][1]*int(sc))
                elif p.startswith('0x'): disp+= -int(p,16) if sgn=='-' else int(p,16)
                else:
                    r=r64(p)
                    if r in st and idxv is None: idxv=st[r]
                    else: base=r
            if idxv and op!='lea':
                out.append((a,op,base,idxv[0],idxv[1]+disp,ins))
        dst=args.split(',')[0].strip()
        d=r64(dst) if re.match(r'^[a-z0-9]+$',dst) else None
        src=args.split(',',1)[1].strip() if ',' in args else ''
        if d is None: continue
        if op in ('mov','movsxd','movzx') and re.match(r'^[a-z0-9]+$',src):
            s=r64(src)
            if s in st: st[d]=st[s]
            else: st.pop(d,None)
        elif op=='lea':
            mm=re.match(r'\[(.*)\]',src)
            expr=mm.group(1) if mm else ''
            terms=re.findall(r'([+-]?)\s*([a-z0-9]+(?:\*\d)?|0x[0-9a-f]+)',expr)
            mul=0; add=0; ok=False; other=False
            for sgn,p in terms:
                if '*' in p:
                    r,sc=p.split('*'); r=r64(r)
                    if r in st: mul+=st[r][0]*int(sc); add+=st[r][1]*int(sc); ok=True
                    else: other=True
                elif p.startswith('0x'): add+= -int(p,16) if sgn=='-' else int(p,16)
                else:
                    r=r64(p)
                    if r in st: mul+=st[r][0]; add+=st[r][1]; ok=True
                    else: other=True
            if ok and not other: st[d]=(mul,add)
            elif ok and other: out.append((a,'lea-base',None,mul,add,ins)); st.pop(d,None)
            else: st.pop(d,None)
        elif op=='add' and d in st:
            if src.startswith('0x'): st[d]=(st[d][0],st[d][1]+int(src,16))
            elif r64(src) in st: st[d]=(st[d][0]+st[r64(src)][0],st[d][1]+st[r64(src)][1])
            else: out.append((a,'add-base',r64(src),st[d][0],st[d][1],ins)); st.pop(d)
        elif op=='sub' and d in st and src.startswith('0x'): st[d]=(st[d][0],st[d][1]-int(src,16))
        elif op=='shl' and d in st and src.startswith('0x'): k=1<<int(src,16); st[d]=(st[d][0]*k,st[d][1]*k)
        elif op=='imul' and d in st and re.match(r'0x',src.split(',')[-1].strip()):
            k=int(src.split(',')[-1],16); st[d]=(st[d][0]*k,st[d][1]*k)
        elif op=='imul':
            parts=[p.strip() for p in args.split(',')]
            if len(parts)==3 and r64(parts[1]) in st: k=int(parts[2],16); st[d]=(st[r64(parts[1])][0]*k, st[r64(parts[1])][1]*k)
            elif d in st: st.pop(d)
        elif op in ('inc','dec') : pass
        elif op in ('cdqe',): pass
        elif d in st and op not in ('cmp','test'):
            st.pop(d,None)
    return out
if __name__=='__main__':
    sites=[int(re.match(r'\s+0x([0-9a-f]+)',l).group(1),16) for l in open(SP+'/ability_type_sites.txt') if re.match(r'\s+0x[0-9a-f]+\s+cmp',l)]
    res=[]
    for a in sites:
        i=pos[a]; reg=re.search(r'cmp +(\w+),',L[i]).group(1)
        seed={r64(reg):(1,0)}
        for back in L[max(0,i-4):i]:
            mb=re.search(r'lea +%s,\[(\w+)-0x1\]'%reg, back.split('\t')[-1])
            if mb: seed={r64(mb.group(1)):(1,0), r64(reg):(1,-1)}
            if re.search(r'dec +%s$'%reg, back.split('\t')[-1]): seed={r64(reg):(1,-1)}
        for t in trace(i+1,reg,400,seed): res.append((hex(a),)+t)
    json.dump(res,open(SP+'/idtrace_out.json','w'))
    groups=collections.defaultdict(list)
    for r in res:
        site,a,op,base,mul,add,ins=r
        if op in ('lea-base','add-base'): key=('ptr', mul, add)
        else: key=('mem', mul, add)
        groups[key].append((site,a,base,ins))
    for k,v in sorted(groups.items(), key=lambda x:(-len(x[1]))):
        print('%s  id*%-4s + %-7s %3d uses  e.g. %s'%(k[0],hex(k[1]),hex(k[2]),len(v),v[0][3]))
