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

    def _parse_date(self, date_val):
        """다양한 형식의 날짜를 datetime 객체로 변환"""
        if pd.isna(date_val) or date_val is None:
            return None
        try:
            s_date = str(date_val).strip().replace(".0", "")
            if len(s_date) == 8: # YYYYMMDD
                return datetime.strptime(s_date, "%Y%m%d")
            elif len(s_date) == 6: # YYMMDD (이미지 예시 251231 등)
                year = int(s_date[:2])
                year += 2000 if year < 50 else 1900
                return datetime.strptime(f"{year}{s_date[2:]}", "%Y%m%d")
            return pd.to_datetime(date_val)
        except:
            return None

    def _check_date_validity(self, date_val, label, row_info):
        """월 > 12 또는 일 > 31 체크"""
        if pd.isna(date_val) or date_val is None:
            return None
        
        s_date = str(date_val).strip().replace(".0", "")
        if len(s_date) >= 6:
            # 뒷부분 4자리 추출 (MMDD)
            mmdd = s_date[-4:]
            mm = int(mmdd[:2])
            dd = int(mmdd[2:])
            if mm > 12 or dd > 31:
                return f"[{label}] 날짜 형식 오류 (월:{mm}, 일:{dd})"
        return None

    def validate(self):
        results = []
        
        for sheet_name, data in self.all_data.items():
            # 기초자료 요약 시트는 별도 룰이 생기기 전까지 개별 행 검증 제외
            if "기초자료" in sheet_name:
                continue

            df = pd.DataFrame(data)
            for idx, row in df.iterrows():
                row_id = row.get('사원번호', f"Row {idx+1}")
                ctx = f"[{sheet_name} | {row_id}]"

                # 13. 필수값 누락 체크 (사원번호, 생년월일, 입사일자, 기준급여, 종업원 구분)
                for col in ['사원번호', '생년월일', '입사일자', '기준급여', '종업원 구분']:
                    val = row.get(col)
                    if pd.isna(val) or val is None or str(val).strip() == "":
                        results.append(f"{ctx} 필수값 누락: {col}")

                # 1-3. 음수 체크 (추계액, 중간정산액)
                for col in ['당년도 퇴직금추계액', '차년도 퇴직금추계액', '발생금액']:
                    val = row.get(col)
                    if val is not None and isinstance(val, (int, float)) and val < 0:
                        results.append(f"{ctx} {col} 음수 발생: {val}")

                # 14-16. 직종(종업원 구분) 관련 조건부 체크
                job_type = row.get('종업원 구분')
                try:
                    # 직종이 숫자로 들어올 경우 처리
                    job_type_num = float(job_type) if job_type is not None else 0
                except:
                    job_type_num = 0

                if job_type_num > 2:
                    curr_est = row.get('당년도 퇴직금추계액')
                    next_est = row.get('차년도 퇴직금추계액')
                    
                    # 당년도 < 차년도 체크 (이미지: if 직종>2, 당년도퇴직금 < 차년도퇴직금)
                    if curr_est is not None and next_est is not None:
                        if not (curr_est < next_est):
                            results.append(f"{ctx} 직종 {job_type} 오류: 당년도 추계액({curr_est:,.0f})이 차년도({next_est:,.0f})보다 크거나 같음")
                    
                    # 당년도/차년도 추계액 blank or 0 체크
                    if pd.isna(curr_est) or curr_est is None or curr_est == 0:
                        results.append(f"{ctx} 직종 {job_type} 오류: 당년도 추계액 누락 또는 0")
                    if pd.isna(next_est) or next_est is None or next_est == 0:
                        results.append(f"{ctx} 직종 {job_type} 오류: 차년도 추계액 누락 또는 0")

                # 날짜 변환
                birth_date = self._parse_date(row.get('생년월일'))
                join_date = self._parse_date(row.get('입사일자'))
                interim_date = self._parse_date(row.get('사유발생일')) # 중간정산일 등

                # 4-5. 입사 관련 체크
                if birth_date and join_date:
                    # 입사연령 체크
                    age_at_join = join_date.year - birth_date.year
                    if age_at_join < 17 or age_at_join > 70:
                        results.append(f"{ctx} 입사연령 이상: {age_at_join}세 (입사일:{join_date.date()}, 생년:{birth_date.year})")
                    
                    # 입사일 < 생년월일
                    if join_date < birth_date:
                        results.append(f"{ctx} 입사일이 생년월일보다 빠름: {join_date.date()} < {birth_date.date()}")

                # 6. 중간정산일 <= 입사일
                if interim_date and join_date:
                    if interim_date <= join_date:
                        results.append(f"{ctx} 중간정산일이 입사일보다 빠르거나 같음: {interim_date.date()} <= {join_date.date()}")

                # 7-8. 시산일(기준일) 관련 체크
                if join_date and self.base_date:
                    if self.base_date <= join_date:
                        results.append(f"{ctx} 기준일이 입사일보다 빠르거나 같음 (검증 필요): {self.base_date.date()} <= {join_date.date()}")
                
                if interim_date and self.base_date:
                    if self.base_date <= interim_date:
                        results.append(f"{ctx} 기준일이 중간정산일보다 빠르거나 같음: {self.base_date.date()} <= {interim_date.date()}")

                # 9-11. 월/일 유효성 체크
                for col, label in [('생년월일', '생년월일'), ('입사일자', '입사일'), ('사유발생일', '중간정산일')]:
                    err = self._check_date_validity(row.get(col), label, row)
                    if err:
                        results.append(f"{ctx} {err}")

                # 12. 기준급여 < 1,700,000
                salary = row.get('기준급여')
                if salary is not None and isinstance(salary, (int, float)) and salary < 1700000:
                    results.append(f"{ctx} 기준급여 170만 미만: {salary:,.0f}원")
        
        return results

