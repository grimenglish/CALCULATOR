"""식혜명가 주문 계산기 PRO v15.0 (PC/모바일, 빠른 부분 재실행).

- Streamlit fragment: 입력 조작 시 앱 전체 대신 계산기만 재실행
- 직접 입력 수량 / 카톡 주문 문구 합산
- 고객 배송비와 업체 부담 배송비 구분
- 계산 엔진은 Streamlit과 분리된 순수 함수로 구성
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from html import escape
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="식혜명가 주문 계산기 | PRO",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PRODUCTS: dict[str, int] = {
    "일반식혜 1L": 5000,
    "일반식혜 500ml": 2950,
    "일반식혜 200ml 파우치": 1550,
    "단호박식혜 1L": 6700,
    "단호박식혜 500ml": 3950,
}
BANK_DEFAULT = "IM뱅크 508106077707"
OWNER_DEFAULT = "이서백"
EXAMPLE = (
    "식혜 1L 3개\n"
    "호박감주 500ml 2개\n"
    "200x4\n"
    "식혜 1L 4개랑 단호박식혜 500ml 1개 주세요"
)
KOREAN_NUMBERS = {
    "하나": 1, "한": 1, "두": 2, "둘": 2, "세": 3, "셋": 3,
    "네": 4, "넷": 4, "다섯": 5, "여섯": 6, "일곱": 7,
    "여덟": 8, "아홉": 9, "열": 10,
}
BASE = r"(?:단\s*호박\s*(?:식혜|식해|감주)?|호박\s*(?:식혜|식해|감주)?|일반\s*(?:식혜|식해|감주)?|식혜|식해|감주)"
SIZE = r"(?:1000\s*(?:ml|mℓ)|1\s*(?:l|리터)|500\s*(?:ml|mℓ)|0\.5\s*l|200\s*(?:ml|mℓ)|0\.2\s*l|200|500|1000|큰\s*거|큰\s*것|큰\s*병|큰거|대병|파우치|pouch)"
QTY = r"(?:\d{1,4}|하나|한|두|둘|세|셋|네|넷|다섯|여섯|일곱|여덟|아홉|열)"
UNIT = r"(?:개|병|통|팩|봉|박스|개입|파우치|잔)"
ORDER_PATTERNS = tuple(re.compile(x, re.IGNORECASE) for x in (
    rf"(?P<base>{BASE})\s*(?P<size>{SIZE})\s*(?:짜리)?\s*(?:x|×|\*|에)?\s*(?P<qty>{QTY})\s*{UNIT}?",
    rf"(?P<size>{SIZE})\s*(?P<base>{BASE})\s*(?P<qty>{QTY})\s*{UNIT}?",
    rf"(?P<size>{SIZE})\s*(?:x|×|\*|에|짜리)?\s*(?P<qty>{QTY})\s*{UNIT}?",
    rf"(?P<base>{BASE})\s*(?P<qty>{QTY})\s*{UNIT}",
    rf"(?P<qty>{QTY})\s*{UNIT}\s*(?P<base>{BASE})\s*(?P<size>{SIZE})?",
    rf"(?P<base>{BASE})\s*(?P<size>{SIZE})",
))
UNSUPPORTED_PUMPKIN = re.compile(
    rf"(?:단\s*호박|호박)\s*(?:식혜|식해|감주)?\s*200\s*(?:ml|mℓ)?(?:\s*(?:파우치|팩))?(?:\s*\d+\s*{UNIT})?",
    re.IGNORECASE,
)


def normalize(text: str) -> str:
    text = str(text).translate(str.maketrans("１２３４５６７８９０Ｌｌ", "1234567890Ll"))
    text = text.replace("㎖", "ml").replace("ℓ", "l").replace("밀리", "ml").replace("미리", "ml")
    # '식혜 200ml 파우치 3개'는 한 제품을 뜻하므로 중복 탐지를 방지
    text = re.sub(r"200\s*(?:ml|mℓ)\s*(?:파우치|팩)", "파우치", text, flags=re.I)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r" *\n *", "\n", text).strip()


def to_quantity(raw: str | None) -> int:
    if not raw:
        return 1
    raw = raw.strip()
    return int(raw) if raw.isdigit() else KOREAN_NUMBERS.get(raw, 1)


def identify_product(base: str | None, size: str | None, default_size: str) -> str | None:
    kind = "단호박식혜" if "호박" in re.sub(r"\s+", "", base or "") else "일반식혜"
    size_str = re.sub(r"\s+", "", size or "").lower()
    if not size_str:
        volume = default_size
    elif any(x in size_str for x in ("200", "0.2", "파우치", "pouch")):
        volume = "200ml 파우치"
    elif "500" in size_str or "0.5" in size_str:
        volume = "500ml"
    else:
        volume = "1L"
    if kind == "단호박식혜" and volume == "200ml 파우치":
        return None
    return f"{kind} {volume}"


def parse_orders(text: str, default_size: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Return per-item results and unsupported notes. No Streamlit dependencies."""
    text = normalize(text)
    if not text:
        return [], []
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    # Huge chat logs should not be evaluated blindly in the browser app.
    for line in text.splitlines()[:150]:
        if not line.strip():
            continue
        blocked_spans = [m.span() for m in UNSUPPORTED_PUMPKIN.finditer(line)]
        if blocked_spans:
            warnings.append("단호박식혜 200ml 파우치는 등록되지 않아 제외했어요.")
        candidates = []
        for priority, pattern in enumerate(ORDER_PATTERNS):
            for match in pattern.finditer(line):
                if any(match.start() < end and match.end() > start for start, end in blocked_spans):
                    continue
                d = match.groupdict()
                prod = identify_product(d.get("base"), d.get("size"), default_size)
                if prod is None:
                    continue
                q = to_quantity(d.get("qty"))
                if not 1 <= q <= 9999:
                    continue
                candidates.append((match.start(), match.end(), priority, prod, q, match.group().strip()))
        selected = []
        for c in sorted(candidates, key=lambda x: (x[2], -(x[1] - x[0]), x[0])):
            if any(c[0] < existing[1] and c[1] > existing[0] for existing in selected):
                continue
            selected.append(c)
        for c in sorted(selected, key=lambda x: x[0]):
            rows.append({"품목": c[3], "수량": c[4], "원문": c[5], "입력": "카톡"})
    if len(text.splitlines()) > 150:
        warnings.append("150줄까지만 분석했어요. 주문이 더 있으면 나누어 입력해 주세요.")
    return rows, list(dict.fromkeys(warnings))


