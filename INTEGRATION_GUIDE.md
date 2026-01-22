# 프론트엔드 + 백엔드 실행 가이드

## 1. 백엔드 실행

### 터미널 1 (백엔드)
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

백엔드 서버가 `http://localhost:8000`에서 실행됩니다.

## 2. 프론트엔드 실행

### 터미널 2 (프론트엔드)
```powershell
cd frontend
npm install
npm run dev
```

프론트엔드가 `http://localhost:3000`에서 실행됩니다.

## 3. 사용 방법

1. 브라우저에서 `http://localhost:3000` 접속
2. 엑셀 파일 업로드 (명부 파일)
3. "검증 시작하기" 클릭
4. 검증 결과 확인:
   - **요약 리포트**: 각 시트별로 확인이 필요한 사항
   - **통계**: 총 데이터, 정상 데이터, 오류, 경고 수
   - **오류 목록**: 반드시 수정해야 하는 항목들
   - **경고 목록**: 확인이 권장되는 항목들

## 4. API 엔드포인트

- `POST /api/validate` - 파일 업로드 및 검증
- `GET /health` - 서버 상태 확인

## 5. 검증 결과 구조

```json
{
  "message": "검증이 완료되었습니다",
  "filename": "명부.xlsx",
  "validation_results": {
    "total_records": 150,
    "valid_records": 146,
    "invalid_records": 4,
    "errors": [
      {
        "sheet": "재직자명부",
        "row": 12,
        "column": "emp_id",
        "emp_id": "123456",
        "type": "required_field_missing",
        "message": "필수 필드 '사원번호'가 비어있습니다",
        "severity": "error"
      }
    ],
    "warnings": [
      {
        "sheet": "재직자명부",
        "row": 45,
        "column": "base_salary",
        "emp_id": "789012",
        "type": "low_salary",
        "message": "기준급여가 최저임금보다 낮습니다",
        "severity": "warning"
      }
    ],
    "summary_report": [
      "'재직자명부' 시트에서 [필수 필드 '사원번호'가 비어있습니다] 등을 확인해 주세요.",
      "'퇴직자명부' 시트에서 [퇴직일자가 입사일자보다 빠릅니다] 등을 확인해 주세요."
    ]
  }
}
```

## 6. 주요 기능

### ✅ 1차 검증 (하드코딩 규칙)
- 필수 필드 검증
- 수치 범위 검증
- 날짜 유효성 검증
- 논리적 일관성 검증
- 시트 간 교차 검증

### ✅ 2차 검증 (K-IFRS 1019 AI 맥락)
- 급여 대비 추계액 적정성
- 연령 대비 근속연수 논리성
- 퇴직금액 범위 검증

### ✅ 검증 리포트
- 시트별 확인 사항 요약
- 오류/경고 구분
- 상세 오류 정보 제공


