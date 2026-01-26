class DataValidator:
    """
    데이터의 유효성을 검사하는 규칙(Rule) 엔진 클래스
    """
    def __init__(self, df, base_date, calculation_method):
        self.df = df
        self.base_date = base_date
        self.calculation_method = calculation_method

    def validate(self):
        # 데이터가 맞는지 틀리는지 검사하는 규칙 로직 (추후 구현)
        results = []
        return results

