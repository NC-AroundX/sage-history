#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_images.py — 사건별 수채화 이미지 생성 레인
events/*.md 카드마다 GPT 이미지 API로 세피아 수채화를 생성해
assets/images/<slug>.jpg 로 저장한다. 이미 있는 이미지는 건너뛴다.
- 스타일 프롬프트를 고정해 화풍 통일을 최대화한다.
- 이미지는 '무드 장식'이며 고증을 보장하지 않는다(사용자 승인된 원칙).
환경변수: OPENAI_API_KEY (필수), IMAGE_MODEL(기본 gpt-image-1)
인자: --limit N (N건만 생성, 테스트용) / --slugs a,b,c (특정 slug만)
"""
import os, re, glob, json, base64, argparse, urllib.request, urllib.error, sys, time
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(ROOT, "events")
OUT = os.path.join(ROOT, "assets", "images")
API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("IMAGE_MODEL", "gpt-image-1")

# 화풍 고정 프롬프트 — 모든 이미지에 동일 적용해 '한 가문' 통일감을 만든다
STYLE = ("muted sepia and soft teal watercolor illustration, historical mise-en-scène, "
         "loose ink linework with gentle watercolor washes and paper texture, "
         "warm cream background, atmospheric and dignified, no text, no words, no captions, "
         "no modern elements, painterly and timeless")

def parse_meta(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    meta, body = {}, text
    if m:
        body = text[m.end():]
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    return meta, body

def subject_of(meta, body):
    title = meta.get("title", "")
    region = meta.get("region", "")
    m = re.search(r"\*\*한 줄 정의:?\*\*\s*(.+)", body)
    gist = m.group(1)[:120] if m else ""
    # 사건의 시대·지역·주제를 장면 묘사로 (텍스트 렌더링 방지 위해 명사 위주)
    return f"A historical scene evoking: {title}. Setting: {region}. Mood: {gist}"

# 특정 slug의 자동 생성 프롬프트가 안전필터에 걸릴 때, 중립적 묘사로 대체
SUBJECT_OVERRIDES = {
    "gandhi-salt-march-1930": (
        "A tranquil historical scene set in early 20th-century coastal India: "
        "a line of people in simple traditional clothing walking peacefully along "
        "a coastal path toward the sea at dawn, calm and contemplative mood, "
        "gentle morning light, no conflict, no crowds of confrontation"
    ),
}

def build_prompt(meta, body):
    slug = meta.get("slug", "")
    subject = SUBJECT_OVERRIDES.get(slug) or subject_of(meta, body)
    return f"{subject}. Style: {STYLE}."

def gen_image(prompt):
    body = json.dumps({
        "model": MODEL, "prompt": prompt,
        "size": "1024x1536", "quality": "medium", "n": 1,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations", data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read().decode("utf-8"))
    d0 = data["data"][0]
    if d0.get("b64_json"):
        return base64.b64decode(d0["b64_json"])
    # URL 형태 대비
    with urllib.request.urlopen(d0["url"], timeout=120) as ir:
        return ir.read()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--slugs", type=str, default="")
    args = ap.parse_args()
    if not API_KEY:
        print("OPENAI_API_KEY 없음 — 중단"); return
    os.makedirs(OUT, exist_ok=True)
    want = set(s.strip() for s in args.slugs.split(",") if s.strip())
    made = 0
    for path in sorted(glob.glob(os.path.join(EV, "*.md"))):
        text = open(path, encoding="utf-8").read()
        meta, body = parse_meta(text)
        slug = meta.get("slug", os.path.splitext(os.path.basename(path))[0])
        if want and slug not in want:
            continue
        dest = os.path.join(OUT, f"{slug}.jpg")
        if os.path.exists(dest):
            continue
        if args.limit and made >= args.limit:
            break
        prompt = build_prompt(meta, body)
        print(f"생성 중: {meta.get('title', slug)}")
        try:
            blob = gen_image(prompt)
            with open(dest, "wb") as f:
                f.write(blob)
            made += 1
            print(f"  저장: assets/images/{slug}.jpg ({len(blob)//1024}KB)")
        except urllib.error.HTTPError as e:
            print(f"  실패: HTTP {e.code} — {e.read().decode('utf-8','replace')[:200]}")
        except Exception as e:
            print(f"  실패: {e}")
        time.sleep(1)
    print(f"\n완료: 신규 {made}건")

if __name__ == "__main__":
    main()
