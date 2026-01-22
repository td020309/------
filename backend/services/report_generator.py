from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    검증 결과를 바탕으로 사용자 친화적인 리포트를 생성하는 클래스
    """
    
    def __init__(self):
        pass

    def generate_summary_report(self, validation_results: Dict[str, Any]) -> List[str]:
        """
        검증 결과를 요약하여 "이 쉬트에서 이거이거 확인해달라" 형식의 리포트 생성
        """
        report_lines = []
        
        errors = validation_results.get("errors", [])
        warnings = validation_results.get("warnings", [])
        
        # 시트별로 이슈 그룹화
        sheet_issues = {}
        
        # 에러 처리
        for error in errors:
            sheet_name = error.get("sheet", "기타")
            if sheet_name not in sheet_issues:
                sheet_issues[sheet_name] = {"errors": [], "warnings": []}
            sheet_issues[sheet_name]["errors"].append(error)
            
        # 경고 처리
        for warning in warnings:
            sheet_name = warning.get("sheet", "기타")
            if sheet_name not in sheet_issues:
                sheet_issues[sheet_name] = {"errors": [], "warnings": []}
            sheet_issues[sheet_name]["warnings"].append(warning)
            
        if not sheet_issues:
            return ["모든 데이터가 정상입니다. 별도의 확인 사항이 없습니다."]

        for sheet_name, issues in sheet_issues.items():
            error_count = len(issues["errors"])
            warning_count = len(issues["warnings"])
            
            if error_count > 0 or warning_count > 0:
                # 해당 시트의 주요 이슈 메시지 추출 (중복 제거)
                unique_messages = []
                
                # 에러 메시지 우선 수집
                for err in issues["errors"]:
                    msg = err.get("message", "알 수 없는 오류")
                    if msg not in unique_messages:
                        unique_messages.append(msg)
                
                # 경고 메시지 수집
                for warn in issues["warnings"]:
                    msg = warn.get("message", "알 수 없는 경고")
                    if msg not in unique_messages:
                        unique_messages.append(msg)
                
                # 리포트 라인 구성
                issue_summary = ", ".join(unique_messages[:3]) # 너무 많으면 상위 3개만 표시
                if len(unique_messages) > 3:
                    issue_summary += f" 외 {len(unique_messages) - 3}건"
                
                line = f"'{sheet_name}' 시트에서 [{issue_summary}] 등을 확인해 주세요."
                report_lines.append(line)
                
        return report_lines


