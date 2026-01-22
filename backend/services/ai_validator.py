import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AIValidator:
    """
    K-IFRS 1019 기준 AI 맥락 검증 클래스
    데이터 간의 논리적 개연성 및 통계적 이상치를 탐지합니다.
    """
    
    def __init__(self):
        pass

    def validate_context(self, all_sheets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        2차 검증: K-IFRS 1019 기준 AI 맥락 검증 실행
        """
        result = {
            "total_records": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "errors": [],
            "warnings": []
        }
        
        for sheet_name, df in all_sheets.items():
            sheet_name_lower = sheet_name.lower().replace(" ", "")
            
            # 재직자 명부 맥락 검증
            if "재직자" in sheet_name_lower:
                self._ai_validate_active_employees(sheet_name, df, result)
            
            # 퇴직자 명부 맥락 검증
            elif "퇴직자" in sheet_name_lower or "dc전환" in sheet_name_lower:
                self._ai_validate_retired_employees(sheet_name, df, result)

        return result

    def _ai_validate_active_employees(self, sheet_name: str, df: pd.DataFrame, result: Dict):
        """
        재직자 명부의 맥락적 이상치 검증 (K-IFRS 1019 기준)
        """
        today = datetime.now()
        
        for idx, row in df.iterrows():
            emp_id = str(row.get('emp_id', ''))
            if not self._is_valid_emp_id(emp_id):
                continue

            # 1. 급여 vs 추계액 논리성 체크
            # K-IFRS 1019: 확정급여채무는 근무용역의 대가로 미래에 지급될 금액의 현재가치
            base_salary = row.get('base_salary')
            hire_date = self._parse_date(row.get('hire_date'))
            current_severance = row.get('current_year_severance')
            multiplier = row.get('applicable_multiplier', 1.0)
            
            if pd.isnull(multiplier) or multiplier == 0:
                multiplier = 1.0

            if pd.notnull(base_salary) and hire_date and pd.notnull(current_severance):
                # 근속연수 계산
                service_years = (today - hire_date).days / 365.25
                
                if service_years > 1:
                    # 대략적인 추계액 범위 계산 (상식적인 수준)
                    expected_min = base_salary * (service_years - 1) * multiplier * 0.7
                    expected_max = base_salary * (service_years + 1) * multiplier * 1.3
                    
                    if current_severance < expected_min or current_severance > expected_max:
                        result["warnings"].append({
                            "sheet": sheet_name,
                            "row": idx + 2,
                            "column": "current_year_severance",
                            "emp_id": emp_id,
                            "type": "ai_context_anomaly",
                            "message": f"K-IFRS 1019: 급여({base_salary:,.0f}) 및 근속({service_years:.1f}년) 대비 추계액({current_severance:,.0f})이 맥락상 이상치로 의심됩니다.",
                            "severity": "warning"
                        })

            # 2. 연령 대비 근속연수 이상치
            birth_date = self._parse_date(row.get('birth_date'))
            if birth_date and hire_date:
                age = (today - birth_date).days / 365.25
                service_years = (today - hire_date).days / 365.25
                
                if age - service_years < 15:
                    result["warnings"].append({
                        "sheet": sheet_name,
                        "row": idx + 2,
                        "column": "hire_date",
                        "emp_id": emp_id,
                        "type": "ai_context_anomaly",
                        "message": f"맥락상 이상치: 연령({age:.1f}세) 대비 근속연수({service_years:.1f}년)가 비정상적으로 깁니다.",
                        "severity": "warning"
                    })

    def _ai_validate_retired_employees(self, sheet_name: str, df: pd.DataFrame, result: Dict):
        """
        퇴직자/DC전환자 명부의 맥락적 이상치 검증
        """
        for idx, row in df.iterrows():
            emp_id = str(row.get('emp_id', ''))
            if not self._is_valid_emp_id(emp_id):
                continue
                
            amount = row.get('retirement_or_dc_amount')
            if pd.notnull(amount) and amount > 0:
                if amount < 100000: # 10만원 미만
                    result["warnings"].append({
                        "sheet": sheet_name,
                        "row": idx + 2,
                        "column": "retirement_or_dc_amount",
                        "emp_id": emp_id,
                        "type": "ai_context_anomaly",
                        "message": f"퇴직/전환 금액({amount:,.0f})이 일반적인 수준보다 너무 적습니다. 데이터 누락인지 확인 필요.",
                        "severity": "warning"
                    })

    # 헬퍼 메서드 (중복 방지를 위해 내부 정의)
    def _is_valid_emp_id(self, emp_id: Any) -> bool:
        if pd.isnull(emp_id):
            return False
        emp_id_str = str(emp_id).strip()
        return emp_id_str not in ['', 'nan', 'None', 'NaN']

    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        if pd.isnull(date_str):
            return None
        try:
            date_str = str(date_str).strip()
            if date_str in ['', 'nan', 'None']:
                return None
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return None


