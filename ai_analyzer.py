import openai
import pandas as pd

class AIAnalyzer:
    """
    K-IFRS 1019 지식을 활용하여 명부 데이터의 맥락적 오류를 분석하는 클래스
    """
    def __init__(self, api_key):
        self.client = openai.OpenAI(api_key=api_key)

    def analyze(self, processed_data, validation_results, base_date, calculation_method):
        """
        AI 분석 로직 (프롬프트 및 구성은 추후 결정)
        """
        # 현재는 입력 데이터가 잘 전달되는지만 확인하는 용도
        summary_text = self._generate_summary(processed_data)
        validation_text = self._generate_validation_summary(validation_results)
        
        system_prompt = "당신은 퇴직급여 평가 전문가입니다. 데이터를 분석할 준비가 되었습니다."
        
        user_prompt = f"""
        데이터가 입력되었습니다. (프롬프트 구성 대기 중)
        - 기준일: {base_date}
        - 계산방법: {calculation_method}
        - 시트 수: {len(processed_data)}
        """

        try:
            # 추후 프롬프트 확정 시 실제 호출 로직 구현
            return "AI 분석 로직 및 프롬프트 구성 대기 중입니다. (데이터 전달 확인 완료)"
        except Exception as e:
            return f"AI 분석 중 오류가 발생했습니다: {str(e)}"

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI 분석 중 오류가 발생했습니다: {str(e)}"

    def _generate_validation_summary(self, validation_results):
        """
        규칙 기반 검증 결과를 AI가 이해하기 쉽게 요약
        """
        if not validation_results:
            return "시스템 검증 결과 발견된 명시적 규칙 위반 사항이 없습니다."
        
        summary = ""
        for sheet_name, results in validation_results.items():
            summary += f"\n- 시트: {sheet_name}\n"
            for category, items in results.items():
                summary += f"  * {category}: {len(items)}건 발견\n"
                # 너무 많으면 상위 3건만 예시로 제공
                for item in items[:3]:
                    summary += f"    > (사원번호: {item[0]}) {item[1]}\n"
                if len(items) > 3:
                    summary += f"    > ... 외 {len(items)-3}건 더 있음\n"
        return summary

    def _generate_summary(self, processed_data):
        """
        AI가 이해하기 쉽게 데이터를 텍스트 형태로 요약 (통계 정보 및 샘플 포함)
        """
        summary = ""
        for sheet_name, data in processed_data.items():
            df = pd.DataFrame(data)
            summary += f"\n### 시트: {sheet_name}\n"
            summary += f"- 총 행 수: {len(df)}개\n"
            summary += f"- 주요 컬럼: {', '.join(df.columns)}\n"
            
            # 수치형 데이터 통계 (급여, 추계액 등)
            numeric_cols = df.select_dtypes(include=['number']).columns
            if not numeric_cols.empty:
                summary += "- 수치 데이터 요약:\n"
                for col in numeric_cols:
                    summary += f"  * {col}: 평균 {df[col].mean():,.0f}, 최소 {df[col].min():,.0f}, 최대 {df[col].max():,.0f}\n"
            
            # 날짜 데이터 범위
            date_keywords = ['입사', '생년', '퇴직', '일자', '날짜']
            for col in df.columns:
                if any(k in str(col) for k in date_keywords):
                    # 문자열로 된 날짜를 처리하기 위해 시도
                    try:
                        temp_dates = pd.to_datetime(df[col], errors='coerce').dropna()
                        if not temp_dates.empty:
                            summary += f"  * {col} 범위: {temp_dates.min().date()} ~ {temp_dates.max().date()}\n"
                    except:
                        pass
            
            # 데이터 샘플 (최대 5행)
            summary += "- 데이터 샘플 (상위 5행):\n"
            try:
                summary += df.head(5).to_markdown(index=False) + "\n"
            except ImportError:
                # tabulate가 없는 경우 간단한 텍스트로 대체
                summary += df.head(5).to_string(index=False) + "\n"
            
        return summary

