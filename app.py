"""식혜 주문 자동계산기 PRO v12 - 모바일/PC 반응형 단일 Streamlit 앱."""
import hashlib
import re
from datetime import datetime
from html import escape

import pandas as pd
import streamlit as st

st.set_page_config(page_title="식혜 주문 계산기 PRO", page_icon="🥤", layout="wide", initial_sidebar_state="collapsed")

PRODUCTS = {
    "일반식혜 1L": 5000,
    "일반식혜 500ml": 2950,
    "일반식혜 200ml 파우치": 1550,
    "단호박식혜 1L": 6700,
    "단호박식혜 500ml": 3950,
}
EXAMPLE = "식혜 1L 3개\n호박감주 500ml 2개\n200x4\n식혜 1L 4개랑 단호박식혜 500ml 1개 주세요"
DEFAULT_BANK = "3333-29-8917220"
DEFAULT_OWNER = "이서백(식혜명가)"

CSS = """
<style>
:root { --ink:#152237; --muted:#61738c; --border:#dce4ef; --blue:#2558bf; }
.stApp { background:linear-gradient(145deg,#f8fbff 0%,#edf3fa 58%,#f8fbff 100%); }
.block-container { max-width:1280px; padding-top:1.3rem; padding-bottom:4rem; }
/* Hide unused sidebar toggle/empty-space, since settings are now on the page. */
[data-testid="stSidebar"] { display:none !important; }
[data-testid="collapsedControl"] { display:none !important; }
.hero { display:flex; align-items:center; justify-content:space-between; gap:1.5rem; padding:22px 28px;
        background:linear-gradient(115deg,#111e34,#263f66); border-radius:22px; color:white;
        box-shadow:0 13px 30px #0b1e3930; margin-bottom:20px; }
.hero h1 { font-size:28px; line-height:1.15; letter-spacing:-.04em; font-weight:900; margin:0 0 6px; }
.hero p { margin:0; color:#d4e6ff; font-size:14px; }
.hero-tag { border:1px solid #b9d4fb88; color:#e6f2ff; border-radius:24px; padding:7px 12px;
            font-weight:750; white-space:nowrap; font-size:12px; }
.section-label { color:#152237; font-size:22px; font-weight:900; margin:.3rem 0 .55rem; letter-spacing:-.035em; }
.sub-note { color:#64748b; font-size:13px; margin-bottom:10px; }
/* Group cards */
div[data-testid="stVerticalBlockBorderWrapper"] { background:#f3f6fa; border:1px solid #d8e1ed;
    border-radius:18px; box-shadow:0 2px 6px #16376408; }
.product-name { color:#142033; font-size:17px; font-weight:850; margin-bottom:3px; }
.product-price { color:#62738c; font-size:13px; margin-bottom:4px; }
/* Calculator buttons, 54px touch targets */
div[class*="st-key-qbtn_"] button { min-height:52px !important; width:100%; border:1px solid #cedbec;
    border-radius:14px !important; background:#fff !important; box-shadow:0 2px 6px #122c4a14; }
div[class*="st-key-qbtn_"] button p,div[class*="st-key-qbtn_"] button span {
    font-size:22px !important; font-weight:900 !important; line-height:1 !important; color:#1a355f !important; }
div[class*="st-key-qbtn_"] button:hover { border-color:#4c78db; background:#f1f6ff !important; }
div[data-testid="stNumberInput"] input { font-size:18px !important; font-weight:800 !important; }
/* Specific pricing controls clearly visible even on mobile */
div[class*="st-key-shipping_on"] label { font-weight:850 !important; }
div[data-testid="stMetricValue"] { font-weight:850; }
div[data-testid="stTextArea"] textarea { font-size:16px !important; line-height:1.55; }
.total-card { border-radius:20px; padding:23px 25px; background:linear-gradient(140deg,#101c31,#203655);
    color:#fff; box-shadow:0 12px 28px #14274530; }
.total-title { color:#bdd7fb; font-weight:800; font-size:13px; }
.total-number { color:#ffcd4e; font-size:43px; font-weight:950; letter-spacing:-.045em; margin:6px 0 14px; white-space:nowrap; }
.total-row { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:9px 0;
    border-top:1px solid #ffffff22; font-size:14px; color:#e7eef9; }
.total-row strong { color:#fff; font-size:15px; }
.ship-free { background:#ddfaeb; color:#16643c; padding:4px 9px; border-radius:8px; font-weight:800; font-size:12px; }
.ship-pay { background:#e2eeff; color:#174ea6; padding:4px 9px; border-radius:8px; font-weight:800; font-size:12px; }
.quick-summary { background:#e9f2ff; border:1px solid #c9dcf8; border-radius:16px; padding:14px 16px; margin:5px 0 14px; }
.quick-label { color:#3d6395; font-weight:800; font-size:12px; }
.quick-value { font-size:27px; font-weight:950; color:#173a77; margin-top:2px; }
.foot-note { font-size:12px; color:#7b8799; }
.desktop-only { display:block; }
.mobile-only { display:none; }
@media(max-width: 760px) {
  .block-container { padding: .7rem .85rem 2.8rem !important; }
  .hero { padding:15px 17px; border-radius:16px; margin-bottom:12px; }
  .hero h1 { font-size:22px; }
  .hero p { font-size:12px; }
  .hero-tag { display:none; }
  .section-label { font-size:19px; }
  .desktop-only { display:none !important; }
  .mobile-only { display:block !important; }
  .total-card { padding:17px 19px; border-radius:17px; }
  .total-number { font-size:34px; margin:3px 0 8px; }
  .total-row { font-size:13px; padding:7px 0; }
  .total-row strong { font-size:14px; }
  .product-name { font-size:16px; }
  div[class*="st-key-qbtn_"] button { min-height:49px !important; border-radius:12px !important; }
  div[class*="st-key-qbtn_"] button p { font-size:23px !important; }
  div[data-testid="stNumberInput"] input { font-size:18px !important; }
  div[data-testid="stTextArea"] textarea { font-size:16px !important; }
  /* Outer Streamlit column gutter is smaller on phones */
  div[data-testid="stVerticalBlockBorderWrapper"] { border-radius:15px; }
  /* Keep FOUR calculator keys on one row, even on narrow phones. */
  div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-qbtn_"]) {
     flex-direction:row !important; flex-wrap:nowrap !important; gap:6px !important;
  }
  div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-qbtn_"]) > div[data-testid="stColumn"] {
     flex:1 1 0 !important; min-width:0 !important; width:auto !important;
  }
  /* Settings are never squeezed into two tiny columns on phones. */
  div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-shipping_on"]),
  div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-price_0"]) {
     flex-direction:column !important;
  }
  div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-shipping_on"]) > div[data-testid="stColumn"],
  div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-price_0"]) > div[data-testid="stColumn"] {
     flex:1 1 auto !important; width:100% !important; min-width:0 !important;
  }
  /* Main two-column desktop layout becomes a single full-width column on phones. */
  div[data-testid="stHorizontalBlock"]:has(.product-name) {
     flex-direction:column !important;
  }
  div[data-testid="stHorizontalBlock"]:has(.product-name) > div[data-testid="stColumn"] {
     flex:1 1 auto !important; width:100% !important; min-width:0 !important;
  }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# --------- Order parsing: pure functions, independently testable ---------
KOREAN_NUMBERS = {"하나":1,"한":1,"두":2,"둘":2,"세":3,"셋":3,"네":4,"넷":4,"다섯":5,"여섯":6,"일곱":7,"여덟":8,"아홉":9,"열":10}
BASE_PART = r"(?:단\s*호박\s*(?:식혜|식해|감주)?|호박\s*(?:식혜|식해|감주)?|일반\s*(?:식혜|식해|감주)?|식혜|식해|감주)"
SIZE_PART = r"(?:1000\s*(?:ml|mℓ)|1\s*(?:l|리터)|500\s*(?:ml|mℓ)|0\.5\s*l|200\s*(?:ml|mℓ)|0\.2\s*l|200|500|1000|큰\s*거|큰\s*것|큰\s*병|큰거|대병|파우치|pouch)"
QTY_PART = r"(?:\d{1,4}|하나|한|두|둘|세|셋|네|넷|다섯|여섯|일곱|여덟|아홉|열)"
UNIT_PART = r"(?:개|병|통|팩|봉|박스|개입|파우치|잔)?"
# Use full known size and number in preference to accidentally parsing '500' as qty.
ORDER_PATTERNS = [
    re.compile(rf"(?P<base>{BASE_PART})\s*(?P<size>{SIZE_PART})\s*(?:짜리)?\s*(?:x|×|\*|에)?\s*(?P<qty>{QTY_PART})\s*{UNIT_PART}", re.I),
    re.compile(rf"(?P<size>{SIZE_PART})\s*(?P<base>{BASE_PART})\s*(?P<qty>{QTY_PART})\s*{UNIT_PART}", re.I),
    re.compile(rf"(?P<size>{SIZE_PART})\s*(?:x|×|\*|에|짜리)?\s*(?P<qty>{QTY_PART})\s*(?:개|병|통|팩|봉|박스|개입|파우치)?", re.I),
    re.compile(rf"(?P<base>{BASE_PART})\s*(?P<qty>{QTY_PART})\s*(?:개|병|통|팩|봉|박스|파우치|잔)", re.I),
    re.compile(rf"(?P<qty>{QTY_PART})\s*(?:개|병|통|팩|봉|박스)\s*(?P<base>{BASE_PART})\s*(?P<size>{SIZE_PART})?", re.I),
    re.compile(rf"(?P<base>{BASE_PART})\s*(?P<size>{SIZE_PART})", re.I),
]


def normalize(text):
    text = str(text).translate(str.maketrans("１２３４５６７８９０Ｌｌ", "1234567890Ll"))
    text = text.replace("㎖", "ml").replace("ℓ", "l").replace("밀리", "ml").replace("미리", "ml")
    # Treat '200ml 파우치' as ONE product descriptor, not two separate orders.
    text = re.sub(r"200\s*(?:ml|mℓ)?\s*(?:파우치|팩)", "파우치", text, flags=re.I)
    # Newlines are intentional order boundaries: do not merge two different orders.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def quantity(raw):
    if not raw:
        return 1
    raw = raw.strip()
    if raw.isdigit():
        return int(raw)
    return KOREAN_NUMBERS.get(raw, 1)


def get_product(base, size, default_size):
    b = re.sub(r"\s+", "", base or "")
    kind = "단호박식혜" if "호박" in b else "일반식혜"
    s = re.sub(r"\s+", "", size or "").lower()
    if not s:
        size_label = default_size
    elif "200" in s or "0.2" in s or "파우치" in s or "pouch" in s:
        size_label = "200ml 파우치"
    elif "500" in s or "0.5" in s:
        size_label = "500ml"
    else:
        size_label = "1L"
    if kind == "단호박식혜" and size_label == "200ml 파우치":
        return None  # 미등록 상품을 다른 용량으로 임의 변환하지 않음
    return f"{kind} {size_label}"


def parse_orders(text, prices, default_size):
    text = normalize(text)
    if not text:
        return []
    final_rows = []
    for line in text.splitlines():
        matches = []
        # Do not silently turn unregistered pumpkin 200ml into ordinary 200ml.
        unsupported = [m.span() for m in re.finditer(
            rf"(?:단\s*호박|호박)\s*(?:식혜|식해|감주)?\s*200\s*(?:ml)?\s*(?:\d+\s*(?:개|병|팩|파우치))?",
            line, re.I,
        )]
        for pattern_index, pat in enumerate(ORDER_PATTERNS):
            for match in pat.finditer(line):
                if any(match.start() < b and match.end() > a for a,b in unsupported):
                    continue
                d = match.groupdict()
                base, size, qty = d.get("base"), d.get("size"), d.get("qty")
                if not (base or size):
                    continue
                prod = get_product(base, size, default_size)
                if prod is None or prod not in prices:
                    continue
                q = quantity(qty)
                if q < 1 or q > 10000:
                    continue
                matches.append((match.start(), match.end(), pattern_index, prod, q, match.group().strip()))
        selected = []
        for m in sorted(matches, key=lambda x: (x[2], -(x[1]-x[0]), x[0])):
            if any(m[0] < chosen[1] and m[1] > chosen[0] for chosen in selected):
                continue
            selected.append(m)
        final_rows.extend(
            {"입력방식":"문구 인식", "원문":m[5], "품목":m[3], "수량":m[4], "단가":prices[m[3]], "금액":m[4]*prices[m[3]]}
            for m in sorted(selected, key=lambda x:x[0])
        )
    return final_rows


def make_message_templates(summary, subtotal, rate, discount, charge_shipping, fee, amount, account, holder):
    product_lines = [f"- {r['품목']} {int(r['수량'])}개 = {int(r['금액']):,}원" for _,r in summary.iterrows()]
    shipping_line = f"택배비 = {fee if charge_shipping else 0:,}원"
    free_note = "택배비는 업체에서 부담합니다." if not charge_shipping else None
    discount_text = f"할인 {rate:g}% = -{discount:,}원" if discount > 0 else None
    def cleaned(lines):
        return "\n".join([x for x in lines if x is not None])
    basic = cleaned(["안녕하세요. 주문 금액 안내드립니다.", "", *product_lines, "", f"상품 합계 = {subtotal:,}원", discount_text, shipping_line, free_note, f"최종 결제금액 = {amount:,}원", "", "감사합니다."])
    receipt = cleaned(["[식혜명가 주문 계산서]", "--------------------", *product_lines, "--------------------", f"상품 합계   {subtotal:,}원", f"할인 금액   -{discount:,}원" if discount else None, f"택배비      {fee if charge_shipping else 0:,}원", "※ 택배비는 업체 부담" if not charge_shipping else None, "--------------------", f"최종 결제금액   {amount:,}원"])
    deposit = cleaned(["주문 금액 안내드립니다.", "", *product_lines, "", f"상품 합계: {subtotal:,}원", f"할인 금액: -{discount:,}원" if discount else None, f"택배비: {fee if charge_shipping else 0:,}원", free_note, f"입금하실 금액: {amount:,}원", "", f"입금계좌: {account.strip() or '미입력'}", f"예금주: {holder.strip() or '미입력'}", "", "입금 후 성함 남겨주시면 확인하겠습니다."])
    free = cleaned(["안녕하세요. 주문 금액 안내드립니다.", "", *product_lines, "", f"상품 합계 = {subtotal:,}원", discount_text, shipping_line, free_note if free_note else "택배비는 주문자가 부담합니다.", f"최종 결제금액 = {amount:,}원", "", "감사합니다."])
    return {"1. 친절 기본형":basic, "2. 깔끔 영수증형":receipt, "3. 입금 안내형":deposit, "4. 배송비 안내형":free}


def reset_quantities():
    for i in range(len(PRODUCTS)):
        st.session_state[f"qty_{i}"] = 0


def adjust_quantity(index, delta):
    key = f"qty_{index}"
    st.session_state[key] = max(0, int(st.session_state.get(key, 0)) + delta)


def fill_example():
    st.session_state["order_text"] = EXAMPLE


# --------- Interactive app ---------
for i in range(len(PRODUCTS)):
    st.session_state.setdefault(f"qty_{i}", 0)
st.session_state.setdefault("order_text", "")

st.markdown('''<div class="hero"><div><h1>🥤 식혜 주문 계산기 <span style="color:#91c7ff">PRO</span></h1>
<p>수량 선택 · 주문 문구 인식 · 할인 · 배송비까지 한 번에</p></div>
<div class="hero-tag">휴대폰 · PC 최적화</div></div>''', unsafe_allow_html=True)

st.markdown('<div class="section-label">① 결제 설정</div>', unsafe_allow_html=True)
st.caption("휴대폰에서도 바로 조정할 수 있도록 배송비와 할인 설정을 메인 화면에 배치했습니다.")

with st.container(border=True):
    ctrl_left, ctrl_right = st.columns([1.25, 1], gap="small", vertical_alignment="bottom")
    with ctrl_left:
        shipping_on = st.toggle("택배비 받기", value=True, key="shipping_on", help="끄면 무료배송으로 처리합니다. 배송비는 업체 부담으로 고객 문구에 반영됩니다.")
        st.caption("✅ 배송비 0원 · 업체 부담" if not shipping_on else "택배비가 최종 결제금액에 추가됩니다")
    with ctrl_right:
        configured_fee = st.number_input("택배비 설정 (원)", min_value=0, step=500, value=4000, key="fee")
    rate = st.number_input("상품 전체 할인율 (%)", min_value=0.0, max_value=100.0, step=1.0, value=0.0, key="discount")

with st.expander("⚙️ 상품 가격 · 계좌 · 기본 용량 수정"):
    st.caption("기본 가격과 계좌가 미리 입력되어 있으며 필요할 때 수정할 수 있습니다.")
    price_col1, price_col2 = st.columns(2, gap="medium")
    prices = {}
    for i, (product, base_price) in enumerate(PRODUCTS.items()):
        with (price_col1 if i < 3 else price_col2):
            prices[product] = int(st.number_input(product, min_value=0, value=base_price, step=50, key=f"price_{i}"))
    default_size = st.selectbox("용량이 없는 주문의 기본 크기", ["1L", "500ml", "200ml 파우치"], key="size_default")
    st.markdown("**입금 안내 계좌**")
    account_number = st.text_input("계좌번호", value=DEFAULT_BANK, key="bank")
    account_holder = st.text_input("예금주", value=DEFAULT_OWNER, key="holder")

# The controls inside an expander still execute, even when visually collapsed.
st.markdown('<div class="section-label">② 주문 문구 붙여넣기</div>', unsafe_allow_html=True)
st.caption("카톡 대화나 간단한 주문을 붙여넣으세요. 예시는 입력하지 않는 한 계산되지 않습니다.")
text_input = st.text_area("주문 내용", height=125, placeholder=EXAMPLE, key="order_text", label_visibility="collapsed")
with st.expander("입력 예시 확인"):
    st.code(EXAMPLE, language=None)
    st.button("예시 불러오기", on_click=fill_example, key="load_example")

# Calculate once from current widget state, for all presentation layouts.
rows = parse_orders(text_input, prices, default_size)
for i, product in enumerate(PRODUCTS):
    q = int(st.session_state[f"qty_{i}"])
    if q:
        rows.append({"입력방식":"수량 버튼", "원문":"", "품목":product, "수량":q, "단가":prices[product], "금액":q*prices[product]})

if rows:
    df = pd.DataFrame(rows)
    summary = df.groupby(["품목", "단가"], sort=False, as_index=False).agg({"수량":"sum", "금액":"sum"})
    summary["_sort"] = summary["품목"].map({p:i for i,p in enumerate(PRODUCTS)})
    summary = summary.sort_values("_sort").drop(columns="_sort")
    subtotal = int(summary["금액"].sum())
    total_qty = int(summary["수량"].sum())
else:
    df = pd.DataFrame(columns=["입력방식", "원문", "품목", "수량", "단가", "금액"])
    summary = pd.DataFrame(columns=["품목", "단가", "수량", "금액"])
    subtotal = total_qty = 0

discount_amount = round(subtotal * rate / 100)
shipping_cost = configured_fee if shipping_on and total_qty else 0
final_amount = max(0, subtotal - discount_amount) + shipping_cost


def total_card(class_name):
    shipping_status = '<span class="ship-pay">구매자 부담</span>' if shipping_on else '<span class="ship-free">업체 부담 / 무료배송</span>'
    return f'''<div class="{class_name}"><div class="total-card">
      <div class="total-title">최종 결제금액</div><div class="total-number">{final_amount:,}원</div>
      <div class="total-row"><span>총 수량</span><strong>{total_qty:,}개</strong></div>
      <div class="total-row"><span>상품 합계</span><strong>{subtotal:,}원</strong></div>
      {f'<div class="total-row"><span>상품 할인 ({rate:g}%)</span><strong>-{discount_amount:,}원</strong></div>' if discount_amount > 0 else ''}
      <div class="total-row"><span>택배비 {shipping_status}</span><strong>{shipping_cost:,}원</strong></div>
    </div></div>'''

# On phones this card appears BEFORE five product rows, rather than below them.
st.markdown(total_card("mobile-only"), unsafe_allow_html=True)

left, right = st.columns([1.26, 1], gap="large")
with left:
    st.markdown('<div class="section-label">③ 수량 버튼 계산기</div>', unsafe_allow_html=True)
    st.button("수량 전체 초기화", on_click=reset_quantities, key="reset_all")
    for i, (product, price) in enumerate(prices.items()):
        with st.container(border=True):
            st.markdown(f'<div class="product-name">{escape(product)}</div><div class="product-price">단가 {price:,}원</div>', unsafe_allow_html=True)
            # Full-width numeric input + four equal-sized touch keys: never over-nest columns.
            st.number_input("수량", min_value=0, step=1, key=f"qty_{i}", label_visibility="collapsed")
            bs = st.columns(4, gap="small")
            for col, (symbol, delta) in zip(bs, [("−", -1), ("+", 1), ("+5", 5), ("0", None)]):
                with col:
                    if delta is None:
                        st.button(symbol, key=f"qbtn_{i}_zero", on_click=adjust_quantity, args=(i, -999999), use_container_width=True)
                    else:
                        st.button(symbol, key=f"qbtn_{i}_{delta}", on_click=adjust_quantity, args=(i, delta), use_container_width=True)

with right:
    st.markdown('<div class="section-label desktop-only">총합계</div>', unsafe_allow_html=True)
    st.markdown(total_card("desktop-only"), unsafe_allow_html=True)
    st.markdown('<div class="sub-note desktop-only">수량 또는 배송비를 바꾸면 바로 다시 계산됩니다.</div>', unsafe_allow_html=True)

st.divider()
st.markdown('<div class="section-label">④ 주문 계산 내역</div>', unsafe_allow_html=True)
if summary.empty:
    st.info("수량 버튼을 누르거나 주문 문구를 입력하면 계산 내역이 나타납니다.")
else:
    presentation = summary.copy()
    presentation["단가"] = presentation["단가"].apply(lambda x: f"{x:,}원")
    presentation["금액"] = presentation["금액"].apply(lambda x: f"{x:,}원")
    st.dataframe(presentation, hide_index=True, use_container_width=True)
    with st.expander("입력별 인식 내역 확인"):
        st.dataframe(df, hide_index=True, use_container_width=True)

st.divider()
st.markdown('<div class="section-label">⑤ 고객에게 보낼 계산 문구</div>', unsafe_allow_html=True)
if summary.empty:
    st.caption("주문이 생기면 고객 메시지를 자동 생성합니다.")
else:
    templates = make_message_templates(summary, subtotal, rate, discount_amount, shipping_on, configured_fee, final_amount, account_number, account_holder)
    st.selectbox("문구 형식", list(templates), key="template_type")
    draft = templates[st.session_state["template_type"]]
    signature = hashlib.sha256(draft.encode("utf-8")).hexdigest()
    if st.session_state.get("draft_signature") != signature:
        st.session_state["message_edit"] = draft
        st.session_state["draft_signature"] = signature
    edited_message = st.text_area("문구 직접 수정", key="message_edit", height=230)
    st.caption("아래 메시지의 복사 아이콘을 누르면 휴대폰에서도 복사할 수 있습니다.")
    st.code(edited_message, language=None)
    download_left, download_right = st.columns(2, gap="small")
    with download_left:
        st.download_button("문구 TXT 저장", edited_message.encode("utf-8-sig"), file_name="식혜_주문안내.txt", mime="text/plain", use_container_width=True)
    with download_right:
        st.download_button("계산 CSV 저장", summary.to_csv(index=False).encode("utf-8-sig"), file_name="식혜_계산결과.csv", mime="text/csv", use_container_width=True)

st.caption("휴대폰/PC 공용 | 개인정보와 주문 내역은 이 앱의 별도 데이터베이스에 저장하지 않습니다.")
