"""식혜 주문 자동계산기 PRO v13 - 모바일 화면 수리, 합계 카드 안전 렌더링."""
import hashlib
import re
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

# CSS는 시각 요소에만 쓰고 계산값/고객 문구는 Streamlit 기본 컴포넌트로 표시합니다.
st.markdown(r'''<style>
:root { --ink:#13233a; --muted:#66788d; --border:#d7e2ee; }
.stApp { background:linear-gradient(145deg,#f8fbff 0%,#edf3fa 55%,#f8fbff 100%); }
.block-container { max-width:1200px; padding-top:1.3rem; padding-bottom:3rem; }
[data-testid="stSidebar"], [data-testid="collapsedControl"] {display:none!important;}
.hero { border-radius:20px; background:linear-gradient(110deg,#101d32,#294369); color:#fff; padding:23px 28px; margin-bottom:18px; box-shadow:0 12px 25px #20304a20; }
.hero-kicker {color:#bcd8ff; font-size:12px; font-weight:750; margin-bottom:4px;}
.hero-title { font-size:27px; font-weight:900; letter-spacing:-.04em; line-height:1.25; }
.hero-desc { font-size:13px; color:#d7e7fe; margin-top:6px; }
.section-title {font-size:21px; font-weight:900; color:#14223a; letter-spacing:-.025em; padding:4px 0 8px; }
.caption-small {font-size:13px; color:#64748b; margin-bottom:8px;}
/* 모바일에서도 배송비 설정과 수량 카드 영역을 읽기 쉽게 */
div[class*="st-key-prod_"] { background:#f1f5f9!important; border:1px solid #d4dfec!important; border-radius:16px!important; padding:13px 14px!important; margin-bottom:6px; }
div[class*="st-key-prod_"] .stMarkdown { margin-bottom:0!important; }
div[class*="st-key-prod_"] [data-testid="stNumberInput"] input {font-size:19px!important; font-weight:850!important;}
/* 네 개의 계산기 버튼: 굵고 큼. 동시에 글자가 잘리지 않도록 min-width 없앰 */
div[class*="st-key-qbtn_"] button {height:46px!important; width:100%!important; min-width:0!important; padding:0 2px!important; border-radius:12px!important; border:1px solid #c7d5e7!important; background:#fff!important;}
div[class*="st-key-qbtn_"] button p, div[class*="st-key-qbtn_"] button span { font-size:clamp(15px,1.55vw,19px)!important; font-weight:900!important; white-space:nowrap!important; color:#15345a!important; }
/* 합계는 raw HTML 대신 기본 요소를 쓰므로 코드 노출이 없음 */
div.st-key-mobile_total, div.st-key-desktop_total { background:linear-gradient(135deg,#12223c,#243d5d)!important; border:0!important; border-radius:18px!important; padding:18px 20px!important; box-shadow:0 12px 28px #13253b25!important; }
div.st-key-mobile_total *,div.st-key-desktop_total * {color:#edf4ff!important;}
div.st-key-mobile_total [data-testid="stMetricValue"], div.st-key-desktop_total [data-testid="stMetricValue"] {color:#ffcd51!important; font-size:34px!important; font-weight:900!important;}
div.st-key-mobile_total [data-testid="stMetricLabel"],div.st-key-desktop_total [data-testid="stMetricLabel"] {color:#b9d8ff!important;}
div.st-key-mobile_total p,div.st-key-desktop_total p {line-height:1.5!important;}
/* PC에서만 우측 합계 표시 */
.st-key-mobile_total {display:none!important;}
@media (max-width:800px) {
  .block-container { padding: .85rem .75rem 2rem!important; max-width:100%!important; }
  .hero {padding:17px; border-radius:15px; margin-bottom:12px;}
  .hero-title {font-size:21px;}
  .hero-desc {font-size:12px;}
  .section-title {font-size:18px;}
  /* Streamlit 그리드가 웹뷰에서 자동으로 접히지 않는 경우를 강제로 보정 */
  div[data-testid="stHorizontalBlock"]:has(.st-key-desktop_total) {flex-direction:column!important;flex-wrap:nowrap!important;gap:0!important;width:100%!important;}
  div[data-testid="stHorizontalBlock"]:has(.st-key-desktop_total) > div[data-testid="stColumn"] {flex:1 1 auto!important; width:100%!important;max-width:100%!important;min-width:0!important;}
  .st-key-mobile_total {display:block!important;}
  .st-key-desktop_total {display:none!important;}
  /* 모바일 4버튼은 반드시 한 줄; 폰 화면 전체 너비 사용 */
  div[class*="st-key-keypad_"] div[data-testid="stHorizontalBlock"] {flex-direction:row!important;flex-wrap:nowrap!important;gap:6px!important;width:100%!important;}
  div[class*="st-key-keypad_"] div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {flex:1 1 0!important;min-width:0!important;max-width:25%!important;width:0!important;}
  div[class*="st-key-qbtn_"] button {height:48px!important;min-width:0!important;padding:0!important;}
  div[class*="st-key-qbtn_"] button p, div[class*="st-key-qbtn_"] button span {font-size:17px!important;}
  div[class*="st-key-prod_"] {padding:12px!important; margin-bottom:4px;}
  div[data-testid="stTextArea"] textarea {font-size:16px!important;}
  div.st-key-mobile_total [data-testid="stMetricValue"] {font-size:32px!important;}
}
@media (max-width:355px) {
 div[class*="st-key-qbtn_"] button p, div[class*="st-key-qbtn_"] button span {font-size:15px!important;}
}
</style>''', unsafe_allow_html=True)

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



