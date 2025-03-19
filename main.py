import os
import zipfile
import xml.etree.ElementTree as ET
import shutil
import re
import tempfile
import argparse

########
# python transHWP.py --input ./example.hwpx --output ./output.txt
########

def hwpx_to_txt_with_tables(hwpx_file, output_txt_file):
    # 임시 디렉토리 생성
    temp_dir = "temp_hwpx_extract"
    os.makedirs(temp_dir, exist_ok=True)
    
    # 임시 zip 파일 경로 생성
    temp_zip_file = None
    
    try:
        # 임시 zip 파일 생성 (확장자만 변경)
        temp_zip_file = tempfile.mktemp(suffix='.zip')
        shutil.copy2(hwpx_file, temp_zip_file)
        
        # 임시 zip 파일 압축 해제
        with zipfile.ZipFile(temp_zip_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # 결과 텍스트를 저장할 변수
        result_text = ""
        
        # XML 네임스페이스 처리를 위한 패턴
        ns_pattern = re.compile(r'\{.*?\}')
        
        # section 파일들 처리 (여러 섹션이 있을 수 있음)
        section_files = []
        contents_dir = os.path.join(temp_dir, "Contents")
        for file in os.listdir(contents_dir):
            if file.startswith("section") and file.endswith(".xml"):
                section_files.append(os.path.join(contents_dir, file))
        
        for section_file in sorted(section_files):
            tree = ET.parse(section_file)
            root = tree.getroot()
            
            # 문단 및 표 처리
            for element in root.iter():
                tag = ns_pattern.sub('', element.tag)
                
                # 텍스트 처리
                if tag == 't':
                    if element.text:
                        result_text += element.text + "\n"
                
                # 표 처리
                elif tag == 'tbl':
                    result_text += "\n"  # 표 전에 빈 줄 추가
                    
                    # 표 데이터 추출
                    table_data = extract_table_data(element, ns_pattern)
                    
                    # 마크다운 표 생성
                    if table_data:
                        result_text += table_to_markdown(table_data)
                        result_text += "\n"  # 표 후에 빈 줄 추가
        
        # 결과를 텍스트 파일로 저장
        with open(output_txt_file, 'w', encoding='utf-8') as f:
            f.write(result_text)
            
        return True
        
    except Exception as e:
        print(f"오류 발생: {e}")
        return False
    
    finally:
        # 임시 파일 및 디렉토리 삭제
        if temp_zip_file and os.path.exists(temp_zip_file):
            os.remove(temp_zip_file)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def extract_table_data(table_element, ns_pattern):
    """표 요소에서 데이터를 추출하여 2차원 배열로 반환"""
    rows = int(table_element.get('rowCnt', 0))
    cols = int(table_element.get('colCnt', 0))
    
    # 빈 테이블 초기화
    table_data = [["" for _ in range(cols)] for _ in range(rows)]
    
    # 셀 정보 추출
    for tc in table_element.iter():
        if ns_pattern.sub('', tc.tag) == 'tc':
            row_idx = int(tc.get('rowIdx', 0))
            col_idx = int(tc.get('colIdx', 0))
            
            # 셀 내용 추출
            cell_text = ""
            for t in tc.iter():
                if ns_pattern.sub('', t.tag) == 't' and t.text:
                    cell_text += t.text.strip() + " "
            
            # 셀 데이터 저장 (범위 체크)
            if 0 <= row_idx < rows and 0 <= col_idx < cols:
                table_data[row_idx][col_idx] = cell_text.strip()
    
    return table_data

def table_to_markdown(table_data):
    """2차원 배열을 마크다운 표로 변환"""
    if not table_data or not table_data[0]:
        return ""
    
    markdown = ""
    
    # 헤더 행
    markdown += "| " + " | ".join(table_data[0]) + " |\n"
    
    # 구분선
    markdown += "| " + " | ".join(["---"] * len(table_data[0])) + " |\n"
    
    # 데이터 행
    for row in table_data[1:]:
        markdown += "| " + " | ".join(row) + " |\n"
    
    return markdown

def main():
    # 명령줄 인자 파서 생성
    parser = argparse.ArgumentParser(description='HWPX 파일을 TXT 파일로 변환합니다.')
    
    # 인자 추가
    parser.add_argument('--input', '-i', required=True, help='입력 HWPX 파일 경로')
    parser.add_argument('--output', '-o', required=True, help='출력 TXT 파일 경로')
    
    # 인자 파싱
    args = parser.parse_args()
    
    # 변환 실행
    success = hwpx_to_txt_with_tables(args.input, args.output)
    
    if success:
        print(f"변환 완료: {args.input} -> {args.output}")
    else:
        print("변환 실패")

if __name__ == "__main__":
    main()
