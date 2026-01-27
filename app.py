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
    
    # AI 설정
    st.sidebar.subheader("🤖 AI 분석 설정")
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    
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
            
            # 원본 데이터 섹션
            st.divider()
            st.header("📋 원본 데이터")
            
            # 탭을 생성하여 시트별로 원본 데이터 보기
            data_tabs = st.tabs(list(processed_data.keys()))
            
            for tab, (sheet_name, data) in zip(data_tabs, processed_data.items()):
                with tab:
                    st.subheader(f"'{sheet_name}' 시트 데이터")
                    
                    # 리스트 형태의 데이터를 데이터프레임으로 변환하여 표시
                    df = pd.DataFrame(data)
                    st.dataframe(df, width='stretch')
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("행 수", len(df))
                    col2.metric("기준일", str(base_date))
                    col3.metric("계산방법", calc_method)
            
            # 검증 섹션
            st.divider()
            st.header("🔍 데이터 검증")
            
            if st.button("🚀 검증 시작", type="primary"):
                from validator import DataValidator
                
                # 검증 실행
                validator = DataValidator(processed_data, base_date, calc_method)
                v_results = validator.validate()
                
                # 세션 상태에 검증 결과 저장
                st.session_state['validation_results'] = v_results
                st.session_state['validation_done'] = True
            
            # 검증 결과 표시
            if st.session_state.get('validation_done', False):
                v_results = st.session_state.get('validation_results', {})
                
                st.divider()
                st.subheader("📊 검증 결과")
                
                # 검증된 시트만 필터링 (데이터가 있는 시트)
                validated_sheets = [name for name in processed_data.keys() 
                                   if name in v_results]
                
                if validated_sheets:
                    # 시트별 탭 생성
                    result_tabs = st.tabs(validated_sheets)
                    
                    for tab, sheet_name in zip(result_tabs, validated_sheets):
                        with tab:
                            sheet_errors = v_results.get(sheet_name, {})
                            
                            # _global 키 제외하고 사원번호별 오류만 카운트
                            employee_errors = {k: v for k, v in sheet_errors.items() if k != "_global"}
                            global_errors = sheet_errors.get("_global", [])
                            
                            total_error_count = sum(len(errs) for errs in employee_errors.values()) + len(global_errors)
                            
                            if total_error_count == 0:
                                st.success(f"✅ 오류 0건 - 이상 없음")
                            else:
                                st.error(f"⚠️ 총 {total_error_count}건의 오류 발견 (사원 {len(employee_errors)}명)")
                                
                                # 전역 오류 먼저 표시
                                if global_errors:
                                    with st.expander("🔸 전체 관련 오류", expanded=True):
                                        for err in global_errors:
                                            st.warning(f"• {err}")
                                
                                # 사원번호별 오류 표시
                                for emp_id, errors in sorted(employee_errors.items()):
                                    with st.expander(f"👤 사원번호: {emp_id} ({len(errors)}건)", expanded=False):
                                        for err in errors:
                                            st.warning(f"• {err}")
                else:
                    st.info("검증 가능한 시트가 없습니다.")
            
        except Exception as e:
            st.error(f"오류 발생: {e}")
            st.exception(e) # 개발 중 상세 오류 확인용
    else:
        st.info("왼쪽 사이드바에서 엑셀 파일을 업로드해 주세요.")

if __name__ == "__main__":
    main()
