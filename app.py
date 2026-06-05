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
    "일반식혜 500ml": 2950,
    "일반식혜 200ml 파우치": 1550,
    "단호박식혜 1L": 6700,
    "단호박식혜 500ml": 3950,
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


st.markdown(
    """
<style>
:root {
    --ink: #0f172a;
    --muted: #64748b;
    --line: rgba(148, 163, 184, 0.34);
    --soft: #f8fafc;
    --softbox: #f1f5f9;
    --navy1: #0f172a;
    --navy2: #1e293b;
    --navy3: #334155;
    --gold: #fbbf24;
    --teal: #22c55e;
    --red: #ef4444;
}
.stApp {
    background:
        radial-gradient(circle at top left, rgba(59,130,246,.09), transparent 28%),
        radial-gradient(circle at top right, rgba(251,191,36,.08), transparent 25%),
        linear-gradient(135deg, #f8fafc 0%, #eef2f7 48%, #f8fafc 100%);
}
.block-container {
    padding-top: 1.4rem;
    padding-bottom: 3rem;
}

/* HERO */
.hero {
    background: linear-gradient(135deg, #111827 0%, #1b2940 56%, #31445f 100%);
    color: white;
    padding: 32px 34px;
    border-radius: 28px;
    box-shadow: 0 22px 48px rgba(15, 23, 42, .22);
    margin-bottom: 22px;
    overflow: hidden;
}
.hero-grid {
    display: grid;
    grid-template-columns: 1.2fr .8fr;
    gap: 22px;
    align-items: center;
}
.hero-title {
    font-size: 40px;
    font-weight: 950;
    letter-spacing: -0.05em;
    margin: 0 0 10px 0;
}
.hero-sub {
    color: #dbeafe;
    font-size: 17px;
    line-height: 1.65;
    margin-bottom: 18px;
}
.badge-wrap {
    display: flex;
    gap: 9px;
    flex-wrap: wrap;
}
.badge {
    display: inline-flex;
    align-items: center;
    padding: 8px 13px;
    border-radius: 999px;
    background: rgba(255,255,255,.94);
    color: #1e3a8a;
    font-size: 13px;
    font-weight: 900;
}
.hero-illus {
    background: linear-gradient(135deg, rgba(255,255,255,.10), rgba(255,255,255,.05));
    border: 1px solid rgba(255,255,255,.12);
    border-radius: 24px;
    padding: 14px;
    backdrop-filter: blur(6px);
}
.section-title {
    font-size: 25px;
    font-weight: 950;
    color: var(--ink);
    margin: 8px 0 6px;
    letter-spacing: -0.05em;
}
.help-text {
    color: var(--muted);
    font-size: 14px;
    margin-bottom: 14px;
}
.product-name {
    font-size: 18px;
    font-weight: 950;
    color: var(--ink);
    letter-spacing: -0.04em;
    margin-bottom: 2px;
}
.product-price {
    color: #475569;
    font-size: 14px;
    margin-bottom: 10px;
}
.summary-card {
    background: linear-gradient(135deg, #0f172a 0%, #111827 50%, #14213a 100%);
    color: white;
    border-radius: 28px;
    padding: 28px 30px;
    box-shadow: 0 24px 54px rgba(15, 23, 42, .30);
    border: 1px solid rgba(255,255,255,.08);
    position: sticky;
    top: 1rem;
}
.summary-card .label {
    color: #93c5fd;
    font-weight: 900;
    font-size: 14px;
    margin-bottom: 6px;
}
.summary-card .money {
    font-size: 48px;
    font-weight: 950;
    color: #fbbf24;
    letter-spacing: -0.06em;
    margin-bottom: 18px;
}
.summary-row {
    display: flex;
    justify-content: space-between;
    border-top: 1px solid rgba(255,255,255,.11);
    padding-top: 12px;
    margin-top: 12px;
    font-size: 16px;
}
.summary-row b {
    font-size: 18px;
}
.mini-metric {
    background: rgba(255,255,255,.86);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 16px 18px;
    box-shadow: 0 10px 24px rgba(15,23,42,.05);
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
hr.soft {
    border: none;
    border-top: 1px solid rgba(148,163,184,.35);
    margin: 28px 0;
}

/* Product box */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(241,245,249,.96);
    border: 1px solid rgba(148,163,184,.42);
    border-radius: 22px;
    box-shadow: 0 12px 26px rgba(15,23,42,.05);
}

/* Buttons bigger */
div[data-testid="stButton"] > button {
    min-height: 46px;
    font-size: 18px !important;
    font-weight: 900 !important;
    border-radius: 14px !important;
}

/* Make +/- rows feel like calculator buttons */
div[data-testid="stButton"] > button[kind="secondary"] {
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    border: 1px solid rgba(148,163,184,.55);
    box-shadow: 0 3px 10px rgba(15,23,42,.06);
}

/* Force Streamlit button label size */
div[data-testid="stButton"] button p,
div[data-testid="stButton"] button span,
div[data-testid="stButton"] button {
    font-size: 24px !important;
    font-weight: 950 !important;
    line-height: 1.1 !important;
}

/* Keep long action buttons slightly smaller */
button[title="전체 수량 초기화"] p {
    font-size: 16px !important;
}

/* Number input internal +/- buttons */
div[data-testid="stNumberInput"] button,
div[data-testid="stNumberInput"] button svg {
    font-size: 22px !important;
    font-weight: 950 !important;
}

/* Textareas */
div[data-testid="stTextArea"] textarea {
    font-size: 16px;
    line-height: 1.55;
}

/* Select */
div[data-baseweb="select"] > div {
    border-radius: 12px;
}

/* Pure HTML illustration - no SVG, prevents Streamlit from printing SVG code */
.hero-illus {
    background: linear-gradient(135deg, rgba(255,255,255,.13), rgba(255,255,255,.05));
    border: 1px solid rgba(255,255,255,.13);
    border-radius: 26px;
    padding: 20px;
    min-height: 230px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}
.illu-stage {
    width: 100%;
    max-width: 470px;
    display: grid;
    grid-template-columns: 0.9fr 1.1fr;
    gap: 18px;
    align-items: center;
}
.illu-phone {
    background: linear-gradient(180deg, #f8fafc 0%, #dbeafe 100%);
    border-radius: 28px;
    padding: 18px;
    box-shadow: 0 18px 35px rgba(0,0,0,.18);
}
.illu-screen {
    background: #0f172a;
    border-radius: 20px;
    padding: 16px;
}
.illu-money {
    color: #fbbf24;
    font-size: 25px;
    font-weight: 950;
    letter-spacing: -0.05em;
    margin-bottom: 14px;
}
.illu-keyrow {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
}
.illu-key {
    background: #eff6ff;
    color: #1e3a8a;
    border-radius: 12px;
    text-align: center;
    padding: 8px 0;
    font-weight: 950;
    font-size: 18px;
}
.illu-panel {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.illu-card {
    background: rgba(255,255,255,.94);
    border: 1px solid rgba(219,234,254,.8);
    border-radius: 20px;
    padding: 14px 16px;
    box-shadow: 0 12px 26px rgba(15,23,42,.12);
}
.illu-card-title {
    color: #0f172a;
    font-size: 14px;
    font-weight: 950;
    margin-bottom: 8px;
}
.illu-line {
    height: 10px;
    background: #cbd5e1;
    border-radius: 999px;
    margin: 7px 0;
}
.illu-line.short { width: 68%; }
.illu-line.blue { background: #93c5fd; width: 86%; }
.illu-check {
    display: inline-flex;
    width: 34px;
    height: 34px;
    border-radius: 999px;
    background: linear-gradient(135deg, #2563eb, #0ea5e9);
    color: white;
    align-items: center;
    justify-content: center;
    font-weight: 950;
    margin-right: 8px;
}

@media (max-width: 900px) {
    .hero-grid {
        grid-template-columns: 1fr;
    }
    .hero-title {
        font-size: 32px;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


for product in PRODUCT_ORDER:
    st.session_state.setdefault(f"qty_{product}", 0)
st.session_state.setdefault("order_text", "")


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def change_qty(product, delta):
    key = f"qty_{product}"
    current = safe_int(st.session_state.get(key, 0), 0)
    st.session_state[key] = max(0, current + delta)


def set_qty_zero(product):
    st.session_state[f"qty_{product}"] = 0


def reset_all_qty():
    for p in PRODUCT_ORDER:
        st.session_state[f"qty_{p}"] = 0


def put_example():
    st.session_state["order_text"] = EXAMPLE_TEXT


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
    re.compile(
        rf"(?P<base>{BASE_RE})?\s*(?P<size>{SIZE_RE})\s*(?:짜리)?\s*(?:x|X|×|\*|곱하기|에)?\s*(?P<qty>{QTY_RE})\s*{UNIT_RE}",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?P<size>{SIZE_RE})\s*(?P<base>{BASE_RE})\s*(?P<qty>{QTY_RE})\s*{UNIT_RE}",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?P<base>{BASE_RE})\s*(?P<qty>{QTY_RE})\s*(?:개|병|통|팩|봉|개입|파우치|잔|박스|box)",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?P<qty>{QTY_RE})\s*(?:개|병|통|팩|봉|개입|파우치|잔|박스|box)\s*(?P<base>{BASE_RE})\s*(?P<size>{SIZE_RE})?",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?P<base>{BASE_RE})\s*(?P<size>{SIZE_RE})",
        re.IGNORECASE,
    ),
]


def normalize_for_parse(text):
    text = str(text)
    replacements = {
        "１": "1", "２": "2", "３": "3", "４": "4", "５": "5",
        "６": "6", "７": "7", "８": "8", "９": "9", "０": "0",
        "Ｌ": "L", "ｌ": "l", "×": "x",
        "미리": "ml", "밀리": "ml",
    }
    for a, b in replacements.items():
        text = text.replace(a, b)
    text = text.replace("㎖", "ml").replace("ℓ", "L")
    text = re.sub(r"(\d)\s*(l|L|ml|ML)", lambda m: m.group(1) + m.group(2).lower(), text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def qty_to_int(value):
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


def parse_text_orders(text, prices, default_size):
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

            if not base_text and not size_text:
                continue

            product = product_from_parts(base_text, size_text, default_size)
            if product not in prices:
                continue

            qty = max(1, qty_to_int(qty_text))
            rows.append({
                "입력방식": "문구 인식",
                "원문": m.group(0).strip(),
                "품목": product,
                "수량": qty,
                "단가": int(prices[product]),
                "금액": qty * int(prices[product]),
            })
            used_spans.append(m.span())
    return rows


def parse_button_orders(prices):
    rows = []
    for product in PRODUCT_ORDER:
        qty = safe_int(st.session_state.get(f"qty_{product}", 0), 0)
        if qty > 0:
            rows.append({
                "입력방식": "버튼 입력",
                "원문": "-",
                "품목": product,
                "수량": qty,
                "단가": int(prices[product]),
                "금액": qty * int(prices[product]),
            })
    return rows


def build_templates(summary, subtotal, discount_rate, discount_amount, shipping_fee, shipping_enabled, final_amount, account, depositor):
    item_lines = []
    for _, r in summary.iterrows():
        item_lines.append(f"- {r['품목']} {int(r['수량'])}개 = {int(r['금액']):,}원")

    account_text = account.strip() if account and account.strip() else "계좌번호 미입력"
    depositor_text = depositor.strip() if depositor and depositor.strip() else "예금주 미입력"
    real_shipping = shipping_fee if shipping_enabled else 0
    shipping_note = "택배비는 업체에서 부담합니다." if not shipping_enabled else ""

    basic = "\n".join([
        "안녕하세요. 주문 금액 안내드립니다.",
        "",
        *item_lines,
        "",
        f"상품 합계 = {subtotal:,}원",
        f"할인 {discount_rate:.1f}% = -{discount_amount:,}원",
        f"택배비 = {real_shipping:,}원",
        f"최종 결제금액 = {final_amount:,}원",
        *( [shipping_note] if shipping_note else [] ),
        "",
        "확인 부탁드립니다. 감사합니다.",
    ])

    receipt = "\n".join([
        "[식혜명가 주문 계산서]",
        "--------------------",
        *item_lines,
        "--------------------",
        f"상품 합계       {subtotal:,}원",
        f"할인 금액      -{discount_amount:,}원",
        f"택배비          {real_shipping:,}원",
        "--------------------",
        f"최종 결제금액   {final_amount:,}원",
        *( ["※ 택배비는 업체 부담"] if not shipping_enabled else [] ),
    ])

    deposit = "\n".join([
        "주문 금액 안내드립니다.",
        "",
        *item_lines,
        "",
        f"상품 합계: {subtotal:,}원",
        f"할인 금액: -{discount_amount:,}원",
        f"택배비: {real_shipping:,}원",
        f"입금하실 금액: {final_amount:,}원",
        *( [shipping_note] if shipping_note else [] ),
        "",
        f"입금계좌: {account_text}",
        f"예금주: {depositor_text}",
        "",
        "입금 후 성함 남겨주시면 확인하겠습니다.",
    ])

    free_shipping = "\n".join([
        "안녕하세요. 무료배송으로 주문 금액 안내드립니다.",
        "",
        *item_lines,
        "",
        f"상품 합계 = {subtotal:,}원",
        f"할인 {discount_rate:.1f}% = -{discount_amount:,}원",
        "택배비 = 0원",
        "택배비는 업체에서 부담합니다.",
        f"최종 결제금액 = {final_amount:,}원",
        "",
        "확인 부탁드립니다. 감사합니다.",
    ])

    return {
        "1. 친절 기본형": basic,
        "2. 깔끔 영수증형": receipt,
        "3. 입금 안내형": deposit,
        "4. 무료배송 안내형": free_shipping,
    }


with st.sidebar:
    st.markdown("## 가격 설정")
    prices = {}
    for product, default_price in PRODUCTS.items():
        prices[product] = int(st.number_input(product, min_value=0, value=default_price, step=100, key=f"price_{product}"))

    st.divider()
    st.markdown("## 할인 / 배송")
    discount_rate = float(st.number_input("상품 전체 할인율 (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0))
    shipping_fee_setting = int(st.number_input("택배비", min_value=0, value=4000, step=500))
    shipping_enabled = st.toggle("택배비 적용", value=True, help="끄면 택배비가 최종금액에 합산되지 않습니다.")

    st.divider()
    st.markdown("## 자동 인식")
    default_size = st.selectbox("크기 미기재 시 기본값", ["1L", "500ml", "200ml 파우치"], index=0)
    st.caption("예: '식혜 3개'처럼 크기가 없으면 이 기준으로 계산")

    st.divider()
    st.markdown("## 입금 안내")
    account_number = st.text_input(
        "계좌번호",
        value="3333-29-8917220",
        placeholder="예: 농협 000-0000-0000-00",
        help="기본값이 들어가 있지만 필요하면 수정할 수 있습니다.",
    )
    account_holder = st.text_input(
        "예금주",
        value="이서백(식혜명가)",
        placeholder="예: 식혜명가",
        help="기본값이 들어가 있지만 필요하면 수정할 수 있습니다.",
    )


button_rows = parse_button_orders(prices)
text_rows = parse_text_orders(st.session_state.get("order_text", ""), prices, default_size)
rows = button_rows + text_rows

if rows:
    df = pd.DataFrame(rows)
    summary = df.groupby(["품목", "단가"], as_index=False).agg({"수량": "sum", "금액": "sum"})
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

st.markdown(
    """
<div class="hero">
    <div class="hero-grid">
        <div>
            <div class="hero-title">식혜 주문 자동계산기 PRO</div>
            <div class="hero-sub">왼쪽에서 상품 수량을 빠르게 누르고, 오른쪽에서 최종금액을 바로 확인합니다.<br>카톡 주문 문구 인식, 무료배송 문구, 입금 안내 문구까지 한 번에 처리합니다.</div>
            <div class="badge-wrap">
                <span class="badge">세로형 수량 계산</span>
                <span class="badge">카톡 문구 자동 인식</span>
                <span class="badge">택배비 ON/OFF</span>
                <span class="badge">무료배송 문구 추가</span>
                <span class="badge">계좌문구 자동 삽입</span>
            </div>
        </div>
        <div class="hero-illus">
            <div class="illu-stage">
                <div class="illu-phone">
                    <div class="illu-screen">
                        <div class="illu-money">28,000원</div>
                        <div class="illu-keyrow">
                            <div class="illu-key">-</div>
                            <div class="illu-key">+</div>
                            <div class="illu-key">+5</div>
                        </div>
                    </div>
                </div>
                <div class="illu-panel">
                    <div class="illu-card">
                        <div class="illu-card-title"><span class="illu-check">✓</span>주문 자동 인식</div>
                        <div class="illu-line blue"></div>
                        <div class="illu-line short"></div>
                    </div>
                    <div class="illu-card">
                        <div class="illu-card-title">식혜 1L × 3</div>
                        <div class="illu-line"></div>
                        <div class="illu-line blue"></div>
                    </div>
                    <div class="illu-card">
                        <div class="illu-card-title">무료배송 문구 자동 생성</div>
                        <div class="illu-line blue"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)


