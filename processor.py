import pandas as pd
import abc

class SheetProcessor(metaclass=abc.ABCMeta):
    """
    각 시트별 처리 로직의 기본이 되는 추상 클래스
    """
    def __init__(self, sheet_name, df):
        self.sheet_name = sheet_name
        self.raw_df = df
        self.header_keywords = [] # 추출(Extract) 시 사용할 키워드
        self.schema_map = {}      # 변환(Parse) 시 사용할 스키마

    def process(self):
        # 3. 청소 (Clean) -> 4. 추출 (Extract) -> 5. 변환 (Parse) 순서로 실행
        df = self.clean(self.raw_df)
        df = self.extract(df)
        data = self.parse(df)
        return data

    def _refine_data(self, df):
        """
        데이터프레임의 타입을 정리 (NaN 처리, 날짜 변환 등)
        """
        # '참고사항' 컬럼 제거
        cols_to_drop = [col for col in df.columns if "참고사항" in str(col)]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)

        # 0. 데이터가 없는 행 제거 (모든 열이 NaN인 경우)
        df = df.dropna(how='all')

        # 1. 핵심 데이터(앞쪽 3개 컬럼 중 하나라도 데이터가 있는 경우)만 유지
        # 중간정산액 합계 등 앞쪽 정보가 비어있는 불필요한 행 제거
        if not df.empty:
            cols_to_check = df.columns[:min(3, len(df.columns))]
            df = df.dropna(subset=cols_to_check, how='all')

        # 2. 날짜형 컬럼 처리 (Timestamp -> YYYYMMDD 문자열)
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%Y%m%d')
        
        # 3. NaN(빈칸) 처리 -> None으로 변환
        df = df.where(pd.notnull(df), None)
        
        return df.reset_index(drop=True)

    def _make_columns_unique(self, columns):
        """
        중복된 컬럼 이름이 있을 경우 유니크하게 변경 (예: 항목, 항목.1, 항목.2)
        """
        new_columns = []
        counts = {}
        for col in columns:
            col_str = str(col)
            if col_str in counts:
                counts[col_str] += 1
                new_columns.append(f"{col_str}.{counts[col_str]}")
            else:
                counts[col_str] = 0
                new_columns.append(col_str)
        return new_columns

    @abc.abstractmethod
    def clean(self, df):
        """상단 비고란, 의미 없는 빈 행 삭제"""
        pass

    @abc.abstractmethod
    def extract(self, df):
        """header_keywords를 이용해 실제 데이터 시작 지점 포착"""
        pass

    @abc.abstractmethod
    def parse(self, df):
        """schema_map을 기준으로 JSON 객체 리스트로 변환"""
        pass

class EmployeeProcessor(SheetProcessor):
    def __init__(self, sheet_name, df):
        super().__init__(sheet_name, df)
        # 이미지에 기반한 핵심 키워드들
        self.header_keywords = ["사원번호", "생년월일", "입사일자", "성별"]

    def clean(self, df):
        # 모든 행이 비어있는 경우 제거
        return df.dropna(how='all').reset_index(drop=True)

    def extract(self, df):
        """
        '사원번호' 등이 2개 이상 포함된 행을 찾아 헤더로 설정
        """
        header_row_idx = -1
        
        # 행을 하나씩 돌면서 키워드가 있는지 확인
        for i, row in df.iterrows():
            row_str = " ".join(row.astype(str))
            # 키워드 중 2개 이상이 한 행에 존재할 때만 진짜 헤더로 간주
            match_count = sum(1 for keyword in self.header_keywords if keyword in row_str)
            if match_count >= 2: 
                header_row_idx = i
                break
        
        if header_row_idx != -1:
            # 헤더를 찾은 행을 컬럼명으로 설정
            new_header = df.iloc[header_row_idx].fillna("Unnamed").tolist()
            # 중복 컬럼 이름 유니크하게 처리
            new_header = self._make_columns_unique(new_header)
            
            df = df.iloc[header_row_idx + 1:].copy()
            df.columns = new_header
            # 인덱스 재설정 및 빈 행 제거
            df = df.dropna(how='all').reset_index(drop=True)
        
        return df

    def parse(self, df):
        # 데이터 타입 정제 후 JSON 변환
        df = self._refine_data(df)
        return df.to_dict(orient='records')

