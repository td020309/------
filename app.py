import streamlit as st
import pandas as pd
from processor import ExcelProcessor

def main():
    st.set_page_config(page_title="엑셀 명부 검증 프로그램", layout="wide")
    st.title("📊 엑셀 명부 검증 프로그램")
    
    st.sidebar.header("설정")
    
    # 검증 기준 설정
    st.sidebar.subheader("📌 검증 설정")
    base_date = st.sidebar.date_input("검증 기준일", value=pd.Timestamp.now())
    calc_method = st.sidebar.selectbox(
        "계산 방법",
        options=["월상", "월사", "일할"],
        help="월상: 월의 첫날 기준, 월사: 월의 마지막날 기준, 일할: 실제 일수 기준"
    )
    
    st.sidebar.divider()
    uploaded_file = st.sidebar.file_uploader("엑셀 파일을 업로드하세요", type=["xlsx", "xls"])

    if uploaded_file is not None:
        processor = ExcelProcessor(uploaded_file)
        
        try:
            # 시트별 정제된 데이터 가져오기
            processed_data = processor.process()
            
            if not processed_data:
                st.warning("매칭된 시트가 없습니다. 시트 이름을 확인해 주세요 (예: '직원명부', '급여대장')")
                return

            st.success(f"총 {len(processed_data)}개의 시트가 처리되었습니다.")
            
            # 탭을 생성하여 시트별로 결과 보기
            tabs = st.tabs(list(processed_data.keys()))
            
            for tab, (sheet_name, data) in zip(tabs, processed_data.items()):
                with tab:
                    st.subheader(f"'{sheet_name}' 시트 데이터")
                    
                    # 리스트 형태의 데이터를 데이터프레임으로 변환하여 표시
                    df = pd.DataFrame(data)
                    st.dataframe(df)
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("행 수", len(df))
                    col2.metric("기준일", str(base_date))
                    col3.metric("계산방법", calc_method)
                    
                    st.info("검증 로직(validator.py)은 추후 연결될 예정입니다.")
            
        except Exception as e:
            st.error(f"오류 발생: {e}")
            st.exception(e) # 개발 중 상세 오류 확인용
    else:
        st.info("왼쪽 사이드바에서 엑셀 파일을 업로드해 주세요.")

if __name__ == "__main__":
    main()
