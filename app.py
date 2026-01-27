import streamlit as st
import pandas as pd
from processor import ExcelProcessor
from ai_analyzer import AIAnalyzer

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
            
            # 메인 탭 생성
            tab_original, tab_rule, tab_ai = st.tabs(["📋 원본 데이터", "🔍 규칙 기반 검증", "🤖 AI 심층 분석"])

            # --- 1. 원본 데이터 탭 ---
            with tab_original:
                st.header("원본 데이터 확인")
                # 시트별 내부 탭
                sheet_tabs = st.tabs(list(processed_data.keys()))
                for tab, (sheet_name, data) in zip(sheet_tabs, processed_data.items()):
                    with tab:
                        st.subheader(f"'{sheet_name}' 시트 데이터")
                        df = pd.DataFrame(data)
                        st.dataframe(df, use_container_width=True)
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("행 수", len(df))
                        col2.metric("기준일", str(base_date))
                        col3.metric("계산방법", calc_method)
            
            # --- 2. 규칙 기반 검증 탭 ---
            with tab_rule:
                st.header("데이터 검증 (Hard Rules)")
                if st.button("🚀 규칙 기반 검증 시작", type="primary", key="btn_rule"):
                    from validator import DataValidator
                    validator = DataValidator(processed_data, base_date, calc_method)
                    v_results = validator.validate()
                    st.session_state['validation_results'] = v_results
                    st.session_state['validation_done'] = True
                
                if st.session_state.get('validation_done', False):
                    v_results = st.session_state.get('validation_results', {})
                    st.subheader("📊 검증 결과")
                    
                    validated_sheets = [name for name in processed_data.keys() if name in v_results]
                    if validated_sheets:
                        result_tabs = st.tabs(validated_sheets)
                        for tab, sheet_name in zip(result_tabs, validated_sheets):
                            with tab:
                                sheet_errors = v_results.get(sheet_name, {})
                                employee_errors = {k: v for k, v in sheet_errors.items() if k != "_global"}
                                global_errors = sheet_errors.get("_global", [])
                                total_error_count = sum(len(errs) for errs in employee_errors.values()) + len(global_errors)
                                
                                if total_error_count == 0:
                                    st.success("✅ 오류 0건 - 이상 없음")
                                else:
                                    st.error(f"⚠️ 총 {total_error_count}건의 오류 발견 (사원 {len(employee_errors)}명)")
                                    if global_errors:
                                        with st.expander("🔸 전체 관련 오류", expanded=True):
                                            for err in global_errors:
                                                st.warning(f"• {err}")
                                    for emp_id, errors in sorted(employee_errors.items()):
                                        with st.expander(f"👤 사원번호: {emp_id} ({len(errors)}건)", expanded=False):
                                            for err in errors:
                                                st.warning(f"• {err}")
                                
                                # 하단 여백 추가
                                st.markdown("<br>" * 15, unsafe_allow_html=True)
                    else:
                        st.info("검증 가능한 시트가 없습니다.")

            # --- 3. AI 심층 분석 탭 ---
            with tab_ai:
                st.header("AI 심층 분석 (K-IFRS 1019)")
                if not openai_api_key:
                    st.info("AI 분석을 사용하려면 왼쪽 사이드바에 OpenAI API Key를 입력해 주세요.")
                else:
                    if st.button("🧠 AI 분석 시작", type="secondary", key="btn_ai"):
                        with st.spinner("AI가 K-IFRS 1019 기준에 따라 데이터를 정밀 분석 중입니다..."):
                            analyzer = AIAnalyzer(openai_api_key)
                            ai_result = analyzer.analyze(processed_data, base_date, calc_method)
                            st.session_state['ai_analysis_result'] = ai_result
                            st.session_state['ai_analysis_done'] = True

                    if st.session_state.get('ai_analysis_done', False):
                        st.markdown("### 📋 AI 분석 보고서")
                        st.markdown(st.session_state.get('ai_analysis_result', ""))
                        st.download_button(
                            label="AI 분석 결과 다운로드 (TXT)",
                            data=st.session_state.get('ai_analysis_result', ""),
                            file_name=f"ai_analysis_{base_date}.txt",
                            mime="text/plain"
                        )
                
                # 하단 여백 추가
                st.markdown("<br>" * 15, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"오류 발생: {e}")
            st.exception(e) # 개발 중 상세 오류 확인용
    else:
        st.info("왼쪽 사이드바에서 엑셀 파일을 업로드해 주세요.")

if __name__ == "__main__":
    main()
