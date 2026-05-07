def calculate_average(grades):
    """
    전체 학생의 평균 점수를 계산하는 함수
    
    Args:
        grades (dict): 학생 이름과 점수가 담긴 딕셔너리
    
    Returns:
        float: 평균 점수
    """
    if not grades:
        return 0.0
    
    total_score = sum(grades.values())
    return total_score / len(grades)


def find_top_student(grades):
    """
    가장 높은 점수를 받은 학생을 찾는 함수
    
    Args:
        grades (dict): 학생 이름과 점수가 담긴 딕셔너리
    
    Returns:
        tuple: (학생 이름, 점수) 또는 (None, None)
    """
    if not grades:
        return None, None
    
    top_student = max(grades.items(), key=lambda x: x[1])
    return top_student[0], top_student[1]


def find_passing_students(grades, passing_score=60):
    """
    합격 점수 이상인 학생들을 찾는 함수
    
    Args:
        grades (dict): 학생 이름과 점수가 담긴 딕셔너리
        passing_score (int): 합격 점수 기준 (기본값: 60점)
    
    Returns:
        list: 합격한 학생들의 이름 리스트
    """
    passing_students = []
    for student, score in grades.items():
        if score >= passing_score:
            passing_students.append(student)
    
    return passing_students


def sort_students_by_grade(grades, reverse=True):
    """
    학생들을 성적순으로 정렬하는 함수
    
    Args:
        grades (dict): 학생 이름과 점수가 담긴 딕셔너리
        reverse (bool): True면 내림차순, False면 오름차순
    
    Returns:
        list: (학생 이름, 점수) 튜플의 정렬된 리스트
    """
    return sorted(grades.items(), key=lambda x: x[1], reverse=reverse)


def print_grade_report(grades):
    """
    성적 보고서를 출력하는 함수
    
    Args:
        grades (dict): 학생 이름과 점수가 담긴 딕셔너리
    """
    if not grades:
        print("등록된 학생이 없습니다!")
        return
    
    print("=== 성적 관리 보고서 ===")
    
    # 1. 평균 점수
    average = calculate_average(grades)
    print(f"평균 점수: {average:.1f}")
    
    # 2. 최고 점수 학생
    top_name, top_score = find_top_student(grades)
    print(f"최고 점수 학생: {top_name} ({top_score}점)")
    
    # 3. 합격자 명단 (60점 이상)
    passing_students = find_passing_students(grades)
    if passing_students:
        print(f"합격자 명단: {', '.join(passing_students)}")
    else:
        print("합격자가 없습니다.")
    
    # 4. 성적순 정렬
    sorted_students = sort_students_by_grade(grades)
    print("성적순 정렬:")
    for i, (name, score) in enumerate(sorted_students, 1):
        print(f"{i}. {name}: {score}점")


def parse_grades_input(input_str):
    """
    사용자 입력을 파싱하여 성적 딕셔너리로 변환하는 함수
    
    Args:
        input_str (str): 사용자 입력 문자열
    
    Returns:
        dict: 학생 이름과 점수가 담긴 딕셔너리 또는 None (오류 시)
    """
    try:
        # 딕셔너리 형태의 문자열을 실제 딕셔너리로 변환
        grades = eval(input_str)
        
        # 딕셔너리인지 확인
        if not isinstance(grades, dict):
            return None
        
        # 모든 값이 숫자인지 확인
        for name, score in grades.items():
            if not isinstance(score, (int, float)) or score < 0 or score > 100:
                return None
        
        return grades
    except:
        return None


def test_with_sample_data():
    """
    테스트 케이스를 실행하는 함수
    """
    print("=== 테스트 케이스 실행 ===")
    sample_grades = {
        "김철수": 85,
        "이영희": 92,
        "박민수": 78,
        "최지원": 55,
        "정하나": 88
    }
    
    print(f"입력: {sample_grades}")
    print()
    
    print_grade_report(sample_grades)


def main():
    """
    메인 함수 - 사용자 입력을 받아 성적 관리 수행
    """
    print("학생 성적 관리 프로그램")
    print("=====================")
    print("학생 이름과 점수를 딕셔너리 형태로 입력하세요.")
    print('예시: {"김철수": 85, "이영희": 92, "박민수": 78}')
    print()
    
    try:
        user_input = input("성적 데이터를 입력하세요: ")
        
        # 사용자 입력 파싱
        grades = parse_grades_input(user_input)
        
        if grades is None:
            print("오류: 올바른 딕셔너리 형식으로 입력해주세요!")
            print("점수는 0-100 사이의 숫자여야 합니다.")
            return
        
        if not grades:
            print("오류: 최소 한 명 이상의 학생 데이터를 입력해주세요!")
            return
        
        print(f"\n입력받은 성적 데이터: {grades}")
        print()
        
        # 성적 보고서 출력
        print_grade_report(grades)
        
    except KeyboardInterrupt:
        print("\n프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"예상치 못한 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    # 테스트 케이스 실행
    test_with_sample_data()
    
    print("\n" + "="*50 + "\n")
    
    # 대화형 모드 실행
    main() 