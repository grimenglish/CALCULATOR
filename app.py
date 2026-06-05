import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="식혜 주문 자동계산기", page_icon="🥤", layout="wide")

# -----------------------------
# 기본 설정
# -----------------------------
DEFAULT_PRODUCTS = {
    "일반식혜 1L": 5000,
    "일반식혜 500ml": 3000,
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

st.title("🥤 식혜 주문 자동계산기")
st.caption("카톡/문자 주문 내용을 그대로 붙여넣으면 품목, 수량, 금액을 자동 계산합니다.")

with st.sidebar:
    st.header("가격 설정")
    prices = {}
    for product, price in DEFAULT_PRODUCTS.items():
        prices[product] = st.number_input(product, min_value=0, value=price, step=100)

    st.divider()
    default_size = st.selectbox("크기 미기재 시 기본값", ["1L", "500ml"], index=0)
    st.caption("예: '식혜 3개'처럼 크기가 없으면 이 기준으로 계산")

# -----------------------------
# 파싱 함수
# -----------------------------
def normalize_text(text: str) -> str:
    text = text.replace("１", "1").replace("Ｌ", "L").replace("ｌ", "l")
    text = text.replace("리터", "L").replace("리뜨", "L")
    text = text.replace("미리", "ml").replace("밀리", "ml")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_product(line: str):
    line_low = line.lower()

    # 상품 종류
    if any(x in line for x in ["호박", "단호박", "호박감주", "호박 감주"]):
        base = "단호박식혜"
    elif any(x in line for x in ["식혜", "감주"]):
        base = "일반식혜"
    else:
        return None

    # 용량
    if re.search(r"(500\s*ml|500ml|500|0\.5\s*l|0.5l)", line_low):
        size = "500ml"
    elif re.search(r"(1\s*l|1l|1000\s*ml|1000ml|1\s*리터)", line_low):
        size = "1L"
    else:
        size = default_size

    return f"{base} {size}"


def detect_quantity(line: str) -> int:
    # 30개, 30 병, 30통처럼 단위가 붙은 숫자를 최우선 인식
    unit_matches = re.findall(r"(\d+)\s*(개|병|통|팩|봉|개입)", line)
    if unit_matches:
        return int(unit_matches[-1][0])

    # 한개, 두 개 등 간단 한글 숫자
    for word, num in KOR_NUM.items():
        if re.search(fr"{word}\s*(개|병|통|팩|봉)", line):
            return num

    # 단위 없이 숫자만 있으면 마지막 숫자를 수량 후보로 사용
    # 단, '식혜 1L'처럼 용량 숫자만 있는 경우는 1개로 처리
    numbers = re.findall(r"\d+", line)
    if len(numbers) >= 2:
        return int(numbers[-1])
    if len(numbers) == 1 and not re.search(r"(\d+)\s*(l|L|ml|ML)", line):
        return int(numbers[0])

    return 1


def parse_order(text: str):
    rows = []
    warnings = []
    lines = [normalize_text(x) for x in text.splitlines() if normalize_text(x)]

    for line in lines:
        product = detect_product(line)
        if not product:
            warnings.append(f"인식 제외: {line}")
            continue

        qty = detect_quantity(line)
        unit_price = prices.get(product, 0)
        amount = qty * unit_price

        rows.append({
            "원문": line,
            "품목": product,
            "수량": qty,
            "단가": unit_price,
            "금액": amount,
        })

    return rows, warnings


sample = """식혜 1L 3개
호박 감주 1L 2개
식혜 500ml 5개
단호박식혜 500ml 4개"""

order_text = st.text_area("주문 내용 붙여넣기", value=sample, height=220)

rows, warnings = parse_order(order_text)

if rows:
    df = pd.DataFrame(rows)

    # 같은 품목끼리 합산
    summary = (
        df.groupby(["품목", "단가"], as_index=False)
        .agg({"수량": "sum", "금액": "sum"})
        .sort_values("품목")
    )

    total_qty = int(summary["수량"].sum())
    total_amount = int(summary["금액"].sum())

    col1, col2, col3 = st.columns(3)
    col1.metric("총 수량", f"{total_qty:,}개")
    col2.metric("총 금액", f"{total_amount:,}원")
    col3.metric("인식된 주문 줄", f"{len(df):,}줄")

    st.subheader("계산 결과")
    show_summary = summary.copy()
    show_summary["단가"] = show_summary["단가"].map(lambda x: f"{x:,}원")
    show_summary["금액"] = show_summary["금액"].map(lambda x: f"{x:,}원")
    st.dataframe(show_summary, use_container_width=True, hide_index=True)

    st.subheader("고객에게 보낼 계산 문구")
    message_lines = []
    for _, r in summary.iterrows():
        message_lines.append(f"{r['품목']} {int(r['수량'])}개 = {int(r['금액']):,}원")
    message_lines.append(f"총합 = {total_amount:,}원")
    result_message = "\n".join(message_lines)
    st.code(result_message, language="text")

    st.subheader("상세 인식 내역")
    detail = df.copy()
    detail["단가"] = detail["단가"].map(lambda x: f"{x:,}원")
    detail["금액"] = detail["금액"].map(lambda x: f"{x:,}원")
    st.dataframe(detail, use_container_width=True, hide_index=True)

    csv = summary.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "계산 결과 CSV 다운로드",
        data=csv,
        file_name="sikhye_order_result.csv",
        mime="text/csv",
    )
else:
    st.warning("아직 인식된 주문이 없습니다. 예: 식혜 1L 3개 / 호박감주 500ml 2개")

if warnings:
    with st.expander("인식하지 못한 줄"):
        for w in warnings:
            st.write("- " + w)

st.divider()
st.caption("개인정보 보호: 이 앱은 입력 내용을 서버에 따로 저장하지 않습니다. 배포 환경에 따라 로그 저장 여부는 별도 확인이 필요합니다.")
