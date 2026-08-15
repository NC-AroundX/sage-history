#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_timeline.py — sage history 타임라인 뷰어 생성기
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
<title>sage history — 청사의 방</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&family=Gowun+Batang&display=swap" rel="stylesheet">
<style>
:root{--night:#151A26;--night2:#1B2233;--paper:#EEE8DA;--dim:#B9B2A0;--seal:#C4472F;--brass:#B9955C;--line:rgba(238,232,218,.14)}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--night);color:var(--paper);font-family:'Gowun Batang','Noto Serif KR',serif;-webkit-font-smoothing:antialiased}
header{padding:56px 6vw 26px;border-bottom:1px solid var(--line)}
.eyebrow{font-size:12px;letter-spacing:.35em;color:var(--brass);text-transform:uppercase}
h1{font-family:'Noto Serif KR',serif;font-weight:900;font-size:clamp(30px,4.5vw,52px);margin:10px 0 6px}
.sub{color:var(--dim);font-size:15px}
.toolbar{display:flex;flex-wrap:wrap;gap:9px;align-items:center;padding:16px 6vw;border-bottom:1px solid var(--line);position:sticky;top:0;background:rgba(21,26,38,.93);backdrop-filter:blur(8px);z-index:5}
.chip{border:1px solid var(--line);background:none;color:var(--dim);padding:7px 13px;border-radius:999px;font-family:inherit;font-size:13px;cursor:pointer;display:flex;align-items:center;gap:7px;transition:.2s}
.chip .dot{width:8px;height:8px;border-radius:50%}
.chip:hover{border-color:var(--brass);color:var(--paper)}
.chip.on{background:var(--paper);border-color:var(--paper);color:#1B1912;font-weight:700}
#q{margin-left:auto;background:var(--night2);border:1px solid var(--line);color:var(--paper);padding:9px 14px;border-radius:8px;font-family:inherit;font-size:14px;min-width:190px}
#q:focus{outline:2px solid var(--brass);outline-offset:1px}
.count{padding:20px 6vw 0;color:var(--dim);font-size:13px;letter-spacing:.15em}
.tl{position:relative;padding:34px 6vw 90px;max-width:980px}
.tl::before{content:"";position:absolute;left:calc(6vw + 90px);top:0;bottom:0;width:2px;background:linear-gradient(var(--line),var(--brass),var(--line))}
.era{position:relative;margin:38px 0 6px;padding-left:126px;font-family:'Noto Serif KR',serif;font-weight:900;font-size:15px;letter-spacing:.3em;color:var(--brass)}
.era::before{content:"";position:absolute;left:84px;top:50%;width:14px;height:14px;transform:translateY(-50%) rotate(45deg);background:var(--night);border:2px solid var(--brass)}
.ev{position:relative;display:flex;gap:0;margin:16px 0;cursor:pointer;background:none;border:none;text-align:left;color:var(--paper);font-family:inherit;width:100%}
.ev .yr{width:90px;flex:none;text-align:right;padding:16px 18px 0 0;font-family:'Noto Serif KR',serif;font-weight:600;font-size:14px;color:var(--dim)}
.ev .node{position:absolute;left:84.5px;top:22px;width:13px;height:13px;border-radius:50%;background:var(--night);border:3px solid var(--seal)}
.ev .card{margin-left:36px;flex:1;background:var(--night2);border:1px solid var(--line);border-left:4px solid var(--seal);border-radius:6px;padding:15px 18px;transition:transform .2s,border-color .2s}
.ev:hover .card,.ev:focus-visible .card{transform:translateX(5px);border-color:var(--brass)}
.ev:focus-visible{outline:2px solid var(--brass);outline-offset:3px;border-radius:8px}
.card .tk{font-size:11px;letter-spacing:.22em;margin-bottom:5px}
.card .tt{font-family:'Noto Serif KR',serif;font-weight:900;font-size:18px;line-height:1.4;word-break:keep-all}
.card .ol{color:var(--dim);font-size:13.5px;line-height:1.7;margin-top:7px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.card .meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;font-size:11.5px;color:var(--dim)}
.badge{border:1px solid var(--line);border-radius:999px;padding:2px 9px}
.badge.rh{border-color:var(--seal);color:var(--seal)}
dialog{width:min(780px,93vw);max-height:87vh;background:var(--paper);color:#221E15;border:none;border-radius:10px;padding:0}
dialog::backdrop{background:rgba(10,13,20,.74);backdrop-filter:blur(3px)}
.dhead{padding:30px 38px 18px;border-bottom:1px solid rgba(34,30,21,.15);position:sticky;top:0;background:var(--paper)}
.dhead .cat{font-size:12px;letter-spacing:.28em;color:var(--seal)}
.dhead h2{font-family:'Noto Serif KR',serif;font-weight:900;font-size:25px;margin:6px 0 4px;word-break:keep-all}
.dhead .who{color:#6E6553;font-size:14px}
.dbody{padding:24px 38px 44px;overflow-y:auto;font-size:15.5px;line-height:1.85}
.dbody h3{font-family:'Noto Serif KR',serif;margin:24px 0 10px;font-size:19px;border-bottom:1px solid rgba(34,30,21,.15);padding-bottom:6px}
.dbody h4,.dbody h5{margin:16px 0 8px}
.dbody p{margin:10px 0}.dbody ul,.dbody ol{margin:10px 0 10px 22px}.dbody li{margin:7px 0}
.dbody blockquote{border-left:3px solid var(--brass);padding-left:14px;color:#5E5646;margin:12px 0}
.dbody em{color:#7A6433}
.close{position:absolute;top:22px;right:24px;background:none;border:1px solid rgba(34,30,21,.3);border-radius:999px;width:34px;height:34px;font-size:16px;cursor:pointer;font-family:inherit}
.empty{padding:60px 6vw;color:var(--dim)}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
@media (max-width:620px){
 .tl::before{left:calc(6vw + 8px)}
 .ev .yr{position:absolute;left:30px;top:-2px;width:auto;text-align:left;padding:0;font-size:12.5px}
 .ev .node{left:2.5px}
 .ev .card{margin-left:30px;margin-top:20px}
 .era{padding-left:34px}.era::before{left:2px}
 .dhead,.dbody{padding-left:22px;padding-right:22px}
}
</style>
</head>
<body>
<header>
  <div class="eyebrow">Sage History</div>
  <h1>청사(靑史)의 방</h1>
  <div class="sub"><a href="compare.html" style="color:var(--brass);text-decoration:none">▦ 대조 연표로 보기</a> · 잊지 말아야 할 사건 __N__건 · 카드를 누르면 배경과 인사이트, <span style="color:var(--seal)">↺ 반복의 라임</span>이 열립니다</div>
</header>
<div class="toolbar" id="chips"><input id="q" type="search" placeholder="사건·지역·태그 검색"></div>
<div class="count" id="count"></div>
<div class="tl" id="tl"></div>
<dialog id="dlg"><button class="close" onclick="dlg.close()" aria-label="닫기">✕</button><div class="dhead"><div class="cat" id="dcat"></div><h2 id="dtitle"></h2><div class="who" id="dwho"></div></div><div class="dbody" id="dbody"></div></dialog>
<script>
const EVS=__DATA__;
const TRACKS=__TRACKS__;
const COLORS=__COLORS__;
let track="전체", q="";
const chips=document.getElementById("chips"), tl=document.getElementById("tl");
["전체",...TRACKS].forEach(t=>{const b=document.createElement("button");b.className="chip"+(t==="전체"?" on":"");
 b.innerHTML=(t==="전체"?"":`<span class="dot" style="background:${COLORS[t]||"#9AA3AF"}"></span>`)+t;
 b.onclick=()=>{track=t;document.querySelectorAll(".chip").forEach(x=>x.classList.toggle("on",x===b));draw()};
 chips.insertBefore(b,document.getElementById("q"))});
document.getElementById("q").addEventListener("input",e=>{q=e.target.value.trim().toLowerCase();draw()});
function match(e){const inT=track==="전체"||e.track===track;const hay=(e.title+e.region+e.track+(e.tags||[]).join(" ")).toLowerCase();return inT&&(!q||hay.includes(q))}
function eraLabel(y){if(y<1)return "기원전";return (Math.floor((y-1)/100)+1)+"세기"}
function draw(){
  const list=EVS.filter(match);
  document.getElementById("count").textContent=list.length+" / "+EVS.length+"건 · 연대순";
  tl.innerHTML="";
  if(!list.length){tl.innerHTML='<div class="empty">이 조건의 사건이 아직 없습니다. 필터를 바꾸거나 검색어를 지워보세요.</div>';return}
  let era=null;
  list.forEach(e=>{
    const el2=eraLabel(e.ys);
    if(el2!==era){era=el2;const d=document.createElement("div");d.className="era";d.textContent=era;tl.appendChild(d)}
    const b=document.createElement("button");b.className="ev";
    b.innerHTML=`<div class="yr">${e.period}</div><div class="node" style="border-color:${e.color}"></div>
      <div class="card" style="border-left-color:${e.color}">
        <div class="tk" style="color:${e.color}">${e.track}</div>
        <div class="tt">${e.title}</div>
        <div class="ol">${e.one}</div>
        <div class="meta"><span class="badge">${e.region}</span><span class="badge">${e.reliability}</span>${e.rhymes?`<span class="badge rh">↺ 라임 ${e.rhymes}</span>`:""}</div>
      </div>`;
    b.onclick=()=>open(e);
    tl.appendChild(b);
  });
}
function open(e){
  document.getElementById("dcat").textContent=e.track+" · "+e.period+" · "+e.region+" · "+e.reliability;
  document.getElementById("dtitle").textContent=e.title;
  document.getElementById("dwho").textContent=(e.tags||[]).map(t=>"#"+t).join("  ");
  document.getElementById("dbody").innerHTML=e.html;
  document.getElementById("dbody").scrollTop=0;
  dlg.showModal();
}
draw();
</script>
</body>
</html>""".replace("__DATA__", data).replace("__TRACKS__", json.dumps(tracks, ensure_ascii=False)).replace("__COLORS__", json.dumps(TRACK_COLORS, ensure_ascii=False)).replace("__N__", str(len(evs)))

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
                f'<button class="chip2" data-i="{evs.index(e)}" style="border-left-color:{e["color"]}"><span class="cy">{e["ys"]}</span>{html.escape(e["title"])}</button>'
                for e in sorted(grid[c][l], key=lambda x: x["ys"]))
            cells.append(f'<td>{chips}</td>')
        rows.append(f'<tr><th class="lane">{l}</th>{"".join(cells)}</tr>')
    body = "".join(rows)
    return """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>sage history — 대조 연표</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&family=Gowun+Batang&display=swap" rel="stylesheet">
<style>
:root{--night:#151A26;--night2:#1B2233;--paper:#EEE8DA;--dim:#B9B2A0;--seal:#C4472F;--brass:#B9955C;--line:rgba(238,232,218,.14)}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--night);color:var(--paper);font-family:'Gowun Batang','Noto Serif KR',serif}
header{padding:46px 5vw 22px;border-bottom:1px solid var(--line)}
.eyebrow{font-size:12px;letter-spacing:.35em;color:var(--brass);text-transform:uppercase}
h1{font-family:'Noto Serif KR',serif;font-weight:900;font-size:clamp(26px,4vw,44px);margin:10px 0 6px}
.sub{color:var(--dim);font-size:14.5px}
.sub a{color:var(--brass);text-decoration:none}
.wrap{overflow-x:auto;padding:26px 5vw 80px}
table{border-collapse:separate;border-spacing:0;min-width:760px;width:100%}
thead th{position:sticky;top:0;background:var(--night);border-bottom:2px solid var(--brass);padding:10px 12px;text-align:left;min-width:150px}
.cn{font-family:'Noto Serif KR',serif;font-weight:900;font-size:17px}
.hg{font-size:11px;color:var(--dim);letter-spacing:.12em;margin-top:2px}
.hg::before{content:"패권: "}
th.lane{position:sticky;left:0;background:var(--night2);border-right:2px solid var(--brass);padding:12px 14px;font-family:'Noto Serif KR',serif;font-weight:900;font-size:15px;letter-spacing:.2em;writing-mode:vertical-rl;text-orientation:upright;min-width:0;width:52px}
td{border-bottom:1px solid var(--line);border-right:1px dashed rgba(238,232,218,.08);padding:10px 8px;vertical-align:top}
.chip2{display:block;width:100%;text-align:left;background:var(--night2);border:1px solid var(--line);border-left:4px solid var(--seal);border-radius:5px;color:var(--paper);font-family:inherit;font-size:12.5px;line-height:1.5;padding:7px 9px;margin:5px 0;cursor:pointer;word-break:keep-all;transition:.15s}
.chip2:hover{border-color:var(--brass);transform:translateX(3px)}
.chip2 .cy{color:var(--dim);font-size:11px;margin-right:6px}
dialog{width:min(780px,93vw);max-height:87vh;background:var(--paper);color:#221E15;border:none;border-radius:10px;padding:0}
dialog::backdrop{background:rgba(10,13,20,.74)}
.dhead{padding:28px 36px 16px;border-bottom:1px solid rgba(34,30,21,.15);position:sticky;top:0;background:var(--paper)}
.dhead .cat{font-size:12px;letter-spacing:.28em;color:var(--seal)}
.dhead h2{font-family:'Noto Serif KR',serif;font-weight:900;font-size:24px;margin:6px 0 2px;word-break:keep-all}
.dbody{padding:22px 36px 42px;overflow-y:auto;font-size:15.5px;line-height:1.85}
.dbody h3{font-family:'Noto Serif KR',serif;margin:22px 0 10px;font-size:18px;border-bottom:1px solid rgba(34,30,21,.15);padding-bottom:6px}
.dbody p{margin:10px 0}.dbody ul,.dbody ol{margin:10px 0 10px 22px}.dbody li{margin:6px 0}
.dbody em{color:#7A6433}
.close{position:absolute;top:20px;right:22px;background:none;border:1px solid rgba(34,30,21,.3);border-radius:999px;width:33px;height:33px;cursor:pointer;font-family:inherit}
@media (max-width:620px){th.lane{writing-mode:horizontal-tb;width:auto;font-size:13px;letter-spacing:.1em}}
</style></head><body>
<header><div class="eyebrow">Sage History</div><h1>동서 대조 연표</h1>
<div class="sub"><a href="timeline.html">← 연대기로 돌아가기</a> · 세기 × 권역 격자 · 패권 캡션은 통설 기준 참고 정보</div></header>
<div class="wrap"><table><thead><tr><th></th>__HEAD__</tr></thead><tbody>__BODY__</tbody></table></div>
<dialog id="dlg"><button class="close" onclick="dlg.close()">✕</button><div class="dhead"><div class="cat" id="dcat"></div><h2 id="dtitle"></h2></div><div class="dbody" id="dbody"></div></dialog>
<script>
const EVS=__DATA__;
document.querySelectorAll(".chip2").forEach(b=>b.onclick=()=>{const e=EVS[+b.dataset.i];
 document.getElementById("dcat").textContent=e.track+" · "+e.period+" · "+e.region+" · "+e.reliability;
 document.getElementById("dtitle").textContent=e.title;
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
