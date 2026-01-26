import openai
import pandas as pd

class AIAnalyzer:
    """
    K-IFRS 1019 지식을 활용하여 명부 데이터의 맥락적 오류를 분석하는 클래스
    """
    def __init__(self, api_key):
        self.client = openai.OpenAI(api_key=api_key)

    def analyze(self, processed_data, base_date, calculation_method):
        """
        GPT-4o를 이용한 맥락적 분석 수행
        """
        # 데이터 요약 생성 로직 (추후 구현 가능)
        summary_text = self._generate_summary(processed_data)
        
        system_prompt = f"""
        당신은 K-IFRS 1019(종업원 급여) 퇴직급여 평가 전문가입니다.
        제공된 명부 데이터를 분석하여 회계적/논리적 모순이 있는지 검토하세요.
        - 기준일: {base_date}
        - 계산방법: {calculation_method}
        """
        
        user_prompt = f"다음은 정제된 명부 데이터의 요약입니다:\n\n{summary_text}\n\n분석 결과를 보고해 주세요."

        # 실제 API 호출 부분 (틀만 유지)
        # response = self.client.chat.completions.create(
        #     model="gpt-4o",
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": user_prompt}
        #     ]
        # )
        # return response.choices[0].message.content
        return "AI 분석 기능의 틀이 준비되었습니다. (실제 API 호출은 주석 처리됨)"

    def _generate_summary(self, processed_data):
        """
        AI가 이해하기 쉽게 데이터를 텍스트 형태로 요약
        """
        summary = ""
        for sheet_name, data in processed_data.items():
            df = pd.DataFrame(data)
            summary += f"\n[시트: {sheet_name}] (총 {len(df)}행)\n"
            summary += f"컬럼: {', '.join(df.columns)}\n"
        return summary

