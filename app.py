import re
from datetime import datetime

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="식혜 주문 자동계산기 PRO",
    page_icon="🥤",
    layout="wide",
)


PRODUCTS = {
    "일반식혜 1L": 5000,
    "일반식혜 500ml": 3000,
    "일반식혜 200ml 파우치": 1800,
    "단호박식혜 1L": 6700,
    "단호박식혜 500ml": 4000,
}

PRODUCT_ORDER = list(PRODUCTS.keys())

KOR_NUM = {
    "한": 1, "하나": 1, "일": 1,
    "두": 2, "둘": 2, "이": 2,
    "세": 3, "셋": 3, "삼": 3,
    "네": 4, "넷": 4, "사": 4,
    "다섯": 5, "오": 5,
    "여섯": 6, "육": 6,
    "일곱": 7, "칠": 7,
    "여덟": 8, "팔": 8,
    "아홉": 9, "구": 9,
    "열": 10, "십": 10,
}

EXAMPLE_TEXT = """식혜 1L 3개
호박감주 500ml 2개
200x4
새벽에 식혜 1L 4개랑 단호박식혜 500ML 1개줘"""


# -----------------------------
# CSS
# -----------------------------
st.markdown(
    """
<style>
:root {
    --navy: #111827;
    --navy2: #172033;
    --ink: #0f172a;
    --muted: #64748b;
    --card: rgba(255, 255, 255, 0.86);
    --line: rgba(148, 163, 184, 0.28);
    --gold: #fbbf24;
    --green: #16a34a;
    --red: #dc2626;
}
.stApp {
    background:
        radial-gradient(circle at top left, rgba(59, 130, 246, .10), transparent 32%),
        linear-gradient(135deg, #f8fafc 0%, #eef2f7 45%, #f8fafc 100%);
}
.block-container {
    padding-top: 1.8rem;
    padding-bottom: 3rem;
}
.hero {
    background: linear-gradient(135deg, #111827 0%, #1f2937 60%, #334155 100%);
    color: white;
    padding: 30px 36px;
    border-radius: 24px;
    box-shadow: 0 20px 45px rgba(15, 23, 42, .22);
    margin-bottom: 24px;
}
.hero h1 {
    margin: 0 0 10px 0;
    font-size: 34px;
    line-height: 1.2;
    letter-spacing: -0.04em;
}
.hero p {
    color: #dbeafe;
    margin: 0;
    font-size: 16px;
}
.badge-wrap {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 18px;
}
.badge {
    background: rgba(255,255,255,.92);
    color: #1e3a8a;
    padding: 8px 12px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 800;
}
.section-title {
    font-size: 24px;
    font-weight: 900;
    color: var(--ink);
    margin: 10px 0 6px;
    letter-spacing: -0.04em;
}
.help-text {
    color: var(--muted);
    font-size: 14px;
    margin-bottom: 14px;
}
.card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 18px;
    box-shadow: 0 12px 26px rgba(15, 23, 42, .06);
}
.dark-card {
    background: linear-gradient(135deg, #0f172a 0%, #111827 100%);
    color: white;
    border-radius: 24px;
    padding: 24px;
    box-shadow: 0 22px 50px rgba(15,23,42,.28);
}
.big-money {
    font-size: 38px;
    font-weight: 950;
    color: #fbbf24;
    letter-spacing: -0.05em;
}
.dark-label {
    color: #93c5fd;
    font-weight: 800;
    font-size: 14px;
}
.product-title {
    font-size: 16px;
    font-weight: 900;
    color: var(--ink);
    margin-bottom: 2px;
}
.price-small {
    color: var(--muted);
    font-size: 13px;
    margin-bottom: 10px;
}
hr.soft {
    border: none;
    border-top: 1px solid rgba(148,163,184,.35);
    margin: 28px 0;
}
.copy-box {
    background: #f8fafc;
    border: 1px dashed rgba(100,116,139,.50);
    padding: 14px 16px;
    border-radius: 14px;
    white-space: pre-wrap;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    color: #334155;
}
</style>
""",
    unsafe_allow_html=True,
)


# -----------------------------
# Session state
# -----------------------------
for product in PRODUCT_ORDER:
    st.session_state.setdefault(f"qty_{product}", 0)

st.session_state.setdefault("order_text", "")


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def change_qty(product: str, delta: int):
    key = f"qty_{product}"
    current = safe_int(st.session_state.get(key, 0), 0)
    st.session_state[key] = max(0, current + delta)


def set_qty_zero(product: str):
    st.session_state[f"qty_{product}"] = 0


