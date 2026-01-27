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

    def validate(self):
        """
        데이터 검증을 수행하고 오류 목록을 반환합니다.
        """
        results = []
        
        # 여기에 검증 규칙을 추가하세요
        
        return results