def calculate(prices: dict[str, int], quantities: dict[str, int], pasted: list[dict[str, Any]],
              rate: float, shipping_on: bool, configured_fee: int) -> dict[str, Any]:
    """Compute whole order exactly once; avoid dataframe dependencies and rerenders."""
    summed = defaultdict(int)
    details = []
    for product, qty in quantities.items():
        if product in prices and qty > 0:
            summed[product] += qty
            details.append({"입력": "버튼", "원문": "", "품목": product, "수량": qty})
    for row in pasted:
        if row["품목"] in prices and row["수량"] > 0:
            summed[row["품목"]] += row["수량"]
            details.append(row)
    items = [{"품목": p, "수량": summed[p], "단가": prices[p], "금액": summed[p] * prices[p]}
             for p in prices if summed[p] > 0]
    subtotal = sum(item["금액"] for item in items)
    # Python round => banker's rounding; monetary amounts use 0.5 -> round half up.
    from decimal import Decimal, ROUND_HALF_UP
    discount = int((Decimal(subtotal) * Decimal(str(rate)) / Decimal(100))
                   .quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    after_discount = subtotal - discount
    shipping = int(configured_fee) if shipping_on and items else 0
    return {"items": items, "details": details, "total_qty": sum(x["수량"] for x in items),
            "subtotal": subtotal, "discount": discount, "after_discount": after_discount,
            "shipping": shipping, "final": after_discount + shipping, "rate": rate,
            "shipping_on": shipping_on}


def make_messages(order: dict[str, Any], account: str, owner: str) -> dict[str, str]:
    lines = [f"- {it['품목']} {it['수량']}개 = {it['금액']:,}원" for it in order["items"]]
    total = order["subtotal"]
    discount = order["discount"]
    shipping = order["shipping"]
    final = order["final"]
    free_note = "택배비는 업체에서 부담합니다." if not order["shipping_on"] else None
    disc1 = f"할인 {order['rate']:g}% = -{discount:,}원" if discount else None
    disc2 = f"할인 금액: -{discount:,}원" if discount else None

    def join(*entries: str | None) -> str:
        return "\n".join(x for x in entries if x is not None)

    friendly = join("안녕하세요. 식혜명가입니다.", "주문 금액 안내드립니다.", "", *lines, "",
                    f"상품 합계 = {total:,}원", disc1, f"택배비 = {shipping:,}원", free_note,
                    f"최종 결제금액 = {final:,}원", "", "감사합니다!")
    receipt = join("[식혜명가 주문 계산서]", "--------------------", *lines,
                   "--------------------", f"상품 합계  {total:,}원",
                   f"할인 금액  -{discount:,}원" if discount else None,
                   f"택배비  {shipping:,}원", "※ 택배비는 업체 부담" if free_note else None,
                   "--------------------", f"최종 결제금액  {final:,}원", "",
                   f"입금계좌: {account.strip() or '미입력'}",
                   f"예금주: {owner.strip() or '미입력'}", "",
                   "감사합니다.")
    deposit = join("안녕하세요. 주문 금액 및 입금계좌 안내드립니다.", "", *lines, "",
                   f"상품 합계: {total:,}원", disc2, f"택배비: {shipping:,}원", free_note,
                   f"입금하실 금액: {final:,}원", "", f"입금계좌: {account.strip() or '미입력'}",
                   f"예금주: {owner.strip() or '미입력'}", "", "감사합니다.")
    shipping_note = free_note or "택배비는 고객 부담으로 계산되었습니다."
    shipping_template = join("[식혜명가 배송비 안내]", "", *lines, "",
                             f"상품 합계 = {total:,}원", disc1, f"택배비 = {shipping:,}원",
                             shipping_note, f"최종 결제금액 = {final:,}원")
    return {"친절 기본형": friendly, "깔끔 영수증형": receipt,
            "입금 안내형": deposit, "배송비 안내형": shipping_template}



def make_copy_button_html(message: str) -> str:
    """One-touch clipboard button. All customer text is JS-string encoded, never parsed as markup."""
    # Encoding the string as a JS literal while escaping HTML special chars prevents
    # a malicious pasted message from ending the script or altering the page.
    payload = (json.dumps(message, ensure_ascii=False)
               .replace("<", "\\u003c").replace(">", "\\u003e")
               .replace("&", "\\u0026").replace("\u2028", "\\u2028")
               .replace("\u2029", "\\u2029"))
    return r"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box} html,body{margin:0;padding:0;background:transparent;font-family:system-ui,-apple-system,'Malgun Gothic',sans-serif}
button{width:100%;height:49px;padding:0 12px;background:#2563eb;color:#fff;border:0;border-radius:11px;
font-weight:850;font-size:16px;cursor:pointer;touch-action:manipulation;-webkit-tap-highlight-color:transparent}
button:active{transform:scale(.99)}button:focus-visible{outline:3px solid #93c5fd}
button.ok{background:#15803d}button.fail{background:#b45309}
#status{display:block;height:17px;padding:3px 2px 0;font-size:11px;color:#475569}
</style></head><body>
<button id="copy" type="button" aria-label="고객 안내 문구 바로 복사">📋 고객 안내 문구 바로 복사</button>
<span id="status" role="status" aria-live="polite"></span>
<script>
const message = __MESSAGE__;
const button = document.getElementById('copy');
const status = document.getElementById('status');
function legacyCopy() {
  const area=document.createElement('textarea');
  area.value=message; area.setAttribute('readonly','readonly');
  area.style.cssText='position:fixed;top:0;left:-9999px;opacity:0;';
  document.body.appendChild(area); area.focus(); area.select(); area.setSelectionRange(0,area.value.length);
  let success=false;
  try { success=document.execCommand('copy'); } catch(e) { success=false; }
  area.remove(); return success;
}
button.addEventListener('click', async () => {
  button.disabled=true;
  let copied=false;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(message);
      copied=true;
    }
  } catch(e) { copied=false; }
  if (!copied) copied=legacyCopy();
  button.disabled=false;
  if (copied) {
    button.className='ok';button.textContent='✓ 복사 완료';
    status.textContent='카톡 채팅창에 붙여넣으면 됩니다.';
  } else {
    button.className='fail';button.textContent='복사가 차단됐어요';
    status.textContent='브라우저가 복사를 제한했습니다. 아래 원본 문구를 길게 눌러 복사하세요.';
  }
});
</script></body></html>""".replace('__MESSAGE__', payload)

def change_qty(index: int, delta: int | None) -> None:
    key = f"qty_{index}"
    if delta is None:
        st.session_state[key] = 0
    else:
        st.session_state[key] = max(0, int(st.session_state.get(key, 0)) + delta)


def clear_qty() -> None:
    for i in range(len(PRODUCTS)):
        st.session_state[f"qty_{i}"] = 0


def load_example() -> None:
    st.session_state["order_text"] = EXAMPLE


def clear_text() -> None:
    st.session_state["order_text"] = ""


CSS = """
<style>
:root{--ink:#162438;--muted:#68798e;--line:#dce5ef;--paper:#fff;--bg:#f5f8fc;--accent:#2862db}
.stApp{background:var(--bg)}
.block-container{max-width:1180px;padding-top:1.2rem;padding-bottom:3rem}
header[data-testid="stHeader"]{background:transparent}
/* 모바일 웹뷰에서 페이지 확대/가로 넘침 최소화 */
*,*:before,*:after{box-sizing:border-box}
.hero{background:linear-gradient(110deg,#132540,#203f68);border-radius:18px;padding:22px 28px;color:#fff;margin-bottom:12px}
.hero .eyebrow{font-size:11px;letter-spacing:.10em;color:#b4d1ff;font-weight:800}
.hero h1{font-size:27px;line-height:1.25;letter-spacing:-.05em;margin:6px 0;color:#fff;font-weight:900}
.hero p{font-size:13px;color:#ddeaff;margin:5px 0 0}
.sec{font-size:18px;letter-spacing:-.035em;color:var(--ink);font-weight:850;margin:8px 0 10px}
.hint{font-size:12px;color:var(--muted)}
/* 작업영역의 시각적 카드만: Streamlit HTML 코드 직접 삽입 금지 */
.st-key-settings_card,.st-key-sum_card,.st-key-product_panel,.st-key-paste_card{border:1px solid var(--line)!important;background:var(--paper)!important;border-radius:17px!important;padding:15px!important;box-shadow:0 4px 16px rgba(24,43,70,.035)}
.st-key-settings_card{margin-bottom:16px}
.st-key-sum_card{background:linear-gradient(135deg,#12233b,#213d64)!important;border:0!important;padding:22px!important;box-shadow:0 10px 20px rgba(10,22,44,.14)}
.st-key-sum_card *{color:#edf4ff!important}
.st-key-sum_card [data-testid="stMetricValue"]{font-size:38px!important;font-weight:900!important;color:#ffd15c!important;letter-spacing:-.055em}
.st-key-sum_card [data-testid="stMetricLabel"]{font-size:14px!important;color:#bbd2ef!important}
.st-key-sum_card .sum-amount{color:#ffd15c!important}
.st-key-sum_card hr{border-color:#46607e}
.st-key-products_panel div[class*="st-key-product_"]{background:#eff3f8!important;margin-bottom:9px;padding:13px 15px!important}
.st-key-products_panel div[class*="st-key-product_"] .stMarkdown p{margin:0}
.st-key-products_panel div[class*="st-key-product_"] [data-testid="stNumberInput"] input{text-align:center;font-size:21px;font-weight:850;color:#18304c}
/* 수량 카드만 기본 숫자 input +/- 숨김: 하단 큰 버튼에서 조절 */
.st-key-products_panel div[class*="st-key-product_"] [data-testid="stNumberInput"] button{display:none!important}
/* 원터치 버튼: 텍스트가 네 칸 밖으로 잘리지 않도록 너비 제약 없음 */
div[class*="st-key-keypad_"] div[data-testid="stHorizontalBlock"]{flex-direction:row!important;flex-wrap:nowrap!important;gap:7px!important;width:100%!important}
div[class*="st-key-keypad_"] div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]{min-width:0!important;width:0!important;flex:1 1 0!important}
div[class*="st-key-qtybtn_"] button{min-height:44px!important;width:100%!important;min-width:0!important;padding:0 2px!important;border-radius:10px!important;border:1px solid #ccd9e9!important;background:#fff!important}
div[class*="st-key-qtybtn_"] button p{font-weight:900!important;font-size:18px!important;line-height:1.1!important;white-space:nowrap!important;color:#173f7c!important}
.st-key-products_panel div[class*="st-key-product_"] div[data-testid="stVerticalBlock"]{gap:.30rem}
/* 오른쪽 금액 영역은 PC에서 스크롤해도 보기 쉬운 위치 유지 */
@media(min-width:831px){.st-key-receipt_panel{position:sticky;top:1rem}}
/* 모바일 탭 반응성과 텍스트 자동 확대 억제 */
div[class*="st-key-qtybtn_"] button{touch-action:manipulation}
/* 유틸 컴포넌트 */
.st-key-order_text textarea{font-size:15px!important;min-height:112px}
div[data-testid="stAlert"]{border-radius:13px}
div[data-testid="stTextArea"] textarea{font-size:15px!important}
@media(max-width:830px){
 .block-container{max-width:100%;padding:.65rem .65rem 2rem!important}
 .hero{padding:16px;border-radius:14px;margin-bottom:10px}
 .hero h1{font-size:20px}
 .hero p{font-size:12px}
 .sec{font-size:17px}
 /* PC 좌우열을 모바일 세로로, 합계/붙여넣기를 위에 배치 */
 div[data-testid="stHorizontalBlock"]:has(.st-key-products_panel):has(.st-key-receipt_panel){flex-direction:column!important;flex-wrap:nowrap!important;gap:12px!important}
 div[data-testid="stHorizontalBlock"]:has(.st-key-products_panel):has(.st-key-receipt_panel)>div[data-testid="stColumn"]{min-width:0!important;max-width:100%!important;width:100%!important;flex:1 1 100%!important}
 div[data-testid="stHorizontalBlock"]:has(.st-key-products_panel):has(.st-key-receipt_panel)>div[data-testid="stColumn"]:has(.st-key-receipt_panel){order:-1!important}
 .st-key-sum_card{padding:18px!important}
 .st-key-sum_card [data-testid="stMetricValue"]{font-size:34px!important}
 .st-key-products_panel div[class*="st-key-product_"]{padding:12px!important;margin-bottom:7px}
 .st-key-settings_card,.st-key-paste_card{padding:12px!important}
 div[class*="st-key-qtybtn_"] button{min-height:47px!important}
 div[class*="st-key-qtybtn_"] button p{font-size:18px!important}
 div[data-testid="stTextArea"] textarea{font-size:16px!important}
}
@media(max-width:355px){div[class*="st-key-qtybtn_"] button p{font-size:16px!important}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(
    '<div class="hero"><div class="eyebrow">SIKHYE MYEONGGA / ORDER DESK</div>'
    '<h1>🥤 식혜 주문 자동계산기 PRO</h1>'
    '<p>수량 선택 · 카톡 주문 인식 · 할인과 배송 · 고객 안내까지 한 화면에서</p></div>',
    unsafe_allow_html=True,
)

# State pre-initialization must happen before widgets are instantiated.
for i in range(len(PRODUCTS)):
    st.session_state.setdefault(f"qty_{i}", 0)
st.session_state.setdefault("order_text", "")


@st.fragment
def calculator_app() -> None:
    with st.container(border=False, key="settings_card"):
        st.markdown('<div class="sec">① 결제 설정</div>', unsafe_allow_html=True)
        shipping_on = st.toggle("고객에게 택배비 받기", value=False, key="ship_on")
        if not shipping_on:
            st.caption("무료배송 적용 중 · 택배비는 업체가 부담합니다")
        s1, s2 = st.columns(2, gap="small")
        with s1:
            fee = st.number_input("택배비 (원)", min_value=0, value=4000, step=500, key="shipping_fee", disabled=not shipping_on)
        with s2:
            rate = st.number_input("상품 할인율 (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, key="discount_rate")

    with st.expander("⚙️ 기본 가격과 입금계좌 수정", expanded=False):
        st.caption("처음 등록된 가격과 계좌는 아래에서 언제든 변경할 수 있습니다.")
        prices = {}
        for i, (product, price) in enumerate(PRODUCTS.items()):
            prices[product] = int(st.number_input(product, min_value=0, value=price, step=50, key=f"price_{i}"))
        default_size = st.selectbox("용량을 적지 않은 주문 기본값", ["1L", "500ml", "200ml 파우치"], key="default_size")
        # 입금 정보는 운영자가 요청한 고정 정보입니다. 설정에서 변경되지 않습니다.
        bank = BANK_DEFAULT
        owner = OWNER_DEFAULT
        st.caption("입금계좌 (고정)")
        st.info(f"{bank}  |  예금주 {owner}")

    # Parse pasted orders once at the start. The fragment re-renders only its own UI on button clicks.
    paste_rows, warnings = parse_orders(st.session_state["order_text"], default_size)
    quantities = {p: int(st.session_state.get(f"qty_{i}", 0)) for i, p in enumerate(PRODUCTS)}
    order = calculate(prices, quantities, paste_rows, float(rate), shipping_on, int(fee))

    with st.container(key="work_layout"):
        left, right = st.columns([1.08, 0.92], gap="medium")
        with left:
            with st.container(key="products_panel"):
                st.markdown('<div class="sec">② 수량 버튼 계산기</div>', unsafe_allow_html=True)
                st.button("전체 수량 초기화", on_click=clear_qty, key="reset_qty")
                for i, (product, price) in enumerate(prices.items()):
                    with st.container(border=False, key=f"product_{i}"):
                        st.markdown(f"**{escape(product)}**")
                        st.caption(f"단가 {price:,}원")
                        st.number_input(f"{product} 수량", min_value=0, step=1,
                                        key=f"qty_{i}", label_visibility="collapsed")
                        with st.container(key=f"keypad_{i}"):
                            buttons = st.columns(4, gap="small")
                            for col, (txt, delta, suffix) in zip(buttons, [
                                ("−", -1, "minus"), ("+", 1, "plus"), ("+5", 5, "plus5"), ("0", None, "zero")
                            ]):
                                with col:
                                    with st.container(key=f"qtybtn_{i}_{suffix}"):
                                        st.button(txt, key=f"btn_{i}_{suffix}", on_click=change_qty,
                                                  args=(i, delta), use_container_width=True)
        with right:
            with st.container(key="receipt_panel"):
                with st.container(key="sum_card"):
                    st.metric("최종 결제금액", f"{order['final']:,}원")
                    st.markdown(f"**총 수량**　{order['total_qty']:,}개")
                    st.markdown(f"**상품 합계**　{order['subtotal']:,}원")
                    if order["discount"]:
                        st.markdown(f"**상품 할인**　-{order['discount']:,}원 ({rate:g}%)")
                    st.markdown(f"**택배비**　{order['shipping']:,}원")
                    if not shipping_on:
                        st.caption("✓ 택배비는 업체에서 부담합니다.")
                with st.container(key="paste_card"):
                    st.markdown('<div class="sec">③ 카톡 주문 붙여넣기</div>', unsafe_allow_html=True)
                    st.text_area("카톡 주문 문구", key="order_text", placeholder=EXAMPLE,
                                 height=125, label_visibility="collapsed")
                    e1, e2 = st.columns(2, gap="small")
                    with e1:
                        st.button("예시 불러오기", key="load_sample", on_click=load_example, use_container_width=True)
                    with e2:
                        st.button("문구 지우기", key="clear_sample", on_click=clear_text, use_container_width=True)
                    if warnings:
                        for warning in warnings:
                            st.warning(warning, icon="⚠️")

    st.markdown('<div class="sec">④ 계산 내역</div>', unsafe_allow_html=True)
    if not order["items"]:
        st.info("수량 버튼을 누르거나 카톡 주문 문구를 입력하면 계산됩니다.")
    else:
        st.dataframe(
            [{"품목": x["품목"], "수량": x["수량"], "단가": f"{x['단가']:,}원", "금액": f"{x['금액']:,}원"}
             for x in order["items"]],
            hide_index=True, use_container_width=True,
        )
        with st.expander("카톡 인식 상세내역 확인"):
            st.dataframe(order["details"], hide_index=True, use_container_width=True)

    st.markdown('<div class="sec">⑤ 고객에게 보낼 계산 문구</div>', unsafe_allow_html=True)
    if not order["items"]:
        st.caption("주문이 생기면 네 가지 안내 문구를 자동으로 만들어 줍니다.")
    else:
        templates = make_messages(order, bank, owner)
        selected = st.selectbox("안내 문구 스타일", list(templates), key="message_style")
        generated = templates[selected]
        signature = hashlib.sha256(generated.encode("utf-8")).hexdigest()
        if st.session_state.get("message_signature") != signature:
            st.session_state["editable_message"] = generated
            st.session_state["message_signature"] = signature
        message = st.text_area("문구 수정하기", key="editable_message", height=235)
        # 고객이 수정한 문구를 버튼을 한 번 누르는 즉시 복사합니다.
        # iframe의 사용자 클릭 이벤트에서 브라우저 Clipboard API를 호출합니다.
        components.html(make_copy_button_html(message), height=68, scrolling=False)
        # 일부 앱 내장 브라우저에서 클립보드 권한을 차단할 경우를 대비한 대안.
        with st.expander("복사 버튼이 차단될 경우 (대체 방법)", expanded=False):
            st.code(message, language=None)
        d1, d2 = st.columns(2, gap="small")
        with d1:
            st.download_button("안내 문구 저장", data=message.encode("utf-8-sig"),
                               file_name="식혜명가_안내문구.txt", mime="text/plain", use_container_width=True)
        with d2:
            import csv
            from io import StringIO
            out = StringIO()
            writer = csv.DictWriter(out, fieldnames=["품목", "수량", "단가", "금액"])
            writer.writeheader()
            writer.writerows(order["items"])
            st.download_button("계산 내역 CSV", data=out.getvalue().encode("utf-8-sig"),
                               file_name="식혜명가_주문계산.csv", mime="text/csv", use_container_width=True)


calculator_app()
st.caption("PC · 모바일 공용 | 주문 내용을 별도의 데이터베이스에 저장하지 않습니다.")
