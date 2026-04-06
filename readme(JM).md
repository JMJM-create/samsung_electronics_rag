📊 Financial Report RAG System
금융 감사보고서 자동 파싱 및 자연어 질의응답 시스템

이 프로젝트는 기업의 htm 형식 감사보고서(재무제표, 주석 등)를 자동으로 파싱하여 구조화된 데이터로 변환하고, 이를 바탕으로 사용자가 자연어로 질문했을 때 정확한 답변을 제공하는 RAG(Retrieval-Augmented Generation) 시스템입니다.

🚀 주요 기능
1. Financial Report Parser (parser.py)
자동 섹션 분류: 재무상태표, 손익계산서, 현금흐름표, 주석 등 감사보고서의 주요 섹션을 정규표현식(Regex)을 통해 자동으로 탐지하고 분류합니다.

표(Table) 구조화: 복잡한 htm 형태의 재무제표 테이블을 Pandas DataFrame으로 변환하며, 콤마(,)가 포함된 숫자 데이터 및 연도별 데이터를 클리닝합니다.

대용량 처리: 다수 연도의 감사보고서를 일괄 처리하여 분석 가능한 데이터셋으로 병합합니다.

2. Natural Language QA (natural_rag.ipynb)
임베딩 및 검색: RobertaModel 등을 활용하여 텍스트 데이터를 벡터화하고, 사용자 질문과 가장 관련 있는 섹션을 검색합니다.

대화형 인터페이스: 대화 기록(History)을 관리하여 문맥을 유지하는 질의응답을 지원합니다.

하드웨어 가속: Apple Silicon(MPS) 디바이스를 지원하여 빠른 임베딩 및 추론 속도를 제공합니다.

🛠 Tech Stack
Language: Python 3.10+

Data Processing: Pandas, BeautifulSoup4, Re (Regex)

NLP/Deep Learning: PyTorch, Transformers (RobertaModel), HuggingFace

Environment: Jupyter Notebook, Anaconda

📂 파일 구조
parser.py: htm 파일을 읽어 재무제표 및 주석 데이터를 추출하는 파이프라인

natural_rag.ipynb: 추출된 데이터를 기반으로 RAG 시스템을 구동하는 메인 노트북

감사보고서_*.htm: (Input) 분석 대상이 되는 원본 기업 공시 파일

📝 사용 방법
데이터 준비:
분석하고자 하는 감사보고서 htm 파일들을 작업 디렉토리에 위치시킵니다.

데이터 파싱:

Python
from parser import parse_all
df_sections, df_tables = parse_all(data_dir=".")
질의응답 실행:
natural_rag.ipynb를 실행하여 모델을 로드하고 질문을 입력합니다.

Plaintext
질문 > 2025년도 연결재무제표상 영업이익은 얼마인가요?
━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━
답변: 2025년도 영업이익은 약 XXX억 원으로 확인됩니다. 이는 전년 대비 XX% 증가한 수치입니다.
━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━​━