# ---- 입력 위젯을 먼저 렌더링하고 마지막에 합계를 한 번만 계산 ----
for i in range(len(PRODUCTS)):
    st.session_state.setdefault(f"qty_{i}", 0)
st.session_state.setdefault("order_text", "")

st.markdown('<div class="hero"><div class="hero-kicker">SIKHYE MYEONGGA · ORDER TOOLS</div><div class="hero-title">🥤 식혜 주문 자동계산기 PRO</div><div class="hero-desc">수량 선택 · 주문 문구 인식 · 배송비 · 할인 · 고객 안내</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">① 결제 설정</div>', unsafe_allow_html=True)
with st.container(border=True, key="payment_settings"):
    shipping_on = st.toggle("택배비 받기", value=True, key="shipping_on", help="끄면 배송비 0원이며 업체 부담으로 고객 문구에 표시합니다.")
    st.caption("무료배송 · 배송비는 업체 부담" if not shipping_on else "배송비를 고객 결제금액에 추가합니다")
    s_col, d_col = st.columns(2, gap="small")
    with s_col:
        configured_fee = st.number_input("택배비 설정 (원)", min_value=0, step=500, value=4000, key="fee", disabled=not shipping_on)
    with d_col:
        rate = st.number_input("상품 할인율 (%)", min_value=0.0, max_value=100.0, step=1.0, value=0.0, key="discount")

with st.expander("⚙️ 상품 가격 · 입금계좌 수정"):
    st.caption("기본 가격과 계좌정보를 수정할 수 있습니다.")
    prices = {}
    for i, (product, default_price) in enumerate(PRODUCTS.items()):
        prices[product] = int(st.number_input(product, min_value=0, value=default_price, step=50, key=f"price_{i}"))
    default_size = st.selectbox("용량 미기재 시 기본 크기", ["1L", "500ml", "200ml 파우치"], key="size_default")
    account_number = st.text_input("계좌번호", value=DEFAULT_BANK, key="bank")
    account_holder = st.text_input("예금주", value=DEFAULT_OWNER, key="holder")

st.markdown('<div class="section-title">② 카톡 주문 붙여넣기</div>', unsafe_allow_html=True)
st.caption("예시는 흐리게 보일 뿐 계산에는 포함되지 않습니다. 직접 입력하거나 붙여넣으세요.")
order_text = st.text_area("주문 내용", key="order_text", height=120, placeholder=EXAMPLE, label_visibility="collapsed")
with st.expander("주문 입력 예시 복사/불러오기"):
    st.code(EXAMPLE, language=None)
    st.button("예시를 입력창에 넣기", on_click=fill_example, key="sample_load")

# 주문 문구는 위에서 받고, 버튼 수량은 세션 상태를 통해 반영되므로
# 요약을 계산기보다 앞에 두어도 버튼 클릭 시 즉시 재계산됩니다.
rows = parse_orders(order_text, prices, default_size)
for i, product in enumerate(PRODUCTS):
    q = int(st.session_state.get(f"qty_{i}", 0))
    if q:
        rows.append({"입력방식":"버튼 입력", "원문":"", "품목":product, "수량":q, "단가":prices[product], "금액":q*prices[product]})

if rows:
    df = pd.DataFrame(rows)
    summary = df.groupby(["품목", "단가"], as_index=False, sort=False).agg({"수량":"sum", "금액":"sum"})
    summary["_order"] = summary["품목"].map({p:i for i,p in enumerate(PRODUCTS)})
    summary = summary.sort_values("_order").drop(columns="_order")
    subtotal = int(summary["금액"].sum())
    total_qty = int(summary["수량"].sum())