main_left, main_right = st.columns([1.28, 1], gap="large")

with main_left:
    st.markdown('<div class="section-title">① 수량 버튼 계산기</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-text">상품별 박스가 세로로 정리되어 구분이 쉽습니다. 카톡 문구와 합산됩니다.</div>', unsafe_allow_html=True)

    c_reset, c_info = st.columns([1, 1.5])
    with c_reset:
        st.button("전체 수량 초기화", on_click=reset_all_qty, use_container_width=True)
    with c_info:
        st.caption("버튼 입력 + 문구 입력 합산")

    for product in PRODUCT_ORDER:
        with st.container(border=True):
            st.markdown(f'<div class="product-name">{product}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="product-price">단가 {prices[product]:,}원</div>', unsafe_allow_html=True)

            q1, q2 = st.columns([1.1, 1.8])
            with q1:
                st.number_input(
                    f"{product} 수량",
                    min_value=0,
                    step=1,
                    key=f"qty_{product}",
                    label_visibility="collapsed",
                )
            with q2:
                b1, b2, b3, b4 = st.columns(4)
                b1.button("-", key=f"minus_{product}", on_click=change_qty, args=(product, -1), use_container_width=True)
                b2.button("+", key=f"plus_{product}", on_click=change_qty, args=(product, 1), use_container_width=True)
                b3.button("+5", key=f"plus5_{product}", on_click=change_qty, args=(product, 5), use_container_width=True)
                b4.button("0", key=f"zero_{product}", on_click=set_qty_zero, args=(product,), use_container_width=True)