def reset_all_qty():
    for p in PRODUCT_ORDER:
        st.session_state[f"qty_{p}"] = 0


def put_example():
    st.session_state["order_text"] = EXAMPLE_TEXT


# -----------------------------
# Parser
# -----------------------------
BASE_ALIASES = [
    "단호박식혜", "단호박 식혜", "단호박감주", "단호박 감주",
    "호박감주", "호박 감주", "호박식혜", "호박 식혜", "단호박", "호박",
    "일반식혜", "일반 식혜", "일반감주", "일반 감주",
    "식혜", "식해", "감주",
]
BASE_RE = "|".join(re.escape(x) for x in sorted(BASE_ALIASES, key=len, reverse=True))

SIZE_WORDS = [
    "1000ml", "1000 ml", "1리터", "1 리터", "1l", "1 l", "1L", "1 L",
    "500ml", "500 ml", "0.5l", "0.5 l", "500",
    "200ml", "200 ml", "0.2l", "0.2 l", "200",
    "큰거", "큰 것", "큰것", "큰병", "대병", "대", "큰",
    "파우치", "팩", "pouch",
]
SIZE_RE = "|".join(re.escape(x) for x in sorted(SIZE_WORDS, key=len, reverse=True))

QTY_WORDS = list(KOR_NUM.keys()) + [str(i) for i in range(1, 1000)]
QTY_RE = "|".join(re.escape(x) for x in sorted(QTY_WORDS, key=len, reverse=True))
UNIT_RE = r"(?:개|병|통|팩|봉|개입|파우치|잔|박스|box)?"

PATTERNS = [
    # 식혜 1L 3개 / 단호박식혜500ml1개 / 200x4 / 500 4개
    re.compile(
        rf"(?P<base>{BASE_RE})?\s*(?P<size>{SIZE_RE})\s*(?:짜리)?\s*(?:x|X|×|\*|곱하기|에)?\s*(?P<qty>{QTY_RE})\s*{UNIT_RE}",
        re.IGNORECASE,
    ),
    # 1L 식혜 3개 / 500 호박 2개
    re.compile(
        rf"(?P<size>{SIZE_RE})\s*(?P<base>{BASE_RE})\s*(?P<qty>{QTY_RE})\s*{UNIT_RE}",
        re.IGNORECASE,
    ),
    # 식혜 3개 / 호박감주 두개 / 감주 4병
    re.compile(
        rf"(?P<base>{BASE_RE})\s*(?P<qty>{QTY_RE})\s*(?:개|병|통|팩|봉|개입|파우치|잔|박스|box)",
        re.IGNORECASE,
    ),
    # 3개 식혜 1L / 2병 호박감주 500
    re.compile(
        rf"(?P<qty>{QTY_RE})\s*(?:개|병|통|팩|봉|개입|파우치|잔|박스|box)\s*(?P<base>{BASE_RE})\s*(?P<size>{SIZE_RE})?",
        re.IGNORECASE,
    ),
    # 식혜 1L 처럼 수량이 없으면 1개 처리
    re.compile(
        rf"(?P<base>{BASE_RE})\s*(?P<size>{SIZE_RE})",
        re.IGNORECASE,
    ),
]


