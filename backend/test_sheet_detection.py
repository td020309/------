"""
시트 이름 자동 인식 테스트 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from services.excel_reader import ExcelReader

def test_sheet_names():
    """
    다양한 시트 이름 패턴 테스트
    """
    print("=" * 80)
    print("📋 시트 이름 자동 인식 테스트")
    print("=" * 80)
    
    # 테스트 케이스
    test_cases = [
        # 원본 시트 이름 → 인식되어야 할 표준 이름
        ("재직자 명부", "재직자 명부"),
        ("(2-2)재직자 명부", "재직자 명부"),
        ("2-2 재직자명부", "재직자 명부"),
        ("재직자명부", "재직자 명부"),
        
        ("퇴직자 및 DC전환자 명부", "퇴직자 및 DC전환자 명부"),
        ("(2-4)퇴직자 및 DC전환자 명부", "퇴직자 및 DC전환자 명부"),
        ("2-4 퇴직자및DC전환자명부", "퇴직자 및 DC전환자 명부"),
        
        ("추가 명부(장기근속)", "추가 명부(장기근속)"),
        ("(2-5)추가명부", "추가 명부(장기근속)"),
        ("2-5 추가명부", "추가 명부(장기근속)"),
        
        ("기타장기 재직자 명부", "기타장기 재직자 명부"),
        ("(2-3) 기타장기 재직자 명부", "기타장기 재직자 명부"),
        ("2-3 기타장기재직자명부", "기타장기 재직자 명부"),
    ]
    
    reader = ExcelReader("")
    
    print("\n🔍 테스트 케이스:")
    print("-" * 80)
    
    for original_name, expected_standard in test_cases:
        # 테스트를 위해 가상의 시트 목록 생성
        available_sheets = [original_name]
        
        # 키워드 찾기
        for standard_name, keywords in reader.SHEET_KEYWORDS.items():
            found = reader._find_sheet_by_keywords(standard_name, keywords, available_sheets)
            
            if found and standard_name == expected_standard:
                print(f"✅ '{original_name}' → '{standard_name}' 매칭 성공")
                break
        else:
            print(f"❌ '{original_name}' → 매칭 실패 (예상: '{expected_standard}')")
    
    print("\n" + "=" * 80)
    print("✅ 테스트 완료!")
    print("=" * 80)

if __name__ == "__main__":
    test_sheet_names()

