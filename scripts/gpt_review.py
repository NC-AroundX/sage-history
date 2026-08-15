#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gpt_review.py — 2차 감수자(GPT) 레인
직전 커밋에서 추가·수정된 events/*.md 카드만 골라 GPT API로 사실관계 감수를 받고,
결과를 reports/gpt-review-<날짜>.md 로 저장한다. 카드 자체는 절대 수정하지 않는다.
필요 환경변수: OPENAI_API_KEY (필수), OPENAI_MODEL (선택, 기본 gpt-5-mini)
"""
import os, re, json, subprocess, urllib.request, urllib.error, datetime, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
MAX_CARDS = 12          # 폭주 방지: 한 실행당 감수 카드 상한
MAX_CHARS = 7000        # 카드당 전송 길이 상한 (비용 통제)

SYSTEM_PROMPT = """당신은 역사 아카이브의 2차 감수자다. 다른 AI가 작성한 역사 사건 카드를 받는다.
당신의 임무는 '사실관계 오류'를 찾는 것이며, 문체·구성·의견에 대한 코멘트는 하지 않는다.

점검 항목:
1) 연도·날짜·기간 오류  2) 인명·지명·기관명 오류  3) 수치(퍼센트, 금액, 인원)의 명백한 오류
4) 인용문의 오귀속(다른 사람 말을 잘못 붙임)  5) 인과관계의 명백한 왜곡
6) '반복의 라임' 섹션의 과잉 유추(메커니즘이 실제로 다른데 닮았다고 주장)

출력 규칙 (반드시 준수):
- 지적은 두 등급으로만 분류한다: [오류확실] = 당신이 확실히 아는 오류, [검토제안] = 의심되지만 확실하지 않은 것.
- 확실하지 않은 것을 [오류확실]로 올리지 마라. 근거를 한 줄 덧붙여라.
- 문제가 없으면 "지적 없음" 한 줄만 출력한다.
- 각 지적은 "- [등급] 원문 표현 → 문제점과 근거" 형식의 목록으로.
- 카드에 이미 ⚠️ 표시된 문장은 작성자도 불확실함을 아는 부분이니, 오류가 확실한 경우에만 지적한다.
- 출력은 한국어로, 카드당 최대 8건까지만."""

def changed_cards():
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-status", "HEAD~1", "HEAD", "--", "events/"],
            cwd=ROOT, text=True)
    except subprocess.CalledProcessError:
        out = subprocess.check_output(
            ["git", "show", "--name-status", "--pretty=format:", "HEAD", "--", "events/"],
            cwd=ROOT, text=True)
    files = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0][:1] in ("A", "M") and parts[-1].endswith(".md"):
            files.append(parts[-1])
    return files[:MAX_CARDS]

def call_gpt(card_title, card_text):
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"다음 카드를 감수하라.\n\n{card_text[:MAX_CHARS]}"},
        ],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {API_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        return f"(감수 실패: HTTP {e.code} — {detail})"
    except Exception as e:
        return f"(감수 실패: {e})"

def main():
    if not API_KEY:
        print("OPENAI_API_KEY 없음 — 감수 건너뜀"); return
    files = changed_cards()
    if not files:
        print("변경된 카드 없음 — 감수 건너뜀"); return
    today = datetime.date.today().isoformat()
    lines = [f"# GPT 감수 리포트 ({today})", "",
             f"모델: {MODEL} · 대상 {len(files)}건 · 이 리포트는 참고용이며 카드에 자동 반영되지 않는다.",
             "타당한 지적만 feedback.md에 옮겨 적으면 다음 배치에서 반영된다.", ""]
    flagged = 0
    for f in files:
        path = os.path.join(ROOT, f)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        m = re.search(r"^title:\s*(.+)$", text, re.M)
        title = m.group(1).strip() if m else os.path.basename(f)
        print(f"감수 중: {title}")
        verdict = call_gpt(title, text)
        if "지적 없음" not in verdict:
            flagged += 1
        lines += [f"## {title}", f"`{f}`", "", verdict, ""]
    lines.insert(4, f"**요약: {len(files)}건 중 {flagged}건에 지적 있음**")
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    out_path = os.path.join(ROOT, "reports", f"gpt-review-{today}.md")
    # 같은 날 재실행 시 덮어쓰지 않고 이어붙임
    mode = "a" if os.path.exists(out_path) else "w"
    with open(out_path, mode, encoding="utf-8") as fp:
        if mode == "a":
            fp.write("\n---\n\n")
        fp.write("\n".join(lines))
    print(f"리포트 저장: {out_path}")

if __name__ == "__main__":
    main()
