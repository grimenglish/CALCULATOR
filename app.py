import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

# =============================
# Page
# =============================
st.set_page_config(
    page_title="식혜 주문 자동계산기 PRO",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================
# Style
# =============================
st.markdown(
    """
    <style>
    :root {
        --bg: #f4f6fb;
        --card: #ffffff;
        --ink: #172033;
        --muted: #6b7280;
        --line: #e5e7eb;
        --primary: #111827;
        --accent: #f59e0b;
        --accent2: #2563eb;
        --good: #059669;
        --danger: #dc2626;
    }
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 45%, #f8fafc 100%);
    }
    [data-testid="stSidebar"] {
        background: #f3f4f6;
        border-right: 1px solid #e5e7eb;
    }
    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 3rem;
        max-width: 1320px;
    }
    .hero-card {
        background: linear-gradient(135deg, #111827 0%, #1f2937 55%, #334155 100%);
        border-radius: 28px;
        padding: 30px 34px;
        color: white;
        box-shadow: 0 22px 55px rgba(15, 23, 42, .22);
        margin-bottom: 22px;
        border: 1px solid rgba(255,255,255,.09);
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 900;
        letter-spacing: -0.04em;
        margin-bottom: 8px;
    }
    .hero-sub {
        color: #d1d5db;
        font-size: 1rem;
        line-height: 1.6;
    }
    .calc-shell {
        background: #111827;
        border-radius: 28px;
        padding: 22px;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.08), 0 18px 40px rgba(17,24,39,.22);
        border: 1px solid rgba(255,255,255,.08);
    }
    .calc-display {
        background: linear-gradient(180deg, #0f172a 0%, #020617 100%);
        border-radius: 20px;
        padding: 24px 22px;
        border: 1px solid rgba(255,255,255,.1);
        color: white;
        margin-bottom: 14px;
    }
    .display-label {
        color: #9ca3af;
        font-size: .9rem;
        margin-bottom: 4px;
    }
    .display-amount {
        font-size: 2.25rem;
        font-weight: 950;
        letter-spacing: -0.05em;
        color: #fbbf24;
    }
    .key-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
    }
    .key-card {
        background: #1f2937;
        color: white;
        border-radius: 16px;
        padding: 14px;
        border: 1px solid rgba(255,255,255,.07);
    }
    .key-label { color: #9ca3af; font-size: .82rem; }
    .key-value { font-size: 1.18rem; font-weight: 850; margin-top: 3px; }
    .white-card {
        background: rgba(255,255,255,.88);
        border-radius: 24px;
        padding: 24px;
        box-shadow: 0 14px 32px rgba(15, 23, 42, .07);
        border: 1px solid rgba(226,232,240,.9);
        margin-bottom: 18px;
    }
    .section-title {
        color: #111827;
        font-size: 1.2rem;
        font-weight: 900;
        letter-spacing: -0.02em;
        margin-bottom: 8px;
    }
    .tiny-muted {
        color: #6b7280;
        font-size: .9rem;
        margin-bottom: 14px;
    }
    .pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 12px;
    }
    .pill {
        background: #eef2ff;
        color: #3730a3;
        border: 1px solid #c7d2fe;
        border-radius: 999px;
        padding: 6px 10px;
        font-size: .82rem;
        font-weight: 700;
    }
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,.86);
        border: 1px solid #e5e7eb;
        padding: 16px 18px;
        border-radius: 20px;
        box-shadow: 0 8px 20px rgba(15, 23, 42, .05);
    }
    div[data-testid="stMetricValue"] {
        font-weight: 900;
        letter-spacing: -0.04em;
    }
    textarea, input, .stSelectbox div[data-baseweb="select"] > div {
        border-radius: 14px !important;
    }
    .footer-note {
        color:#6b7280;
        font-size:.84rem;
        text-align:center;
        margin-top:20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# Defaults
# =============================
DEFAULT_PRODUCTS: Dict[str, int] = {
    "일반식혜 1L": 5000,
    "일반식혜 500ml": 3000,
    "일반식혜 200ml 파우치": 1800,
    "단호박식혜 1L": 6700,
    "단호박식혜 500ml": 4000,
}

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
# Sidebar
# =============================
with st.sidebar:
    st.header("⚙️ 설정")

    brand_name = st.text_input("상호명", value="식혜명가")
    bank_account = st.text_input("입금계좌 / 안내문구", value="입금계좌를 입력하세요")

    st.divider()
    st.subheader("가격 설정")
    prices: Dict[str, int] = {}
    for product, price in DEFAULT_PRODUCTS.items():
        prices[product] = st.number_input(product, min_value=0, value=price, step=100)

    st.divider()
    st.subheader("할인 / 배송")
    discount_rate = st.number_input(
        "상품 전체 할인율 (%)",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=1.0,
        help="상품 금액 합계에만 적용됩니다. 택배비는 할인 후 별도 합산됩니다.",
    )
    shipping_fee = st.number_input("택배비", min_value=0, value=0, step=500)

    st.divider()
    st.subheader("자동 인식")
    default_size = st.selectbox("크기 미기재 시 기본값", ["1L", "500ml", "200ml 파우치"], index=0)
    st.caption("예: '식혜 3개'처럼 크기가 없으면 이 기준으로 계산합니다.")

# =============================
# Parser
# =============================
def normalize_text(text: str) -> str:
    replacements = {
        "１": "1", "２": "2", "３": "3", "４": "4", "５": "5",
        "６": "6", "７": "7", "８": "8", "９": "9", "０": "0",
        "Ｌ": "L", "ｌ": "l", "리터": "L", "리뜨": "L",
        "미리": "ml", "밀리": "ml",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_base(line: str) -> Optional[str]:
    if any(x in line for x in ["호박", "단호박", "호박감주", "호박 감주"]):
        return "단호박식혜"
    if any(x in line for x in ["식혜", "감주"]):
        return "일반식혜"
    return None


def detect_size(line: str, base: str) -> Tuple[Optional[str], Optional[str]]:
    line_low = line.lower()

    if re.search(r"(200\s*ml|200ml|0\.2\s*l|0.2l)", line_low) or "파우치" in line or "pouch" in line_low:
        if base == "단호박식혜":
            return None, "단호박식혜 200ml 파우치는 기본 상품에 없습니다."
        return "200ml 파우치", None

    if re.search(r"(500\s*ml|500ml|0\.5\s*l|0.5l)", line_low) or any(x in line for x in ["작은거", "작은 것", "소자", "소 "]):
        return "500ml", None

    if re.search(r"(1\s*l|1l|1000\s*ml|1000ml|1\s*리터)", line_low) or any(x in line for x in ["큰거", "큰 것", "대자", "대 "]):
        return "1L", None

    return default_size, None


def detect_product(line: str) -> Tuple[Optional[str], Optional[str]]:
    base = detect_base(line)
    if not base:
        return None, None

    size, warning = detect_size(line, base)
    if warning:
        return None, warning

    product = f"{base} {size}"
    if product not in prices:
        return None, f"등록되지 않은 상품: {product}"
    return product, None


def detect_quantity(line: str) -> int:
    # 30개, 30 병, 30통, 30파우치 등
    unit_matches = re.findall(r"(\d+)\s*(개|병|통|팩|봉|개입|파우치)", line)
    if unit_matches:
        return int(unit_matches[-1][0])

    # 한개, 두 병 등
    for word, num in sorted(KOR_NUM.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(fr"{word}\s*(개|병|통|팩|봉|파우치)", line):
            return num

    # 단위 없이 숫자만 있는 경우: 마지막 숫자를 수량 후보로 사용
    numbers = re.findall(r"\d+", line)
    if len(numbers) >= 2:
        return int(numbers[-1])
    if len(numbers) == 1 and not re.search(r"(\d+)\s*(l|L|ml|ML)", line):
        return int(numbers[0])

    return 1


def parse_order(text: str):
    rows: List[Dict] = []
    warnings: List[str] = []
    lines = [normalize_text(x) for x in text.splitlines() if normalize_text(x)]

    for line in lines:
        product, warning = detect_product(line)
        if warning:
            warnings.append(f"{warning} → {line}")
            continue
        if not product:
            warnings.append(f"인식 제외 → {line}")
            continue

        qty = detect_quantity(line)
        unit_price = int(prices.get(product, 0))
        amount = qty * unit_price

        rows.append({
            "원문": line,
            "품목": product,
            "수량": qty,
            "단가": unit_price,
            "금액": amount,
        })

    return rows, warnings


def money(value: int) -> str:
    return f"{int(value):,}원"


def build_items_text(summary: pd.DataFrame, style: str) -> str:
    lines = []
    for _, r in summary.iterrows():
        qty = int(r["수량"])
        unit_price = int(r["단가"])
        amount = int(r["금액"])
        if style == "receipt":
            lines.append(f"{r['품목']:<15} {qty}개  {money(amount)}")
        else:
            lines.append(f"- {r['품목']} {qty}개 × {money(unit_price)} = {money(amount)}")
    return "\n".join(lines)


def build_message(
    template_name: str,
    summary: pd.DataFrame,
    subtotal_amount: int,
    discount_rate: float,
    discount_amount: int,
    product_after_discount: int,
    shipping_fee: int,
    final_amount: int,
    brand_name: str,
    bank_account: str,
) -> str:
    today = datetime.now().strftime("%Y.%m.%d")
    basic_items = build_items_text(summary, "basic")
    receipt_items = build_items_text(summary, "receipt")

    discount_line = ""
    if discount_rate > 0:
        discount_line = f"\n할인 {discount_rate:.1f}%: -{money(discount_amount)}\n할인 적용 상품금액: {money(product_after_discount)}"

    shipping_line = f"택배비: {money(shipping_fee)}" if shipping_fee > 0 else "택배비: 무료 또는 별도 없음"

    if template_name == "1. 친절 기본형":
        return f"""안녕하세요. {brand_name}입니다 :)
주문 금액 안내드립니다.

{basic_items}

상품 합계: {money(subtotal_amount)}{discount_line}
{shipping_line}
총 결제금액: {money(final_amount)}

확인 부탁드립니다. 감사합니다."""

    if template_name == "2. 깔끔 영수증형":
        return f"""[{brand_name} 주문 계산서]
작성일: {today}

{receipt_items}

------------------------------
상품 합계      {money(subtotal_amount)}
할인 금액      -{money(discount_amount)}
택배비         {money(shipping_fee)}
------------------------------
최종 결제금액  {money(final_amount)}"""

    return f"""안녕하세요. {brand_name}입니다.
주문 확인되었습니다.

{basic_items}

상품 합계: {money(subtotal_amount)}{discount_line}
{shipping_line}
최종 결제금액: {money(final_amount)}

입금 안내: {bank_account}
입금 후 성함 남겨주시면 확인 도와드리겠습니다.
감사합니다."""

# =============================
# Header
# =============================
st.markdown(
    """
    <div class="hero-card">
        <div class="hero-title">식혜 주문 자동계산기 PRO</div>
        <div class="hero-sub">
            카톡 주문을 그대로 붙여넣으면 품목·수량·할인·택배비·최종 결제금액까지 계산합니다.<br>
            계산기 모티브의 대시보드와 고객 발송용 문구 3종을 제공합니다.
        </div>
        <div class="pill-row">
            <span class="pill">1L 자동 인식</span>
            <span class="pill">500ml 자동 인식</span>
            <span class="pill">200ml 파우치</span>
            <span class="pill">할인율 적용</span>
            <span class="pill">택배비 합산</span>
            <span class="pill">문구 선택/수정</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

sample = """식혜 1L 3개
호박 감주 1L 2개
식혜 500ml 5개
식혜 200ml 파우치 10개
단호박식혜 500ml 4개"""

left, right = st.columns([1.15, 0.85], gap="large")

with left:
    st.markdown('<div class="white-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">주문 내용 붙여넣기</div>', unsafe_allow_html=True)
    st.markdown('<div class="tiny-muted">카톡/문자 주문을 줄 단위로 붙여넣으세요. 예: 식혜 1L 3개 / 호박감주 500ml 2개</div>', unsafe_allow_html=True)
    order_text = st.text_area("", value=sample, height=255, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

rows, warnings = parse_order(order_text)

if rows:
    df = pd.DataFrame(rows)
    summary = (
        df.groupby(["품목", "단가"], as_index=False)
        .agg({"수량": "sum", "금액": "sum"})
        .sort_values("품목")
    )

    total_qty = int(summary["수량"].sum())
    subtotal_amount = int(summary["금액"].sum())
    discount_amount = int(round(subtotal_amount * (discount_rate / 100)))
    product_after_discount = subtotal_amount - discount_amount
    final_amount = product_after_discount + int(shipping_fee)

    with right:
        st.markdown(
            f"""
            <div class="calc-shell">
                <div class="calc-display">
                    <div class="display-label">최종 결제금액</div>
                    <div class="display-amount">{money(final_amount)}</div>
                </div>
                <div class="key-grid">
                    <div class="key-card"><div class="key-label">총 수량</div><div class="key-value">{total_qty:,}개</div></div>
                    <div class="key-card"><div class="key-label">상품 합계</div><div class="key-value">{money(subtotal_amount)}</div></div>
                    <div class="key-card"><div class="key-label">할인 금액</div><div class="key-value">-{money(discount_amount)}</div></div>
                    <div class="key-card"><div class="key-label">택배비</div><div class="key-value">{money(shipping_fee)}</div></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("총 수량", f"{total_qty:,}개")
    m2.metric("상품 합계", money(subtotal_amount))
    m3.metric("할인 적용 후", money(product_after_discount), delta=f"-{money(discount_amount)}")
    m4.metric("최종 결제금액", money(final_amount), delta=f"택배비 {money(shipping_fee)}")

    tab1, tab2, tab3 = st.tabs(["📋 계산 결과", "💬 고객 발송 문구", "🔎 상세 인식 내역"])

    with tab1:
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">품목별 합산</div>', unsafe_allow_html=True)
        show_summary = summary.copy()
        show_summary["단가"] = show_summary["단가"].map(money)
        show_summary["금액"] = show_summary["금액"].map(money)
        st.dataframe(show_summary, use_container_width=True, hide_index=True)

        calc_df = pd.DataFrame(
            [
                {"항목": "상품 합계", "금액": money(subtotal_amount)},
                {"항목": f"할인 ({discount_rate:.1f}%)", "금액": f"-{money(discount_amount)}"},
                {"항목": "할인 적용 상품금액", "금액": money(product_after_discount)},
                {"항목": "택배비", "금액": money(shipping_fee)},
                {"항목": "최종 결제금액", "금액": money(final_amount)},
            ]
        )
        st.markdown('<div class="section-title">결제 계산</div>', unsafe_allow_html=True)
        st.dataframe(calc_df, use_container_width=True, hide_index=True)
        csv = summary.to_csv(index=False).encode("utf-8-sig")
        st.download_button("계산 결과 CSV 다운로드", data=csv, file_name="sikhye_order_result.csv", mime="text/csv")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">고객에게 보낼 계산 문구</div>', unsafe_allow_html=True)
        st.markdown('<div class="tiny-muted">아래 3가지 형식 중 하나를 선택한 뒤, 필요한 부분을 직접 수정해서 복사하면 됩니다.</div>', unsafe_allow_html=True)

        template_name = st.radio(
            "문구 형식 선택",
            ["1. 친절 기본형", "2. 깔끔 영수증형", "3. 입금 안내형"],
            horizontal=True,
        )
        default_message = build_message(
            template_name,
            summary,
            subtotal_amount,
            discount_rate,
            discount_amount,
            product_after_discount,
            int(shipping_fee),
            final_amount,
            brand_name,
            bank_account,
        )
        edited_message = st.text_area(
            "선택한 문구 수정",
            value=default_message,
            height=330,
            key=f"message_{template_name}_{subtotal_amount}_{discount_amount}_{shipping_fee}_{final_amount}",
        )
        st.download_button(
            "문구 TXT 다운로드",
            data=edited_message.encode("utf-8-sig"),
            file_name="customer_message.txt",
            mime="text/plain",
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">상세 인식 내역</div>', unsafe_allow_html=True)
        detail = df.copy()
        detail["단가"] = detail["단가"].map(money)
        detail["금액"] = detail["금액"].map(money)
        st.dataframe(detail, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    with right:
        st.markdown(
            """
            <div class="calc-shell">
                <div class="calc-display">
                    <div class="display-label">최종 결제금액</div>
                    <div class="display-amount">0원</div>
                </div>
                <div class="key-grid">
                    <div class="key-card"><div class="key-label">총 수량</div><div class="key-value">0개</div></div>
                    <div class="key-card"><div class="key-label">상품 합계</div><div class="key-value">0원</div></div>
                    <div class="key-card"><div class="key-label">할인 금액</div><div class="key-value">0원</div></div>
                    <div class="key-card"><div class="key-label">택배비</div><div class="key-value">0원</div></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.warning("아직 인식된 주문이 없습니다. 예: 식혜 1L 3개 / 호박감주 500ml 2개 / 식혜 200ml 파우치 10개")

if warnings:
    with st.expander("인식하지 못한 줄 / 확인 필요"):
        for w in warnings:
            st.write("- " + w)

st.markdown('<div class="footer-note">개인정보 보호: 이 앱은 입력 내용을 별도 저장하지 않습니다. 배포 환경의 로그 저장 여부는 별도 확인이 필요합니다.</div>', unsafe_allow_html=True)
