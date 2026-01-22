from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date

class ActiveEmployeeBase(BaseModel):
    """
    재직자 기본 정보 모델
    """
    emp_id: str = Field(..., description="사원번호")
    birth_date: Optional[str] = Field(None, description="생년월일 (YYYY-MM-DD)")
    gender: Optional[int] = Field(None, description="성별 (1: 남자, 2: 여자)")
    hire_date: Optional[str] = Field(None, description="입사일자 (YYYY-MM-DD)")
    base_salary: Optional[float] = Field(None, description="기준급여")
    current_year_severance: Optional[float] = Field(None, description="당년도 퇴직급여추계액")
    next_year_severance: Optional[float] = Field(None, description="차년도 퇴직급여추계액")
    employee_type: Optional[int] = Field(None, description="중업원 구분 (1: 직원, 3: 임원, 4: 계약직)")
    interim_settlement_date: Optional[str] = Field(None, description="중간정산기준일 (YYYY-MM-DD)")
    interim_settlement_amount: Optional[float] = Field(None, description="중간정산액")
    plan_type: Optional[int] = Field(None, description="제도구분 (1, 2, 3)")
    applicable_multiplier: Optional[float] = Field(None, description="적용배수")
    
    class Config:
        from_attributes = True


class RetiredEmployeeBase(BaseModel):
    """
    퇴직자 및 DC전환자 기본 정보 모델
    """
    emp_id: str = Field(..., description="사원번호")
    birth_date: Optional[str] = Field(None, description="생년월일 (YYYY-MM-DD)")
    gender: Optional[int] = Field(None, description="성별 (1: 남자, 2: 여자)")
    hire_date: Optional[str] = Field(None, description="입사일자 (YYYY-MM-DD)")
    retirement_or_dc_date: Optional[str] = Field(None, description="퇴직일 또는 DC전환일 (YYYYMMDD)")
    retirement_or_dc_amount: Optional[float] = Field(None, description="퇴직금 또는 DC전환금")
    employee_type: Optional[int] = Field(None, description="중업원 구분 (1: 직원, 3: 임원, 4: 계약직)")
    reason: Optional[int] = Field(None, description="사유 (1: 퇴직, 2: DC전환)")
    plan_type: Optional[int] = Field(None, description="제도구분 (1, 2, 3)")
    
    class Config:
        from_attributes = True


class LongTermEmployeeBase(BaseModel):
    """
    기타장기 재직자 기본 정보 모델 (추후 업데이트)
    """
    emp_id: str = Field(..., description="사원번호")
    # TODO: 기타장기 재직자 관련 필드 추가
    
    class Config:
        from_attributes = True


class AdditionalEmployeeBase(BaseModel):
    """
    추가명부 기본 정보 모델
    """
    emp_id: str = Field(..., description="사원번호")
    birth_date: Optional[str] = Field(None, description="생년월일 (YYYY-MM-DD)")
    gender: Optional[int] = Field(None, description="성별 (1: 남자, 2: 여자)")
    hire_date: Optional[str] = Field(None, description="입사일자 (YYYY-MM-DD)")
    base_salary: Optional[float] = Field(None, description="기준급여")
    reason_occurrence_amount: Optional[float] = Field(None, description="사유발생일 시점 발생금액")
    employee_type: Optional[int] = Field(None, description="중업원 구분 (1: 직원, 3: 임원, 4: 계약직)")
    interim_settlement_date: Optional[str] = Field(None, description="중간정산기준일 (YYYY-MM-DD)")
    reason: Optional[int] = Field(None, description="사유 (1:관계사전입, 2:관계사전출, 3:사업합병전, 4:사업합병후, 5:기타장기종업원)")
    reason_occurrence_date: Optional[str] = Field(None, description="사유발생일 (YYYY-MM-DD)")
    
    class Config:
        from_attributes = True


class ValidationError(BaseModel):
    """
    검증 오류 모델
    """
    sheet: str = Field(..., description="시트명")
    row: Optional[int] = Field(None, description="행 번호")
    column: Optional[str] = Field(None, description="컬럼명")
    emp_id: Optional[str] = Field(None, description="사원번호")
    type: str = Field(..., description="오류 타입")
    message: str = Field(..., description="오류 메시지")
    severity: str = Field(default="error", description="심각도 (error, warning)")


class ValidationResult(BaseModel):
    """
    검증 결과 모델
    """
    total_records: int = Field(..., description="전체 레코드 수")
    valid_records: int = Field(..., description="유효한 레코드 수")
    invalid_records: int = Field(..., description="유효하지 않은 레코드 수")
    errors: List[ValidationError] = Field(default_factory=list, description="오류 목록")
    warnings: List[ValidationError] = Field(default_factory=list, description="경고 목록")
    sheet_results: Dict[str, Any] = Field(default_factory=dict, description="시트별 결과")
    summary_report: List[str] = Field(default_factory=list, description="요약 리포트 (사용자 확인용 메시지)")


class UploadResponse(BaseModel):
    """
    파일 업로드 응답 모델
    """
    message: str = Field(..., description="메시지")
    filename: str = Field(..., description="파일명")
    sheets: List[str] = Field(..., description="시트 목록")
    total_records: int = Field(..., description="전체 레코드 수")


class ValidationResponse(BaseModel):
    """
    검증 응답 모델
    """
    message: str = Field(..., description="메시지")
    filename: str = Field(..., description="파일명")
    validation_results: ValidationResult = Field(..., description="검증 결과")
    summary: Dict[str, Any] = Field(..., description="요약 정보")