def normalize_for_parse(text: str) -> str:
    text = str(text)
    replacements = {
        "１": "1", "２": "2", "３": "3", "４": "4", "５": "5",
        "６": "6", "７": "7", "８": "8", "９": "9", "０": "0",
        "Ｌ": "L", "ｌ": "l", "×": "x",
        "리터": "리터", "미리": "ml", "밀리": "ml",
    }
    for a, b in replacements.items():
        text = text.replace(a, b)
    text = text.replace("㎖", "ml").replace("ℓ", "L")
    text = re.sub(r"(\d)\s*(l|L|ml|ML)", lambda m: m.group(1) + m.group(2).lower(), text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def qty_to_int(value) -> int:
    value = str(value).strip()
    if value.isdigit():
        return int(value)
    return KOR_NUM.get(value, 1)


def detect_base(base_text):
    if not base_text:
        return "일반식혜"

    b = base_text.replace(" ", "").lower()

    if "호박" in b or "단호박" in b:
        return "단호박식혜"

    if "일반" in b or "식혜" in b or "식해" in b or "감주" in b:
        return "일반식혜"

    return "일반식혜"


def detect_size(size_text, base, default_size):
    if not size_text:
        size = default_size
    else:
        s = str(size_text).replace(" ", "").lower()
        if any(x in s for x in ["200", "0.2", "파우치", "팩", "pouch"]):
            size = "200ml 파우치"
        elif any(x in s for x in ["500", "0.5"]):
            size = "500ml"
        elif any(x in s for x in ["1l", "1리터", "1000", "큰", "대"]):
            size = "1L"
        else:
            size = default_size

    # 현재 등록 상품에는 단호박 200ml 파우치가 없으므로 200ml 파우치 단독 표기는 일반식혜로 처리
    if base == "단호박식혜" and size == "200ml 파우치":
        return "500ml"

    return size


def product_from_parts(base_text, size_text, default_size):
    base = detect_base(base_text)
    size = detect_size(size_text, base, default_size)

    if size == "200ml 파우치":
        return "일반식혜 200ml 파우치"

    return f"{base} {size}"


def overlaps(span, used_spans):
    s, e = span
    for us, ue in used_spans:
        if s < ue and e > us:
            return True
    return False


def parse_text_orders(text: str, prices: dict, default_size: str):
    text = normalize_for_parse(text)
    rows = []

    if not text:
        return rows

    used_spans = []

    for pat in PATTERNS:
        for m in pat.finditer(text):
            if overlaps(m.span(), used_spans):
                continue

            gd = m.groupdict()
            base_text = gd.get("base")
            size_text = gd.get("size")
            qty_text = gd.get("qty") or "1"

            # 상품명도 없고 용량도 없는 건 주문으로 보지 않음
            if not base_text and not size_text:
                continue

            product = product_from_parts(base_text, size_text, default_size)
            if product not in prices:
                continue

            qty = max(1, qty_to_int(qty_text))
            amount = qty * int(prices[product])

            rows.append(
                {
                    "입력방식": "문구 인식",
                    "원문": m.group(0).strip(),
                    "품목": product,
                    "수량": qty,
                    "단가": int(prices[product]),
                    "금액": amount,
                }
            )
            used_spans.append(m.span())

    return rows


def parse_button_orders(prices: dict):
    rows = []
    for product in PRODUCT_ORDER:
        qty = safe_int(st.session_state.get(f"qty_{product}", 0), 0)
        if qty > 0:
            rows.append(
                {
                    "입력방식": "버튼 입력",
                    "원문": "-",
                    "품목": product,
                    "수량": qty,
                    "단가": int(prices[product]),
                    "금액": qty * int(prices[product]),
                }
            )
    return rows


def build_templates(summary, subtotal, discount_rate, discount_amount, after_discount, shipping_fee, shipping_enabled, final_amount, account, depositor):
    lines = []
    for _, r in summary.iterrows():
        lines.append(f"- {r['품목']} {int(r['수량'])}개 = {int(r['금액']):,}원")

    shipping_line = f"택배비 = {shipping_fee:,}원" if shipping_enabled else "택배비 = 0원"

    basic = "\n".join(
        [
            "안녕하세요. 주문 금액 안내드립니다.",
            "",
            *lines,
            "",
            f"상품 합계 = {subtotal:,}원",
            f"할인 {discount_rate:.1f}% = -{discount_amount:,}원",
            shipping_line,
            f"최종 결제금액 = {final_amount:,}원",
            "",
            "확인 부탁드립니다. 감사합니다.",
        ]
    )

    receipt = "\n".join(
        [
            "[식혜명가 주문 계산서]",
            "--------------------",
            *lines,
            "--------------------",
            f"상품 합계       {subtotal:,}원",
            f"할인 금액      -{discount_amount:,}원",
            f"택배비          {shipping_fee if shipping_enabled else 0:,}원",
            "--------------------",
            f"최종 결제금액   {final_amount:,}원",
        ]
    )

    account_text = account.strip() if account and account.strip() else "계좌번호 미입력"
    depositor_text = depositor.strip() if depositor and depositor.strip() else "예금주 미입력"

    deposit = "\n".join(
        [
            "주문 금액 안내드립니다.",
            "",
            *lines,
            "",
            f"상품 합계: {subtotal:,}원",
            f"할인 금액: -{discount_amount:,}원",
            f"택배비: {shipping_fee if shipping_enabled else 0:,}원",
            f"입금하실 금액: {final_amount:,}원",
            "",
            f"입금계좌: {account_text}",
            f"예금주: {depositor_text}",
            "",
            "입금 후 성함 남겨주시면 확인하겠습니다.",
        ]
    )

    return {
        "1. 친절 기본형": basic,
        "2. 깔끔 영수증형": receipt,
        "3. 입금 안내형": deposit,
    }


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("## 가격 설정")
    prices = {}
    for product, default_price in PRODUCTS.items():
        prices[product] = int(st.number_input(product, min_value=0, value=default_price, step=100, key=f"price_{product}"))

    st.divider()
    st.markdown("## 할인 / 배송")
    discount_rate = float(
        st.number_input(
            "상품 전체 할인율 (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=1.0,
            key="discount_rate",
        )
    )
    shipping_fee_setting = int(
        st.number_input(
            "택배비",
            min_value=0,
            value=4000,
            step=500,
            key="shipping_fee_setting",
        )
    )
    shipping_enabled = st.toggle(
        "택배비 적용",
        value=True,
        key="shipping_enabled",
        help="끄면 택배비가 최종 금액에 합산되지 않습니다.",
    )

    st.divider()
    st.markdown("## 자동 인식")
    default_size = st.selectbox("크기 미기재 시 기본값", ["1L", "500ml", "200ml 파우치"], index=0)
    st.caption("예: '식혜 3개'처럼 크기가 없으면 이 기준으로 계산")

    st.divider()
    st.markdown("## 입금 안내")
    account_number = st.text_input("계좌번호", placeholder="예: 농협 000-0000-0000-00")
    account_holder = st.text_input("예금주", placeholder="예: 식혜명가")


# -----------------------------
# Hero
# -----------------------------
st.markdown(
    """
<div class="hero">
    <h1>식혜 주문 자동계산기 PRO</h1>
    <p>버튼으로 빠르게 수량을 잡고, 카톡 주문 문구도 넓게 인식해 합산 계산합니다.</p>
    <div class="badge-wrap">
        <span class="badge">수량 버튼 계산</span>
        <span class="badge">카톡 문구 자동 인식</span>
        <span class="badge">택배비 ON/OFF</span>
        <span class="badge">계좌 문구 자동 삽입</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# -----------------------------
# Quantity calculator
# -----------------------------
st.markdown('<div class="section-title">① 수량 버튼 계산기</div>', unsafe_allow_html=True)
st.markdown('<div class="help-text">자주 쓰는 주문은 아래 버튼으로 바로 수량을 올리면 됩니다. 카톡 문구와 함께 합산됩니다.</div>', unsafe_allow_html=True)

top_cols = st.columns([1, 1, 5])
with top_cols[0]:
    st.button("전체 수량 초기화", on_click=reset_all_qty, use_container_width=True)
with top_cols[1]:
    st.caption("버튼 입력 + 문구 입력 합산")

product_cols = st.columns(5)
for idx, product in enumerate(PRODUCT_ORDER):
    with product_cols[idx % 5]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="product-title">{product}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="price-small">단가 {prices[product]:,}원</div>', unsafe_allow_html=True)

        st.number_input(
            f"{product} 수량",
            min_value=0,
            step=1,
            key=f"qty_{product}",
            label_visibility="collapsed",
        )

        b1, b2, b3, b4 = st.columns(4)
        b1.button("-", key=f"minus_{product}", on_click=change_qty, args=(product, -1), use_container_width=True)
        b2.button("+", key=f"plus_{product}", on_click=change_qty, args=(product, 1), use_container_width=True)
        b3.button("+5", key=f"plus5_{product}", on_click=change_qty, args=(product, 5), use_container_width=True)
        b4.button("0", key=f"zero_{product}", on_click=set_qty_zero, args=(product,), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


st.markdown('<hr class="soft">', unsafe_allow_html=True)


# -----------------------------
# Text input
# -----------------------------
st.markdown('<div class="section-title">② 주문내용 붙여넣기</div>', unsafe_allow_html=True)
st.markdown('<div class="help-text">카톡 대화처럼 대충 적어도 최대한 인식합니다. 예시는 흐리게만 보이며 계산에는 적용되지 않습니다.</div>', unsafe_allow_html=True)

c1, c2 = st.columns([1, 1])
with c1:
    with st.expander("예시 문구 복사용"):
        st.markdown(f'<div class="copy-box">{EXAMPLE_TEXT}</div>', unsafe_allow_html=True)
with c2:
    st.button("예시를 입력창에 넣기", on_click=put_example, use_container_width=True)

order_text = st.text_area(
    "주문내용 입력",
    key="order_text",
    height=190,
    placeholder=EXAMPLE_TEXT,
    label_visibility="collapsed",
)


# -----------------------------
# Calculate
# -----------------------------
button_rows = parse_button_orders(prices)
text_rows = parse_text_orders(order_text, prices, default_size)
rows = button_rows + text_rows

if rows:
    df = pd.DataFrame(rows)

    summary = (
        df.groupby(["품목", "단가"], as_index=False)
        .agg({"수량": "sum", "금액": "sum"})
    )
    summary["정렬"] = summary["품목"].map({p: i for i, p in enumerate(PRODUCT_ORDER)}).fillna(99)
    summary = summary.sort_values("정렬").drop(columns=["정렬"])

    total_qty = int(summary["수량"].sum())
    subtotal = int(summary["금액"].sum())
else:
    df = pd.DataFrame(columns=["입력방식", "원문", "품목", "수량", "단가", "금액"])
    summary = pd.DataFrame(columns=["품목", "단가", "수량", "금액"])
    total_qty = 0
    subtotal = 0

discount_amount = int(round(subtotal * (discount_rate / 100)))
after_discount = max(0, subtotal - discount_amount)
shipping_fee = shipping_fee_setting if shipping_enabled else 0
final_amount = after_discount + shipping_fee


st.markdown('<hr class="soft">', unsafe_allow_html=True)

metric_cols = st.columns(4)
metric_cols[0].metric("총 수량", f"{total_qty:,}개")
metric_cols[1].metric("상품 합계", f"{subtotal:,}원")
metric_cols[2].metric("할인 적용 후", f"{after_discount:,}원", delta=f"-{discount_amount:,}원")
metric_cols[3].metric("최종 결제금액", f"{final_amount:,}원", delta=f"택배비 {shipping_fee:,}원")


left, right = st.columns([1.45, 1])

with left:
    st.markdown('<div class="section-title">③ 계산 결과</div>', unsafe_allow_html=True)

    if not summary.empty:
        show_summary = summary.copy()
        show_summary["단가"] = show_summary["단가"].map(lambda x: f"{int(x):,}원")
        show_summary["금액"] = show_summary["금액"].map(lambda x: f"{int(x):,}원")
        st.dataframe(show_summary, use_container_width=True, hide_index=True)
    else:
        st.info("아직 계산된 주문이 없습니다. 수량 버튼을 누르거나 주문 문구를 입력하세요.")

    with st.expander("상세 인식 내역"):
        if not df.empty:
            detail = df.copy()
            detail["단가"] = detail["단가"].map(lambda x: f"{int(x):,}원")
            detail["금액"] = detail["금액"].map(lambda x: f"{int(x):,}원")
            st.dataframe(detail, use_container_width=True, hide_index=True)
        else:
            st.write("상세 내역 없음")

with right:
    st.markdown(
        f"""
<div class="dark-card">
    <div class="dark-label">최종 결제금액</div>
    <div class="big-money">{final_amount:,}원</div>
    <br>
    <div>총 수량: <b>{total_qty:,}개</b></div>
    <div>상품 합계: <b>{subtotal:,}원</b></div>
    <div>할인 금액: <b>-{discount_amount:,}원</b></div>
    <div>택배비: <b>{shipping_fee:,}원</b></div>
</div>
""",
        unsafe_allow_html=True,
    )


# -----------------------------
# Message templates
# -----------------------------
st.markdown('<hr class="soft">', unsafe_allow_html=True)
st.markdown('<div class="section-title">④ 고객에게 보낼 계산 문구</div>', unsafe_allow_html=True)

if not summary.empty:
    templates = build_templates(
        summary,
        subtotal,
        discount_rate,
        discount_amount,
        after_discount,
        shipping_fee,
        shipping_enabled,
        final_amount,
        account_number,
        account_holder,
    )

    template_choice = st.selectbox("문구 형식 선택", list(templates.keys()), index=0)
    edited_message = st.text_area(
        "선택 문구 수정",
        value=templates[template_choice],
        height=260,
    )

    d1, d2 = st.columns(2)

    csv = summary.to_csv(index=False).encode("utf-8-sig")
    d1.download_button(
        "계산 결과 CSV 다운로드",
        data=csv,
        file_name=f"sikhye_order_result_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    d2.download_button(
        "고객 문구 TXT 다운로드",
        data=edited_message.encode("utf-8-sig"),
        file_name=f"sikhye_customer_message_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain",
        use_container_width=True,
    )
else:
    st.info("주문이 계산되면 고객 발송 문구가 자동으로 생성됩니다.")


st.caption("개인정보 보호: 이 앱은 입력 내용을 별도 DB에 저장하지 않습니다. 배포 환경의 로그 정책은 별도 확인하세요.")
