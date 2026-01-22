"""
데이터 매핑 및 검증 테스트 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from services.excel_reader import ExcelReader
from services.data_mapper import DataMapper
from services.validator import DataValidator
import json

def test_with_sample_data():
    """
    샘플 데이터로 매핑 및 검증 테스트
    """
    # 샘플 파일 경로
    sample_file = os.path.join("data", "푸본현대 sample.xlsx")
    
    if not os.path.exists(sample_file):
        print(f"❌ 샘플 파일을 찾을 수 없습니다: {sample_file}")
        return
    
    print("=" * 80)
    print("📊 명부 검증 시스템 테스트")
    print("=" * 80)
    
    # 1. 엑셀 파일 읽기
    print("\n[1단계] 엑셀 파일 읽기")
    print("-" * 80)
    
    try:
        reader = ExcelReader(sample_file)
        
        # 먼저 사용 가능한 시트 목록 확인
        import pandas as pd
        excel_file = pd.ExcelFile(sample_file)
        print(f"📂 파일 내 시트 목록: {excel_file.sheet_names}\n")
        
        sheets_data = reader.read_all_sheets()
        
        print(f"✅ 총 {len(sheets_data)}개 시트 읽기 완료:")
        for sheet_name, df in sheets_data.items():
            # 실제 사원 수 계산
            actual_count = reader._count_valid_records(df)
            print(f"   📋 {sheet_name}")
            print(f"      - 사원 수: {actual_count}명")
            print(f"      - 전체 행: {len(df)}행")
            print(f"      - 컬럼 수: {len(df.columns)}개")
            print(f"      - 컬럼 샘플: {', '.join(df.columns.tolist()[:5])}...")
    except Exception as e:
        print(f"❌ 엑셀 읽기 오류: {str(e)}")
        return
    
    # 2. 데이터 매핑
    print("\n[2단계] 데이터 매핑 및 정형화")
    print("-" * 80)
    
    try:
        mapper = DataMapper()
        mapped_data = mapper.map_all_sheets(sheets_data)
        
        print(f"✅ 총 {len(mapped_data)}개 시트 매핑 완료:")
        for sheet_name, df in mapped_data.items():
            print(f"\n   📋 {sheet_name}:")
            print(f"      - 행 수: {len(df)}")
            print(f"      - 컬럼: {', '.join(df.columns.tolist())}")
            
            # 첫 3행 샘플 출력
            if len(df) > 0:
                print(f"\n      샘플 데이터 (첫 3행):")
                for idx, row in df.head(3).iterrows():
                    print(f"      행 {idx+1}:")
                    for col in df.columns:
                        value = row[col]
                        if value is not None and value != '':
                            print(f"        - {col}: {value}")
    except Exception as e:
        print(f"❌ 데이터 매핑 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. 데이터 검증
    print("\n[3단계] 데이터 검증")
    print("-" * 80)
    
    try:
        validator = DataValidator()
        validation_results = validator.validate(mapped_data)
        
        print(f"\n✅ 검증 완료:")
        print(f"   - 전체 레코드: {validation_results['total_records']}건")
        print(f"   - 유효 레코드: {validation_results['valid_records']}건")
        print(f"   - 오류 레코드: {validation_results['invalid_records']}건")
        print(f"   - 오류 개수: {len(validation_results['errors'])}개")
        print(f"   - 경고 개수: {len(validation_results['warnings'])}개")
        
        # 시트별 결과
        print("\n   📊 시트별 검증 결과:")
        for sheet_name, result in validation_results['sheet_results'].items():
            print(f"\n   {sheet_name}:")
            print(f"      - 전체: {result['total_records']}건")
            print(f"      - 유효: {result['valid_records']}건")
            print(f"      - 오류: {result['invalid_records']}건")
        
        # 오류 상세 (최대 10개)
        if validation_results['errors']:
            print("\n   ⚠️  오류 상세 (최대 10개):")
            for i, error in enumerate(validation_results['errors'][:10], 1):
                print(f"      {i}. [{error['type']}] {error['message']}")
                print(f"         시트: {error['sheet']}, 행: {error.get('row', 'N/A')}, "
                      f"컬럼: {error.get('column', 'N/A')}")
        
        # 경고 상세 (최대 5개)
        if validation_results['warnings']:
            print("\n   💡 경고 상세 (최대 5개):")
            for i, warning in enumerate(validation_results['warnings'][:5], 1):
                print(f"      {i}. [{warning['type']}] {warning['message']}")
                print(f"         시트: {warning['sheet']}, 행: {warning.get('row', 'N/A')}")
        
    except Exception as e:
        print(f"❌ 데이터 검증 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 80)
    print("✅ 테스트 완료!")
    print("=" * 80)

if __name__ == "__main__":
    test_with_sample_data()

