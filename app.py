import re
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="식혜 주문 자동계산기 PRO",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# 디자인 CSS
# -----------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #f3f6fb 0%, #eef3f8 46%, #f8fafc 100%);
}

.block-container {
    padding-top: 1.4rem;
    padding-bottom: 3rem;
    max-width: 1280px;
}

.hero {
    background: linear-gradient(135deg, #111827 0%, #1f2937 52%, #334155 100%);
    color: white;
    border-radius: 28px;
    padding: 34px 42px;
    box-shadow: 0 24px 60px rgba(15, 23, 42, 0.22);
    margin-bottom: 22px;
}

.hero h1 {
    margin: 0 0 8px 0;
    font-size: 2.15rem;
    font-weight: 900;
    letter-spacing: -0.04em;
}

.hero p {
    margin: 0;
    color: #dbeafe;
    font-size: 1.02rem;
    line-height: 1.75;
}

.badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 18px;
}

.badge {
    background: rgba(255, 255, 255, 0.92);
    color: #1e3a8a;
    padding: 8px 14px;
    border-radius: 999px;
    font-size: 0.88rem;
    font-weight: 800;
}

.section-card {
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(226, 232, 240, 0.95);
    border-radius: 26px;
    padding: 26px;
    box-shadow: 0 16px 45px rgba(15, 23, 42, 0.08);
    margin-bottom: 22px;
}

.section-title {
    font-size: 1.28rem;
    font-weight: 900;
    color: #111827;
    letter-spacing: -0.03em;
    margin-bottom: 4px;
}

.section-subtitle {
    color: #64748b;
    font-size: 0.94rem;
    margin-bottom: 18px;
}

.result-panel {
    background: linear-gradient(145deg, #020617 0%, #111827 100%);
    color: white;
    border-radius: 28px;
    padding: 28px;
    box-shadow: 0 24px 60px rgba(15, 23, 42, 0.22);
}

.result-label {
    color: #93c5fd;
    font-size: 0.86rem;
    font-weight: 700;
    margin-bottom: 8px;
}

.result-money {
    font-size: 2.5rem;
    line-height: 1;
    font-weight: 900;
    color: #fbbf24;
    letter-spacing: -0.05em;
}

.small-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    margin-top: 18px;
}

.small-box {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    padding: 16px;
}

.small-box-label {
    color: #cbd5e1;
    font-size: 0.82rem;
    margin-bottom: 6px;
}

.small-box-value {
    color: white;
    font-size: 1.25rem;
    font-weight: 900;
}

.quick-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 22px;
    padding: 18px;
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
    height: 100%;
}

.quick-name {
    font-size: 1.02rem;
    font-weight: 900;
    color: #111827;
    margin-bottom: 4px;
}

.quick-price {
    color: #64748b;
    font-size: 0.86rem;
    margin-bottom: 12px;
}

.quick-qty {
    font-size: 1.85rem;
    font-weight: 900;
    color: #1d4ed8;
    margin: 4px 0 12px 0;
}

[data-testid="stMetricValue"] {
    font-weight: 900;
    letter-spacing: -0.04em;
}

button[kind="primary"] {
    border-radius: 14px !important;
    font-weight: 900 !important;
}

.stButton > button {
    border-radius: 13px;
    font-weight: 800;
}

