def calculator():
    """
    두 숫자를 입력받아 사칙연산(덧셈, 뺄셈, 곱셈, 나눗셈)을 수행하는 함수
    """
    try:
        # 사용자로부터 두 숫자 입력받기
        num1 = float(input("첫 번째 숫자를 입력하세요: "))
        num2 = float(input("두 번째 숫자를 입력하세요: "))
        
        # 사칙연산 수행 및 결과 출력
        print(f"\n=== 계산 결과 ===")
        print(f"{num1} + {num2} = {num1 + num2}")
        print(f"{num1} - {num2} = {num1 - num2}")
        print(f"{num1} * {num2} = {num1 * num2}")
        
        # 나눗셈의 경우 0으로 나누는 경우 처리
        if num2 == 0:
            print(f"{num1} / {num2} = 오류: 0으로 나눌 수 없습니다!")
        else:
            print(f"{num1} / {num2} = {num1 / num2}")
            
    except ValueError:
        print("오류: 올바른 숫자를 입력해주세요!")
    except Exception as e:
        print(f"예상치 못한 오류가 발생했습니다: {e}")


def test_calculator_functions(num1, num2):
    """
    테스트를 위한 함수 (입력 없이 숫자를 직접 받아서 계산)
    """
    print(f"\n=== 테스트: {num1}, {num2} ===")
    print(f"{num1} + {num2} = {num1 + num2}")
    print(f"{num1} - {num2} = {num1 - num2}")
    print(f"{num1} * {num2} = {num1 * num2}")
    
    if num2 == 0:
        print(f"{num1} / {num2} = 오류: 0으로 나눌 수 없습니다!")
    else:
        print(f"{num1} / {num2} = {num1 / num2}")


if __name__ == "__main__":
    print("사칙연산 계산기")
    print("================")
    
    # 대화형 계산기 실행
    calculator() 