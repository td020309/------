import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

class EstimateValidator:
    """
    재직자 추계액 계산을 시뮬레이션하고 원본 데이터와 비교 검증하는 클래스
    """
    def __init__(self, df, base_date, calculation_method, progressive_multipliers=None):
        self.df = df.copy()
        self.base_date = pd.to_datetime(base_date)
        self.calculation_method = calculation_method # '일할', '월상' (월할절상), '월사' (월할절사)
        self.progressive_multipliers = progressive_multipliers

    def _get_progressive_multiplier(self, service_years):
        """근속연수에 따른 누진 배수 산출"""
        if self.progressive_multipliers is None or self.progressive_multipliers.empty:
            return 1.0
        
        # 근속연수_이상 컬럼 기준 내림차순 정렬하여 가장 큰 구간을 먼저 찾음
        sorted_table = self.progressive_multipliers.sort_values(by="근속연수_이상", ascending=False)
        for _, row in sorted_table.iterrows():
            if service_years >= row["근속연수_이상"]:
                return float(row["지급배수"])
        
        return 1.0

    def _find_column(self, keyword):
        """키워드 기반 컬럼 찾기"""
        for col in self.df.columns:
            if keyword in str(col):
                return col
        return None

    def _parse_date(self, val):
        if pd.isna(val) or val is None:
            return None
        try:
            s_val = str(val).strip().replace(".0", "")
            if len(s_val) == 8:
                return datetime.strptime(s_val, "%Y%m%d")
            return pd.to_datetime(val)
        except:
            return None

    def validate_calculation(self):
        """
        제공된 추계액 계산 알고리즘 반영
        """
        # 1. 컬럼 매칭
        col_emp_id = self._find_column('사원번호')
        col_join_date = self._find_column('입사일자')
        col_interim_date = self._find_column('중간정산기준일')
        col_salary = self._find_column('기준급여')
        col_multiplier = self._find_column('적용배수')
        col_leave_days = self._find_column('휴직기간등차감') # 일수 기준 가정
        col_leave_years = self._find_column('휴직기간/연') # 연 기준 가정
        col_original_estimate = self._find_column('당년도')

        result_rows = []

        for idx, row in self.df.iterrows():
            # 기본값 설정
            base_salary = pd.to_numeric(row.get(col_salary), errors='coerce') or 0
            
            # 시작일 결정 (중간정산기준일이 있으면 그것을 우선, 없으면 입사일)
            start_date_raw = row.get(col_interim_date) if not pd.isna(row.get(col_interim_date)) else row.get(col_join_date)
            start_date = self._parse_date(start_date_raw)
            end_date = self.base_date

            # 1. 근속연수(service_years) 계산
            service_years = 0.0
            if start_date and end_date and start_date <= end_date:
                if self.calculation_method == '일할':
                    service_years = ((end_date - start_date).days + 1) / 365.0
                elif self.calculation_method == '월상': # 월할절상
                    delta = relativedelta(end_date, start_date)
                    months = delta.years * 12 + delta.months + (1 if delta.days > 0 else 0)
                    service_years = months / 12.0
                elif self.calculation_method == '월사': # 월할절사
                    delta = relativedelta(end_date, start_date)
                    months = delta.years * 12 + delta.months
                    service_years = months / 12.0
                else: # 기본 일할
                    service_years = ((end_date - start_date).days + 1) / 365.0
            
            # 2. 배수 설정
            # 엑셀 내 '적용배수' 추출 및 정규화
            excel_multiplier = pd.to_numeric(row.get(col_multiplier), errors='coerce')
            if pd.isna(excel_multiplier) or excel_multiplier == 0:
                excel_multiplier = 1.0
            elif excel_multiplier >= 10: # 예: 100, 120 등 퍼센트 단위 처리
                excel_multiplier = excel_multiplier / 100.0

            if self.progressive_multipliers is not None:
                # 누진제인 경우: 엑셀 배수가 1.0이 아니면(임원 등) 엑셀 배수 우선 적용
                if excel_multiplier != 1.0:
                    multiplier = excel_multiplier
                else:
                    # 일반 직원은 계산된 근속연수에 따라 테이블에서 배수 결정
                    multiplier = self._get_progressive_multiplier(service_years)
            else:
                # 단일제: 엑셀 내 '적용배수' 그대로 사용
                multiplier = excel_multiplier

            # 3. 휴직차감(leave_deduction_years)
            leave_deduction_years = 0.0
            # 연 단위 우선 확인
            l_years = pd.to_numeric(row.get(col_leave_years), errors='coerce')
            if not pd.isna(l_years) and l_years > 0:
                leave_deduction_years = l_years
            else:
                # 일 단위 확인
                l_days = pd.to_numeric(row.get(col_leave_days), errors='coerce')
                if not pd.isna(l_days) and l_days > 0:
                    leave_deduction_years = l_days / 365.0

            # 4. 최종 지급률 및 추계액
            final_rate = max(0.0, service_years - leave_deduction_years)
            system_estimate = base_salary * final_rate * multiplier
            
            # 5. 오차율 계산
            original_estimate = pd.to_numeric(row.get(col_original_estimate), errors='coerce') or 0
            error_rate = 0.0
            if original_estimate != 0:
                error_rate = (abs(system_estimate - original_estimate) / abs(original_estimate)) * 100

            result_rows.append({
                '사원번호': row.get(col_emp_id),
                '시스템_근속연수': round(service_years, 4),
                '시스템_추계액': round(system_estimate, 0),
                '고객사_추계액': original_estimate,
                '오차율': round(error_rate, 2),
                '기준급여': base_salary,
                '적용배수': multiplier,
                '휴직차감': round(leave_deduction_years, 4)
            })

        return pd.DataFrame(result_rows)

    def get_summary(self, result_df):
        """
        검증 결과 요약 정보 생성
        """
        total_count = len(result_df)
        # 오차율 5% 이상인 경우를 오류로 간주
        error_count = (result_df['오차율'] >= 5).sum()
        
        summary = {
            "total_count": total_count,
            "error_count": error_count,
            "match_rate": ((total_count - error_count) / total_count * 100) if total_count > 0 else 0
        }
        return summary

