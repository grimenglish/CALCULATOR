import re
import hashlib
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="식혜 주문 자동계산기 PRO",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================
# 기본 상품/가격
# =============================
DEFAULT_PRODUCTS = {
    "일반식혜 1L": 5000,
    "일반식혜 500ml": 3000,
    "일반식혜 200ml 파우치": 1800,
    "단호박식혜 1L": 6700,
    "단호박식혜 500ml": 4000,
}

PRODUCT_ORDER = list(DEFAULT_PRODUCTS.keys())

SAMPLE_TEXT = """식혜 1L 3개
호박감주 500ml 2개
식혜 200ml 파우치 10개"""

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

# =============================
# 디자인 CSS
# =============================
st.markdown(
    """
    <style>
    :root {
        --bg: #f4f7fb;
        --card: #ffffff;
        --dark: #0f172a;
        --muted: #64748b;
        --line: #e2e8f0;
        --accent: #f59e0b;
        --accent2: #2563eb;
    }
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(37, 99, 235, .10), transparent 28%),
            linear-gradient(180deg, #f8fafc 0%, #eef3fb 100%);
    }
    section[data-testid="stSidebar"] {
        background: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    .main .block-container {
        padding-top: 1.1rem;
        max-width: 1240px;
    }
    .hero {
        background: linear-gradient(135deg, #172033 0%, #24344d 100%);
        color: white;
        padding: 28px 34px;
        border-radius: 28px;
        box-shadow: 0 20px 50px rgba(15, 23, 42, .22);
        margin-bottom: 22px;
    }
    .hero h1 {
        margin: 0;
        font-size: 34px;
        font-weight: 900;
        letter-spacing: -1px;
    }
    .hero p {
        margin: 10px 0 0 0;
        color: #dbeafe;
        font-size: 15px;
        line-height: 1.7;
    }
    .badge-wrap {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 16px;
    }
    .badge {
        background: rgba(255,255,255,.92);
        color: #1e3a8a;
        border: 1px solid rgba(255,255,255,.65);
        padding: 8px 13px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 800;
    }
    .section-title {
        font-size: 22px;
        font-weight: 900;
        color: #0f172a;
        margin: 12px 0 6px 0;
    }
    .section-sub {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 14px;
    }
    .calc-panel {
        background: rgba(255, 255, 255, .76);
        border: 1px solid rgba(226, 232, 240, .95);
        border-radius: 26px;
        padding: 22px;
        box-shadow: 0 16px 40px rgba(15, 23, 42, .08);
    }
    .dark-card {
        background: linear-gradient(145deg, #111827, #0b1020);
        color: white;
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 28px;
        padding: 26px;
        box-shadow: 0 20px 50px rgba(15, 23, 42, .22);
    }
    .total-label {
        color: #93c5fd;
        font-size: 14px;
        margin-bottom: 8px;
    }
    .total-money {
        color: #fbbf24;
        font-size: 42px;
        font-weight: 950;
        letter-spacing: -1px;
        margin-bottom: 22px;
    }
    .mini-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
    }
    .mini-box {
        background: rgba(255,255,255,.08);
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 16px;
        padding: 14px;
    }
    .mini-box .k {
        color: #cbd5e1;
        font-size: 12px;
        margin-bottom: 6px;
    }
    .mini-box .v {
        color: white;
        font-size: 19px;
        font-weight: 900;
    }
    .product-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 22px;
        padding: 16px;
        box-shadow: 0 10px 26px rgba(15, 23, 42, .06);
        margin-bottom: 12px;
    }
    .product-name {
        font-size: 16px;
        font-weight: 900;
        color: #111827;
        margin-bottom: 4px;
    }
    .product-price {
        color: #64748b;
        font-size: 13px;
        margin-bottom: 8px;
    }
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,.86);
        border: 1px solid #e2e8f0;
        padding: 18px 20px;
        border-radius: 22px;
        box-shadow: 0 10px 25px rgba(15, 23, 42, .06);
    }
    .stButton > button {
        border-radius: 13px;
        font-weight: 900;
        border: 1px solid #dbe3ee;
        background: white;
    }
    .stButton > button:hover {
        border-color: #2563eb;
        color: #1d4ed8;
    }
    textarea::placeholder {
        color: rgba(15, 23, 42, .32) !important;
    }
    .copy-box {
        background: #ffffff;
        border: 1px dashed #cbd5e1;
        border-radius: 18px;
        padding: 14px 16px;
        color: #475569;
        font-size: 14px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# 유틸 함수
# =============================
def won(value: int) -> str:
    return f"{int(value):,}원"


def normalize_text(text: str) -> str:
    text = text.replace("１", "1").replace("Ｌ", "L").replace("ｌ", "l")
    text = text.replace("리터", "L").replace("리뜨", "L")
    text = text.replace("미리", "ml").replace("밀리", "ml")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_product(line: str, default_size: str):
    line_low = line.lower()

    if any(x in line for x in ["호박", "단호박", "호박감주", "호박 감주", "호박식혜"]):
        base = "단호박식혜"
    elif any(x in line for x in ["식혜", "감주"]):
        base = "일반식혜"
    else:
        return None

    is_pouch = "파우치" in line or "pouch" in line_low

    if re.search(r"(200\s*ml|200ml|0\.2\s*l|0.2l)", line_low) or is_pouch:
        size = "200ml 파우치" if base == "일반식혜" else "500ml"
    elif re.search(r"(500\s*ml|500ml|0\.5\s*l|0.5l|반\s*리터)", line_low):
        size = "500ml"
    elif re.search(r"(1\s*l|1l|1000\s*ml|1000ml|1\s*리터|큰거|큰\s*거)", line_low):
        size = "1L"
    else:
        size = default_size

    if base == "단호박식혜" and size == "200ml 파우치":
        size = "500ml"

    return f"{base} {size}"


def detect_quantity(line: str) -> int:
    unit_matches = re.findall(r"(\d+)\s*(개|병|통|팩|봉|개입|파우치)", line)
    if unit_matches:
        return int(unit_matches[-1][0])

    for word, num in KOR_NUM.items():
        if re.search(fr"{word}\s*(개|병|통|팩|봉|파우치)", line):
            return num

    numbers = re.findall(r"\d+", line)
    if len(numbers) >= 2:
        return int(numbers[-1])
    if len(numbers) == 1 and not re.search(r"(\d+)\s*(l|L|ml|ML)", line):
        return int(numbers[0])

    return 1


def parse_order(text: str, prices: dict, default_size: str):
    rows = []
    warnings = []
    lines = [normalize_text(x) for x in text.splitlines() if normalize_text(x)]

    for line in lines:
        product = detect_product(line, default_size)
        if not product:
            warnings.append(f"인식 제외: {line}")
            continue

        qty = detect_quantity(line)
        unit_price = int(prices.get(product, 0))
        rows.append({
            "입력방식": "붙여넣기",
            "원문": line,
            "품목": product,
            "수량": qty,
            "단가": unit_price,
            "금액": qty * unit_price,
        })

    return rows, warnings


def ensure_qty_state():
    if "manual_qty" not in st.session_state:
        st.session_state["manual_qty"] = {product: 0 for product in PRODUCT_ORDER}
    else:
        for product in PRODUCT_ORDER:
            st.session_state["manual_qty"].setdefault(product, 0)

    if "qty_version" not in st.session_state:
        st.session_state["qty_version"] = 0


def get_qty(product: str) -> int:
    ensure_qty_state()
    return int(st.session_state["manual_qty"].get(product, 0) or 0)


def set_qty(product: str, qty: int):
    ensure_qty_state()
    st.session_state["manual_qty"][product] = max(0, int(qty or 0))


def refresh_qty_inputs():
    ensure_qty_state()
    st.session_state["qty_version"] += 1


def change_qty(product: str, delta: int):
    set_qty(product, get_qty(product) + delta)
    refresh_qty_inputs()
    st.rerun()


def zero_qty(product: str):
    set_qty(product, 0)
    refresh_qty_inputs()
    st.rerun()


def get_manual_rows(prices: dict):
    rows = []
    ensure_qty_state()
    for product in PRODUCT_ORDER:
        qty = get_qty(product)
        if qty > 0:
            unit_price = int(prices.get(product, 0))
            rows.append({
                "입력방식": "버튼계산기",
                "원문": "수량 버튼 입력",
                "품목": product,
                "수량": qty,
                "단가": unit_price,
                "금액": qty * unit_price,
            })
    return rows


def make_summary(rows):
    if not rows:
        return pd.DataFrame(columns=["품목", "단가", "수량", "금액"])
    df = pd.DataFrame(rows)
    return (
        df.groupby(["품목", "단가"], as_index=False)
        .agg({"수량": "sum", "금액": "sum"})
        .sort_values("품목")
    )


def build_message(kind, summary, subtotal, discount_rate, discount_amount, product_after_discount, shipping_fee, final_amount, bank_account, account_holder):
    lines = []
    today = datetime.now().strftime("%Y.%m.%d")

    if kind == "1. 친절 기본형":
        lines.append("안녕하세요. 주문 금액 안내드립니다 😊")
        lines.append("")
        for _, r in summary.iterrows():
            lines.append(f"- {r['품목']} {int(r['수량'])}개: {won(r['금액'])}")
        lines.append("")
        lines.append(f"상품 합계: {won(subtotal)}")
        if discount_rate > 0:
            lines.append(f"할인 {discount_rate:.1f}%: -{won(discount_amount)}")
        if shipping_fee > 0:
            lines.append(f"택배비: {won(shipping_fee)}")
        lines.append(f"총 결제금액: {won(final_amount)}")
        lines.append("")
        lines.append("확인 부탁드립니다. 감사합니다.")

    elif kind == "2. 깔끔 영수증형":
        lines.append("[주문 계산서]")
        lines.append(f"작성일: {today}")
        lines.append("--------------------")
        for _, r in summary.iterrows():
            lines.append(f"{r['품목']} x {int(r['수량'])} = {won(r['금액'])}")
        lines.append("--------------------")
        lines.append(f"상품 합계: {won(subtotal)}")
        lines.append(f"할인 금액: -{won(discount_amount)}")
        lines.append(f"할인 적용 후: {won(product_after_discount)}")
        lines.append(f"택배비: {won(shipping_fee)}")
        lines.append(f"최종 결제금액: {won(final_amount)}")

    else:
        lines.append("[입금 안내]")
        lines.append("")
        for _, r in summary.iterrows():
            lines.append(f"- {r['품목']} {int(r['수량'])}개: {won(r['금액'])}")
        lines.append("")
        lines.append(f"상품 합계: {won(subtotal)}")
        if discount_rate > 0:
            lines.append(f"할인 {discount_rate:.1f}%: -{won(discount_amount)}")
        if shipping_fee > 0:
            lines.append(f"택배비: {won(shipping_fee)}")
        lines.append(f"입금 금액: {won(final_amount)}")
        lines.append("")
        if bank_account.strip():
            if account_holder.strip():
                lines.append(f"입금계좌: {bank_account.strip()} / 예금주 {account_holder.strip()}")
            else:
                lines.append(f"입금계좌: {bank_account.strip()}")
        else:
            lines.append("입금계좌: 계좌번호를 입력해주세요")
        lines.append("")
        lines.append("입금 확인 후 발송 준비하겠습니다. 감사합니다.")

    return "\n".join(lines)


def reset_quantities():
    ensure_qty_state()
    for product in PRODUCT_ORDER:
        st.session_state["manual_qty"][product] = 0
    refresh_qty_inputs()
    st.rerun()

# =============================
# 사이드바
# =============================
with st.sidebar:
    st.header("가격 설정")
    prices = {}
    for product, price in DEFAULT_PRODUCTS.items():
        prices[product] = st.number_input(product, min_value=0, value=price, step=100, key=f"price_{product}")

    st.divider()
    st.header("할인 / 배송")
    discount_rate = st.number_input("상품 전체 할인율 (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
    shipping_fee = st.number_input("택배비", min_value=0, value=4000, step=500)

    st.divider()
    st.header("입금 안내")
    bank_account = st.text_input("계좌번호", placeholder="예: 농협 000-0000-0000-00")
    account_holder = st.text_input("예금주", placeholder="예: 식혜명가")

    st.divider()
    st.header("자동 인식")
    default_size = st.selectbox("크기 미기재 시 기본값", ["1L", "500ml", "200ml 파우치"], index=0)
    st.caption("예: '식혜 3개'처럼 크기가 없으면 이 기준으로 계산")

# =============================
# 헤더
# =============================
st.markdown(
    """
    <div class="hero">
        <h1>식혜 주문 자동계산기 PRO</h1>
        <p>수량 버튼으로 빠르게 계산하고, 카톡 주문을 붙여넣어도 자동 인식합니다.<br>
        상품 합계·할인·택배비·최종 결제금액·고객 발송 문구까지 한 번에 정리합니다.</p>
        <div class="badge-wrap">
            <span class="badge">수량 버튼 계산기</span>
            <span class="badge">카톡 주문 자동 인식</span>
            <span class="badge">할인율 적용</span>
            <span class="badge">택배비 합산</span>
            <span class="badge">계좌 자동 삽입</span>
            <span class="badge">문구 3종 선택</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================
# 입력 영역
# =============================
left, right = st.columns([1.55, 1], gap="large")

with left:
    st.markdown('<div class="section-title">① 수량 버튼 계산기</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">자주 쓰는 주문은 아래 버튼으로 바로 수량을 잡으세요. 붙여넣기 주문과 함께 합산됩니다.</div>', unsafe_allow_html=True)

    ensure_qty_state()
    with st.container():
        for idx, product in enumerate(PRODUCT_ORDER):
            c1, c2, c3, c4, c5, c6 = st.columns([2.2, 1.2, .7, .7, .7, .7])
            with c1:
                st.markdown(
                    f"""
                    <div class="product-card">
                        <div class="product-name">{product}</div>
                        <div class="product-price">단가 {won(prices[product])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c2:
                input_key = f"qty_input_{idx}_{st.session_state['qty_version']}"
                entered_qty = st.number_input(
                    "수량",
                    min_value=0,
                    value=get_qty(product),
                    step=1,
                    key=input_key,
                    label_visibility="collapsed",
                )
                if int(entered_qty) != get_qty(product):
                    set_qty(product, int(entered_qty))
            with c3:
                if st.button("-", key=f"minus_{idx}", use_container_width=True):
                    change_qty(product, -1)
            with c4:
                if st.button("+", key=f"plus_{idx}", use_container_width=True):
                    change_qty(product, 1)
            with c5:
                if st.button("+5", key=f"plus5_{idx}", use_container_width=True):
                    change_qty(product, 5)
            with c6:
                if st.button("0", key=f"zero_{idx}", use_container_width=True):
                    zero_qty(product)

    if st.button("전체 수량 초기화", use_container_width=True):
        reset_quantities()

    st.markdown('<div class="section-title">② 주문내용 붙여넣기</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">처음엔 예시가 흐리게만 보이며 계산에 적용되지 않습니다. 직접 입력하거나 아래 예시를 복사/불러오기 하세요.</div>', unsafe_allow_html=True)

    col_ex1, col_ex2 = st.columns([1, 1])
    with col_ex1:
        with st.expander("예시 문구 복사용", expanded=False):
            st.code(SAMPLE_TEXT, language="text")
    with col_ex2:
        if st.button("예시를 입력창에 넣기", use_container_width=True):
            st.session_state["order_text"] = SAMPLE_TEXT

    if "order_text" not in st.session_state:
        st.session_state["order_text"] = ""

    order_text = st.text_area(
        "카톡/문자 주문",
        placeholder=SAMPLE_TEXT,
        height=190,
        key="order_text",
        label_visibility="collapsed",
    )

# 계산
manual_rows = get_manual_rows(prices)
paste_rows, warnings = parse_order(order_text, prices, default_size) if order_text.strip() else ([], [])
rows = manual_rows + paste_rows
summary = make_summary(rows)

if not summary.empty:
    total_qty = int(summary["수량"].sum())
    subtotal = int(summary["금액"].sum())
else:
    total_qty = 0
    subtotal = 0

discount_amount = int(round(subtotal * (float(discount_rate) / 100)))
product_after_discount = max(0, subtotal - discount_amount)
final_amount = product_after_discount + int(shipping_fee if subtotal > 0 else 0)

with right:
    st.markdown(
        f"""
        <div class="dark-card">
            <div class="total-label">최종 결제금액</div>
            <div class="total-money">{won(final_amount)}</div>
            <div class="mini-grid">
                <div class="mini-box"><div class="k">총 수량</div><div class="v">{total_qty:,}개</div></div>
                <div class="mini-box"><div class="k">상품 합계</div><div class="v">{won(subtotal)}</div></div>
                <div class="mini-box"><div class="k">할인 금액</div><div class="v">-{won(discount_amount)}</div></div>
                <div class="mini-box"><div class="k">택배비</div><div class="v">{won(int(shipping_fee if subtotal > 0 else 0))}</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =============================
# 결과 영역
# =============================
st.markdown("---")

m1, m2, m3, m4 = st.columns(4)
m1.metric("총 수량", f"{total_qty:,}개")
m2.metric("상품 합계", won(subtotal))
m3.metric("할인 적용 후", won(product_after_discount), delta=f"-{won(discount_amount)}")
m4.metric("최종 결제금액", won(final_amount), delta=f"택배비 {won(int(shipping_fee if subtotal > 0 else 0))}")

if rows:
    st.markdown('<div class="section-title">③ 계산 결과</div>', unsafe_allow_html=True)
    show_summary = summary.copy()
    show_summary["단가"] = show_summary["단가"].map(won)
    show_summary["금액"] = show_summary["금액"].map(won)
    st.dataframe(show_summary, use_container_width=True, hide_index=True)

    with st.expander("상세 인식 내역"):
        detail = pd.DataFrame(rows)
        detail["단가"] = detail["단가"].map(won)
        detail["금액"] = detail["금액"].map(won)
        st.dataframe(detail, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">④ 고객에게 보낼 계산 문구</div>', unsafe_allow_html=True)
    message_kind = st.selectbox(
        "문구 형식 선택",
        ["1. 친절 기본형", "2. 깔끔 영수증형", "3. 입금 안내형"],
        index=0,
    )

    auto_message = build_message(
        message_kind,
        summary,
        subtotal,
        float(discount_rate),
        discount_amount,
        product_after_discount,
        int(shipping_fee if subtotal > 0 else 0),
        final_amount,
        bank_account,
        account_holder,
    )
    message_hash = hashlib.md5(auto_message.encode("utf-8")).hexdigest()[:8]
    edited_message = st.text_area(
        "선택한 문구를 여기서 바로 수정할 수 있습니다.",
        value=auto_message,
        height=260,
        key=f"customer_message_{message_kind}_{message_hash}",
    )

    col_down1, col_down2 = st.columns(2)
    with col_down1:
        csv = summary.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "계산 결과 CSV 다운로드",
            data=csv,
            file_name="sikhye_order_result.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_down2:
        st.download_button(
            "고객 문구 TXT 다운로드",
            data=edited_message.encode("utf-8-sig"),
            file_name="customer_message.txt",
            mime="text/plain",
            use_container_width=True,
        )
else:
    st.info("수량 버튼을 누르거나 주문 내용을 입력하면 계산이 시작됩니다. 흐리게 보이는 예시는 계산에 적용되지 않습니다.")

if warnings:
    with st.expander("인식하지 못한 줄"):
        for w in warnings:
            st.write("- " + w)

st.caption("개인정보 보호: 이 앱은 입력 내용을 별도로 저장하지 않습니다. 배포 환경의 로그 설정은 별도 확인이 필요합니다.")
