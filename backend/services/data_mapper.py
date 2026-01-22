import pandas as pd
from typing import Dict, List
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class DataMapper:
    """
    엑셀 데이터를 정형화하고 매핑하는 클래스
    """
    
    def __init__(self):
        """
        데이터 매핑 규칙을 초기화합니다.
        """
        # 재직자 명부 컬럼 매핑
        self.active_employee_mapping = {
            "emp_id": ["사원번호", "직원번호", "employee_no"],
            "birth_date": ["생년월일", "생일"],
            "gender": ["성별", "성별(1:남자, 2:여자)"],
            "hire_date": ["입사일자", "입사일"],
            "base_salary": ["기준급여", "급여"],
            "current_year_severance": ["당년도퇴직급여추계액", "당년도 퇴직급여추계액"],
            "next_year_severance": ["차년도퇴직급여추계액", "차년도 퇴직급여추계액"],
            "employee_type": ["중업원 구분", "중업원구분", "직원구분", "중업원 구분(1:직원, 3:임원, 4:계약직)"],
            "interim_settlement_date": ["중간정산기준일", "중간정산 기준일"],
            "interim_settlement_amount": ["중간정산액", "중간정산 액"],
            "plan_type": ["제도구분", "제도구분(1,2,3)", "제도 구분"],
            "applicable_multiplier": ["적용배수", "배수"]
        }
        
        # 퇴직자 및 DC전환자 명부 컬럼 매핑
        self.retired_employee_mapping = {
            "emp_id": ["사원번호", "직원번호", "employee_no"],
            "birth_date": ["생년월일", "생일"],
            "gender": ["성별", "성별(1:남자, 2:여자)"],
            "hire_date": ["입사일자", "입사일"],
            "retirement_or_dc_date": ["퇴직일 또는 DC전환일", "퇴직일또는DC전환일", "퇴직일", "DC전환일"],
            "retirement_or_dc_amount": ["퇴직금 또는 DC전환금", "퇴직금또는DC전환금", "퇴직금", "DC전환금"],
            "employee_type": ["중업원 구분", "중업원구분", "직원구분", "중업원 구분(1:직원, 3:임원, 4:계약직)"],
            "reason": ["사유", "사유(1: 퇴직, 2: DC전환)", "퇴직사유"],
            "plan_type": ["제도구분", "제도구분(1,2,3)", "제도 구분"]
        }
        
        # 기타장기 재직자 명부 컬럼 매핑 (선택사항 - 있을 때만 처리)
        self.long_term_employee_mapping = {
            "emp_id": ["사원번호", "직원번호", "employee_no"],
            "birth_date": ["생년월일", "생일"],
            "gender": ["성별", "성별(1:남자, 2:여자)"],
            "hire_date": ["입사일자", "입사일"],
            "base_salary": ["기준급여", "급여"],
            "employee_type": ["중업원 구분", "중업원구분", "직원구분", "중업원 구분(1:직원, 3:임원, 4:계약직)"]
            # 실제 컬럼에 맞춰 추가 가능
        }
        
        # 추가명부 컬럼 매핑
        self.additional_employee_mapping = {
            "emp_id": ["사원번호", "직원번호", "employee_no"],
            "birth_date": ["생년월일", "생일"],
            "gender": ["성별", "성별(1:남자, 2:여자)"],
            "hire_date": ["입사일자", "입사일"],
            "base_salary": ["기준급여", "급여"],
            "reason_occurrence_amount": ["사유발생일 시점 발생금액", "사유발생일시점발생금액", "발생금액"],
            "employee_type": ["중업원 구분", "중업원구분", "직원구분", "중업원 구분(1:직원, 3:임원, 4:계약직)"],
            "interim_settlement_date": ["중간정산기준일", "중간정산 기준일"],
            "reason": ["사유", "사유(1:관계사전입, 2:관계사전출, 3:사업합병전, 4:사업합병후, 5:기타장기종업원)"],
            "reason_occurrence_date": ["사유발생일", "사유 발생일"]
        }
    
    def map_all_sheets(self, sheets_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        모든 시트의 데이터를 매핑하고 정형화합니다.
        
        Args:
            sheets_data: 원본 시트 데이터
            
        Returns:
            Dict[str, pd.DataFrame]: 정형화된 시트 데이터
        """
        mapped_data = {}
        
        for sheet_name, df in sheets_data.items():
            logger.info(f"시트 '{sheet_name}' 매핑 시작")
            
            try:
                # 시트별 매핑 규칙 선택 (키워드 기반)
                sheet_name_normalized = sheet_name.lower().replace(" ", "")
                
                if "재직자명부" in sheet_name_normalized and "기타장기" not in sheet_name_normalized:
                    df_mapped = self._map_active_employee(df)
                elif "기타장기" in sheet_name_normalized:
                    df_mapped = self._map_long_term_employee(df)
                elif "퇴직자" in sheet_name_normalized or "dc전환자" in sheet_name_normalized:
                    df_mapped = self._map_retired_employee(df)
                elif "추가" in sheet_name_normalized and "명부" in sheet_name_normalized:
                    df_mapped = self._map_additional_employee(df)
                else:
                    logger.warning(f"알 수 없는 시트 타입: {sheet_name}")
                    df_mapped = df.copy()
                
                mapped_data[sheet_name] = df_mapped
                logger.info(f"시트 '{sheet_name}' 매핑 완료: {len(df_mapped)}행")
                
            except Exception as e:
                logger.error(f"시트 '{sheet_name}' 매핑 오류: {str(e)}")
                raise
        
        return mapped_data
    
    def _map_active_employee(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        재직자 명부 데이터를 매핑합니다.
        
        Args:
            df: 원본 DataFrame
            
        Returns:
            pd.DataFrame: 매핑된 DataFrame
        """
        df_mapped = pd.DataFrame()
        
        # 컬럼 매핑 적용
        for standard_col, possible_names in self.active_employee_mapping.items():
            mapped = False
            for col_name in df.columns:
                col_name_clean = str(col_name).strip()
                if col_name_clean in possible_names:
                    df_mapped[standard_col] = df[col_name].copy()
                    mapped = True
                    logger.info(f"'{col_name}' -> '{standard_col}' 매핑")
                    break
            
            if not mapped:
                # 매핑되지 않은 컬럼은 None으로 채움
                df_mapped[standard_col] = None
                logger.warning(f"'{standard_col}' 컬럼을 찾을 수 없습니다")
        
        # 데이터 타입 정형화
        df_mapped = self._normalize_active_employee_data(df_mapped)
        
        return df_mapped
    
    def _map_retired_employee(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        퇴직자 및 DC전환자 명부 데이터를 매핑합니다.
        
        Args:
            df: 원본 DataFrame
            
        Returns:
            pd.DataFrame: 매핑된 DataFrame
        """
        df_mapped = pd.DataFrame()
        
        # 컬럼 매핑 적용
        for standard_col, possible_names in self.retired_employee_mapping.items():
            mapped = False
            for col_name in df.columns:
                col_name_clean = str(col_name).strip()
                if col_name_clean in possible_names:
                    df_mapped[standard_col] = df[col_name].copy()
                    mapped = True
                    logger.info(f"'{col_name}' -> '{standard_col}' 매핑")
                    break
            
            if not mapped:
                # 매핑되지 않은 컬럼은 None으로 채움
                df_mapped[standard_col] = None
                logger.warning(f"'{standard_col}' 컬럼을 찾을 수 없습니다")
        
        # 데이터 타입 정형화
        df_mapped = self._normalize_retired_employee_data(df_mapped)
        
        return df_mapped
    
    def _map_long_term_employee(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        기타장기 재직자 명부 데이터를 매핑합니다 (선택사항).
        
        Args:
            df: 원본 DataFrame
            
        Returns:
            pd.DataFrame: 매핑된 DataFrame
        """
        df_mapped = pd.DataFrame()
        
        # 컬럼 매핑 적용
        for standard_col, possible_names in self.long_term_employee_mapping.items():
            mapped = False
            for col_name in df.columns:
                col_name_clean = str(col_name).strip()
                if col_name_clean in possible_names:
                    df_mapped[standard_col] = df[col_name].copy()
                    mapped = True
                    logger.info(f"'{col_name}' -> '{standard_col}' 매핑")
                    break
            
            if not mapped:
                df_mapped[standard_col] = None
                logger.warning(f"'{standard_col}' 컬럼을 찾을 수 없습니다")
        
        # 기본 정형화만 수행 (재직자와 유사한 구조로 가정)
        df_mapped = self._normalize_long_term_employee_data(df_mapped)
        
        return df_mapped
    
    def _normalize_long_term_employee_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        기타장기 재직자 명부 데이터를 정형화합니다.
        """
        df = df.copy()
        
        if 'emp_id' in df.columns:
            df['emp_id'] = self._normalize_employee_number(df['emp_id'])
        
        if 'birth_date' in df.columns:
            df['birth_date'] = self._normalize_date_from_number(df['birth_date'])
        
        if 'gender' in df.columns:
            df['gender'] = self._normalize_gender(df['gender'])
        
        if 'hire_date' in df.columns:
            df['hire_date'] = self._normalize_date(df['hire_date'])
        
        if 'base_salary' in df.columns:
            df['base_salary'] = self._normalize_number(df['base_salary'])
        
        if 'employee_type' in df.columns:
            df['employee_type'] = self._normalize_employee_type(df['employee_type'])
        
        return df
    
    def _map_additional_employee(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        추가명부 데이터를 매핑합니다.
        
        Args:
            df: 원본 DataFrame
            
        Returns:
            pd.DataFrame: 매핑된 DataFrame
        """
        df_mapped = pd.DataFrame()
        
        # 컬럼 매핑 적용
        for standard_col, possible_names in self.additional_employee_mapping.items():
            mapped = False
            for col_name in df.columns:
                col_name_clean = str(col_name).strip()
                if col_name_clean in possible_names:
                    df_mapped[standard_col] = df[col_name].copy()
                    mapped = True
                    logger.info(f"'{col_name}' -> '{standard_col}' 매핑")
                    break
            
            if not mapped:
                # 매핑되지 않은 컬럼은 None으로 채움
                df_mapped[standard_col] = None
                logger.warning(f"'{standard_col}' 컬럼을 찾을 수 없습니다")
        
        # 데이터 타입 정형화
        df_mapped = self._normalize_additional_employee_data(df_mapped)
        
        return df_mapped
    
    def _normalize_active_employee_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        재직자 명부 데이터를 정형화합니다.
        
        Args:
            df: 매핑된 DataFrame
            
        Returns:
            pd.DataFrame: 정형화된 DataFrame
        """
        df = df.copy()
        
        # 1. 사원번호 정형화 (문자열, 앞뒤 공백 제거)
        if 'emp_id' in df.columns:
            df['emp_id'] = self._normalize_employee_number(df['emp_id'])
        
        # 2. 생년월일 정형화 (YYYYMMDD -> YYYY-MM-DD)
        if 'birth_date' in df.columns:
            df['birth_date'] = self._normalize_date_from_number(df['birth_date'])
        
        # 3. 성별 정형화 (1: 남자, 2: 여자)
        if 'gender' in df.columns:
            df['gender'] = self._normalize_gender(df['gender'])
        
        # 4. 입사일자 정형화 (YYYY-MM-DD)
        if 'hire_date' in df.columns:
            df['hire_date'] = self._normalize_date(df['hire_date'])
        
        # 5. 기준급여 정형화 (숫자)
        if 'base_salary' in df.columns:
            df['base_salary'] = self._normalize_number(df['base_salary'])
        
        # 6. 당년도 퇴직급여추계액 정형화 (숫자)
        if 'current_year_severance' in df.columns:
            df['current_year_severance'] = self._normalize_number(df['current_year_severance'])
        
        # 7. 차년도 퇴직급여추계액 정형화 (숫자)
        if 'next_year_severance' in df.columns:
            df['next_year_severance'] = self._normalize_number(df['next_year_severance'])
        
        # 8. 중업원 구분 정형화 (1: 직원, 3: 임원, 4: 계약직)
        if 'employee_type' in df.columns:
            df['employee_type'] = self._normalize_employee_type(df['employee_type'])
        
        # 9. 중간정산기준일 정형화 (YYYY-MM-DD)
        if 'interim_settlement_date' in df.columns:
            df['interim_settlement_date'] = self._normalize_date(df['interim_settlement_date'])
        
        # 10. 중간정산액 정형화 (숫자)
        if 'interim_settlement_amount' in df.columns:
            df['interim_settlement_amount'] = self._normalize_number(df['interim_settlement_amount'])
        
        # 11. 제도구분 정형화 (1, 2, 3)
        if 'plan_type' in df.columns:
            df['plan_type'] = self._normalize_plan_type(df['plan_type'])
        
        # 12. 적용배수 정형화 (숫자)
        if 'applicable_multiplier' in df.columns:
            df['applicable_multiplier'] = self._normalize_number(df['applicable_multiplier'])
        
        return df
    
    def _normalize_employee_number(self, series: pd.Series) -> pd.Series:
        """
        사원번호를 문자열 형식으로 정형화합니다.
        """
        try:
            # 숫자인 경우 정수로 변환 후 문자열로
            normalized = series.apply(lambda x: str(int(x)) if pd.notnull(x) and x != '' else '')
            normalized = normalized.str.strip()
            return normalized
        except Exception as e:
            logger.warning(f"사원번호 정형화 오류: {str(e)}")
            return series.astype(str).str.strip()
    
    def _normalize_date_from_number(self, series: pd.Series) -> pd.Series:
        """
        숫자 형식의 날짜(YYYYMMDD)를 YYYY-MM-DD 형식으로 정형화합니다.
        """
        def convert_date(value):
            if pd.isnull(value) or value == '':
                return None
            
            try:
                # 숫자인 경우
                date_str = str(int(float(value)))
                
                if len(date_str) == 8:  # YYYYMMDD
                    year = date_str[:4]
                    month = date_str[4:6]
                    day = date_str[6:8]
                    return f"{year}-{month}-{day}"
                elif len(date_str) == 6:  # YYMMDD
                    year = "19" + date_str[:2] if int(date_str[:2]) > 50 else "20" + date_str[:2]
                    month = date_str[2:4]
                    day = date_str[4:6]
                    return f"{year}-{month}-{day}"
                else:
                    return None
            except:
                return None
        
        return series.apply(convert_date)
    
    def _normalize_date(self, series: pd.Series) -> pd.Series:
        """
        날짜 데이터를 YYYY-MM-DD 형식으로 정형화합니다.
        """
        def convert_date(value):
            if pd.isnull(value) or value == '':
                return None
            
            try:
                # 이미 datetime 타입인 경우
                if isinstance(value, pd.Timestamp) or isinstance(value, datetime):
                    return value.strftime('%Y-%m-%d')
                
                # 문자열인 경우 pandas to_datetime 사용
                dt = pd.to_datetime(value, errors='coerce')
                if pd.notnull(dt):
                    return dt.strftime('%Y-%m-%d')
                
                return None
            except:
                return None
        
        return series.apply(convert_date)
    
    def _normalize_gender(self, series: pd.Series) -> pd.Series:
        """
        성별을 정형화합니다 (1: 남자, 2: 여자).
        """
        def convert_gender(value):
            if pd.isnull(value) or value == '':
                return None
            
            try:
                val = int(float(value))
                if val in [1, 2]:
                    return val
                return None
            except:
                return None
        
        return series.apply(convert_gender)
    
    def _normalize_employee_type(self, series: pd.Series) -> pd.Series:
        """
        중업원 구분을 정형화합니다 (1: 직원, 3: 임원, 4: 계약직).
        """
        def convert_type(value):
            if pd.isnull(value) or value == '':
                return None
            
            try:
                val = int(float(value))
                if val in [1, 3, 4]:
                    return val
                return None
            except:
                return None
        
        return series.apply(convert_type)
    
    def _normalize_plan_type(self, series: pd.Series) -> pd.Series:
        """
        제도구분을 정형화합니다 (1, 2, 3).
        """
        def convert_plan(value):
            if pd.isnull(value) or value == '':
                return None
            
            try:
                val = int(float(value))
                if val in [1, 2, 3]:
                    return val
                return None
            except:
                return None
        
        return series.apply(convert_plan)
    
    def _normalize_number(self, series: pd.Series) -> pd.Series:
        """
        숫자 데이터를 정형화합니다.
        """
        def convert_number(value):
            if pd.isnull(value) or value == '':
                return None
            
            try:
                # 문자열인 경우 콤마, 하이픈 제거
                if isinstance(value, str):
                    value = value.replace(',', '').replace('-', '')
                    if value == '' or value == 'nan':
                        return None
                
                return float(value)
            except:
                return None
        
        return series.apply(convert_number)
    
    def _normalize_retired_employee_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        퇴직자 및 DC전환자 명부 데이터를 정형화합니다.
        
        Args:
            df: 매핑된 DataFrame
            
        Returns:
            pd.DataFrame: 정형화된 DataFrame
        """
        df = df.copy()
        
        # 1. 사원번호 정형화 (문자열, 앞뒤 공백 제거)
        if 'emp_id' in df.columns:
            df['emp_id'] = self._normalize_employee_number(df['emp_id'])
        
        # 2. 생년월일 정형화 (YYYYMMDD -> YYYY-MM-DD)
        if 'birth_date' in df.columns:
            df['birth_date'] = self._normalize_date_from_number(df['birth_date'])
        
        # 3. 성별 정형화 (1: 남자, 2: 여자)
        if 'gender' in df.columns:
            df['gender'] = self._normalize_gender(df['gender'])
        
        # 4. 입사일자 정형화 (YYYY-MM-DD)
        if 'hire_date' in df.columns:
            df['hire_date'] = self._normalize_date_from_number(df['hire_date'])
        
        # 5. 퇴직일 또는 DC전환일 정형화 (YYYYMMDD -> YYYY-MM-DD)
        if 'retirement_or_dc_date' in df.columns:
            df['retirement_or_dc_date'] = self._normalize_date_from_number(df['retirement_or_dc_date'])
        
        # 6. 퇴직금 또는 DC전환금 정형화 (숫자)
        if 'retirement_or_dc_amount' in df.columns:
            df['retirement_or_dc_amount'] = self._normalize_number(df['retirement_or_dc_amount'])
        
        # 7. 중업원 구분 정형화 (1: 직원, 3: 임원, 4: 계약직)
        if 'employee_type' in df.columns:
            df['employee_type'] = self._normalize_employee_type(df['employee_type'])
        
        # 8. 사유 정형화 (1: 퇴직, 2: DC전환)
        if 'reason' in df.columns:
            df['reason'] = self._normalize_reason(df['reason'])
        
        # 9. 제도구분 정형화 (1, 2, 3)
        if 'plan_type' in df.columns:
            df['plan_type'] = self._normalize_plan_type(df['plan_type'])
        
        return df
    
    def _normalize_reason(self, series: pd.Series) -> pd.Series:
        """
        사유를 정형화합니다 (1: 퇴직, 2: DC전환).
        """
        def convert_reason(value):
            if pd.isnull(value) or value == '':
                return None
            
            try:
                val = int(float(value))
                if val in [1, 2]:
                    return val
                return None
            except:
                return None
        
        return series.apply(convert_reason)
    
    def _normalize_additional_employee_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        추가명부 데이터를 정형화합니다.
        
        Args:
            df: 매핑된 DataFrame
            
        Returns:
            pd.DataFrame: 정형화된 DataFrame
        """
        df = df.copy()
        
        # 1. 사원번호 정형화 (문자열, 앞뒤 공백 제거, 앞에 0이 있을 수 있음)
        if 'emp_id' in df.columns:
            df['emp_id'] = self._normalize_employee_number_with_leading_zero(df['emp_id'])
        
        # 2. 생년월일 정형화 (YYYY-MM-DD 형식으로 통일)
        if 'birth_date' in df.columns:
            df['birth_date'] = self._normalize_date(df['birth_date'])
        
        # 3. 성별 정형화 (1: 남자, 2: 여자)
        if 'gender' in df.columns:
            df['gender'] = self._normalize_gender(df['gender'])
        
        # 4. 입사일자 정형화 (YYYY-MM-DD)
        if 'hire_date' in df.columns:
            df['hire_date'] = self._normalize_date(df['hire_date'])
        
        # 5. 기준급여 정형화 (숫자)
        if 'base_salary' in df.columns:
            df['base_salary'] = self._normalize_number(df['base_salary'])
        
        # 6. 사유발생일 시점 발생금액 정형화 (숫자)
        if 'reason_occurrence_amount' in df.columns:
            df['reason_occurrence_amount'] = self._normalize_number(df['reason_occurrence_amount'])
        
        # 7. 중업원 구분 정형화 (1: 직원, 3: 임원, 4: 계약직)
        if 'employee_type' in df.columns:
            df['employee_type'] = self._normalize_employee_type(df['employee_type'])
        
        # 8. 중간정산기준일 정형화 (YYYY-MM-DD)
        if 'interim_settlement_date' in df.columns:
            df['interim_settlement_date'] = self._normalize_date(df['interim_settlement_date'])
        
        # 9. 사유 정형화 (1~5)
        if 'reason' in df.columns:
            df['reason'] = self._normalize_additional_reason(df['reason'])
        
        # 10. 사유발생일 정형화 (YYYY-MM-DD)
        if 'reason_occurrence_date' in df.columns:
            df['reason_occurrence_date'] = self._normalize_date(df['reason_occurrence_date'])
        
        return df
    
    def _normalize_employee_number_with_leading_zero(self, series: pd.Series) -> pd.Series:
        """
        사원번호를 문자열 형식으로 정형화합니다 (앞에 0이 있을 수 있음).
        
        Args:
            series: 사원번호 컬럼
            
        Returns:
            pd.Series: 정형화된 사원번호 컬럼
        """
        def convert_emp_id(value):
            if pd.isnull(value) or value == '':
                return ''
            
            try:
                # 문자열로 변환
                emp_id_str = str(value).strip()
                
                # 소수점이 있는 경우 (예: 2120.0) 정수로 변환
                if '.' in emp_id_str:
                    emp_id_str = str(int(float(emp_id_str)))
                
                # 'nan'이나 'None' 문자열은 빈 문자열로
                if emp_id_str.lower() in ['nan', 'none']:
                    return ''
                
                # 4자리 미만이면 앞에 0을 채움
                if len(emp_id_str) < 4 and emp_id_str.isdigit():
                    emp_id_str = emp_id_str.zfill(4)
                
                return emp_id_str
            except:
                return str(value).strip()
        
        return series.apply(convert_emp_id)
    
    def _normalize_additional_reason(self, series: pd.Series) -> pd.Series:
        """
        추가명부 사유를 정형화합니다.
        (1:관계사전입, 2:관계사전출, 3:사업합병전, 4:사업합병후, 5:기타장기종업원)
        """
        def convert_reason(value):
            if pd.isnull(value) or value == '':
                return None
            
            try:
                val = int(float(value))
                if val in [1, 2, 3, 4, 5]:
                    return val
                return None
            except:
                return None
        
        return series.apply(convert_reason)
