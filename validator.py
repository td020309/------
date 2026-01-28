import pandas as pd
from datetime import datetime

class DataValidator:
    """
    정해진 규칙(Hard Rules)에 따라 데이터의 유효성을 검사하는 클래스
    """
    def __init__(self, all_data, base_date, calculation_method):
        self.all_data = all_data
        self.base_date = pd.to_datetime(base_date)
        self.calculation_method = calculation_method

    def _find_column(self, df, keyword, exclude=None):
        """컬럼명에 keyword가 포함된 컬럼을 찾아 반환
        
        Args:
            df: DataFrame
            keyword: 찾을 키워드
            exclude: 제외할 키워드 (예: '발생일'을 제외하고 '사유' 찾기)
        """
        for col in df.columns:
            col_str = str(col)
            if keyword in col_str:
                # 제외 키워드가 있으면 해당 키워드 포함된 컬럼은 건너뛰기
                if exclude and exclude in col_str:
                    continue
                return col
        return None

    def _normalize_employee_id(self, value):
        """사원번호를 정규화 (소수점 제거 등)"""
        if value is None or pd.isna(value):
            return None
        s = str(value).strip()
        # 소수점 제거 (예: "235765.0" -> "235765")
        if s.endswith('.0'):
            s = s[:-2]
        return s

    def _parse_date(self, date_val):
        """다양한 형식의 날짜를 datetime 객체로 변환"""
        if pd.isna(date_val) or date_val is None:
            return None
        
        # 이미 datetime 객체인 경우
        if isinstance(date_val, (datetime, pd.Timestamp)):
            return pd.to_datetime(date_val)
            
        try:
            s_date = str(date_val).strip().replace(".0", "")
            if s_date.isdigit():
                if len(s_date) == 8:  # YYYYMMDD
                    return datetime.strptime(s_date, "%Y%m%d")
                elif len(s_date) == 6:  # YYMMDD
                    year = int(s_date[:2])
                    year += 2000 if year < 50 else 1900
                    return datetime.strptime(f"{year}{s_date[2:]}", "%Y%m%d")
            return pd.to_datetime(s_date)
        except:
            return None

    def _check_date_validity(self, date_val, label):
        """월 > 12 또는 일 > 31 체크"""
        if pd.isna(date_val) or date_val is None:
            return None
        
        s_date = str(date_val).strip().replace(".0", "")
        if len(s_date) >= 6:
            # 뒷부분 4자리 추출 (MMDD)
            mmdd = s_date[-4:]
            try:
                mm = int(mmdd[:2])
                dd = int(mmdd[2:])
                if mm > 12 or dd > 31:
                    return f"{label}, 월>{mm} or 일>{dd} (날짜 형식 오류)"
            except:
                pass
        return None

    def _validate_active_employees(self, sheet_name, data):
        """재직자명부 검증 규칙"""
        results = []
        df = pd.DataFrame(data)
        
        # 컬럼명 찾기 (키워드 기반)
        col_employee_id = self._find_column(df, '사원번호') or self._find_column(df, '사번')
        col_birth_date = self._find_column(df, '생년월일')
        col_join_date = self._find_column(df, '입사일')
        col_salary = self._find_column(df, '기준급여') or self._find_column(df, '급여')
        col_job_type = self._find_column(df, '종업원 구분') or self._find_column(df, '구분')
        col_curr_estimate = self._find_column(df, '당년도')
        col_next_estimate = self._find_column(df, '차년도')
        col_interim_amount = self._find_column(df, '중간정산액')
        col_interim_date = self._find_column(df, '중간정산') or self._find_column(df, '사유발생일')
        
        # 재직자 중복 체크
        if col_employee_id:
            employee_ids = df[col_employee_id].dropna()
            duplicates = employee_ids[employee_ids.duplicated(keep=False)]
            if not duplicates.empty:
                duplicate_ids = duplicates.unique()
                for dup_id in duplicate_ids:
                    count = (employee_ids == dup_id).sum()
                    results.append({
                        "category": "사원번호 중복",
                        "emp_id": self._normalize_employee_id(dup_id),
                        "detail": f"재직자명부 내 {count}건 중복 존재"
                    })
        
        for idx, row in df.iterrows():
            emp_id = self._normalize_employee_id(row.get(col_employee_id)) if col_employee_id else f"Row {idx+1}"

            # 필수값 체크 (blank 검증)
            required_fields = [
                (col_employee_id, '사원번호'),
                (col_birth_date, '생년월일'),
                (col_join_date, '입사일자'),
                (col_salary, '기준급여'),
                (col_job_type, '종업원 구분')
            ]
            for col_name, display_name in required_fields:
                if col_name:
                    val = row.get(col_name)
                    if pd.isna(val) or val is None or str(val).strip() == "":
                        results.append({
                            "category": "필수값 누락",
                            "emp_id": emp_id,
                            "detail": f"{display_name} 데이터 없음"
                        })

            # 음수 체크
            curr_estimate = row.get(col_curr_estimate) if col_curr_estimate else None
            next_estimate = row.get(col_next_estimate) if col_next_estimate else None
            interim_amount = row.get(col_interim_amount) if col_interim_amount else None
            
            if curr_estimate is not None and isinstance(curr_estimate, (int, float)) and curr_estimate < 0:
                results.append({"category": "금액 오류(음수)", "emp_id": emp_id, "detail": f"당년도 추계액 음수 ({curr_estimate:,.0f})"})
            
            if next_estimate is not None and isinstance(next_estimate, (int, float)) and next_estimate < 0:
                results.append({"category": "금액 오류(음수)", "emp_id": emp_id, "detail": f"차년도 추계액 음수 ({next_estimate:,.0f})"})
            
            if interim_amount is not None and isinstance(interim_amount, (int, float)) and interim_amount < 0:
                results.append({"category": "금액 오류(음수)", "emp_id": emp_id, "detail": f"중간정산액 음수 ({interim_amount:,.0f})"})

            # 종업원 구분 > 2 (임원, 계약직) 조건부 체크
            job_type = row.get(col_job_type) if col_job_type else None
            try:
                job_type_num = float(job_type) if job_type is not None else 0
            except:
                job_type_num = 0
            
            if job_type_num > 2:
                if pd.isna(curr_estimate) or curr_estimate is None or curr_estimate == 0:
                    results.append({"category": "추계액 논리 오류(임원/계약직)", "emp_id": emp_id, "detail": "당년도 추계액이 0 또는 누락됨"})
                if pd.isna(next_estimate) or next_estimate is None or next_estimate == 0:
                    results.append({"category": "추계액 논리 오류(임원/계약직)", "emp_id": emp_id, "detail": "차년도 추계액이 0 또는 누락됨"})
                if curr_estimate is not None and next_estimate is not None and not (curr_estimate < next_estimate):
                    results.append({"category": "추계액 논리 오류(임원/계약직)", "emp_id": emp_id, "detail": f"당년도({curr_estimate:,.0f}) >= 차년도({next_estimate:,.0f})"})

            # 날짜 파싱
            birth_date = self._parse_date(row.get(col_birth_date)) if col_birth_date else None
            join_date = self._parse_date(row.get(col_join_date)) if col_join_date else None
            interim_date = self._parse_date(row.get(col_interim_date)) if col_interim_date else None

            # 입사연령 체크
            if birth_date and join_date:
                age_at_join = join_date.year - birth_date.year
                if age_at_join < 17 or age_at_join > 70:
                    results.append({"category": "입사연령 이상", "emp_id": emp_id, "detail": f"입사 시 연령 {age_at_join}세"})

            # 날짜 선후관계
            if birth_date and join_date and join_date < birth_date:
                results.append({"category": "날짜 선후 모순", "emp_id": emp_id, "detail": f"입사일({join_date.date()}) < 생년월일({birth_date.date()})"})

            if pd.notna(interim_date) and pd.notna(join_date) and interim_date <= join_date:
                results.append({"category": "날짜 확인 필요", "emp_id": emp_id, "detail": f"중간정산일({interim_date.date()}) <= 입사일({join_date.date()})"})

            if join_date and self.base_date and self.base_date <= join_date:
                results.append({"category": "날짜 선후 모순", "emp_id": emp_id, "detail": f"기준일({self.base_date.date()}) <= 입사일({join_date.date()})"})

            if interim_date and self.base_date and self.base_date <= interim_date:
                results.append({"category": "날짜 선후 모순", "emp_id": emp_id, "detail": f"기준일({self.base_date.date()}) <= 중간정산일({interim_date.date()})"})

            if interim_date and self.base_date and interim_date.year == self.base_date.year:
                interim_amount = row.get(col_interim_amount) if col_interim_amount else None
                if pd.isna(interim_amount) or interim_amount is None or interim_amount == 0:
                    results.append({
                        "category": "중간정산액 누락", 
                        "emp_id": emp_id, 
                        "detail": f"중간정산일({interim_date.year}년)이 기준일과 같으나 중간정산액이 0원 혹은 누락됨"
                    })

            # 날짜 형식 체크
            date_fields = [(col_birth_date, '생년월일'), (col_join_date, '입사일'), (col_interim_date, '중간정산일')]
            for col, label in date_fields:
                if col:
                    err = self._check_date_validity(row.get(col), label)
                    if err:
                        results.append({"category": "날짜 형식 오류", "emp_id": emp_id, "detail": err})

            # 기준급여 체크
            salary = row.get(col_salary) if col_salary else None
            if salary is not None and isinstance(salary, (int, float)) and salary < 1700000:
                results.append({"category": "저임금 의심", "emp_id": emp_id, "detail": f"기준급여 {salary:,.0f}원 (170만 원 미만)"})

        return results

    def _validate_retired_employees(self, sheet_name, data):
        """퇴직자명부 검증 규칙"""
        results = []
        df = pd.DataFrame(data)
        
        # 컬럼명 찾기
        col_employee_id = self._find_column(df, '사원번호')
        col_birth_date = self._find_column(df, '생년월일')
        col_gender = self._find_column(df, '성별')
        
        for idx, row in df.iterrows():
            emp_id = self._normalize_employee_id(row.get(col_employee_id)) if col_employee_id else f"Row {idx+1}"

            # 필수값 체크
            required_fields = [
                (col_employee_id, '사원번호'),
                (col_birth_date, '생년월일'),
                (col_gender, '성별')
            ]
            for col_name, display_name in required_fields:
                if col_name:
                    val = row.get(col_name)
                    if pd.isna(val) or val is None or str(val).strip() == "":
                        results.append({
                            "category": "필수값 누락",
                            "emp_id": emp_id,
                            "detail": f"{display_name} 데이터 없음"
                        })

        return results

    def _validate_additional_employees(self, sheet_name, data, active_ids, retired_ids):
        """추가명부(중간정산자명부) 검증 규칙"""
        results = []
        df = pd.DataFrame(data)
        
        # 컬럼명 찾기
        col_employee_id = self._find_column(df, '사원번호')
        col_birth_date = self._find_column(df, '생년월일')
        col_gender = self._find_column(df, '성별')
        col_reason = self._find_column(df, '사유', exclude='발생일')
        
        for idx, row in df.iterrows():
            emp_id = self._normalize_employee_id(row.get(col_employee_id)) if col_employee_id else f"Row {idx+1}"

            # 필수값 체크
            required_fields = [
                (col_employee_id, '사원번호'),
                (col_birth_date, '생년월일'),
                (col_gender, '성별'),
                (col_reason, '사유')
            ]
            for col_name, display_name in required_fields:
                if col_name:
                    val = row.get(col_name)
                    if pd.isna(val) or val is None or str(val).strip() == "":
                        results.append({
                            "category": "필수값 누락",
                            "emp_id": emp_id,
                            "detail": f"{display_name} 데이터 없음"
                        })
            
            # 사유별 조건부 검증
            reason = row.get(col_reason) if col_reason else None
            employee_id = self._normalize_employee_id(row.get(col_employee_id)) if col_employee_id else None
            
            if reason is not None and employee_id:
                try:
                    reason_num = int(float(reason))
                    # 사유 1번: 관계사전입 -> 재직자명부에 반드시 있어야 함
                    if reason_num == 1:
                        if employee_id not in active_ids:
                            results.append({"category": "명부 간 불일치", "emp_id": employee_id, "detail": "사유 1번(관계사전입): 재직자명부에 없음 (재직자명부 포함 필수)"})
                    
                    # 사유 2번: 관계사전출 -> 퇴직자명부와 중복 체크
                    elif reason_num == 2:
                        if employee_id in retired_ids:
                            results.append({"category": "명부 간 불일치", "emp_id": employee_id, "detail": "사유 2번(관계사전출): 퇴직자명부와 중복"})
                    
                    # 사유 5번: 기타장기종업원 -> 재직자명부에 반드시 있어야 함
                    elif reason_num == 5:
                        if employee_id not in active_ids:
                            results.append({"category": "명부 간 불일치", "emp_id": employee_id, "detail": "사유 5번(기타장기종업원): 기타장기재직자는 재직자명부에 포함되어야 합니다."})
                except:
                    pass
        
        return results

    def _validate_retirement_benefit_summary(self, sheet_name, data):
        """기초자료 퇴직급여 시트 검증"""
        results = []
        if not data or len(data) == 0:
            return results
        
        summary = data[0]
        reported_active_count = summary.get('재직자수_합계')
        reported_retired_count = summary.get('퇴직자수_합계')
        reported_estimate_sum = summary.get('퇴직금_추계액_합계')
        
        actual_active_count = 0
        actual_retired_count = 0
        actual_estimate_sum = 0
        
        for other_sheet_name, other_data in self.all_data.items():
            df = pd.DataFrame(other_data)
            if "재직자" in other_sheet_name and "기타장기" not in other_sheet_name:
                actual_active_count = len(df)
                col_curr_estimate = self._find_column(df, '당년도')
                if col_curr_estimate:
                    actual_estimate_sum = pd.to_numeric(df[col_curr_estimate], errors='coerce').sum()
            elif "퇴직자" in other_sheet_name:
                actual_retired_count = len(df)
        
        # 합계 불일치는 _global 성격이지만, 통일성을 위해 emp_id=None 혹은 "전체"로 처리
        if reported_active_count is not None:
            try:
                reported = int(float(reported_active_count))
                if reported != actual_active_count:
                    results.append({"category": "합계 불일치", "emp_id": "전체", "detail": f"재직자수: 기초자료({reported:,}명) ≠ 명부({actual_active_count:,}명)"})
            except: pass
        
        if reported_retired_count is not None:
            try:
                reported = int(float(reported_retired_count))
                if reported != actual_retired_count:
                    results.append({"category": "합계 불일치", "emp_id": "전체", "detail": f"퇴직자수: 기초자료({reported:,}명) ≠ 명부({actual_retired_count:,}명)"})
            except: pass
        
        if reported_estimate_sum is not None:
            try:
                reported = float(reported_estimate_sum)
                if abs(reported - actual_estimate_sum) > 1:
                    results.append({"category": "합계 불일치", "emp_id": "전체", "detail": f"추계액 합계: 기초자료({reported:,.0f}) ≠ 명부합계({actual_estimate_sum:,.0f})"})
            except: pass
        
        return results

    def validate(self):
        """
        데이터 검증을 수행하고 시트별, 오류 종류별로 구조화된 결과를 반환합니다.
        
        Returns:
            dict: {
                "시트명": {
                    "오류종류1": [ {"emp_id": "ID1", "detail": "내용"}, ... ],
                    ...
                }
            }
        """
        structured_results = {}
        active_employee_ids = set()
        retired_employee_ids = set()
        
        # 1. 사원번호 수집
        for sheet_name, data in self.all_data.items():
            df = pd.DataFrame(data)
            col_employee_id = self._find_column(df, '사원번호')
            if col_employee_id:
                ids = set(self._normalize_employee_id(eid) for eid in df[col_employee_id].dropna() if self._normalize_employee_id(eid))
                if "재직자" in sheet_name and "기타장기" not in sheet_name:
                    active_employee_ids.update(ids)
                elif "퇴직자" in sheet_name:
                    retired_employee_ids.update(ids)
        
        # 2. 명부 간 교차 중복 체크
        duplicates = active_employee_ids & retired_employee_ids
        if duplicates:
            for sheet_name in self.all_data.keys():
                if ("재직자" in sheet_name and "기타장기" not in sheet_name) or "퇴직자" in sheet_name:
                    if sheet_name not in structured_results: structured_results[sheet_name] = {}
                    if "명부 간 중복" not in structured_results[sheet_name]: structured_results[sheet_name]["명부 간 중복"] = []
                    for dup_id in sorted(duplicates):
                        structured_results[sheet_name]["명부 간 중복"].append({"emp_id": dup_id, "detail": "재직자명부와 퇴직자명부에 모두 존재"})

        # 3. 각 시트별 검증 실행
        for sheet_name, data in self.all_data.items():
            if sheet_name not in structured_results: structured_results[sheet_name] = {}
            
            errors = []
            if "재직자" in sheet_name and "기타장기" not in sheet_name:
                errors = self._validate_active_employees(sheet_name, data)
            elif "퇴직자" in sheet_name:
                errors = self._validate_retired_employees(sheet_name, data)
            elif "추가" in sheet_name or "중간정산" in sheet_name:
                errors = self._validate_additional_employees(sheet_name, data, active_employee_ids, retired_employee_ids)
            elif "기초자료" in sheet_name and "퇴직급여" in sheet_name:
                errors = self._validate_retirement_benefit_summary(sheet_name, data)
            
            # 카테고리별로 묶기
            for err in errors:
                cat = err["category"]
                if cat not in structured_results[sheet_name]:
                    structured_results[sheet_name][cat] = []
                structured_results[sheet_name][cat].append({
                    "emp_id": err["emp_id"],
                    "detail": err["detail"]
                })
        
        return structured_results