class RetireeProcessor(SheetProcessor):
    def __init__(self, sheet_name, df):
        super().__init__(sheet_name, df)
        # 퇴직자명부용 핵심 키워드
        self.header_keywords = ["사원번호", "입사일자", "퇴직일", "DC전환", "사유"]

    def clean(self, df):
        return df.dropna(how='all').reset_index(drop=True)

    def extract(self, df):
        header_row_idx = -1
        for i, row in df.iterrows():
            row_str = " ".join(row.astype(str))
            # 키워드 중 2개 이상이 한 행에 존재할 때만 진짜 헤더로 간주
            match_count = sum(1 for keyword in self.header_keywords if keyword in row_str)
            if match_count >= 2: 
                header_row_idx = i
                break
        
        if header_row_idx != -1:
            new_header = df.iloc[header_row_idx].fillna("Unnamed").tolist()
            df = df.iloc[header_row_idx + 1:].copy()
            df.columns = new_header
            df = df.dropna(how='all').reset_index(drop=True)
        
        return df

    def parse(self, df):
        # 데이터 타입 정제 후 JSON 변환
        df = self._refine_data(df)
        return df.to_dict(orient='records')

class LongServiceProcessor(SheetProcessor):
    def __init__(self, sheet_name, df):
        super().__init__(sheet_name, df)
        # 장기근속/추가명부용 핵심 키워드
        self.header_keywords = ["사원번호", "사유발생일", "발생금액", "직무그룹"]

    def clean(self, df):
        return df.dropna(how='all').reset_index(drop=True)

    def extract(self, df):
        header_row_idx = -1
        for i, row in df.iterrows():
            row_str = " ".join(row.astype(str))
            # 키워드 중 2개 이상이 한 행에 존재할 때만 진짜 헤더로 간주
            match_count = sum(1 for keyword in self.header_keywords if keyword in row_str)
            if match_count >= 2: 
                header_row_idx = i
                break
        
        if header_row_idx != -1:
            new_header = df.iloc[header_row_idx].fillna("Unnamed").tolist()
            df = df.iloc[header_row_idx + 1:].copy()
            df.columns = new_header
            df = df.dropna(how='all').reset_index(drop=True)
        
        return df

    def parse(self, df):
        # 데이터 타입 정제 후 JSON 변환
        df = self._refine_data(df)
        return df.to_dict(orient='records')

class OtherLongServiceProcessor(SheetProcessor):
    def __init__(self, sheet_name, df):
        super().__init__(sheet_name, df)
        # 기타장기재직자명부용 핵심 키워드
        self.header_keywords = ["사원번호", "생년월일", "기준급여", "종업원 구분"]

    def clean(self, df):
        return df.dropna(how='all').reset_index(drop=True)

    def extract(self, df):
        header_row_idx = -1
        for i, row in df.iterrows():
            row_str = " ".join(row.astype(str))
            # 키워드 중 2개 이상이 한 행에 존재할 때만 진짜 헤더로 간주
            match_count = sum(1 for keyword in self.header_keywords if keyword in row_str)
            if match_count >= 2: 
                header_row_idx = i
                break
        
        if header_row_idx != -1:
            new_header = df.iloc[header_row_idx].fillna("Unnamed").tolist()
            df = df.iloc[header_row_idx + 1:].copy()
            df.columns = new_header
            df = df.dropna(how='all').reset_index(drop=True)
        
        return df

    def parse(self, df):
        # 데이터 타입 정제 후 JSON 변환
        df = self._refine_data(df)
        return df.to_dict(orient='records')

