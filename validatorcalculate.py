import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

class EstimateValidator:
    """
    재직자 추계액 계산을 시뮬레이션하고 원본 데이터와 비교 검증하는 클래스
    """
    def __init__(self, df, base_date, calculation_method):
        self.df = df.copy()
        self.base_date = pd.to_datetime(base_date)
        self.calculation_method = calculation_method # '일할', '월상' (월할절상), '월사' (월할절사)

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
            
            # 배수 설정 (없으면 1.0, 100 이상이면 퍼센트로 간주하여 100으로 나눔)
            raw_multiplier = pd.to_numeric(row.get(col_multiplier), errors='coerce')
            if pd.isna(raw_multiplier) or raw_multiplier == 0:
                multiplier = 1.0
            elif raw_multiplier >= 10: # 예: 100, 120 등
                multiplier = raw_multiplier / 100.0
            else:
                multiplier = raw_multiplier

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

            # 2. 휴직차감(leave_deduction_years)
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

            # 3. 최종 지급률 및 추계액
            final_rate = max(0.0, service_years - leave_deduction_years)
            system_estimate = base_salary * final_rate * multiplier
            
            # 4. 오차율 계산
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