textarea, input {
    border-radius: 14px !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# 기본 상품 / 세션
# -----------------------------
DEFAULT_PRODUCTS = {
    "일반식혜 1L": 5000,
    "일반식혜 500ml": 3000,
    "일반식혜 200ml 파우치": 1800,
    "단호박식혜 1L": 6700,
    "단호박식혜 500ml": 4000,
}

PRODUCT_ORDER = list(DEFAULT_PRODUCTS.keys())

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

for product in PRODUCT_ORDER:
    st.session_state.setdefault(f"qty_{product}", 0)

st.session_state.setdefault("message_editor", "")
st.session_state.setdefault("_message_hash", "")

# -----------------------------
# 사이드바
# -----------------------------
with st.sidebar:
    st.header("가격 설정")
    prices = {}
    for product, price in DEFAULT_PRODUCTS.items():
        prices[product] = st.number_input(product, min_value=0, value=price, step=100, key=f"price_{product}")

    st.divider()
    st.header("할인 / 배송")
    discount_rate = st.number_input(
        "상품 전체 할인율 (%)",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=1.0,
        help="상품 합계에만 적용됩니다. 택배비는 할인 후 별도 합산됩니다.",
    )
    shipping_fee = st.number_input("택배비", min_value=0, value=0, step=500)

    st.divider()
    st.header("입금 정보")
    bank_account = st.text_input("계좌번호", placeholder="예: 농협 000-0000-0000-00")
    account_holder = st.text_input("예금주", placeholder="예: 식혜명가")

    st.divider()
    st.header("자동 인식")
    default_size = st.selectbox("크기 미기재 시 기본값", ["1L", "500ml", "200ml 파우치"], index=0)
    st.caption("예: '식혜 3개'처럼 크기가 없으면 이 기준으로 계산됩니다.")

# -----------------------------
# 함수
# -----------------------------
def money(value: int) -> str:
    return f"{int(value):,}원"


def normalize_text(text: str) -> str:
    text = text.replace("１", "1").replace("Ｌ", "L").replace("ｌ", "l")
    text = text.replace("리터", "L").replace("리뜨", "L")
    text = text.replace("미리", "ml").replace("밀리", "ml")
    text = text.replace("큰거", "1L").replace("큰 것", "1L").replace("큰 병", "1L")
    text = text.replace("작은거", "500ml").replace("작은 것", "500ml").replace("작은 병", "500ml")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_product(line: str):
    line_low = line.lower()

    if any(x in line for x in ["호박", "단호박", "호박감주", "호박 감주"]):
        base = "단호박식혜"
    elif any(x in line for x in ["식혜", "감주", "파우치"]):
        base = "일반식혜"
    else:
        return None, None

    if re.search(r"(200\s*ml|200ml|0\.2\s*l|0.2l)", line_low) or "파우치" in line or "pouch" in line_low:
        size = "200ml 파우치" if base == "일반식혜" else None
    elif re.search(r"(500\s*ml|500ml|0\.5\s*l|0.5l|500)", line_low):
        size = "500ml"
    elif re.search(r"(1\s*l|1l|1000\s*ml|1000ml)", line_low):
        size = "1L"
    else:
        size = default_size

    if size is None:
        return None, "단호박 200ml 파우치는 상품 목록에 없습니다."

    product = f"{base} {size}"
    if product not in DEFAULT_PRODUCTS:
        return None, f"상품 목록에 없는 품목입니다: {product}"

    return product, None


def detect_quantity(line: str) -> int:
    # 30개, 30 병, 30통, 30파우치 등
    unit_matches = re.findall(r"(\d+)\s*(개|병|통|팩|봉|개입|파우치)", line)
    if unit_matches:
        return int(unit_matches[-1][0])

    # 한개, 두 개 등
    for word, num in sorted(KOR_NUM.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(fr"{word}\s*(개|병|통|팩|봉|파우치)", line):
            return num

    # 숫자만 있을 때: 용량 숫자는 제외하고 마지막 숫자를 수량으로 사용
    cleaned = re.sub(r"(1\s*l|1l|1000\s*ml|1000ml|500\s*ml|500ml|200\s*ml|200ml|0\.5\s*l|0.5l|0\.2\s*l|0.2l)", " ", line, flags=re.I)
    nums = re.findall(r"\d+", cleaned)
    if nums:
        return int(nums[-1])

    return 1


def parse_order(text: str):
    rows = []
    warnings = []
    lines = [normalize_text(x) for x in text.splitlines() if normalize_text(x)]

    for line in lines:
        product, error = detect_product(line)
        if not product:
            warnings.append(f"{line} → {error or '품목 인식 제외'}")
            continue

        qty = detect_quantity(line)
        unit_price = prices.get(product, 0)
        rows.append({
            "입력방식": "주문 붙여넣기",
            "원문": line,
            "품목": product,
            "수량": qty,
            "단가": unit_price,
            "금액": qty * unit_price,
        })

    return rows, warnings


def change_qty(product: str, delta: int):
    key = f"qty_{product}"
    st.session_state[key] = max(0, int(st.session_state.get(key, 0)) + delta)


def clear_quantities():
    for p in PRODUCT_ORDER:
        st.session_state[f"qty_{p}"] = 0


def make_manual_rows():
    rows = []
    for product in PRODUCT_ORDER:
        qty = int(st.session_state.get(f"qty_{product}", 0))
        if qty <= 0:
            continue
        unit_price = prices.get(product, 0)
        rows.append({
            "입력방식": "수량 버튼",
            "원문": "직접 버튼 입력",
            "품목": product,
            "수량": qty,
            "단가": unit_price,
            "금액": qty * unit_price,
        })
    return rows


def build_message(template_name: str, summary: pd.DataFrame, subtotal: int, discount_amount: int, final_product_amount: int, shipping: int, final_total: int) -> str:
    now = datetime.now().strftime("%Y-%m-%d")
    item_lines_basic = []
    item_lines_receipt = []
    for _, r in summary.iterrows():
        item_lines_basic.append(f"- {r['품목']} {int(r['수량'])}개 = {money(r['금액'])}")
        item_lines_receipt.append(f"{r['품목']} x {int(r['수량'])}개  {money(r['금액'])}")

    discount_line = f"할인금액: -{money(discount_amount)}\n" if discount_amount > 0 else ""
    shipping_line = f"택배비: {money(shipping)}\n" if shipping > 0 else ""
    account_line = ""
    if bank_account or account_holder:
        account_line = f"\n입금계좌: {bank_account}" if bank_account else "\n입금계좌: 미입력"
        if account_holder:
            account_line += f"\n예금주: {account_holder}"

    if template_name == "1. 친절 기본형":
        return (
            "안녕하세요. 주문 금액 안내드립니다 😊\n\n"
            + "\n".join(item_lines_basic)
            + f"\n\n상품합계: {money(subtotal)}\n"
            + discount_line
            + f"할인 적용 후 상품금액: {money(final_product_amount)}\n"
            + shipping_line
            + f"최종 결제금액: {money(final_total)}\n\n"
            + "확인 부탁드립니다. 감사합니다."
        )

    if template_name == "2. 깔끔 영수증형":
        return (
            f"[식혜명가 주문 계산서]\n날짜: {now}\n\n"
            + "\n".join(item_lines_receipt)
            + "\n--------------------\n"
            + f"상품합계: {money(subtotal)}\n"
            + discount_line
            + f"상품금액: {money(final_product_amount)}\n"
            + shipping_line
            + f"총 결제금액: {money(final_total)}"
        )

    return (
        "주문 감사합니다. 입금 안내드립니다.\n\n"
        + "\n".join(item_lines_basic)
        + f"\n\n상품합계: {money(subtotal)}\n"
        + discount_line
        + f"할인 적용 후 상품금액: {money(final_product_amount)}\n"
        + shipping_line
        + f"최종 입금금액: {money(final_total)}"
        + account_line
        + "\n\n입금 확인 후 순차 발송됩니다. 감사합니다."
    )

# -----------------------------
# 화면 헤더
# -----------------------------
st.markdown(
    """
<div class="hero">
    <h1>식혜 주문 자동계산기 PRO</h1>
    <p>수량 버튼으로 빠르게 계산하고, 카톡 주문은 그대로 붙여넣어 자동 인식합니다.<br>할인·택배비·입금계좌까지 반영한 고객 발송 문구를 바로 만들 수 있습니다.</p>
    <div class="badge-row">
        <span class="badge">수량 버튼 계산</span>
        <span class="badge">카톡 주문 자동 인식</span>
        <span class="badge">할인율 적용</span>
        <span class="badge">택배비 합산</span>
        <span class="badge">입금계좌 자동 삽입</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# 빠른 수량 계산기 + 결과 패널
# -----------------------------
left, right = st.columns([1.55, 1], gap="large")

with left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">① 수량 버튼 계산기</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">자주 받는 전화·방문 주문은 여기서 + 버튼만 눌러 계산하세요.</div>', unsafe_allow_html=True)

    top_a, top_b = st.columns([1, 1])
    with top_a:
        if st.button("전체 수량 초기화", use_container_width=True):
            clear_quantities()
            st.rerun()
    with top_b:
        st.caption("버튼 입력과 카톡 붙여넣기 주문은 자동으로 합산됩니다.")

    for i in range(0, len(PRODUCT_ORDER), 2):
        cols = st.columns(2)
        for col, product in zip(cols, PRODUCT_ORDER[i:i+2]):
            with col:
                st.markdown('<div class="quick-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="quick-name">{product}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="quick-price">단가 {money(prices[product])}</div>', unsafe_allow_html=True)
                st.number_input(
                    "수량",
                    min_value=0,
                    value=int(st.session_state[f"qty_{product}"]),
                    step=1,
                    key=f"qty_{product}",
                    label_visibility="collapsed",
                )
                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    if st.button("-", key=f"minus_{product}", use_container_width=True):
                        change_qty(product, -1)
                        st.rerun()
                with b2:
                    if st.button("+", key=f"plus_{product}", use_container_width=True):
                        change_qty(product, 1)
                        st.rerun()
                with b3:
                    if st.button("+5", key=f"plus5_{product}", use_container_width=True):
                        change_qty(product, 5)
                        st.rerun()
                with b4:
                    if st.button("0", key=f"zero_{product}", use_container_width=True):
                        st.session_state[f"qty_{product}"] = 0
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

with right:
    # 임시 계산용: 주문 텍스트는 아래에서 받아서 나중에 다시 출력됨
    pass

# -----------------------------
# 주문 붙여넣기
# -----------------------------
text_col, panel_col = st.columns([1.55, 1], gap="large")

sample = """식혜 1L 3개
호박감주 500ml 2개
식혜 200ml 파우치 10개"""

with text_col:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">② 주문 내용 붙여넣기</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">카톡/문자 주문을 줄 단위로 붙여넣으세요. 예: 식혜 1L 3개 / 호박감주 500ml 2개</div>', unsafe_allow_html=True)
    order_text = st.text_area("주문 내용", value=sample, height=180, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

manual_rows = make_manual_rows()
parsed_rows, warnings = parse_order(order_text)
all_rows = manual_rows + parsed_rows

if all_rows:
    df = pd.DataFrame(all_rows)
    summary = (
        df.groupby(["품목", "단가"], as_index=False)
        .agg({"수량": "sum", "금액": "sum"})
    )
    summary["정렬"] = summary["품목"].apply(lambda x: PRODUCT_ORDER.index(x) if x in PRODUCT_ORDER else 999)
    summary = summary.sort_values("정렬").drop(columns=["정렬"])

    total_qty = int(summary["수량"].sum())
    subtotal_amount = int(summary["금액"].sum())
    discount_amount = int(round(subtotal_amount * (discount_rate / 100)))
    final_product_amount = subtotal_amount - discount_amount
    final_amount = final_product_amount + int(shipping_fee)
else:
    df = pd.DataFrame(columns=["입력방식", "원문", "품목", "수량", "단가", "금액"])
    summary = pd.DataFrame(columns=["품목", "단가", "수량", "금액"])
    total_qty = subtotal_amount = discount_amount = final_product_amount = final_amount = 0

with panel_col:
    st.markdown(
        f"""
<div class="result-panel">
    <div class="result-label">최종 결제금액</div>
    <div class="result-money">{money(final_amount)}</div>
    <div class="small-grid">
        <div class="small-box"><div class="small-box-label">총 수량</div><div class="small-box-value">{total_qty:,}개</div></div>
        <div class="small-box"><div class="small-box-label">상품 합계</div><div class="small-box-value">{money(subtotal_amount)}</div></div>
        <div class="small-box"><div class="small-box-label">할인 금액</div><div class="small-box-value">-{money(discount_amount)}</div></div>
        <div class="small-box"><div class="small-box-label">택배비</div><div class="small-box-value">{money(shipping_fee)}</div></div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

# -----------------------------
# 계산 결과
# -----------------------------
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">③ 계산 결과</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">수량 버튼 입력과 주문 붙여넣기 입력이 합산된 결과입니다.</div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric("총 수량", f"{total_qty:,}개")
m2.metric("상품 합계", money(subtotal_amount))
m3.metric("할인 적용 후", money(final_product_amount), delta=f"-{money(discount_amount)}" if discount_amount else None)
m4.metric("최종 결제금액", money(final_amount), delta=f"택배비 {money(shipping_fee)}" if shipping_fee else None)

if not summary.empty:
    show_summary = summary.copy()
    show_summary["단가"] = show_summary["단가"].map(money)
    show_summary["금액"] = show_summary["금액"].map(money)
    st.dataframe(show_summary, use_container_width=True, hide_index=True)
else:
    st.info("아직 계산할 주문이 없습니다. 수량 버튼을 누르거나 주문 내용을 붙여넣어 주세요.")
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# 고객 문구
# -----------------------------
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">④ 고객에게 보낼 계산 문구</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">문구 형식을 선택하면 자동 생성됩니다. 아래 문구는 직접 수정 가능합니다.</div>', unsafe_allow_html=True)

template_name = st.selectbox("문구 형식 선택", ["1. 친절 기본형", "2. 깔끔 영수증형", "3. 입금 안내형"])

generated_message = build_message(
    template_name,
    summary,
    subtotal_amount,
    discount_amount,
    final_product_amount,
    int(shipping_fee),
    final_amount,
) if not summary.empty else ""

message_hash = f"{template_name}|{subtotal_amount}|{discount_amount}|{final_product_amount}|{shipping_fee}|{final_amount}|{bank_account}|{account_holder}|" + "|".join(
    f"{r['품목']}:{int(r['수량'])}:{int(r['금액'])}" for _, r in summary.iterrows()
)

if st.session_state.get("_message_hash") != message_hash:
    st.session_state["message_editor"] = generated_message
    st.session_state["_message_hash"] = message_hash

st.text_area("수정 가능한 발송 문구", key="message_editor", height=260)

c1, c2 = st.columns(2)
with c1:
    st.download_button(
        "고객 문구 TXT 다운로드",
        data=st.session_state.get("message_editor", "").encode("utf-8-sig"),
        file_name="customer_message.txt",
        mime="text/plain",
        use_container_width=True,
    )
with c2:
    if st.button("선택한 형식으로 문구 다시 생성", use_container_width=True):
        st.session_state["message_editor"] = generated_message
        st.session_state["_message_hash"] = message_hash
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# 상세 내역 / 다운로드
# -----------------------------
with st.expander("상세 인식 내역 보기"):
    if not df.empty:
        detail = df.copy()
        detail["단가"] = detail["단가"].map(money)
        detail["금액"] = detail["금액"].map(money)
        st.dataframe(detail, use_container_width=True, hide_index=True)
    else:
        st.write("상세 내역이 없습니다.")

if warnings:
    with st.expander("인식하지 못한 줄"):
        for w in warnings:
            st.write("- " + w)

if not summary.empty:
    csv = summary.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "계산 결과 CSV 다운로드",
        data=csv,
        file_name="sikhye_order_result.csv",
        mime="text/csv",
    )

st.caption("개인정보 보호: 이 앱은 입력 내용을 앱 내부 DB에 저장하지 않습니다. GitHub/Streamlit 배포 환경 로그 설정은 별도 확인하세요.")
