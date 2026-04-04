
import re
import io
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path

# ── 섹션 헤더 패턴 ──────────────────────────────────────────
SECTION_HEADER_PATTERNS = {
    "재무상태표":    re.compile(r'재\s*무\s*상\s*태\s*표.{0,10}제\s*\d+\s*기'),
    "손익계산서":    re.compile(r'손\s*익\s*계\s*산\s*서.{0,10}제\s*\d+\s*기'),
    "포괄손익계산서": re.compile(r'포\s*괄\s*손\s*익\s*계\s*산\s*서.{0,10}제\s*\d+\s*기'),
    "자본변동표":    re.compile(r'자\s*본\s*변\s*동\s*표.{0,10}제\s*\d+\s*기'),
    "현금흐름표":    re.compile(r'현\s*금\s*흐\s*름\s*표.{0,10}제\s*\d+\s*기'),
    "주석":         re.compile(r'^주\s*석\s'),
    "감사의견":     re.compile(r'독립된\s*감사인'),
    "표지":         re.compile(r'첨부\s*\)?\s*재\s*무\s*제\s*표'),
}


def load_htm(path):
    """HTM 파일을 읽어서 BeautifulSoup 객체로 반환"""
    with open(path, 'rb') as f:
        raw = f.read()
    cleaned = re.sub(b'\xef\xbf\xbd', b' ', raw)
    text = cleaned.decode('euc-kr', errors='ignore')
    return BeautifulSoup(text, 'lxml')


def classify_section(text):
    """텍스트 앞부분의 헤더 패턴으로 섹션 분류"""
    header = text[:100]
    for section, pattern in SECTION_HEADER_PATTERNS.items():
        if pattern.search(header):
            return section
    return "기타"


def parse_sections(soup, year, source):
    """PGBRK 기준으로 블록 분할 후 섹션 분류"""
    results = []
    pgbrks = soup.find_all('p', class_='PGBRK')
    current_section = "기타"

    for i, pgbrk in enumerate(pgbrks):
        block_tags = []
        nxt = pgbrk.find_next_sibling()
        while nxt:
            if 'PGBRK' in nxt.get('class', []):
                break
            block_tags.append(nxt)
            nxt = nxt.find_next_sibling()

        block_text = ' '.join(
            t.get_text(strip=True) for t in block_tags if t.get_text(strip=True)
        )
        if not block_text:
            continue

        classified = classify_section(block_text)
        if classified != "기타":
            current_section = classified

        results.append({
            "year":        year,
            "section":     current_section,
            "block_index": i,
            "content":     block_text,
            "source":      source,
        })

    return results


def parse_number(val):
    """회계 표기 숫자 변환: (123) → -123, - → 0, 10% → 10.0"""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == '-':
        return 0.0
    if s.endswith('%'):
        try:
            return float(s[:-1])
        except:
            return None
    s = re.sub(r'[주원개억만천]$', '', s)
    s = s.replace(',', '').replace(' ', '')
    if s.startswith('(') and s.endswith(')'):
        try:
            return -float(s[1:-1])
        except:
            return None
    try:
        return float(s)
    except:
        return None


def extract_year_from_header(df):
    """테이블 헤더에서 실제 당기 연도 추출"""
    for col in df.columns:
        m = re.search(r'20(\d{2})', str(col))
        if m:
            return int("20" + m.group(1))
    return None


def clean_financial_table(df, year, table_index, source):
    """DataFrame 정제: 컬럼 병합, 소제목 행 제거, 숫자 변환"""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [' '.join(str(c) for c in col).strip() for col in df.columns]

    cols = df.columns.tolist()

    ITEM_KEYWORDS = ['과 목', '구 분', '금융자산', '계 정 과 목', '기업명']
    과목_col = None
    for kw in ITEM_KEYWORDS:
        matched = [c for c in cols if kw in str(c)]
        if matched:
            과목_col = matched[0]
            break
    if 과목_col is None:
        return None

    당기_cols = [c for c in cols if '당기' in str(c)
                                  or '당 기' in str(c)
                                  or '(당)' in str(c)]
    전기_cols = [c for c in cols if '전기' in str(c)
                                  or '전 기' in str(c)
                                  or '(전)' in str(c)]
    if not 당기_cols:
        return None

    df_clean = pd.DataFrame()
    df_clean['항목'] = df[과목_col].astype(str).str.strip()

    if len(당기_cols) >= 2:
        df_clean['당기'] = df[당기_cols[0]].fillna(df[당기_cols[1]])
    else:
        df_clean['당기'] = df[당기_cols[0]]

    if len(전기_cols) >= 2:
        df_clean['전기'] = df[전기_cols[0]].fillna(df[전기_cols[1]])
    elif len(전기_cols) == 1:
        df_clean['전기'] = df[전기_cols[0]]

    # 소제목 행 제거
    df_clean = df_clean[
        df_clean['당기'].astype(str) != df_clean['항목'].astype(str)
    ]
    df_clean = df_clean.dropna(subset=['당기'], how='all')

    df_clean['당기_num'] = df_clean['당기'].apply(parse_number)
    if '전기' in df_clean.columns:
        df_clean['전기_num'] = df_clean['전기'].apply(parse_number)

    df_clean['year']        = year
    df_clean['table_index'] = table_index
    df_clean['source']      = source

    return df_clean


def parse_tables(soup, year, source):
    """HTML 테이블 추출 및 정제"""
    results = []
    tables = soup.find_all('table')

    for i, tbl in enumerate(tables):
        try:
            df = pd.read_html(io.StringIO(str(tbl)))[0]
        except:
            continue
        if df.shape[0] < 3 or df.shape[1] < 2:
            continue

        has_comma_num = bool(re.search(r'\d{1,3}(,\d{3})+', df.to_string()))
        has_float_col = any(df[c].dtype in ['float64', 'int64'] for c in df.columns)
        if not (has_comma_num or has_float_col):
            continue

        actual_year = extract_year_from_header(df) or year
        cleaned = clean_financial_table(df, actual_year, i, source)
        if cleaned is None:
            continue

        cleaned['table_index'] = i
        results.append(cleaned)

    return results


def parse_all(data_dir="."):
    """전체 HTM 파일 파싱 실행"""
    files = sorted(Path(data_dir).glob("감사보고서_*.htm"))
    all_sections, all_tables = [], []

    for f in files:
        year = int(re.search(r'(\d{4})', f.name).group(1))
        soup = load_htm(f)
        all_sections.extend(parse_sections(soup, year=year, source=f.name))
        all_tables.extend(parse_tables(soup, year=year, source=f.name))
        print(f"{year} 완료")

    df_sections = pd.DataFrame(all_sections)
    df_tables = pd.concat(
        [t for t in all_tables if not t.empty], ignore_index=True
    )
    return df_sections, df_tables


if __name__ == "__main__":
    df_sections, df_tables = parse_all()
    df_sections.to_csv("sections.csv", index=False, encoding="utf-8-sig")
    df_tables.to_csv("tables.csv",   index=False, encoding="utf-8-sig")
    print(f"sections.csv: {len(df_sections)}행")
    print(f"tables.csv:   {len(df_tables)}행")
