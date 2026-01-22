import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from .ai_validator import AIValidator
from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class DataValidator:
    """
    퇴직급여 명부 검증 클래스
    - 1차 검증: 하드코딩된 규칙 기반 검증
    - 2차 검증: AI 맥락 검증 (K-IFRS 기준)
    """
    
    def __init__(self):
        """
        검증 규칙을 초기화합니다.
        """
        self.ai_validator = AIValidator()
        self.report_generator = ReportGenerator()
    
    def validate(self, mapped_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        매핑된 데이터에 대해 전체 검증을 수행합니다.
        
        Args:
            mapped_data: 정형화된 시트 데이터
            
        Returns:
            Dict: 검증 결과
        """
        validation_results = {
            "total_records": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "errors": [],
            "warnings": [],
            "sheet_results": {},
            "phase1_results": {},  # 1차 검증 결과
            "phase2_results": {},  # 2차 검증 결과 (AI)
            "summary_report": []   # 요약 리포트 (추가됨)
        }
        
        try:
            # 1차 검증: 하드코딩된 규칙 기반
            phase1_result = self._validate_phase1_rules(mapped_data)
            validation_results["phase1_results"] = phase1_result
            
            # 2차 검증: AI 맥락 검증
            phase2_result = self._validate_phase2_ai_context(mapped_data)
            validation_results["phase2_results"] = phase2_result
            
            # 결과 병합
            for sheet_name in mapped_data.keys():
                if sheet_name in phase1_result["sheet_results"]:
                    sheet_result = phase1_result["sheet_results"][sheet_name]
                    validation_results["sheet_results"][sheet_name] = sheet_result
                    validation_results["total_records"] += sheet_result["total_records"]
                    validation_results["valid_records"] += sheet_result["valid_records"]
                    validation_results["invalid_records"] += sheet_result["invalid_records"]
            
            validation_results["errors"] = phase1_result["errors"] + phase2_result["errors"]
            validation_results["warnings"] = phase1_result["warnings"] + phase2_result["warnings"]
            
            # 요약 리포트 생성
            validation_results["summary_report"] = self.report_generator.generate_summary_report(validation_results)
            
        except Exception as e:
            logger.error(f"검증 중 오류 발생: {str(e)}")
            validation_results["errors"].append({
                "sheet": "전체",
                "type": "validation_error",
                "message": f"검증 중 오류 발생: {str(e)}",
                "severity": "error"
            })
        
        return validation_results
    
    # ========================================
    # 1차 검증: 하드코딩된 규칙 기반
    # ========================================
    
    def _validate_phase1_rules(self, all_sheets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        1차 검증: 정해진 규칙에 따른 하드코딩 검증
        
        Args:
            all_sheets: 모든 시트 데이터
            
        Returns:
            Dict: 검증 결과
        """
        result = {
            "total_records": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "errors": [],
            "warnings": [],
            "sheet_results": {}
        }
        
        # 1단계: 각 시트별 행별 독립 검증 + 시트 내 전체 검증
        for sheet_name, df in all_sheets.items():
            logger.info(f"시트 '{sheet_name}' 검증 시작")
            
            sheet_result = {
                "total_records": self._count_valid_records(df),
                "valid_records": 0,
                "invalid_records": 0,
                "errors": [],
                "warnings": []
            }
            
            # 시트 타입 판단
            sheet_name_lower = sheet_name.lower().replace(" ", "")
            
            # 재직자명부 검증
            if "재직자명부" in sheet_name_lower or "재직자" in sheet_name_lower:
                self._validate_active_employee_sheet(sheet_name, df, sheet_result)
            
            result["sheet_results"][sheet_name] = sheet_result
        
        # 2단계: 시트 간 교차 검증 (한 번만 실행)
        self._validate_cross_sheet(all_sheets, result)
        
        # 전체 통계 집계
        for sheet_result in result["sheet_results"].values():
            result["total_records"] += sheet_result["total_records"]
            result["valid_records"] += sheet_result["valid_records"]
            result["invalid_records"] += sheet_result["invalid_records"]
            result["errors"].extend(sheet_result["errors"])
            result["warnings"].extend(sheet_result["warnings"])
        
        return result
    
    # ========================================
    # 재직자명부 검증
    # ========================================
    
    def _validate_active_employee_sheet(self, sheet_name: str, df: pd.DataFrame, result: Dict):
        """
        재직자명부 행별 검증 및 시트 내 검증
        """
        valid_row_count = 0
        invalid_row_count = 0
        
        # 행별 검증
        for idx, row in df.iterrows():
            # 사원번호가 없는 행은 건너뛰기
            if not self._is_valid_emp_id(row.get('emp_id')):
                continue
            
            row_errors = []
            row_warnings = []
            
            # 필수 필드 검증
            row_errors.extend(self._check_required_fields(sheet_name, idx, row))
            
            # 수치 범위 검증
            row_errors.extend(self._check_numeric_ranges(sheet_name, idx, row))
            row_warnings.extend(self._check_numeric_warnings(sheet_name, idx, row))
            
            # 날짜 유효성 검증
            row_errors.extend(self._check_date_validity(sheet_name, idx, row))
            
            # 논리적 일관성 검증
            row_errors.extend(self._check_logical_consistency(sheet_name, idx, row))
            
            # 조건부 필드 검증
            row_errors.extend(self._check_conditional_fields(sheet_name, idx, row))
            
            # 결과 집계
            if row_errors:
                invalid_row_count += 1
                result["errors"].extend(row_errors)
            else:
                valid_row_count += 1
            
            if row_warnings:
                result["warnings"].extend(row_warnings)
        
        # 시트 내 중복 검증
        duplicate_errors = self._check_duplicates_in_sheet(sheet_name, df)
        result["errors"].extend(duplicate_errors)
        if duplicate_errors:
            invalid_row_count += len(duplicate_errors)
        
        result["valid_records"] = valid_row_count
        result["invalid_records"] = invalid_row_count
    
    # ========================================
    # 필수 필드 검증
    # ========================================
    
    def _check_required_fields(self, sheet_name: str, idx: int, row: pd.Series) -> List[Dict]:
        """
        필수 필드가 비어있는지 검증
        """
        errors = []
        required_fields = {
            "emp_id": "사원번호",
            "birth_date": "생년월일",
            "hire_date": "입사일자",
            "base_salary": "기준급여",
            "employee_type": "직종"
        }
        
        for field, field_name in required_fields.items():
            if field not in row.index or pd.isnull(row[field]) or str(row[field]).strip() == '':
                errors.append({
                    "sheet": sheet_name,
                    "row": idx + 2,  # 엑셀 행 번호 (헤더 포함)
                    "column": field,
                    "emp_id": str(row.get('emp_id', '')),
                    "type": "required_field_missing",
                    "message": f"필수 필드 '{field_name}'가 비어있습니다",
                    "severity": "error"
                })
        
        return errors
    
    # ========================================
    # 수치 범위 검증
    # ========================================
    
    def _check_numeric_ranges(self, sheet_name: str, idx: int, row: pd.Series) -> List[Dict]:
        """
        수치 범위 검증 (오류)
        """
        errors = []
        
        # 최저급여계약 < 0
        if 'min_salary_contract' in row.index and pd.notnull(row['min_salary_contract']):
            if row['min_salary_contract'] < 0:
                errors.append({
                    "sheet": sheet_name,
                    "row": idx + 2,
                    "column": "min_salary_contract",
                    "emp_id": str(row.get('emp_id', '')),
                    "type": "invalid_value",
                    "message": f"최저급여계약이 음수입니다: {row['min_salary_contract']}",
                    "severity": "error"
                })
        
        # 최저급여계약(전년도) < 0
        if 'prev_min_salary_contract' in row.index and pd.notnull(row['prev_min_salary_contract']):
            if row['prev_min_salary_contract'] < 0:
                errors.append({
                    "sheet": sheet_name,
                    "row": idx + 2,
                    "column": "prev_min_salary_contract",
                    "emp_id": str(row.get('emp_id', '')),
                    "type": "invalid_value",
                    "message": f"최저급여계약(전년도)이 음수입니다: {row['prev_min_salary_contract']}",
                    "severity": "error"
                })
        
        # 중간정산액 < 0
        if 'interim_settlement_amount' in row.index and pd.notnull(row['interim_settlement_amount']):
            if row['interim_settlement_amount'] < 0:
                errors.append({
                    "sheet": sheet_name,
                    "row": idx + 2,
                    "column": "interim_settlement_amount",
                    "emp_id": str(row.get('emp_id', '')),
                    "type": "invalid_value",
                    "message": f"중간정산액이 음수입니다: {row['interim_settlement_amount']}",
                    "severity": "error"
                })
        
        return errors
    
    def _check_numeric_warnings(self, sheet_name: str, idx: int, row: pd.Series) -> List[Dict]:
        """
        수치 범위 검증 (경고)
        """
        warnings = []
        
        # 기준급여 < 1,700,000
        if 'base_salary' in row.index and pd.notnull(row['base_salary']):
            if row['base_salary'] < 1700000:
                warnings.append({
                    "sheet": sheet_name,
                    "row": idx + 2,
                    "column": "base_salary",
                    "emp_id": str(row.get('emp_id', '')),
                    "type": "low_salary",
                    "message": f"기준급여가 최저임금보다 낮습니다: {row['base_salary']:,.0f}원 (확인 필요)",
                    "severity": "warning"
                })
        
        return warnings
    
    # ========================================
    # 날짜 유효성 검증
    # ========================================
    
    def _check_date_validity(self, sheet_name: str, idx: int, row: pd.Series) -> List[Dict]:
        """
        날짜 필드의 유효성 검증
        """
        errors = []
        
        # 생년월일 검증
        if 'birth_date' in row.index and pd.notnull(row['birth_date']):
            date_error = self._validate_date_format(row['birth_date'], '생년월일')
            if date_error:
                errors.append({
                    "sheet": sheet_name,
                    "row": idx + 2,
                    "column": "birth_date",
                    "emp_id": str(row.get('emp_id', '')),
                    "type": "invalid_date",
                    "message": date_error,
                    "severity": "error"
                })
        
        # 입사일 검증
        if 'hire_date' in row.index and pd.notnull(row['hire_date']):
            date_error = self._validate_date_format(row['hire_date'], '입사일')
            if date_error:
                errors.append({
                    "sheet": sheet_name,
                    "row": idx + 2,
                    "column": "hire_date",
                    "emp_id": str(row.get('emp_id', '')),
                    "type": "invalid_date",
                    "message": date_error,
                    "severity": "error"
                })
        
        # 중간정산일 검증
        if 'interim_settlement_date' in row.index and pd.notnull(row['interim_settlement_date']):
            date_error = self._validate_date_format(row['interim_settlement_date'], '중간정산일')
            if date_error:
                errors.append({
                    "sheet": sheet_name,
                    "row": idx + 2,
                    "column": "interim_settlement_date",
                    "emp_id": str(row.get('emp_id', '')),
                    "type": "invalid_date",
                    "message": date_error,
                    "severity": "error"
                })
        
        return errors
    
    def _validate_date_format(self, date_str: str, field_name: str) -> Optional[str]:
        """
        날짜 형식 검증 (YYYY-MM-DD)
        월>12, 일>31 체크
        """
        try:
            date_str = str(date_str).strip()
            if date_str in ['', 'nan', 'None']:
                return None
            
            # YYYY-MM-DD 형식 파싱
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            
            # 월, 일 범위 체크
            if date_obj.month > 12:
                return f"{field_name} 월이 12를 초과합니다: {date_str}"
            if date_obj.day > 31:
                return f"{field_name} 일이 31을 초과합니다: {date_str}"
            
            return None
        except ValueError:
            return f"{field_name} 형식이 올바르지 않습니다: {date_str} (YYYY-MM-DD 형식 필요)"
    
    # ========================================
    # 논리적 일관성 검증
    # ========================================
    
    def _check_logical_consistency(self, sheet_name: str, idx: int, row: pd.Series) -> List[Dict]:
        """
        날짜 간 논리적 일관성 검증
        """
        errors = []
        
        birth_date = self._parse_date(row.get('birth_date'))
        hire_date = self._parse_date(row.get('hire_date'))
        interim_date = self._parse_date(row.get('interim_settlement_date'))
        
        # 입사일 < 생년월일 체크
        if birth_date and hire_date:
            if hire_date < birth_date:
                errors.append({
                    "sheet": sheet_name,
                    "row": idx + 2,
                    "column": "hire_date",
                    "emp_id": str(row.get('emp_id', '')),
                    "type": "logical_error",
                    "message": f"입사일({hire_date.strftime('%Y-%m-%d')})이 생년월일({birth_date.strftime('%Y-%m-%d')})보다 빠릅니다",
                    "severity": "error"
                })
            
            # 입사연령 체크 (17세 미만 또는 70세 초과)
            age_at_hire = (hire_date - birth_date).days / 365.25
            if age_at_hire < 17:
                errors.append({
                    "sheet": sheet_name,
                    "row": idx + 2,
                    "column": "hire_date",
                    "emp_id": str(row.get('emp_id', '')),
                    "type": "invalid_age",
                    "message": f"입사연령이 17세 미만입니다: {age_at_hire:.1f}세",
                    "severity": "error"
                })
            elif age_at_hire > 70:
                errors.append({
                    "sheet": sheet_name,
                    "row": idx + 2,
                    "column": "hire_date",
                    "emp_id": str(row.get('emp_id', '')),
                    "type": "invalid_age",
                    "message": f"입사연령이 70세 초과입니다: {age_at_hire:.1f}세",
                    "severity": "error"
                })
        
        # 중간정산일 >= 입사일 체크
        if hire_date and interim_date:
            if interim_date < hire_date:
                errors.append({
                    "sheet": sheet_name,
                    "row": idx + 2,
                    "column": "interim_settlement_date",
                    "emp_id": str(row.get('emp_id', '')),
                    "type": "logical_error",
                    "message": f"중간정산일({interim_date.strftime('%Y-%m-%d')})이 입사일({hire_date.strftime('%Y-%m-%d')})보다 빠릅니다",
                    "severity": "error"
                })
        
        # TODO: 시산일 관련 검증 (시산일 필드가 매핑에 있을 경우)
        
        return errors
    
    # ========================================
    # 조건부 필드 검증
    # ========================================
    
    def _check_conditional_fields(self, sheet_name: str, idx: int, row: pd.Series) -> List[Dict]:
        """
        조건부 필드 검증 (if 직종>2)
        """
        errors = []
        
        employee_type = row.get('employee_type')
        if pd.notnull(employee_type) and employee_type > 2:
            # 당년도퇴직급 체크
            if 'current_year_severance' in row.index:
                if pd.isnull(row['current_year_severance']) or row['current_year_severance'] == 0:
                    errors.append({
                        "sheet": sheet_name,
                        "row": idx + 2,
                        "column": "current_year_severance",
                        "emp_id": str(row.get('emp_id', '')),
                        "type": "conditional_field_missing",
                        "message": f"직종이 {employee_type}일 때 당년도퇴직급이 필요합니다",
                        "severity": "error"
                    })
            
            # 차년도퇴직급 체크
            if 'next_year_severance' in row.index:
                if pd.isnull(row['next_year_severance']) or row['next_year_severance'] == 0:
                    errors.append({
                        "sheet": sheet_name,
                        "row": idx + 2,
                        "column": "next_year_severance",
                        "emp_id": str(row.get('emp_id', '')),
                        "type": "conditional_field_missing",
                        "message": f"직종이 {employee_type}일 때 차년도퇴직급이 필요합니다",
                        "severity": "error"
                    })
        
        return errors
    
    # ========================================
    # 중복 검증
    # ========================================
    
    def _check_duplicates_in_sheet(self, sheet_name: str, df: pd.DataFrame) -> List[Dict]:
        """
        시트 내 사원번호 중복 검증
        """
        errors = []
        
        if 'emp_id' not in df.columns:
            return errors
        
        # 유효한 사원번호만 추출
        valid_emp_ids = df[df['emp_id'].apply(self._is_valid_emp_id)]
        
        # 중복 찾기
        duplicates = valid_emp_ids[valid_emp_ids.duplicated('emp_id', keep=False)]
        
        if not duplicates.empty:
            for emp_id in duplicates['emp_id'].unique():
                dup_indices = duplicates[duplicates['emp_id'] == emp_id].index.tolist()
                errors.append({
                    "sheet": sheet_name,
                    "row": None,
                    "column": "emp_id",
                    "emp_id": str(emp_id),
                    "type": "duplicate_emp_id",
                    "message": f"사원번호 중복: {emp_id} (행: {[i+2 for i in dup_indices]})",
                    "severity": "error"
                })
        
        return errors
    
    # ========================================
    # 시트 간 교차 검증
    # ========================================
    
    def _validate_cross_sheet(self, all_sheets: Dict[str, pd.DataFrame], result: Dict):
        """
        시트 간 교차 검증 (한 번만 실행)
        """
        # 재직자명부와 퇴직자명부 찾기
        active_sheets = {}
        retired_sheets = {}
        additional_sheets = {}
        
        for sheet_name, df in all_sheets.items():
            sheet_name_lower = sheet_name.lower().replace(" ", "")
            if "재직자명부" in sheet_name_lower or "재직자" in sheet_name_lower:
                active_sheets[sheet_name] = df
            elif "퇴직자" in sheet_name_lower or "dc전환자" in sheet_name_lower:
                retired_sheets[sheet_name] = df
            elif "전출입" in sheet_name_lower or "추가" in sheet_name_lower:
                additional_sheets[sheet_name] = df
        
        # 재직자와 퇴직자 중복 검증
        if active_sheets and retired_sheets:
            cross_errors = self._check_active_retired_duplicates(active_sheets, retired_sheets)
            result["errors"].extend(cross_errors)
        
        # 전출입명부 검증
        if additional_sheets and (active_sheets or retired_sheets):
            additional_errors = self._check_additional_sheet(additional_sheets, active_sheets, retired_sheets)
            result["errors"].extend(additional_errors)
        
        # TODO: 전년도 vs 당년도 비교 검증
    
    def _check_active_retired_duplicates(self, active_sheets: Dict, retired_sheets: Dict) -> List[Dict]:
        """
        재직자와 퇴직자 중복 검증
        """
        errors = []
        
        # 모든 재직자 사원번호 수집
        active_emp_ids = set()
        for df in active_sheets.values():
            if 'emp_id' in df.columns:
                valid_ids = df[df['emp_id'].apply(self._is_valid_emp_id)]['emp_id'].unique()
                active_emp_ids.update(valid_ids)
        
        # 퇴직자가 재직자에 있는지 체크
        for retired_sheet_name, retired_df in retired_sheets.items():
            if 'emp_id' not in retired_df.columns:
                continue
            
            for idx, row in retired_df.iterrows():
                emp_id = row.get('emp_id')
                if self._is_valid_emp_id(emp_id) and emp_id in active_emp_ids:
                    errors.append({
                        "sheet": retired_sheet_name,
                        "row": idx + 2,
                        "column": "emp_id",
                        "emp_id": str(emp_id),
                        "type": "duplicate_across_sheets",
                        "message": f"퇴직자({emp_id})가 재직자명부에도 존재합니다",
                        "severity": "error"
                    })
        
        return errors
    
    def _check_additional_sheet(self, additional_sheets: Dict, active_sheets: Dict, retired_sheets: Dict) -> List[Dict]:
        """
        전출입명부(추가명부) 검증
        reason: 1(관계사전입), 2(관계사전출), 5(기타장기종업원) 등
        """
        errors = []
        
        # 재직자 사원번호 수집
        active_emp_ids = set()
        for df in active_sheets.values():
            if 'emp_id' in df.columns:
                valid_ids = df[df['emp_id'].apply(self._is_valid_emp_id)]['emp_id'].unique()
                active_emp_ids.update(valid_ids)
        
        # 퇴직자 사원번호 수집
        retired_emp_ids = set()
        for df in retired_sheets.values():
            if 'emp_id' in df.columns:
                valid_ids = df[df['emp_id'].apply(self._is_valid_emp_id)]['emp_id'].unique()
                retired_emp_ids.update(valid_ids)
        
        for sheet_name, df in additional_sheets.items():
            if 'emp_id' not in df.columns or 'reason' not in df.columns:
                continue
            
            for idx, row in df.iterrows():
                emp_id = row.get('emp_id')
                reason = row.get('reason')
                
                if not self._is_valid_emp_id(emp_id) or pd.isnull(reason):
                    continue
                
                # reason = 1 (관계사전입) 또는 5 (기타장기종업원) → 재직자명부에 있어야 함
                if reason in [1, 5]:
                    if emp_id not in active_emp_ids:
                        reason_name = "관계사전입" if reason == 1 else "기타장기종업원"
                        errors.append({
                            "sheet": sheet_name,
                            "row": idx + 2,
                            "column": "emp_id",
                            "emp_id": str(emp_id),
                            "type": "additional_not_in_active",
                            "message": f"{reason_name}({emp_id})가 재직자명부에 없습니다",
                            "severity": "error"
                        })
                
                # reason = 2 (관계사전출) → 퇴직자명부와 중복되면 안됨
                elif reason == 2:
                    if emp_id in retired_emp_ids:
                        errors.append({
                            "sheet": sheet_name,
                            "row": idx + 2,
                            "column": "emp_id",
                            "emp_id": str(emp_id),
                            "type": "additional_duplicate_retired",
                            "message": f"관계사전출({emp_id})이 퇴직자명부에도 존재합니다",
                            "severity": "error"
                        })
        
        return errors
    
    # ========================================
    # 2차 검증: AI 맥락 검증
    # ========================================
    
    def _validate_phase2_ai_context(self, all_sheets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        2차 검증: K-IFRS 1019 기준 AI 맥락 검증
        AIValidator 클래스로 위임하여 처리합니다.
        """
        return self.ai_validator.validate_context(all_sheets)
    
    # ========================================
    # 헬퍼 메서드
    # ========================================
    
    def _count_valid_records(self, df: pd.DataFrame) -> int:
        """
        유효한 레코드 수를 계산합니다.
        """
        if 'emp_id' not in df.columns:
            return len(df)
        
        return df['emp_id'].apply(self._is_valid_emp_id).sum()
    
    def _is_valid_emp_id(self, emp_id: Any) -> bool:
        """
        사원번호가 유효한지 확인
        """
        if pd.isnull(emp_id):
            return False
        emp_id_str = str(emp_id).strip()
        return emp_id_str not in ['', 'nan', 'None', 'NaN']
    
    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """
        날짜 문자열을 datetime 객체로 변환
        """
        if pd.isnull(date_str):
            return None
        
        try:
            date_str = str(date_str).strip()
            if date_str in ['', 'nan', 'None']:
                return None
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return None
