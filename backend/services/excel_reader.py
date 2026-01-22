import pandas as pd
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class ExcelReader:
    """
    엑셀 파일을 읽고 필요한 시트를 추출하는 클래스
    """
    
    # 시트 이름과 키워드 매핑 (키워드로 유연하게 찾기)
    SHEET_KEYWORDS = {
        "재직자 명부": ["재직자", "명부"],
        "퇴직자 및 DC전환자 명부": ["퇴직자", "DC전환자", "명부"],
        "추가 명부(장기근속)": ["추가", "명부", "장기근속"],
        "기타장기 재직자 명부": ["기타장기"]  # "기타장기"로만 찾기 (재직자명부와 구분)
    }
    
    def __init__(self, file_path: str):
        """
        Args:
            file_path: 엑셀 파일 경로
        """
        self.file_path = file_path
        self.excel_file = None
        
    def read_all_sheets(self) -> Dict[str, pd.DataFrame]:
        """
        필요한 모든 시트를 읽어옵니다.
        
        Returns:
            Dict[str, pd.DataFrame]: 시트명을 키로, DataFrame을 값으로 하는 딕셔너리
        """
        try:
            # 엑셀 파일 읽기
            self.excel_file = pd.ExcelFile(self.file_path)
            available_sheets = self.excel_file.sheet_names
            
            logger.info(f"사용 가능한 시트 목록: {available_sheets}")
            
            sheets_data = {}
            
            # 키워드 기반으로 시트 찾기
            for standard_name, keywords in self.SHEET_KEYWORDS.items():
                found_sheet = self._find_sheet_by_keywords(standard_name, keywords, available_sheets)
                
                if found_sheet:
                    df = pd.read_excel(self.excel_file, sheet_name=found_sheet)
                    sheets_data[standard_name] = df
                    
                    # 실제 사원번호가 있는 행 수 계산
                    actual_count = self._count_valid_records(df)
                    logger.info(f"✅ 시트 '{found_sheet}' → '{standard_name}' 매핑 완료: {actual_count}명 (전체 {len(df)}행)")
                else:
                    # 기타장기 재직자 명부는 선택사항이므로 경고만
                    if "기타장기" in standard_name:
                        logger.info(f"ℹ️  선택사항 시트 '{standard_name}'를 찾을 수 없습니다 (건너뜀)")
                    else:
                        logger.warning(f"⚠️  필수 시트 '{standard_name}'를 찾을 수 없습니다")
            
            if not sheets_data:
                raise ValueError("필요한 시트를 찾을 수 없습니다. 사용 가능한 시트: " + ", ".join(available_sheets))
            
            return sheets_data
            
        except Exception as e:
            logger.error(f"❌ 엑셀 파일 읽기 오류: {str(e)}")
            raise
    
    def _find_sheet_by_keywords(self, standard_name: str, keywords: list, available_sheets: list) -> str:
        """
        키워드 기반으로 시트를 찾습니다.
        
        Args:
            standard_name: 표준 시트 이름
            keywords: 시트를 찾기 위한 키워드 목록
            available_sheets: 사용 가능한 시트 목록
            
        Returns:
            str: 찾은 시트 이름, 없으면 None
        """
        # 각 시트에 대해 키워드 매칭 점수 계산
        best_match = None
        best_score = 0
        
        for sheet in available_sheets:
            # 시트 이름 정규화 (공백 제거, 소문자 변환, 특수문자 제거)
            sheet_normalized = self._normalize_sheet_name(sheet)
            
            # 키워드 매칭 점수 계산
            score = 0
            for keyword in keywords:
                keyword_normalized = self._normalize_sheet_name(keyword)
                if keyword_normalized in sheet_normalized:
                    score += 1
            
            # 더 높은 점수를 가진 시트 선택
            if score > best_score:
                best_score = score
                best_match = sheet
        
        # 최소 키워드 개수 이상 매칭되면 반환
        min_keywords = max(1, len(keywords) - 1)  # 키워드 중 최소 1개 이상 매칭
        if best_score >= min_keywords:
            return best_match
        
        return None
    
    def _normalize_sheet_name(self, name: str) -> str:
        """
        시트 이름을 정규화합니다 (공백, 특수문자 제거, 소문자 변환).
        
        Args:
            name: 원본 시트 이름
            
        Returns:
            str: 정규화된 시트 이름
        """
        import re
        # 공백, 특수문자 제거 (한글, 영문, 숫자만 남김)
        normalized = re.sub(r'[^\w가-힣]', '', name)
        return normalized.lower()
    
    def _count_valid_records(self, df: pd.DataFrame) -> int:
        """
        사원번호가 있는 유효한 레코드 수를 계산합니다.
        
        Args:
            df: DataFrame
            
        Returns:
            int: 유효한 레코드 수
        """
        # 사원번호 컬럼 찾기
        emp_id_columns = [col for col in df.columns if '사원번호' in str(col) or 'employee' in str(col).lower()]
        
        if not emp_id_columns:
            # 사원번호 컬럼이 없으면 전체 행 수 반환
            return len(df)
        
        # 첫 번째 사원번호 컬럼 사용
        emp_col = emp_id_columns[0]
        
        # null이 아니고 빈 문자열이 아닌 행 개수
        valid_count = df[emp_col].notna().sum()
        
        # 빈 문자열도 제외
        if valid_count > 0:
            non_empty = df[emp_col].astype(str).str.strip().ne('').sum()
            valid_count = min(valid_count, non_empty)
        
        return valid_count
    
    def read_single_sheet(self, sheet_name: str) -> pd.DataFrame:
        """
        단일 시트를 읽어옵니다.
        
        Args:
            sheet_name: 시트 이름
            
        Returns:
            pd.DataFrame: 시트 데이터
        """
        try:
            if self.excel_file is None:
                self.excel_file = pd.ExcelFile(self.file_path)
            
            df = pd.read_excel(self.excel_file, sheet_name=sheet_name)
            logger.info(f"시트 '{sheet_name}' 읽기 완료: {len(df)}행")
            return df
            
        except Exception as e:
            logger.error(f"시트 '{sheet_name}' 읽기 오류: {str(e)}")
            raise