with main_right:
    st.markdown('<div class="section-title">총합계</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="summary-card">
    <div class="label">최종 결제금액</div>
    <div class="money">{final_amount:,}원</div>
    <div class="summary-row"><span>총 수량</span><b>{total_qty:,}개</b></div>
    <div class="summary-row"><span>상품 합계</span><b>{subtotal:,}원</b></div>
    <div class="summary-row"><span>할인 금액</span><b>-{discount_amount:,}원</b></div>
    <div class="summary-row"><span>택배비</span><b>{shipping_fee:,}원</b></div>
    <div class="summary-row"><span>할인 적용 후</span><b>{after_discount:,}원</b></div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("### 빠른 확인")
    m1, m2 = st.columns(2)
    with m1:
        st.markdown(f'<div class="mini-metric">상품합계<br><b>{subtotal:,}원</b></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="mini-metric">택배비<br><b>{shipping_fee:,}원</b></div>', unsafe_allow_html=True)


st.markdown('<hr class="soft">', unsafe_allow_html=True)

st.markdown('<div class="section-title">② 주문내용 붙여넣기</div>', unsafe_allow_html=True)
st.markdown('<div class="help-text">카톡 대화처럼 대충 적어도 최대한 인식합니다. 예시는 흐리게만 보이며 계산에는 적용되지 않습니다.</div>', unsafe_allow_html=True)

ex1, ex2 = st.columns([1, 1])
with ex1:
    with st.expander("예시 문구 복사용"):
        st.markdown(f'<div class="copy-box">{EXAMPLE_TEXT}</div>', unsafe_allow_html=True)
with ex2:
    st.button("예시를 입력창에 넣기", on_click=put_example, use_container_width=True)

order_text = st.text_area(
    "주문내용 입력",
    key="order_text",
    height=180,
    placeholder=EXAMPLE_TEXT,
    label_visibility="collapsed",
)

button_rows = parse_button_orders(prices)
text_rows = parse_text_orders(order_text, prices, default_size)
rows = button_rows + text_rows
if rows:
    df = pd.DataFrame(rows)
    summary = df.groupby(["품목", "단가"], as_index=False).agg({"수량": "sum", "금액": "sum"})
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

result_left, result_right = st.columns([1.4, 1], gap="large")

with result_left:
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

with result_right:
    st.markdown('<div class="section-title">④ 고객에게 보낼 계산 문구</div>', unsafe_allow_html=True)

    if not summary.empty:
        templates = build_templates(
            summary,
            subtotal,
            discount_rate,
            discount_amount,
            shipping_fee_setting,
            shipping_enabled,
            final_amount,
            account_number,
            account_holder,
        )

        template_choice = st.selectbox("문구 형식 선택", list(templates.keys()), index=0)
        edited_message = st.text_area(
            "선택 문구 수정",
            value=templates[template_choice],
            height=290,
        )

        d1, d2 = st.columns(2)
        csv = summary.to_csv(index=False).encode("utf-8-sig")

        d1.download_button(
            "CSV 다운로드",
            data=csv,
            file_name=f"sikhye_order_result_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        d2.download_button(
            "문구 TXT 다운로드",
            data=edited_message.encode("utf-8-sig"),
            file_name=f"sikhye_customer_message_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    else:
        st.info("주문이 계산되면 고객 발송 문구가 자동 생성됩니다.")


st.caption("개인정보 보호: 이 앱은 입력 내용을 별도 DB에 저장하지 않습니다. 배포 환경의 로그 정책은 별도 확인하세요.")
