import streamlit as st
import pandas as pd
from processor import ExcelProcessor
from ai_analyzer import AIAnalyzer
from exporter import ExcelExporter

def main():
    st.set_page_config(page_title="엑셀 명부 검증 프로그램", layout="wide")
    st.title("📊 엑셀 명부 검증 프로그램")
    
    # --- 사이드바: 사용법 ---
    with st.sidebar:
        st.header("📖 사용법")
        st.markdown("""
        1. **파일 업로드**: '엑셀 파일 업로드' 영역에 검증할 파일을 올립니다.
        2. **검증 설정**: 기준일과 퇴직금 계산 방식(월상/월사/일할)을 확인합니다.
        3. **데이터 확인**: 업로드된 시트별 데이터를 확인합니다.
        4. **검증 실행**: 하단의 탭을 클릭하여 각 검증을 진행합니다.
           - **규칙 기반**: 주민번호, 날짜 형식 등 데이터 정합성 체크
           - **추계액 검증**: 퇴직금 추계액 계산식 검증
           - **AI 심층 분석**: AI를 통한 종합 분석 (API 키 필요)
        
        ---
        *문의: 시스템 관리자*
        """)
    
    # --- 상단: 입력 섹션 ---
    st.header("📥 입력 정보 및 설정")
    uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요", type=["xlsx", "xls"])
    
    # 새로운 파일이 업로드되면 세션 상태 초기화
    if uploaded_file is not None:
        if 'last_uploaded_file' not in st.session_state or st.session_state['last_uploaded_file'] != uploaded_file.name:
            st.session_state['last_uploaded_file'] = uploaded_file.name
            st.session_state['validation_done'] = False
            st.session_state['calc_done'] = False
            st.session_state['ai_analysis_done'] = False
            if 'validation_results' in st.session_state: del st.session_state['validation_results']
            if 'calc_results_df' in st.session_state: del st.session_state['calc_results_df']
            if 'ai_analysis_result' in st.session_state: del st.session_state['ai_analysis_result']
            if 'calc_summary' in st.session_state: del st.session_state['calc_summary']

    if uploaded_file is not None:
        # 레이아웃 개선: 2행 2열 구조로 변경
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)
        
        with row1_col1:
            st.markdown("#### 📌 검증 기준일")
            default_date = pd.Timestamp.now().strftime("%Y%m%d")
            base_date_input = st.text_input(
                "날짜 입력 (8자리 숫자)", 
                value=default_date,
                label_visibility="collapsed" # 레이블 중복 방지
            )
            try:
                if len(base_date_input) == 8:
                    base_date = pd.to_datetime(base_date_input, format='%Y%m%d').date()
                else:
                    base_date = pd.to_datetime(base_date_input).date()
                st.caption(f"📅 인식된 날짜: {base_date.strftime('%Y-%m-%d')}")
            except:
                st.error("⚠️ 날짜 형식이 잘못되었습니다.")
                return

        with row1_col2:
            st.markdown("#### 🔢 계산 방식")
            calc_method = st.selectbox(
                "계산 방법 선택",
                options=["월상", "월사", "일할"],
                index=2, # 기본 '일할'
                label_visibility="collapsed"
            )
            
        with row2_col1:
            st.markdown("#### ⚖️ 제도 선택")
            benefit_system = st.radio(
                "퇴직금 제도",
                options=["단일제", "누진제"],
                horizontal=True,
                label_visibility="collapsed"
            )

        with row2_col2:
            st.markdown("#### 🤖 AI 설정")
            openai_api_key = st.text_input(
                "OpenAI API Key", 
                type="password", 
                placeholder="sk-...",
                label_visibility="collapsed"
            )

        # --- 누진제 설정 표 (콤팩트한 레이아웃) ---
        multiplier_table = None
        if benefit_system == "누진제":
            st.divider()
            prog_col1, prog_col2 = st.columns([1.2, 1])
            
            with prog_col1:
                st.markdown("#### 📈 누진제 배수 설정")
                default_multipliers = pd.DataFrame([
                    {"근속연수_이상": 0, "지급배수": 1.0},
                    {"근속연수_이상": 5, "지급배수": 1.2},
                    {"근속연수_이상": 10, "지급배수": 1.5},
                ])
                
                multiplier_table = st.data_editor(
                    default_multipliers,
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "근속연수_이상": st.column_config.NumberColumn("근속연수 이상", min_value=0, step=1, format="%d년"),
                        "지급배수": st.column_config.NumberColumn("배수", min_value=1.0, step=0.1, format="%.2f배")
                    },
                    key="progressive_editor"
                )

            with prog_col2:
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.info("""
                **💡 입력 가이드**
                - 구간별 시작 근속연수와 배수를 입력하세요.
                - 표 하단의 빈 공간을 눌러 행을 추가할 수 있습니다.
                - 행 왼쪽의 아이콘으로 삭제가 가능합니다.
                """)

        st.divider()

        processor = ExcelProcessor(uploaded_file)
        
        try:
            # 시트별 정제된 데이터 가져오기
            processed_data = processor.process()
            
            if not processed_data:
                st.warning("매칭된 시트가 없습니다. 시트 이름을 확인해 주세요 (예: '직원명부', '급여대장')")
                return

            # --- 1. 원본 데이터 섹션 (상단 이동) ---
            st.header("📋 원본 데이터 확인")
            sheet_names = list(processed_data.keys())
            if sheet_names:
                sheet_tabs = st.tabs(sheet_names)
                for tab, (sheet_name, data) in zip(sheet_tabs, processed_data.items()):
                    with tab:
                        st.subheader(f"'{sheet_name}' 시트 데이터")
                        
                        # 기초자료 요약 시트인 경우 특별하게 표시
                        if "기초자료" in sheet_name and "퇴직급여" in sheet_name and len(data) > 0 and isinstance(data[0], dict) and data[0].get("구분") == "기초자료_요약":
                            summary = data[0]
                            
                            col_info1, col_info2 = st.columns(2)
                            with col_info1:
                                st.markdown("#### 📋 기본 설정 정보")
                                st.write(f"**• 검증기준일:** {summary.get('검증기준일', '-')}")
                                st.write(f"**• 정년퇴직연령:** {summary.get('정년퇴직연령', '-')}")
                                st.write(f"**• 임금피크제 여부:** {summary.get('임금피크제', '-')}")
                                st.write(f"**• 제도구분:** {summary.get('제도구분', '-')}")
                                st.write(f"**• 급여체계:** {summary.get('연봉제_호봉제', '-')}")
                                st.write(f"**• 할인율 산출기준:** {summary.get('할인율_산출기준', '-')}")
                            
                            with col_info2:
                                st.markdown("#### 📈 임금상승률 (Base-up)")
                                if summary.get('임금상승률'):
                                    growth_df = pd.DataFrame(summary['임금상승률'])
                                    # 인덱스 없이 깔끔하게 표시
                                    st.dataframe(growth_df, use_container_width=True, hide_index=True)
                                else:
                                    st.write("데이터 없음")
                            
                            st.divider()
                            st.markdown("#### 🔢 인원 및 추계액 요약")
                            col_m1, col_m2, col_m3 = st.columns(3)
                            
                            # 숫자 포맷팅 (None 체크 포함)
                            def fmt_num(val):
                                try: return f"{int(val):,}"
                                except: return "0"

                            col_m1.metric("재직자수 합계", f"{fmt_num(summary.get('재직자수_합계'))}명")
                            col_m2.metric("퇴직자수 합계", f"{fmt_num(summary.get('퇴직자수_합계'))}명")
                            col_m3.metric("퇴직금 추계액 합계", f"{fmt_num(summary.get('퇴직금_추계액_합계'))}원")
                            
                        else:
                            # 일반 명부 시트인 경우 기존처럼 표로 표시
                            df = pd.DataFrame(data)
                            st.dataframe(df, use_container_width=True)
                        
                        col1, col2, col3 = st.columns(3)
                        # 기초자료 요약인 경우 len(df) 대신 1이 나오므로 체크 필요
                        display_len = len(data) if isinstance(data, list) else 0
                        col1.metric("데이터 건수", display_len)
                        col2.metric("기준일", base_date.strftime('%Y-%m-%d'))
                        col3.metric("계산방법", calc_method)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.divider()
            st.markdown("<br>", unsafe_allow_html=True)

            # --- 2. 검증 및 분석 섹션 (하단) ---
            st.header("🔍 검증 및 분석")
            
            # 통합 검증 버튼을 상단에 배치
            col_btn1, col_btn2 = st.columns([1, 2])
            with col_btn1:
                if st.button("🚀 통합 검증 시작 (규칙 + 추계액)", type="primary", use_container_width=True):
                    with st.spinner("데이터 정합성 및 추계액 검증을 동시 진행 중..."):
                        # 1. 규칙 기반 검증
                        from validator import DataValidator
                        validator = DataValidator(processed_data, base_date, calc_method)
                        st.session_state['validation_results'] = validator.validate()
                        st.session_state['validation_done'] = True
                        
                        # 2. 추계액 검증
                        active_sheets = [name for name in processed_data.keys() if "재직자" in name and "기타장기" not in name]
                        if active_sheets:
                            from validatorcalculate import EstimateValidator
                            selected_active_sheet = active_sheets[0]
                            active_data = processed_data[selected_active_sheet]
                            df_active = pd.DataFrame(active_data)
                            
                            prog_table = multiplier_table if benefit_system == "누진제" else None
                            calc_validator = EstimateValidator(df_active, base_date, calc_method, progressive_multipliers=prog_table)
                            result_df = calc_validator.validate_calculation()
                            
                            if '사원번호' in result_df.columns:
                                result_df['사원번호'] = pd.to_numeric(result_df['사원번호'], errors='coerce').fillna(0).astype(int)
                            
                            st.session_state['calc_results_df'] = result_df
                            st.session_state['calc_done'] = True
                            st.session_state['calc_summary'] = calc_validator.get_summary(result_df)
            
            # --- 결과 추출 (엑셀) 섹션 ---
            has_results = any([
                st.session_state.get('validation_done', False),
                st.session_state.get('calc_done', False),
                st.session_state.get('ai_analysis_done', False)
            ])
            
            if has_results:
                exporter = ExcelExporter()
                excel_data = exporter.export(
                    processed_data=processed_data, # 원본 데이터 추가
                    validation_results=st.session_state.get('validation_results'),
                    calc_results_df=st.session_state.get('calc_results_df'),
                    ai_result=st.session_state.get('ai_analysis_result'),
                    base_date=base_date.strftime('%Y-%m-%d')
                )
                
                st.download_button(
                    label="📥 검증 결과 엑셀 다운로드 (보고용)",
                    data=excel_data,
                    file_name=f"명부검증결과_{base_date.strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )
                st.markdown("<br>", unsafe_allow_html=True)

            tab_rule, tab_calc, tab_ai = st.tabs([
                "🔍 규칙 기반 검증", 
                "🧮 추계액 검증", 
                "🤖 AI 심층 분석"
            ])

            # --- 2-1. 규칙 기반 검증 탭 ---
            with tab_rule:
                st.header("데이터 검증 (Hard Rules)")
                
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
                    selected_active_sheet = active_sheets[0]
                    
                    if st.session_state.get('calc_done', False):
                        result_df = st.session_state['calc_results_df']
                        summary = st.session_state['calc_summary']
                        
                        # 결과 요약 표시
                        st.subheader(f"'{selected_active_sheet}' 계산 검토 결과")
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("전체 대상", f"{summary['total_count']}명")
                        col2.metric("불일치 의심", f"{summary['error_count']}명", delta_color="inverse")
                        col3.metric("일치율", f"{summary['match_rate']:.1f}%")

                        # 오차율별 상세 내역 표시 (이미지 요청사항 반영)
                        st.divider()
                        
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
                    st.info("AI 분석을 사용하려면 상단 설정에서 OpenAI API Key를 입력해 주세요.")
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
        st.info("상단에서 엑셀 파일을 업로드해 주세요.")

if __name__ == "__main__":
    main()