class RetirementBenefitProcessor(SheetProcessor):
    def __init__(self, sheet_name, df):
        super().__init__(sheet_name, df)

    def process(self):
        """
        양식 형태의 시트에서 특정 좌표(Cell)의 값만 추출
        I29 : 재직자수 합계
        I33 : 퇴직자수 합계
        I39 : 퇴직금 추계액 합계

        추가 추출 항목:
        F103 : 정년퇴직연령
        F104 : 임금피크제 (YES or NO)
        F109 : 제도구분
        I112 : 연봉제 or 호봉제
        E113-I118 : 임금상승률
        D121 : 할인율 산출기준
        """
        try:
            # Excel 좌표 -> Pandas iloc 변환 (header=0 가정 시 Row N은 Index N-2)
            # Column F=5, I=8, E=4, D=3
            
            def safe_get(r, c):
                if r < len(self.raw_df) and c < len(self.raw_df.columns):
                    val = self.raw_df.iloc[r, c]
                    # NaN이나 NaT는 None으로 변환
                    if pd.isna(val):
                        return None
                    return val
                return None

            # 임금상승률 (E113-F118) 추출: 연도와 값만 추출
            wage_growth_rates = []
            for r in range(111, 117): # Row 113 to 118 (Index 111-116)
                year = safe_get(r, 4)  # Column E (Index 4)
                rate = safe_get(r, 5)  # Column F (Index 5)
                if year is not None or rate is not None:
                    # 0.0% 같은 백분율 처리
                    if isinstance(rate, (float, int)):
                        rate_str = f"{rate * 100:.1f}%" if rate < 1 else f"{rate:.1f}%"
                    else:
                        rate_str = str(rate) if rate else "-"
                    
                    wage_growth_rates.append({
                        "연도": str(year) if year else "-",
                        "상승률": rate_str
                    })

            data = {
                "구분": "기초자료_요약",
                "재직자수_합계": safe_get(27, 8),      # I29 (Index 27, 8)
                "퇴직자수_합계": safe_get(31, 8),      # I33 (Index 31, 8)
                "퇴직금_추계액_합계": safe_get(37, 8), # I39 (Index 37, 8)
                "정년퇴직연령": safe_get(101, 5),      # F103 (Index 101, 5)
                "임금피크제": safe_get(102, 5),        # F104 (Index 102, 5)
                "제도구분": safe_get(107, 5),          # F109 (Index 107, 5)
                "연봉제_호봉제": safe_get(110, 8),      # I112 (Index 110, 8)
                "임금상승률": wage_growth_rates,       # 리스트 객체
                "할인율_산출기준": safe_get(119, 3)     # D121 (Index 119, 3)
            }
            # 다른 프로세서들과 형식을 맞추기 위해 리스트에 담아 반환
            return [data]
        except Exception as e:
            print(f"Error extracting coordinate data from {self.sheet_name}: {e}")
            return []

    def clean(self, df): return df
    def extract(self, df): return df
    def parse(self, df): return df

class SalaryProcessor(SheetProcessor):
    def clean(self, df):
        # 급여 대장 특화 청소 로직 (구체적 구현은 추후)
        return df

    def extract(self, df):
        # 키워드 기반 헤더 찾기 (구체적 구현은 추후)
        return df

    def parse(self, df):
        # 데이터 타입 정제 후 JSON 변환
        df = self._refine_data(df)
        return df.to_dict(orient='records')

class ExcelProcessor:
    def __init__(self, file):
        self.file = file

    def process(self):
        # 1. 로드 (Load): 모든 시트를 날것으로 가져옴 (sheet_name=None)
        all_sheets = pd.read_excel(self.file, sheet_name=None)
        
        results = {}
        for sheet_name, df in all_sheets.items():
            # 2. 매칭 (Match): 시트 이름에 따라 프로세서 결정
            processor = self._get_processor(sheet_name, df)
            
            if processor:
                # 3, 4, 5 단계 실행 (Clean, Extract, Parse)
                results[sheet_name] = processor.process()
        
        return results

    def _get_processor(self, sheet_name, df):
        # 번호는 달라질 수 있으므로 고정된 '이름' 키워드로 매칭
        # (2-1) 명부 작성방법 등 불필요한 시트는 매칭되지 않음
        
        name = sheet_name.replace(" ", "").lower() # 공백 제거 및 소문자 변환 추가

        # 시스템용/원본 시트는 무시 (이름에 시스템, input, 원본 등이 포함된 경우)
        if any(x in name for x in ["시스템", "input", "원본", "작성방법"]):
            return None

        if "기초자료" in name and "퇴직급여" in name:
            return RetirementBenefitProcessor(sheet_name, df)
        elif "기타장기재직자명부" in name:
            return OtherLongServiceProcessor(sheet_name, df)
        elif "재직자명부" in name:
            return EmployeeProcessor(sheet_name, df)
        elif "퇴직자및dc전환자명부" in name:
            return RetireeProcessor(sheet_name, df)
        elif "추가명부" in name:
            return LongServiceProcessor(sheet_name, df)
            
        return None
