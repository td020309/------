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
        # 데이터 요약 생성
        summary_text = self._generate_summary(processed_data)
        
        system_prompt = f"""
        당신은 K-IFRS 1019(종업원 급여) 퇴직급여 평가 전문가이자 계리사입니다.
        제공된 명부 데이터를 분석하여 회계적/논리적 모순이 있는지 검토하고, 퇴직부채 평가 시 발생할 수 있는 잠재적 리스크를 지적하세요.

        [K-IFRS 1019 검토 핵심 원칙]
        1. 데이터 일관성: 시트 간(재직자, 퇴직자, 중간정산자) 사원번호 중복이나 상태 모순 확인
        2. 급여의 합리성: 직급/연령 대비 급여 수준의 극단적 이상치, 혹은 평가 제외 대상 여부 판단
        3. 근무기간의 적정성: 입사일, 생년월일, 기준일 간의 관계 (아동노동, 정년 초과 등)
        4. DB/DC 구분: 명부 내 DC 전환자 정보가 있는 경우, DB 부채 평가 대상에서 제외되었는지 확인
        5. 평가 방법론: {calculation_method} 방식에 따른 일수 계산의 적정성 및 단수 처리 논리

        [분석 가이드라인]
        - 단순한 오타보다는 '회계적 영향'이 큰 사항을 우선순위로 보고하세요.
        - 통계적 이상치(Outlier)가 발견되면 구체적인 사원번호를 언급하세요.
        - 데이터 요약을 바탕으로 전체적인 데이터 품질 점수를 100점 만점으로 제시하세요.
        - 기준일({base_date})을 기준으로 모든 시점이 논리적인지 확인하세요.

        답변은 한국어로 작성하며, '분석 요약', '주요 리스크 및 오류', '권고사항'의 형식을 갖추어 주세요.
        """
        
        user_prompt = f"다음은 정제된 명부 데이터의 요약 정보입니다:\n\n{summary_text}\n\n위 원칙에 따라 정밀 분석 결과를 보고해 주세요."

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

