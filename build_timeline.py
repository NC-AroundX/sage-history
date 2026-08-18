#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_timeline.py (v2 · 헤리티지) — sage history 뮤지엄 연대기 뷰어 생성기
events/*.md 카드를 읽어 timeline.html + index.html을 만든다. (표준 라이브러리만)
사용: 저장소 루트에서  python build_timeline.py
"""
import os, re, glob, html, json, sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
EV_DIR = os.path.join(ROOT, "events")

TRACK_COLORS = {
    "경제위기의 사이클": "#B9955C",
    "개혁과 반동": "#C4472F",
    "전쟁과 기록": "#7D8CA3",
    "화해와 전환": "#8FA98F",
    "전염병과 사회 변동": "#A67C9D",
    "기술·항로·패권": "#5E8FA8",
    "제도와 문서의 힘": "#C9A227",
    "대중·정보·여론": "#B06A5A",
}
DEFAULT_COLOR = "#9AA3AF"

def parse_frontmatter(text):
    meta, body = {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if m:
        body = text[m.end():]
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                v = v.strip()
                if v.startswith("[") and v.endswith("]"):
                    v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
                meta[k.strip()] = v
    return meta, body

def md_to_html(md):
    lines, out, i = md.splitlines(), [], 0
    in_ul = in_ol = in_bq = False
    def close():
        nonlocal in_ul, in_ol, in_bq
        if in_ul: out.append("</ul>"); in_ul = False
        if in_ol: out.append("</ol>"); in_ol = False
        if in_bq: out.append("</blockquote>"); in_bq = False
    def inline(s):
        s = html.escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", s)
        return s
    while i < len(lines):
        ln = lines[i]
        if re.match(r"^\s*$", ln): close(); i += 1; continue
        h = re.match(r"^(#{1,4})\s+(.*)", ln)
        if h: close(); lv = min(len(h.group(1)) + 1, 5); out.append(f"<h{lv}>{inline(h.group(2))}</h{lv}>"); i += 1; continue
        if ln.startswith(">"):
            if not in_bq: close(); out.append("<blockquote>"); in_bq = True
            out.append(f"<p>{inline(ln.lstrip('> '))}</p>"); i += 1; continue
        m_ol = re.match(r"^\s*\d+\.\s+(.*)", ln)
        m_ul = re.match(r"^\s*[-*]\s+(.*)", ln)
        if m_ol:
            if not in_ol: close(); out.append("<ol>"); in_ol = True
            out.append(f"<li>{inline(m_ol.group(1))}</li>"); i += 1; continue
        if m_ul:
            if not in_ul: close(); out.append("<ul>"); in_ul = True
            out.append(f"<li>{inline(m_ul.group(1))}</li>"); i += 1; continue
        close(); out.append(f"<p>{inline(ln)}</p>"); i += 1
    close()
    return "\n".join(out)

def one_liner(body):
    m = re.search(r"\*\*한 줄 정의:?\*\*\s*(.+)", body)
    return m.group(1).strip() if m else ""

def rhyme_count(body):
    m = re.search(r"## 반복의 라임\n(.*?)(\n## |\Z)", body, re.S)
    return len(re.findall(r"↺", m.group(1))) if m else 0

def year_int(v):
    m = re.search(r"-?\d+", str(v))
    return int(m.group()) if m else 9999

def load_events():
    evs = []
    for path in sorted(glob.glob(os.path.join(EV_DIR, "*.md"))):
        if os.path.basename(path).startswith("_"): continue
        with open(path, encoding="utf-8") as f: text = f.read()
        meta, body = parse_frontmatter(text)
        track = str(meta.get("track", "기타"))
        ys = year_int(meta.get("year_start", 9999))
        ye = year_int(meta.get("year_end", ys))
        evs.append({
            "title": str(meta.get("title", os.path.basename(path))),
            "ys": ys, "ye": ye,
            "period": (f"{ys}" if ys == ye else f"{ys}–{ye}"),
            "region": str(meta.get("region", "")),
            "track": track,
            "color": TRACK_COLORS.get(track, DEFAULT_COLOR),
            "tags": meta.get("tags", []) if isinstance(meta.get("tags"), list) else [],
            "reliability": str(meta.get("reliability", "미상")),
            "one": one_liner(body),
            "rhymes": rhyme_count(body),
            "html": md_to_html(body),
        })
    evs.sort(key=lambda e: (e["ys"], e["ye"]))
    return evs

# ==== v2 헤리티지 렌더러 (뮤지엄 연대기 스타일) ====

def render(evs):
    tracks = [t for t in TRACK_COLORS if any(e["track"] == t for e in evs)]
    tracks += sorted({e["track"] for e in evs} - set(TRACK_COLORS))
    data = json.dumps(evs, ensure_ascii=False).replace("</", "<\\/")
    return """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>청사의 방 — sage history</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&family=Noto+Serif+KR:wght@400;500;600&display=swap" rel="stylesheet">
<style>
html{scroll-behavior:smooth}
*{margin:0;padding:0;box-sizing:border-box}
:root{--paper:oklch(96.5% .012 80);--ink:oklch(26% .02 60);--sub:oklch(46% .025 65);--gold:oklch(58% .085 75);--line:oklch(26% .02 60 / .16);--hair:oklch(26% .02 60 / .22)}
body{font-family:'Noto Serif KR',serif;background:var(--paper);color:var(--ink);min-height:100vh;position:relative}
body::before,body::after{content:"";position:fixed;border-radius:50%;filter:blur(70px);pointer-events:none;z-index:0}
body::before{width:520px;height:520px;top:-140px;right:-120px;background:oklch(75% .07 75 / .16)}
body::after{width:460px;height:460px;bottom:-160px;left:-140px;background:oklch(60% .05 50 / .1)}
a{color:inherit;text-decoration:none}
header{position:sticky;top:0;z-index:50;background:oklch(96.5% .012 80 / .92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:16px 5vw;display:flex;align-items:center;gap:26px;flex-wrap:wrap}
.brand{font-family:'Nanum Myeongjo',serif;font-weight:800;font-size:19px;letter-spacing:.42em;padding-right:.42em}
nav{display:flex;gap:20px;flex-wrap:wrap;font-size:12.5px;letter-spacing:.14em;color:var(--sub)}
nav button{background:none;border:none;font-family:inherit;font-size:inherit;letter-spacing:inherit;color:inherit;cursor:pointer;padding:4px 0;border-bottom:1px solid transparent}
nav button:hover{color:var(--ink)}
nav button.on{color:var(--ink);border-bottom-color:var(--gold)}
#q{margin-left:auto;background:transparent;border:none;border-bottom:1px solid var(--hair);padding:8px 2px;font-family:inherit;font-size:13.5px;color:var(--ink);min-width:180px}
#q:focus{outline:none;border-bottom-color:var(--gold)}
.hero{position:relative;z-index:1;text-align:center;padding:88px 5vw 66px}
.hero .eyebrow{font-style:italic;color:var(--gold);font-size:15px;letter-spacing:.06em}
.hero h1{font-family:'Nanum Myeongjo',serif;font-weight:800;font-size:clamp(34px,5.4vw,62px);letter-spacing:.3em;padding-left:.3em;margin:18px 0 20px;display:flex;align-items:center;justify-content:center;gap:26px}
.hero h1::before,.hero h1::after{content:"";height:1px;width:clamp(40px,9vw,130px);background:var(--hair)}
.hero .sub{color:var(--sub);font-size:15px;line-height:1.9;max-width:54ch;margin:0 auto}
.stats{text-align:center;color:var(--sub);font-size:12.5px;letter-spacing:.22em;padding-bottom:44px}
.stats a{color:var(--gold);border-bottom:1px solid oklch(58% .085 75 / .4)}
.tl{position:relative;z-index:1;max-width:1080px;margin:0 auto;padding:10px 5vw 110px}
.tl::before{content:"";position:absolute;left:50%;top:0;bottom:0;width:1px;background:var(--hair)}
.era{position:relative;text-align:center;margin:74px 0 30px;display:flex;align-items:center;justify-content:center;gap:22px}
.era span{font-family:'Nanum Myeongjo',serif;font-weight:700;font-size:clamp(21px,2.6vw,30px);letter-spacing:.5em;padding:0 0 0 .5em;background:var(--paper)}
.era::before,.era::after{content:"";height:1px;flex:1;max-width:150px;background:var(--hair)}
.ev{position:relative;width:calc(50% - 46px);margin:34px 0;cursor:pointer;background:none;border:none;text-align:inherit;font-family:inherit;color:var(--ink);display:block}
.ev.L{margin-right:auto;text-align:right}
.ev.R{margin-left:auto;text-align:left}
.ev .dot{position:absolute;top:12px;width:9px;height:9px;border-radius:50%;background:var(--paper);border:2px solid var(--gold)}
.ev.L .dot{right:-51px}.ev.R .dot{left:-51px}
.ev .conn{position:absolute;top:16px;height:1px;width:34px;background:var(--hair)}
.ev.L .conn{right:-40px}.ev.R .conn{left:-40px}
.ev .yr{font-family:'Nanum Myeongjo',serif;font-size:17px;letter-spacing:.14em;color:var(--ink)}
.ev .num{font-family:'Nanum Myeongjo',serif;color:var(--gold);font-size:13px;letter-spacing:.2em;margin:14px 0 2px}
.ev .track{font-style:italic;color:var(--gold);font-size:13.5px;margin:6px 0 4px}
.ev h3{font-family:'Nanum Myeongjo',serif;font-weight:800;font-size:clamp(19px,2.2vw,25px);line-height:1.45;letter-spacing:.06em;word-break:keep-all;transition:color .2s}
.ev:hover h3{color:oklch(45% .09 65)}
.ev .one{color:var(--sub);font-size:14px;line-height:1.85;margin-top:9px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.ev .meta{margin-top:11px;font-size:11.5px;letter-spacing:.14em;color:var(--sub)}
.ev .meta b{color:var(--gold);font-weight:400}
.empty{text-align:center;padding:70px 5vw;color:var(--sub)}
dialog{width:min(780px,94vw);max-height:88vh;background:var(--paper);color:var(--ink);border:none;border-radius:4px;padding:0;box-shadow:0 40px 90px oklch(26% .02 60 / .35)}
dialog::backdrop{background:oklch(26% .02 60 / .5);backdrop-filter:blur(3px)}
.dhead{padding:44px 52px 22px;text-align:center;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--paper)}
.dhead .cat{font-style:italic;color:var(--gold);font-size:14px}
.dhead h2{font-family:'Nanum Myeongjo',serif;font-weight:800;font-size:27px;letter-spacing:.1em;margin:10px 0 8px;word-break:keep-all}
.dhead .who{font-size:12.5px;letter-spacing:.2em;color:var(--sub)}
.dbody{padding:28px 52px 52px;font-size:15px;line-height:1.95;color:oklch(32% .02 60)}
.dbody h2,.dbody h3{font-family:'Nanum Myeongjo',serif;margin:26px 0 10px;font-size:18px;letter-spacing:.08em;color:var(--ink);display:flex;align-items:center;gap:14px}
.dbody h2::after,.dbody h3::after{content:"";height:1px;flex:1;background:var(--line)}
.dbody h4,.dbody h5{margin:16px 0 8px}
.dbody p{margin:10px 0}.dbody ul,.dbody ol{margin:10px 0 10px 20px}.dbody li{margin:7px 0}
.dbody blockquote{border-left:2px solid var(--gold);padding-left:14px;color:var(--sub);margin:12px 0}
.dbody em{color:oklch(48% .08 70)}
.dclose{position:absolute;top:18px;right:22px;border:1px solid var(--hair);background:none;border-radius:50%;width:34px;height:34px;font-size:15px;cursor:pointer;color:var(--sub);font-family:serif}
.dclose:hover{color:var(--ink);border-color:var(--ink)}
footer{position:relative;z-index:1;text-align:center;padding:30px 5vw 70px;color:var(--sub);font-size:11.5px;letter-spacing:.28em}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
@media (max-width:720px){
 .tl::before{left:14px}
 .ev,.ev.L,.ev.R{width:auto;margin-left:44px;text-align:left}
 .ev.L .dot,.ev.R .dot{left:-35px;right:auto}
 .ev.L .conn,.ev.R .conn{left:-26px;right:auto;width:18px}
 .era{justify-content:flex-start;padding-left:44px}.era::before{display:none}
 .dhead,.dbody{padding-left:24px;padding-right:24px}
 #q{min-width:0;width:100%;margin-left:0}}
</style>
</head>
<body>
<header>
  <a class="brand" href="#top">청사의 방</a>
  <nav id="nav"></nav>
  <input id="q" type="search" placeholder="사건 · 지역 · 태그 검색">
</header>
<div id="top"></div>

<section class="hero">
  <div class="eyebrow">History repeats, insight remains</div>
  <h1>잊지 말아야 할 것들</h1>
  <div class="sub">역사는 순환하고 반복됩니다. 이 방은 __N__건의 사건을 시간 위에 놓고,
  오늘과 닮은 <b style="color:var(--gold);font-weight:400">↺ 반복의 라임</b>을 짝지어 보관합니다.</div>
</section>
<div class="stats"><a href="compare.html">▦ 동서 대조 연표로 보기</a> &nbsp;·&nbsp; 매주 자동으로 자라는 아카이브</div>

<div class="tl" id="tl"></div>
<footer>청사의 방 — SAGE HISTORY</footer>

<dialog id="dlg"><button class="dclose" onclick="dlg.close()" aria-label="닫기">×</button><div class="dhead"><div class="cat" id="dcat"></div><h2 id="dtitle"></h2><div class="who" id="dwho"></div></div><div class="dbody" id="dbody"></div></dialog>
<script>
const EVS=__DATA__;
const TRACKS=__TRACKS__;
let track="전체", q="";
const nav=document.getElementById("nav"), tl=document.getElementById("tl");
["전체",...TRACKS].forEach(t=>{const b=document.createElement("button");b.className=t==="전체"?"on":"";b.textContent=t;
 b.onclick=()=>{track=t;nav.querySelectorAll("button").forEach(x=>x.classList.toggle("on",x===b));draw()};nav.appendChild(b)});
document.getElementById("q").addEventListener("input",e=>{q=e.target.value.trim().toLowerCase();draw()});
function match(e){const inT=track==="전체"||e.track===track;
 const hay=(e.title+e.region+e.track+(e.tags||[]).join(" ")).toLowerCase();
 return inT&&(!q||hay.includes(q))}
function eraLabel(y){if(y<1)return "기원전";return (Math.floor((y-1)/100)+1)+"세기"}
function draw(){
  const list=EVS.filter(match);
  tl.innerHTML="";
  if(!list.length){tl.innerHTML='<div class="empty">이 조건의 사건이 아직 없습니다.</div>';return}
  let era=null, side=0, idx=0;
  list.forEach(e=>{
    const el2=eraLabel(e.ys);
    if(el2!==era){era=el2;const d=document.createElement("div");d.className="era";d.innerHTML=`<span>${era}</span>`;tl.appendChild(d)}
    idx++;
    const b=document.createElement("button");b.className="ev "+(side%2? "R":"L");side++;
    b.innerHTML=`<span class="dot"></span><span class="conn"></span>
      <div class="yr">${e.period}</div>
      <div class="num">${String(idx).padStart(2,"0")}</div>
      <div class="track">${e.track}</div>
      <h3>${e.title}</h3>
      <div class="one">${e.one}</div>
      <div class="meta">${e.region} · ${e.reliability}${e.rhymes?` · <b>↺ 라임 ${e.rhymes}</b>`:""}</div>`;
    b.onclick=()=>open(e);
    tl.appendChild(b);
  });
}
function open(e){
  document.getElementById("dcat").textContent=e.track;
  document.getElementById("dtitle").textContent=e.title;
  document.getElementById("dwho").textContent=e.period+" · "+e.region+" · "+e.reliability;
  document.getElementById("dbody").innerHTML=e.html;
  document.getElementById("dbody").scrollTop=0;
  dlg.showModal();
}
draw();
</script>
</body>
</html>""".replace("__DATA__", data).replace("__TRACKS__", json.dumps(tracks, ensure_ascii=False)).replace("__N__", str(len(evs)))

LANES = ["한국", "동아시아", "유럽", "미주", "세계"]
HEGEMON = {14:"몽골·명", 15:"명·오스만", 16:"스페인·명", 17:"네덜란드·청", 18:"영국·청", 19:"영국", 20:"미국·소련", 21:"미국·중국"}

def lane_of(region):
    r = str(region)
    for l in LANES:
        if l in r: return l
    return "세계"

def century(y):
    return (y - 1) // 100 + 1 if y >= 1 else 0

def render_compare(evs):
    cents = sorted({century(e["ys"]) for e in evs})
    grid = {c: {l: [] for l in LANES} for c in cents}
    for e in evs:
        grid[century(e["ys"])][lane_of(e["region"])].append(e)
    data = json.dumps(evs, ensure_ascii=False).replace("</", "<\\/")
    head = "".join(f'<th><div class="cn">{c}세기</div><div class="hg">{HEGEMON.get(c,"")}</div></th>' for c in cents)
    rows = []
    for l in LANES:
        cells = []
        for c in cents:
            chips = "".join(
                f'<button class="chip2" data-i="{evs.index(e)}"><span class="cy">{e["ys"]}</span>{html.escape(e["title"])}</button>'
                for e in sorted(grid[c][l], key=lambda x: x["ys"]))
            cells.append(f'<td>{chips}</td>')
        rows.append(f'<tr><th class="lane"><span>{l}</span></th>{"".join(cells)}</tr>')
    body = "".join(rows)
    return """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>동서 대조 연표 — 청사의 방</title>
<link href="https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&family=Noto+Serif+KR:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--paper:oklch(96.5% .012 80);--ink:oklch(26% .02 60);--sub:oklch(46% .025 65);--gold:oklch(58% .085 75);--line:oklch(26% .02 60 / .14);--hair:oklch(26% .02 60 / .22)}
body{font-family:'Noto Serif KR',serif;background:var(--paper);color:var(--ink)}
a{color:inherit;text-decoration:none}
header{text-align:center;padding:66px 5vw 30px}
.eyebrow{font-style:italic;color:var(--gold);font-size:14px}
h1{font-family:'Nanum Myeongjo',serif;font-weight:800;font-size:clamp(26px,4vw,44px);letter-spacing:.32em;padding-left:.32em;margin:14px 0 12px;display:flex;align-items:center;justify-content:center;gap:22px}
h1::before,h1::after{content:"";height:1px;width:clamp(30px,8vw,110px);background:var(--hair)}
.sub{color:var(--sub);font-size:13.5px;letter-spacing:.1em}
.sub a{color:var(--gold);border-bottom:1px solid oklch(58% .085 75/.4)}
.wrap{overflow-x:auto;padding:34px 4vw 90px}
table{border-collapse:separate;border-spacing:0;min-width:780px;width:100%}
thead th{position:sticky;top:0;background:var(--paper);border-bottom:2px solid var(--gold);padding:12px;text-align:left;min-width:152px}
.cn{font-family:'Nanum Myeongjo',serif;font-weight:800;font-size:17px;letter-spacing:.12em}
.hg{font-size:11px;color:var(--sub);letter-spacing:.1em;margin-top:3px}
.hg:not(:empty)::before{content:"패권 · "}
th.lane{position:sticky;left:0;background:var(--paper);border-right:1px solid var(--gold);padding:12px 10px;width:56px}
th.lane span{font-family:'Nanum Myeongjo',serif;font-weight:800;font-size:14px;letter-spacing:.3em;writing-mode:vertical-rl;text-orientation:upright}
td{border-bottom:1px solid var(--line);border-right:1px dashed oklch(26% .02 60 / .08);padding:12px 9px;vertical-align:top}
.chip2{display:block;width:100%;text-align:left;background:oklch(98% .008 80);border:1px solid var(--line);border-left:2px solid var(--gold);border-radius:2px;color:var(--ink);font-family:inherit;font-size:12.5px;line-height:1.55;padding:8px 10px;margin:5px 0;cursor:pointer;word-break:keep-all;transition:.15s}
.chip2:hover{border-color:var(--gold);background:oklch(96% .02 78)}
.chip2 .cy{color:var(--gold);font-family:'Nanum Myeongjo',serif;font-size:11px;letter-spacing:.06em;margin-right:7px}
dialog{width:min(780px,94vw);max-height:88vh;background:var(--paper);color:var(--ink);border:none;border-radius:4px;padding:0;box-shadow:0 40px 90px oklch(26% .02 60/.35)}
dialog::backdrop{background:oklch(26% .02 60/.5);backdrop-filter:blur(3px)}
.dhead{padding:40px 48px 20px;text-align:center;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--paper)}
.dhead .cat{font-style:italic;color:var(--gold);font-size:14px}
.dhead h2{font-family:'Nanum Myeongjo',serif;font-weight:800;font-size:25px;letter-spacing:.08em;margin:9px 0 7px;word-break:keep-all}
.dhead .who{font-size:12px;letter-spacing:.18em;color:var(--sub)}
.dbody{padding:26px 48px 48px;font-size:15px;line-height:1.95;color:oklch(32% .02 60)}
.dbody h2,.dbody h3{font-family:'Nanum Myeongjo',serif;margin:24px 0 9px;font-size:17.5px;letter-spacing:.08em;display:flex;align-items:center;gap:13px}
.dbody h2::after,.dbody h3::after{content:"";height:1px;flex:1;background:var(--line)}
.dbody p{margin:9px 0}.dbody ul,.dbody ol{margin:9px 0 9px 20px}.dbody li{margin:6px 0}
.dbody em{color:oklch(48% .08 70)}
.dclose{position:absolute;top:16px;right:20px;border:1px solid var(--hair);background:none;border-radius:50%;width:33px;height:33px;cursor:pointer;color:var(--sub);font-family:serif}
@media (max-width:640px){.dhead,.dbody{padding-left:22px;padding-right:22px}}
</style></head><body>
<header><div class="eyebrow">One timeline, many worlds</div><h1>동서 대조 연표</h1>
<div class="sub"><a href="timeline.html">← 연대기로 돌아가기</a> · 세기 × 권역 · 패권 표기는 통설 기준 참고 정보</div></header>
<div class="wrap"><table><thead><tr><th></th>__HEAD__</tr></thead><tbody>__BODY__</tbody></table></div>
<dialog id="dlg"><button class="dclose" onclick="dlg.close()">×</button><div class="dhead"><div class="cat" id="dcat"></div><h2 id="dtitle"></h2><div class="who" id="dwho"></div></div><div class="dbody" id="dbody"></div></dialog>
<script>
const EVS=__DATA__;
document.querySelectorAll(".chip2").forEach(b=>b.onclick=()=>{const e=EVS[+b.dataset.i];
 document.getElementById("dcat").textContent=e.track;
 document.getElementById("dtitle").textContent=e.title;
 document.getElementById("dwho").textContent=e.period+" · "+e.region+" · "+e.reliability;
 document.getElementById("dbody").innerHTML=e.html;document.getElementById("dbody").scrollTop=0;dlg.showModal();});
</script></body></html>""".replace("__DATA__", data).replace("__HEAD__", head).replace("__BODY__", body)

if __name__ == "__main__":
    evs = load_events()
    out = render(evs)
    for name in ("timeline.html", "index.html"):
        with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
            f.write(out)
    with open(os.path.join(ROOT, "compare.html"), "w", encoding="utf-8") as f:
        f.write(render_compare(evs))
    print(f"timeline.html + index.html + compare.html 생성 완료 — {len(evs)}건 수록")
