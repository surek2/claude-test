def process_string(text):
    """
    입력된 문자열에 대해 다양한 처리를 수행하는 함수
    
    Args:
        text (str): 처리할 문자열
    
    Returns:
        dict: 처리 결과를 담은 딕셔너리
    """
    if not isinstance(text, str):
        return {"error": "문자열이 아닙니다!"}
    
    # 문자열 길이
    length = len(text)
    
    # 대문자/소문자 변환
    uppercase = text.upper()
    lowercase = text.lower()
    
    # 문자열 뒤집기
    reversed_text = text[::-1]
    
    # 각 단어의 첫 글자만 대문자로 변환 (title case)
    title_case = text.title()
    
    # 공백 제거
    no_spaces = text.replace(" ", "")
    
    return {
        "original": text,
        "length": length,
        "uppercase": uppercase,
        "lowercase": lowercase,
        "reversed": reversed_text,
        "title_case": title_case,
        "no_spaces": no_spaces
    }


def print_results(results):
    """
    처리 결과를 출력하는 함수
    
    Args:
        results (dict): process_string 함수의 결과
    """
    if "error" in results:
        print(results["error"])
        return
    
    print(f"원본 문자열: \"{results['original']}\"")
    print(f"문자열 길이: {results['length']}")
    print(f"대문자: {results['uppercase']}")
    print(f"소문자: {results['lowercase']}")
    print(f"뒤집기: {results['reversed']}")
    print(f"첫 글자 대문자: {results['title_case']}")
    print(f"공백 제거: {results['no_spaces']}")



def test_with_sample_data():
    """
    테스트 케이스를 실행하는 함수
    """
    print("=== 테스트 케이스 실행 ===")
    test_string = "Hello Python World"
    print(f"입력: \"{test_string}\"")
    print()
    
    results = process_string(test_string)
    print_results(results)


def main():
    """
    메인 함수 - 사용자 입력을 받아 문자열 처리 수행
    """
    print("문자열 처리 프로그램")
    print("===================")
    print("처리할 문자열을 입력하세요.")
    print()
    
    try:
        user_input = input("문자열을 입력하세요: ")
        
        if not user_input.strip():
            print("오류: 빈 문자열입니다!")
            return
        
        print(f"\n=== 처리 결과 ===")
        
        # 문자열 처리 및 결과 출력
        results = process_string(user_input)
        print_results(results)
        
    except KeyboardInterrupt:
        print("\n프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"예상치 못한 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    # 테스트 케이스 실행
    test_with_sample_data()
    
    print("\n" + "="*40 + "\n")
    
    # 대화형 모드 실행
    main() 