else:
    df = pd.DataFrame(columns=["입력방식", "원문", "품목", "수량", "단가", "금액"])
    summary = pd.DataFrame(columns=["품목", "단가", "수량", "금액"])
    subtotal = total_qty = 0

discount_amount = round(subtotal * rate / 100)
shipping_cost = int(configured_fee) if (shipping_on and total_qty > 0) else 0
final_amount = subtotal - discount_amount + shipping_cost

# 중요: 합계 카드에 여러 줄 문자열 HTML을 사용하지 않음.
# 기본 Streamlit 요소는 Markdown 자동 렌더링/코드 블럭 오작동의 영향을 받지 않습니다.
def render_summary(key):
    with st.container(border=True, key=key):
        st.metric("최종 결제금액", f"{final_amount:,}원")
        st.markdown(f"**총 수량**  {total_qty:,}개")
        st.markdown(f"**상품 합계**  {subtotal:,}원")
        if discount_amount:
            st.markdown(f"**상품 할인 ({rate:g}%)**  -{discount_amount:,}원")
        st.markdown(f"**택배비**  {shipping_cost:,}원")
        if not shipping_on:
            st.caption("✓ 택배비는 업체에서 부담합니다.")

# 모바일에는 합계를 먼저 표시하고, PC에는 오른쪽에 표시
render_summary("mobile_total")

left, right = st.columns([1.25, 1], gap="large")
with left:
    st.markdown('<div class="section-title">③ 수량 버튼 계산기</div>', unsafe_allow_html=True)
    st.button("수량 전체 초기화", on_click=reset_quantities, key="reset_all")
    for i, (product, price) in enumerate(prices.items()):
        with st.container(border=True, key=f"prod_{i}"):
            st.markdown(f"**{escape(product)}**")
            st.caption(f"단가 {price:,}원")
            st.number_input(f"{product} 수량", min_value=0, step=1, key=f"qty_{i}", label_visibility="collapsed")
            with st.container(key=f"keypad_{i}"):
                btn_cols = st.columns(4, gap="small")
                for col, (label, delta) in zip(btn_cols, [("−", -1), ("+", 1), ("+5", 5), ("0", None)]):
                    with col:
                        st.button(label, key=f"qbtn_{i}_{'zero' if delta is None else str(delta)}", on_click=adjust_quantity,
                                  args=(i, -999999 if delta is None else delta), use_container_width=True)
with right:
    render_summary("desktop_total")

st.divider()
st.markdown('<div class="section-title">④ 주문 계산 내역</div>', unsafe_allow_html=True)
if summary.empty:
    st.info("수량 버튼을 누르거나 주문 문구를 입력하면 계산 내역이 나타납니다.")
else:
    shown = summary.copy()
    shown["단가"] = shown["단가"].map(lambda x: f"{int(x):,}원")
    shown["금액"] = shown["금액"].map(lambda x: f"{int(x):,}원")
    st.dataframe(shown, hide_index=True, use_container_width=True)
    with st.expander("상세 인식 내역 확인"):
        st.dataframe(df, hide_index=True, use_container_width=True)

st.divider()
st.markdown('<div class="section-title">⑤ 고객에게 보낼 계산 문구</div>', unsafe_allow_html=True)
if summary.empty:
    st.caption("주문이 생기면 고객 메시지를 자동 생성합니다.")
else:
    templates = make_message_templates(summary, subtotal, rate, discount_amount, shipping_on,
                                       int(configured_fee), final_amount, account_number, account_holder)
    chosen = st.selectbox("문구 형식", list(templates), key="template_type")
    draft = templates[chosen]
    signature = hashlib.sha256(draft.encode("utf-8")).hexdigest()
    if st.session_state.get("draft_signature") != signature:
        st.session_state["message_edit"] = draft
        st.session_state["draft_signature"] = signature
    message = st.text_area("고객 발송 문구 (수정 가능)", key="message_edit", height=245)
    st.caption("아래 문구 오른쪽 위 복사 버튼을 눌러 복사하세요.")
    st.code(message, language=None)
    st.download_button("문구 TXT 다운로드", message.encode("utf-8-sig"), file_name="식혜_주문안내.txt", mime="text/plain", use_container_width=True)
    st.download_button("계산 결과 CSV 다운로드", summary.to_csv(index=False).encode("utf-8-sig"), file_name="식혜_계산결과.csv", mime="text/csv", use_container_width=True)

st.caption("휴대폰/PC 공용 · 주문·개인정보를 앱의 별도 데이터베이스에 저장하지 않습니다.")
