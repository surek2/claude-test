def process_list(numbers):
    """
    숫자 리스트를 처리하여 최댓값, 최솟값, 평균값을 구하고
    정렬 및 짝수 필터링을 수행하는 함수
    
    Args:
        numbers (list): 숫자들이 담긴 리스트
    
    Returns:
        dict: 처리 결과를 담은 딕셔너리
    """
    if not numbers:
        return {"error": "빈 리스트입니다!"}
    
    # 최댓값, 최솟값, 평균값 계산
    max_value = max(numbers)
    min_value = min(numbers)
    average = sum(numbers) / len(numbers)
    
    # 오름차순 정렬
    sorted_list = sorted(numbers)
    
    # 짝수만 필터링
    even_numbers = [num for num in numbers if num % 2 == 0]
    
    return {
        "max_value": max_value,
        "min_value": min_value,
        "average": average,
        "sorted_list": sorted_list,
        "even_numbers": even_numbers
    }


def print_results(results):
    """
    처리 결과를 출력하는 함수
    
    Args:
        results (dict): process_list 함수의 결과
    """
    if "error" in results:
        print(results["error"])
        return
    
    print(f"최댓값: {results['max_value']}")
    print(f"최솟값: {results['min_value']}")
    print(f"평균값: {results['average']}")
    print(f"정렬된 리스트: {results['sorted_list']}")
    print(f"짝수 리스트: {results['even_numbers']}")


def parse_input(input_str):
    """
    사용자 입력을 파싱하여 숫자 리스트로 변환하는 함수
    
    Args:
        input_str (str): 사용자 입력 문자열
    
    Returns:
        list: 숫자 리스트 또는 None (오류 시)
    """
    try:
        # 쉼표로 구분된 숫자들을 파싱
        input_str = input_str.strip()
        
        # 대괄호 제거 (있는 경우)
        if input_str.startswith('[') and input_str.endswith(']'):
            input_str = input_str[1:-1]
        
        # 쉼표로 분리하고 숫자로 변환
        numbers = [float(x.strip()) for x in input_str.split(',') if x.strip()]
        
        # 정수인 경우 int로 변환 (소수점이 .0인 경우)
        numbers = [int(num) if num.is_integer() else num for num in numbers]
        
        return numbers
    except (ValueError, AttributeError):
        return None


def test_with_sample_data():
    """
    테스트 케이스를 실행하는 함수
    """
    print("=== 테스트 케이스 실행 ===")
    test_data = [5, 2, 8, 1, 9, 4, 6]
    print(f"입력: {test_data}")
    print()
    
    results = process_list(test_data)
    print_results(results)


def main():
    """
    메인 함수 - 사용자 입력을 받아 리스트 처리 수행
    """
    print("리스트 처리 프로그램")
    print("===================")
    print("숫자들을 쉼표로 구분하여 입력하세요 (예: 5, 2, 8, 1, 9, 4, 6)")
    print("또는 대괄호를 포함해서 입력하세요 (예: [5, 2, 8, 1, 9, 4, 6])")
    print()
    
    try:
        user_input = input("숫자 리스트를 입력하세요: ")
        
        # 사용자 입력 파싱
        numbers = parse_input(user_input)
        
        if numbers is None:
            print("오류: 올바른 숫자 형식으로 입력해주세요!")
            return
        
        if not numbers:
            print("오류: 최소 하나 이상의 숫자를 입력해주세요!")
            return
        
        print(f"\n입력받은 리스트: {numbers}")
        print("\n=== 처리 결과 ===")
        
        # 리스트 처리 및 결과 출력
        results = process_list(numbers)
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