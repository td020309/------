import pandas as pd
import io
from datetime import datetime

class ExcelExporter:
    def __init__(self):
        self.header_format = None
        self.error_format = None
        self.warning_format = None
        self.normal_format = None

    def export(self, processed_data, validation_results, calc_results_df, ai_result, base_date):
        output = io.BytesIO()
        
        # NaN/Inf 처리를 위해 engine_kwargs 추가
        with pd.ExcelWriter(output, engine='xlsxwriter', engine_kwargs={'options': {'nan_inf_to_errors': True}}) as writer:
            workbook = writer.book
            
            # 포맷 정의 (더 세련된 색상 조합)
            self.header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#2F5597', # 진한 파랑
                'font_color': 'white',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'font_name': '맑은 고딕',
                'font_size': 10
            })
            self.title_format = workbook.add_format({
                'bold': True, 
                'font_size': 22, 
                'font_color': '#2F5597',
                'font_name': '맑은 고딕',
                'bottom': 2,
                'bottom_color': '#2F5597'
            })
            self.greeting_format = workbook.add_format({
                'font_size': 12,
                'font_color': '#44546A',
                'font_name': '맑은 고딕',
                'valign': 'vcenter'
            })
            self.error_format = workbook.add_format({
                'bg_color': '#FFC7CE',
                'font_color': '#9C0006',
                'border': 1,
                'font_name': '맑은 고딕',
                'align': 'center'
            })
            self.warning_format = workbook.add_format({
                'bg_color': '#FFEB9C',
                'font_color': '#9C6500',
                'border': 1,
                'font_name': '맑은 고딕',
                'align': 'center'
            })
            self.money_format = workbook.add_format({
                'num_format': '#,##0',
                'border': 1,
                'font_name': '맑은 고딕',
                'align': 'right'
            })
            self.percent_format = workbook.add_format({
                'num_format': '0.00%',
                'border': 1,
                'font_name': '맑은 고딕',
                'align': 'right'
            })
            self.center_format = workbook.add_format({
                'align': 'center',
                'border': 1,
                'font_name': '맑은 고딕'
            })
            self.border_format = workbook.add_format({
                'border': 1,
                'font_name': '맑은 고딕'
            })
            self.label_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D9E1F2', # 연한 파랑 (헤더와 매칭)
                'border': 1,
                'font_name': '맑은 고딕',
                'align': 'center'
            })
            self.summary_box_format = workbook.add_format({
                'border': 2,
                'border_color': '#2F5597',
                'bg_color': '#F8F9FA'
            })

            # 1. 요약 시트
            self._create_summary_sheet(writer, validation_results, calc_results_df, base_date)

            # 2. 각 시트별 검증 결과 시트 (원본 데이터 대신 검증 결과를 각 시트명으로 생성)
            self._create_per_sheet_validation_results(writer, validation_results)

            # 3. 추계액 검증 결과 (요청하신 오차율별 그룹화 리포트)
            self._create_calc_grouped_report_sheet(writer, calc_results_df)

            # 4. 추계액 검산 상세 (전체 리스트)
            self._create_calc_validation_sheet(writer, calc_results_df)

            # 5. AI 분석 리포트 시트
            self._create_ai_report_sheet(writer, ai_result)

        return output.getvalue()

    def _create_summary_sheet(self, writer, validation_results, calc_results_df, base_date):
        workbook = writer.book
        worksheet = workbook.add_worksheet('검증요약')
        writer.sheets['검증요약'] = worksheet

        # 컬럼 너비 설정
        worksheet.set_column('A:A', 3)  # 왼쪽 여백
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 35)
        worksheet.set_column('D:D', 15)

        # 제목 및 인사말
        worksheet.write('B2', '명부 검증 결과 보고서', self.title_format)
        
        greeting_text = [
            '안녕하세요. 위키소프트 계리법인입니다.',
            '명부 검증 결과를 확인해 주시기 바랍니다.',
            '본 보고서는 데이터 정합성 검증 및 퇴직금 추계액 시뮬레이션 결과를 포함하고 있습니다.'
        ]
        for i, text in enumerate(greeting_text):
            worksheet.write(3 + i, 1, text, self.greeting_format)
        
        # 보고서 정보 요약 박스
        worksheet.write('B8', '보고서 정보', self.header_format)
        worksheet.write('C8', '', self.header_format)
        
        worksheet.write('B9', '검증 기준일', self.label_format)
        worksheet.write('C9', base_date, self.border_format)
        worksheet.write('B10', '보고서 생성일', self.label_format)
        worksheet.write('C10', datetime.now().strftime("%Y-%m-%d %H:%M"), self.border_format)

        # 1. 데이터 정합성 검증 요약
        row = 12
        worksheet.write(row, 1, '1. 데이터 정합성 검증 요약', self.header_format)
        worksheet.write(row, 2, '대상 시트', self.header_format)
        worksheet.write(row, 3, '이슈 건수', self.header_format)
        
        row += 1
        total_rule_errors = 0
        if validation_results:
            start_row = row
            for sheet_name, categories in validation_results.items():
                sheet_errors = sum(len(items) for items in categories.values())
                worksheet.write(row, 1, '정합성 체크', self.label_format)
                worksheet.write(row, 2, sheet_name, self.border_format)
                worksheet.write(row, 3, f"{sheet_errors}건", self.error_format if sheet_errors > 0 else self.center_format)
                total_rule_errors += sheet_errors
                row += 1
            
            # 합계 행
            worksheet.write(row, 1, '총계', self.label_format)
            worksheet.write(row, 2, '-', self.center_format)
            worksheet.write(row, 3, f"{total_rule_errors}건", self.error_format if total_rule_errors > 0 else self.center_format)
        else:
            worksheet.write(row, 1, '검증 결과 없음', self.border_format)
            worksheet.merge_range(row, 1, row, 3, '수행된 규칙 기반 검증 결과가 없습니다.', self.center_format)
            row += 1

        # 2. 추계액 검증 요약
        row += 2
        worksheet.write(row, 1, '2. 추계액 시뮬레이션 요약', self.header_format)
        worksheet.merge_range(row, 1, row, 3, '2. 추계액 시뮬레이션 요약', self.header_format)
        
        row += 1
        if calc_results_df is not None and not calc_results_df.empty:
            total_calc = len(calc_results_df)
            mismatch_calc = (calc_results_df['오차율'] >= 5).sum()
            match_rate = (total_calc - mismatch_calc) / total_calc * 100
            
            summary_items = [
                ('전체 대상 인원', f"{total_calc}명", self.border_format),
                ('불일치 의심 (5% 이상)', f"{mismatch_calc}명", self.error_format if mismatch_calc > 0 else self.border_format),
                ('계산 일치율', f"{match_rate:.2f}%", self.border_format)
            ]
            
            for label, value, val_fmt in summary_items:
                worksheet.write(row, 1, label, self.label_format)
                worksheet.merge_range(row, 2, row, 3, value, val_fmt)
                row += 1
        else:
            worksheet.merge_range(row, 1, row, 3, '수행된 추계액 검증 결과가 없습니다.', self.center_format)
            row += 1

        # 안내 문구
        row += 2
        worksheet.write(row, 1, '* 상세 내용은 각 시트를 참조해 주시기 바랍니다.', self.greeting_format)

    def _create_per_sheet_validation_results(self, writer, validation_results):
        if not validation_results:
            return

        workbook = writer.book
        
        # 카테고리 헤더 포맷
        category_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E1F2',
            'border': 1,
            'font_name': '맑은 고딕',
            'font_size': 11
        })

        for sheet_name, categories in validation_results.items():
            # 시트 이름 제한 (31자) 및 특수문자 제거
            safe_name = "".join([c for c in sheet_name if c.isalnum() or c in ' '])[:31]
            worksheet = workbook.add_worksheet(safe_name)
            writer.sheets[safe_name] = worksheet
            
            worksheet.set_column('A:A', 2)  # 왼쪽 여백
            worksheet.set_column('B:B', 15) # 사원번호
            worksheet.set_column('C:C', 80) # 상세내용
            
            # 시트 제목
            worksheet.write('B1', f"[{sheet_name}] 검증 상세 내역", self.title_format)
            
            row = 2
            if not categories:
                worksheet.write(row, 1, "✅ 발견된 이슈가 없습니다.", self.greeting_format)
                continue

            for category, items in categories.items():
                # 카테고리 제목 행
                row += 1
                worksheet.merge_range(row, 1, row, 2, f"🔸 {category} ({len(items)}건)", category_format)
                row += 1
                
                # 헤더
                worksheet.write(row, 1, '사원번호', self.header_format)
                worksheet.write(row, 2, '상세내용', self.header_format)
                row += 1
                
                # 데이터
                for item in items:
                    emp_id = item.get('emp_id', '-')
                    detail = item.get('detail', '')
                    
                    # '전체' 등으로 표시된 불필요한 사번 정보 정제
                    if emp_id == '전체': emp_id = '-'
                    
                    # NaN 처리
                    if pd.isna(emp_id): emp_id = '-'
                    if pd.isna(detail): detail = '-'
                    
                    worksheet.write(row, 1, emp_id, self.center_format)
                    worksheet.write(row, 2, detail, self.border_format)
                    row += 1
                row += 1 # 카테고리 간 간격

    def _create_calc_grouped_report_sheet(self, writer, calc_results_df):
        if calc_results_df is None or calc_results_df.empty:
            return

        workbook = writer.book
        sheet_name = '추계액검증결과'
        worksheet = workbook.add_worksheet(sheet_name)
        writer.sheets[sheet_name] = worksheet

        # 스타일
        group_header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E1F2',
            'border': 1,
            'font_name': '맑은 고딕',
            'font_size': 11
        })
        
        worksheet.set_column('A:A', 2)
        worksheet.set_column('B:E', 18)
        
        worksheet.write('B1', "추계액 시뮬레이션 요약 보고", self.title_format)
        
        row = 3
        
        # 1. 오차율 TOP 5
        worksheet.merge_range(row, 1, row, 4, "🏆 오차율 TOP 5 (가장 높은 5명)", group_header_format)
        row += 1
        headers = ['사원번호', '시스템_추계액', '고객사_추계액', '오차율(%)']
        for i, h in enumerate(headers):
            worksheet.write(row, i + 1, h, self.header_format)
        row += 1
        
        df_top5 = calc_results_df.sort_values(by='오차율', ascending=False).head(5)
        for _, r_data in df_top5.iterrows():
            worksheet.write(row, 1, r_data['사원번호'], self.center_format)
            worksheet.write(row, 2, r_data['시스템_추계액'], self.money_format)
            worksheet.write(row, 3, r_data['고객사_추계액'], self.money_format)
            worksheet.write(row, 4, r_data['오차율'], self.error_format)
            row += 1
        
        row += 2 # 공백
        
        # 2. 오차율 10% 이상
        df_high = calc_results_df[calc_results_df['오차율'] >= 10]
        worksheet.merge_range(row, 1, row, 4, f"🔴 오차율 10% 이상 ({len(df_high)}건)", group_header_format)
        row += 1
        for i, h in enumerate(headers):
            worksheet.write(row, i + 1, h, self.header_format)
        row += 1
        for _, r_data in df_high.iterrows():
            worksheet.write(row, 1, r_data['사원번호'], self.center_format)
            worksheet.write(row, 2, r_data['시스템_추계액'], self.money_format)
            worksheet.write(row, 3, r_data['고객사_추계액'], self.money_format)
            worksheet.write(row, 4, r_data['오차율'], self.error_format)
            row += 1

        row += 2 # 공백

        # 3. 오차율 5% ~ 10% 미만
        df_mid = calc_results_df[(calc_results_df['오차율'] >= 5) & (calc_results_df['오차율'] < 10)]
        worksheet.merge_range(row, 1, row, 4, f"🟡 오차율 5% ~ 10% 미만 ({len(df_mid)}건)", group_header_format)
        row += 1
        for i, h in enumerate(headers):
            worksheet.write(row, i + 1, h, self.header_format)
        row += 1
        for _, r_data in df_mid.iterrows():
            worksheet.write(row, 1, r_data['사원번호'], self.center_format)
            worksheet.write(row, 2, r_data['시스템_추계액'], self.money_format)
            worksheet.write(row, 3, r_data['고객사_추계액'], self.money_format)
            worksheet.write(row, 4, r_data['오차율'], self.warning_format)
            row += 1

    def _create_calc_validation_sheet(self, writer, calc_results_df):
        if calc_results_df is None or calc_results_df.empty:
            return

        sheet_name = '추계액검산상세'
        export_df = calc_results_df.copy()
        column_map = {
            '사원번호': '사원번호',
            '시스템_근속연수': '시스템_근속연수',
            '시스템_추계액': '시스템_추계액',
            '고객사_추계액': '고객사_추계액',
            '오차율': '오차율(%)',
            '기준급여': '기준급여',
            '적용배수': '적용배수',
            '휴직차감': '휴직차감(연)'
        }
        
        # 실제 존재하는 컬럼만 필터링
        existing_cols = [c for c in column_map.keys() if c in export_df.columns]
        export_df = export_df[existing_cols].rename(columns={k: column_map[k] for k in existing_cols})
        
        export_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, startcol=1)
        worksheet = writer.sheets[sheet_name]
        
        worksheet.set_column('A:A', 2) # 왼쪽 여백
        for col_num in range(len(export_df.columns)):
            worksheet.set_column(col_num + 1, col_num + 1, 18)
        
        for col_num, value in enumerate(export_df.columns.values):
            worksheet.write(1, col_num + 1, value, self.header_format)

        for i, row in export_df.iterrows():
            r = i + 2
            for c, col_name in enumerate(export_df.columns):
                val = row[col_name]
                
                # NaN 또는 Inf 처리
                if pd.isna(val) or val == float('inf') or val == float('-inf'):
                    worksheet.write(r, c + 1, '-', self.center_format)
                    continue

                fmt = self.border_format
                
                if '추계액' in col_name or '급여' in col_name:
                    fmt = self.money_format
                elif '오차율' in col_name:
                    try:
                        err_val = float(val)
                        if err_val >= 10: fmt = self.error_format
                        elif err_val >= 5: fmt = self.warning_format
                        else: fmt = self.center_format
                    except:
                        fmt = self.center_format
                elif col_name == '사원번호':
                    fmt = self.center_format
                
                worksheet.write(r, c + 1, val, fmt)

    def _create_ai_report_sheet(self, writer, ai_result):
        if not ai_result:
            return

        sheet_name = 'AI분석보고서'
        workbook = writer.book
        worksheet = workbook.add_worksheet(sheet_name)
        writer.sheets[sheet_name] = worksheet

        report_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'font_name': '맑은 고딕',
            'font_size': 10,
            'border': 1
        })
        
        worksheet.set_column('A:A', 2)
        worksheet.set_column('B:K', 12)
        
        worksheet.write('B1', 'AI 심층 분석 보고서 (K-IFRS 1019 기준)', self.header_format)
        worksheet.merge_range('B1:K1', 'AI 심층 분석 보고서 (K-IFRS 1019 기준)', self.header_format)
        worksheet.merge_range('B2:K60', ai_result, report_format)


