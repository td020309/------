import openai
import pandas as pd
import json

class AIAnalyzer:
    """
    K-IFRS 1019 및 퇴직급여 평가 지식을 활용하여 명부 데이터의 맥락적 오류를 분석하는 클래스
    """
    def __init__(self, api_key):
        self.client = openai.OpenAI(api_key=api_key)

    def analyze(self, processed_data, validation_results, base_date, calculation_method):
        """
        AI를 통한 심층 데이터 분석 수행
        """
        # 1. 기초 설정 정보(Summary) 추출
        summary_info = self._extract_summary_info(processed_data)
        
        # 2. 규칙 기반 검증 결과 요약
        validation_text = self._generate_validation_summary(validation_results)
        
        # 3. 데이터 통계 및 샘플 요약
        data_summary_text = self._generate_data_summary(processed_data, base_date, summary_info)
        
        system_prompt = """당신은 대한민국 최고의 보험계리사이며 K-IFRS 1019 퇴직급여 평가 전문가입니다.
당신의 임무는 '시스템이 규칙 기반으로 잡은 단순 오류'를 넘어, 데이터 간의 '맥락적 모순'과 '계리적 리스크'를 찾아내는 것입니다.
제공된 기초 설정 정보와 명부 데이터를 비교하여, 부채 평가 결과에 심각한 왜곡을 줄 수 있는 잠재적 오류를 지적하세요.

보고서는 매우 '구체적'이어야 합니다. 다음 원칙을 반드시 지키세요:
1. **추상적인 설명 금지**: "일부 사원의 급여가 이상합니다" 대신 "사원번호 12345, 67890의 경우 직종 대비 급여가 현저히 낮아 확인이 필요합니다"와 같이 특정 사원을 짚어주세요.
2. **이유 명시**: 왜 그 데이터가 리스크인지 계리적/논리적 근거를 설명하세요. (예: 임금피크제 적용 연령임에도 급여가 상승함)
3. **증거 제시**: 분석에 사용한 구체적인 데이터 수치나 패턴을 예시로 드세요."""

        user_prompt = f"""
### [1. 평가 환경 및 기초 설정 정보]
- 검증기준일: {base_date}
- 계산방법(단수처리): {calculation_method}
- 정년퇴직연령: {summary_info.get('정년퇴직연령', '정보없음')}
- 임금피크제 여부: {summary_info.get('임금피크제', '정보없음')}
- 제도구분: {summary_info.get('제도구분', '정보없음')}
- 임금상승률(Base-up): {json.dumps(summary_info.get('임금상승률', []), ensure_ascii=False)}

### [2. 시스템 규칙 검증 결과 (이미 발견된 오류)]
{validation_text}
※ 위 오류들은 이미 시스템이 식별했으므로, 보고서에서는 이와 중복되지 않는 '새로운 맥락적 모순'에 집중하세요.

### [3. 명부 데이터 분석용 상세 정보 및 샘플]
{data_summary_text}

### [4. 분석 요청 사항 (구체적인 사례 위주로 작성)]
다음 항목들을 중점적으로 검토하여 '전문가적 의심'이 드는 부분을 지적해 주세요. **반드시 사원번호(ID)를 포함한 구체적 예시를 2-3개씩 포함하세요.**

1. **임금피크제 적용 적정성:** 정년(예: 60세)에 근접한 사원들 중 급여가 삭감되지 않았거나 오히려 크게 오른 구체적인 사례는?
2. **추계액 변동 및 급여 정합성:** 당년도와 차년도 추계액 차이가 근속 1년 증가분 및 임금상승률에 비해 비정상적으로 큰 사례(급격한 급여 변동 등)는?
3. **중간정산 및 근속 기간 모순:** 중간정산일이 있음에도 추계액이 입사일부터 전 기간을 반영한 것처럼 과다하게 산출된 사례는?
4. **급여 이상치 (최저임금/고액급여):** 직종/연령 대비 급여가 비상식적으로 높거나 낮은 구체적인 사례는?
5. **데이터 가공 의심 패턴:** 입사일, 생년월일 등이 특정 날짜로 편중되어 데이터의 신뢰도가 의심되는 정황은?

분석 결과는 '발견된 잠재 리스크'와 '데이터 확인 요청'으로 구분하여 한국어로 전문성 있게 작성해 주세요. 각 리스크마다 **[확인 필요 대상: 사번 000, 000]** 형식으로 대상을 명확히 짚어주세요.
"""

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

    def _extract_summary_info(self, processed_data):
        """기초자료 시트에서 설정 정보 추출"""
        for sheet_name, data in processed_data.items():
            if "기초자료" in sheet_name and "퇴직급여" in sheet_name:
                if data and len(data) > 0:
                    return data[0]
        return {}

    def _generate_validation_summary(self, validation_results):
        """규칙 검증 결과를 텍스트로 요약"""
        if not validation_results:
            return "- 발견된 명시적 규칙 위반 사항이 없습니다."
        
        summary = ""
        for sheet_name, categories in validation_results.items():
            if not isinstance(categories, dict): continue
            
            # 실제 오류가 있는 카테고리만 필터링
            active_categories = {cat: items for cat, items in categories.items() if items}
            
            if active_categories:
                summary += f"\n- [{sheet_name}] 시트:\n"
                for cat, items in active_categories.items():
                    summary += f"  * {cat}: {len(items)}건 발견\n"
                    for item in items[:2]:
                        # 모든 데이터 타입을 안전하게 처리 (딕셔너리, 리스트 등)
                        emp_id = "Unknown"
                        detail = "No detail"
                        
                        if isinstance(item, dict):
                            emp_id = item.get('emp_id', item.get('사원번호', 'Unknown'))
                            detail = item.get('detail', item.get('상세내용', 'No detail'))
                        elif isinstance(item, (list, tuple)) and len(item) >= 2:
                            emp_id = item[0]
                            detail = item[1]
                        
                        summary += f"    > (ID: {emp_id}) {detail}\n"
        
        return summary if summary else "- 발견된 명시적 규칙 위반 사항이 없습니다."

    def _generate_data_summary(self, processed_data, base_date, summary_info=None):
        """데이터 통계 및 다각도 샘플링 요약 (AI가 구체적 사례를 찾을 수 있도록)"""
        summary = ""
        retirement_age = 60
        if summary_info and '정년퇴직연령' in summary_info:
            try: retirement_age = int(str(summary_info['정년퇴직연령']).replace("세", ""))
            except: pass

        for sheet_name, data in processed_data.items():
            if any(k in sheet_name for k in ["기초자료", "방법"]): continue
            
            df = pd.DataFrame(data)
            if df.empty: continue
            
            summary += f"\n#### 시트: {sheet_name} (총 {len(df)}명)\n"
            
            # 1. 수치형 데이터 통계
            numeric_cols = df.select_dtypes(include=['number']).columns
            for col in numeric_cols:
                if any(k in str(col) for k in ['급여', '추계액', '정산액']):
                    try:
                        val_sum = df[col].sum()
                        val_avg = df[col].mean()
                        summary += f"- {col}: 합계 {val_sum:,.0f}원, 평균 {val_avg:,.0f}원\n"
                    except: pass
            
            # 2. 날짜 범위
            for col in df.columns:
                if any(k in str(col) for k in ['입사', '생년', '정산', '일자']):
                    try:
                        temp_dates = pd.to_datetime(df[col], errors='coerce').dropna()
                        if not temp_dates.empty:
                            summary += f"- {col} 범위: {temp_dates.min().date()} ~ {temp_dates.max().date()}\n"
                    except: pass

            # 3. 전략적 샘플링 (AI에게 줄 구체적 사례 후보군)
            important_keywords = ['사번', '사원번호', '성별', '입사', '생년', '급여', '추계액', '정산', '당년도', '차년도']
            sample_cols = [c for c in df.columns if any(k in str(c) for k in important_keywords)]
            if not sample_cols: continue
            
            actual_cols = [c for c in sample_cols if c in df.columns]
            samples = []

            # (1) 상위/하위 급여 및 추계액
            for col in numeric_cols:
                if '급여' in str(col) or '추계액' in str(col):
                    samples.append(df.nlargest(3, col))
                    samples.append(df.nsmallest(3, col))
            
            # (2) 정년 근접자 (임금피크제 확인용)
            birth_col = next((c for c in df.columns if '생년' in str(c)), None)
            if birth_col:
                base_year = pd.to_datetime(base_date).year
                df['_temp_age'] = pd.to_datetime(df[birth_col], errors='coerce').apply(lambda x: base_year - x.year if pd.notnull(x) else 0)
                samples.append(df[df['_temp_age'] >= (retirement_age - 2)].head(5))

            # (3) 추계액 변동폭 큰 케이스
            curr_col = next((c for c in df.columns if '당년도' in str(c)), None)
            next_col = next((c for c in df.columns if '차년도' in str(c)), None)
            if curr_col and next_col:
                df['_temp_diff'] = (df[next_col] - df[curr_col]).abs()
                samples.append(df.nlargest(5, '_temp_diff'))

            # (4) 기본 샘플
            samples.append(df.head(10))
            
            # 중복 제거 및 결합
            combined_samples = pd.concat(samples).drop_duplicates().head(50)
            if '_temp_age' in combined_samples.columns: combined_samples = combined_samples.drop(columns=['_temp_age'])
            if '_temp_diff' in combined_samples.columns: combined_samples = combined_samples.drop(columns=['_temp_diff'])

            summary += "- 주요 분석 대상 데이터 샘플 (상세 분석용):\n"
            summary += combined_samples[actual_cols].to_string(index=False) + "\n"
            
        return summary
