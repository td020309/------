from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from services.excel_reader import ExcelReader
from services.data_mapper import DataMapper
from services.validator import DataValidator
import tempfile
import os

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    엑셀 파일을 업로드하고 초기 검증을 수행합니다.
    """
    # 파일 확장자 검증
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="엑셀 파일만 업로드 가능합니다 (.xlsx, .xls)")
    
    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # 엑셀 파일 읽기
        excel_reader = ExcelReader(temp_file_path)
        sheets_data = excel_reader.read_all_sheets()
        
        # 실제 사원 수 계산 (사원번호가 있는 행만)
        total_employees = 0
        sheet_info = {}
        for sheet_name, df in sheets_data.items():
            count = excel_reader._count_valid_records(df)
            total_employees += count
            sheet_info[sheet_name] = count
        
        # 임시 파일 삭제
        os.unlink(temp_file_path)
        
        return JSONResponse(content={
            "message": "파일이 성공적으로 업로드되었습니다",
            "filename": file.filename,
            "sheets": list(sheets_data.keys()),
            "total_records": total_employees,
            "sheet_details": sheet_info
        })
    
    except Exception as e:
        # 임시 파일이 있으면 삭제
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류 발생: {str(e)}")


@router.post("/validate")
async def validate_data(file: UploadFile = File(...)):
    """
    엑셀 파일을 업로드하고 전체 검증을 수행합니다.
    """
    # 파일 확장자 검증
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="엑셀 파일만 업로드 가능합니다 (.xlsx, .xls)")
    
    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # 1. 엑셀 파일 읽기
        excel_reader = ExcelReader(temp_file_path)
        sheets_data = excel_reader.read_all_sheets()
        
        # 2. 데이터 매핑 및 정형화
        data_mapper = DataMapper()
        mapped_data = data_mapper.map_all_sheets(sheets_data)
        
        # 3. 데이터 검증
        validator = DataValidator()
        validation_results = validator.validate(mapped_data)
        
        # 임시 파일 삭제
        os.unlink(temp_file_path)
        
        return JSONResponse(content={
            "message": "검증이 완료되었습니다",
            "filename": file.filename,
            "validation_results": validation_results,
            "summary": {
                "total_records": validation_results.get("total_records", 0),
                "valid_records": validation_results.get("valid_records", 0),
                "invalid_records": validation_results.get("invalid_records", 0),
                "errors": validation_results.get("errors", [])
            }
        })
    
    except Exception as e:
        # 임시 파일이 있으면 삭제
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"검증 중 오류 발생: {str(e)}")

