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
    
    # 날짜 입력을 텍스트로 변경 (사용자 요청: 숫자로 입력하는 것이 편리함)
    default_date = pd.Timestamp.now().strftime("%Y%m%d")
    base_date_input = st.sidebar.text_input(
        "검증 기준일 (8자리 숫자)", 
        value=default_date,
        help="예: 20241231"
    )
    
    try:
        if len(base_date_input) == 8:
            base_date = pd.to_datetime(base_date_input, format='%Y%m%d').date()
        else:
            base_date = pd.to_datetime(base_date_input).date()
        st.sidebar.caption(f"📅 인식된 날짜: {base_date.strftime('%Y-%m-%d')}")
    except:
        st.sidebar.error("⚠️ 날짜 형식이 잘못되었습니다. (예: 20241231)")
        return

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
            
            # --- 1. 원본 데이터 섹션 (상단 이동) ---
            st.header("📋 원본 데이터 확인")
            sheet_names = list(processed_data.keys())
            if sheet_names:
                sheet_tabs = st.tabs(sheet_names)
                for tab, (sheet_name, data) in zip(sheet_tabs, processed_data.items()):
                    with tab:
                        st.subheader(f"'{sheet_name}' 시트 데이터")
                        df = pd.DataFrame(data)
                        st.dataframe(df, use_container_width=True)
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("행 수", len(df))
                        col2.metric("기준일", base_date.strftime('%Y-%m-%d'))
                        col3.metric("계산방법", calc_method)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.divider()
            st.markdown("<br>", unsafe_allow_html=True)

            # --- 2. 검증 및 분석 섹션 (하단) ---
            tab_rule, tab_calc, tab_ai = st.tabs([
                "🔍 규칙 기반 검증", 
                "🧮 추계액 검증", 
                "🤖 AI 심층 분석"
            ])

            # --- 2-1. 규칙 기반 검증 탭 ---
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
                                sheet_results = v_results.get(sheet_name, {})
                                
                                if not sheet_results:
                                    st.success("✅ 오류 0건 - 이상 없음")
                                else:
                                    total_errors = sum(len(items) for items in sheet_results.values())
                                    st.error(f"⚠️ 총 {total_errors}건의 이슈 발견")
                                    
                                    # 오류 종류별로 표시
                                    for category, items in sheet_results.items():
                                        with st.expander(f"🔸 {category} ({len(items)}건)", expanded=True):
                                            # 데이터프레임 형태로 표시 (스크롤 가능하도록 height 설정)
                                            err_df = pd.DataFrame(items)
                                            err_df.columns = ["사원번호", "상세내용"]
                                            st.dataframe(err_df, use_container_width=True, height=300, hide_index=True)
                                
                                # 하단 여백 충분히 추가
                                st.markdown("<br>" * 30, unsafe_allow_html=True)
                    else:
                        st.info("검증 가능한 시트가 없습니다.")
                        st.markdown("<br>" * 30, unsafe_allow_html=True)
                else:
                    # 초기 상태에서도 여백 확보
                    st.markdown("<br>" * 30, unsafe_allow_html=True)

            # --- 2-2. 추계액 검증 탭 (재직자 전용) ---
            with tab_calc:
                st.header("🧮 재직자 추계액 계산 검증")
                
                # 재직자 명부 시트 찾기
                active_sheets = [name for name in processed_data.keys() if "재직자" in name and "기타장기" not in name]
                
                if not active_sheets:
                    st.info("추계액 검증을 위한 '재직자명부' 시트가 없습니다.")
                else:
                    # 첫 번째 재직자 명부를 자동으로 선택
                    selected_active_sheet = active_sheets[0]
                    
                    if st.button("📊 추계액 시뮬레이션 실행", type="primary"):
                        from validatorcalculate import EstimateValidator
                        
                        active_data = processed_data[selected_active_sheet]
                        df_active = pd.DataFrame(active_data)
                        
                        # 검증기 초기화 및 실행
                        calc_validator = EstimateValidator(df_active, base_date, calc_method)
                        result_df = calc_validator.validate_calculation()
                        
                        # 사원번호를 정수형으로 변환 (사용자 요청사항)
                        if '사원번호' in result_df.columns:
                            result_df['사원번호'] = pd.to_numeric(result_df['사원번호'], errors='coerce').fillna(0).astype(int)
                        
                        summary = calc_validator.get_summary(result_df)
                        
                        # 결과 요약 표시
                        st.subheader(f"'{selected_active_sheet}' 계산 검토 결과")
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("전체 대상", f"{summary['total_count']}명")
                        col2.metric("불일치 의심", f"{summary['error_count']}명", delta_color="inverse")
                        col3.metric("일치율", f"{summary['match_rate']:.1f}%")

                        # 오차율별 상세 내역 표시 (이미지 요청사항 반영)
                        st.divider()
                        
                        # 데이터 준비
                        col_original = calc_validator._find_column('당년도')
                        col_salary = calc_validator._find_column('기준급여')
                        col_emp_id = calc_validator._find_column('사원번호')

                        # 오차율 5% ~ 10% 미만
                        df_mid_error = result_df[(result_df['오차율'] >= 5) & (result_df['오차율'] < 10)].copy()
                        
                        st.markdown(f"#### 🟡 오차율 5% ~ 10% 미만 ({len(df_mid_error)}건)")
                        
                        display_df_mid = pd.DataFrame(columns=['사원번호', '계산액', '고객사액', '오차율'])
                        if not df_mid_error.empty:
                            display_df_mid['사원번호'] = df_mid_error['사원번호']
                            display_df_mid['계산액'] = df_mid_error['시스템_추계액'].map('{:,.0f}원'.format)
                            display_df_mid['고객사액'] = df_mid_error['고객사_추계액'].map('{:,.0f}원'.format)
                            display_df_mid['오차율'] = df_mid_error['오차율'].map('{:.2f}%'.format)
                        
                        st.dataframe(display_df_mid, use_container_width=True, height=250, hide_index=True)

                        # 오차율 10% 이상 필터링
                        df_high_error = result_df[result_df['오차율'] >= 10].copy()
                        
                        st.markdown(f"#### 🔴 오차율 10% 이상 ({len(df_high_error)}건)")
                        
                        # 표시용 데이터프레임 가공
                        display_df = pd.DataFrame(columns=['사원번호', '계산액', '고객사액', '오차율'])
                        if not df_high_error.empty:
                            display_df['사원번호'] = df_high_error['사원번호']
                            display_df['계산액'] = df_high_error['시스템_추계액'].map('{:,.0f}원'.format)
                            display_df['고객사액'] = df_high_error['고객사_추계액'].map('{:,.0f}원'.format)
                            display_df['오차율'] = df_high_error['오차율'].map('{:.2f}%'.format)
                        
                        # 데이터가 없어도 칸은 보여줌
                        st.dataframe(display_df, use_container_width=True, height=250, hide_index=True)

                        # --- 오차율 TOP 5 추가 ---
                        st.markdown("#### 🏆 오차율 TOP 5 (가장 높은 5명)")
                        df_top5 = result_df.sort_values(by='오차율', ascending=False).head(5).copy()
                        
                        display_df_top5 = pd.DataFrame(columns=['사원번호', '계산액', '고객사액', '오차율'])
                        if not df_top5.empty:
                            display_df_top5['사원번호'] = df_top5['사원번호']
                            display_df_top5['계산액'] = df_top5['시스템_추계액'].map('{:,.0f}원'.format)
                            display_df_top5['고객사액'] = df_top5['고객사_추계액'].map('{:,.0f}원'.format)
                            display_df_top5['오차율'] = df_top5['오차율'].map('{:.2f}%'.format)
                        
                        st.dataframe(display_df_top5, use_container_width=True, hide_index=True)
                        # -----------------------

                        # 전체 결과 데이터프레임 (접기 가능)
                        with st.expander("전체 검증 데이터 상세 보기"):
                            # 가독성을 위해 컬럼 순서 조정
                            final_cols = ['사원번호', '시스템_추계액', '고객사_추계액', '오차율', '시스템_근속연수', '기준급여', '적용배수', '휴직차감']
                            st.dataframe(result_df[final_cols], use_container_width=True, hide_index=True)
                        
                        st.success("시뮬레이션이 완료되었습니다. 제공해주실 알고리즘에 따라 '시스템_추계액'이 계산될 예정입니다.")

                # 하단 여백 충분히 추가
                st.markdown("<br>" * 30, unsafe_allow_html=True)

            # --- 2-3. AI 심층 분석 탭 ---
            with tab_ai:
                st.header("AI 심층 분석 (K-IFRS 1019)")
                if not openai_api_key:
                    st.info("AI 분석을 사용하려면 왼쪽 사이드바에 OpenAI API Key를 입력해 주세요.")
                else:
                    if st.button("🧠 AI 종합 분석 시작", type="secondary", key="btn_ai"):
                        with st.spinner("AI가 정제 데이터와 규칙 검증 결과를 통합 분석 중입니다..."):
                            # 규칙 기반 검증이 수행되지 않았다면 여기서 수행
                            if 'validation_results' not in st.session_state:
                                from validator import DataValidator
                                validator = DataValidator(processed_data, base_date, calc_method)
                                st.session_state['validation_results'] = validator.validate()
                            
                            analyzer = AIAnalyzer(openai_api_key)
                            ai_result = analyzer.analyze(
                                processed_data, 
                                st.session_state['validation_results'], 
                                base_date, 
                                calc_method
                            )
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
                
                # 하단 여백 충분히 추가
                st.markdown("<br>" * 30, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"오류 발생: {e}")
            st.exception(e) # 개발 중 상세 오류 확인용
    else:
        st.info("왼쪽 사이드바에서 엑셀 파일을 업로드해 주세요.")

if __name__ == "__main__":
    main()
