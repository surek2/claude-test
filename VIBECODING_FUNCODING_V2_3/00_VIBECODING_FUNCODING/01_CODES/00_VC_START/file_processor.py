import os
from collections import Counter
import re


def read_file(filename):
    """
    텍스트 파일을 읽어서 내용을 반환하는 함수
    
    Args:
        filename (str): 읽을 파일명
    
    Returns:
        list: 파일의 각 줄을 담은 리스트 또는 None (오류 시)
    """
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            # 줄 끝의 개행문자 제거
            lines = [line.strip() for line in lines]
            return lines
    except FileNotFoundError:
        print(f"오류: '{filename}' 파일을 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f"파일 읽기 오류: {e}")
        return None


def count_words_per_line(lines):
    """
    각 줄의 단어 수를 계산하는 함수
    
    Args:
        lines (list): 텍스트 줄들의 리스트
    
    Returns:
        list: 각 줄의 단어 수 리스트
    """
    word_counts = []
    for line in lines:
        # 공백으로 구분하여 단어 개수 계산
        words = line.split()
        word_counts.append(len(words))
    return word_counts


def get_all_words(lines):
    """
    모든 줄에서 단어들을 추출하는 함수
    
    Args:
        lines (list): 텍스트 줄들의 리스트
    
    Returns:
        list: 모든 단어들의 리스트 (소문자로 변환, 구두점 제거)
    """
    all_words = []
    for line in lines:
        # 구두점 제거하고 소문자로 변환
        words = re.findall(r'\b\w+\b', line.lower())
        all_words.extend(words)
    return all_words


def find_most_frequent_words(words):
    """
    가장 많이 나타나는 단어들을 찾는 함수
    
    Args:
        words (list): 단어들의 리스트
    
    Returns:
        list: (단어, 빈도) 튜플의 리스트 (빈도 내림차순)
    """
    word_counter = Counter(words)
    return word_counter.most_common()


def analyze_text_file(filename):
    """
    텍스트 파일을 분석하는 함수
    
    Args:
        filename (str): 분석할 파일명
    
    Returns:
        dict: 분석 결과를 담은 딕셔너리 또는 None (오류 시)
    """
    # 파일 읽기
    lines = read_file(filename)
    if lines is None:
        return None
    
    # 각 줄의 단어 수 계산
    words_per_line = count_words_per_line(lines)
    
    # 모든 단어 추출
    all_words = get_all_words(lines)
    
    # 가장 많이 나타나는 단어 찾기
    word_frequencies = find_most_frequent_words(all_words)
    
    return {
        "lines": lines,
        "total_lines": len(lines),
        "total_words": len(all_words),
        "words_per_line": words_per_line,
        "word_frequencies": word_frequencies
    }


def write_analysis_result(analysis, output_filename):
    """
    분석 결과를 파일에 저장하는 함수
    
    Args:
        analysis (dict): analyze_text_file 함수의 결과
        output_filename (str): 출력 파일명
    
    Returns:
        bool: 저장 성공 여부
    """
    try:
        with open(output_filename, 'w', encoding='utf-8') as file:
            file.write("원본 파일 분석 결과:\n")
            file.write(f"총 줄 수: {analysis['total_lines']}\n")
            file.write(f"총 단어 수: {analysis['total_words']}\n\n")
            
            file.write("각 줄의 단어 수:\n")
            for i, word_count in enumerate(analysis['words_per_line'], 1):
                file.write(f"{i}번째 줄: {word_count}개\n")
            
            file.write("\n가장 많이 나타난 단어:\n")
            
            # 가장 높은 빈도 찾기
            max_frequency = analysis['word_frequencies'][0][1] if analysis['word_frequencies'] else 0
            
            # 가장 높은 빈도를 가진 단어들만 출력
            for word, frequency in analysis['word_frequencies']:
                if frequency == max_frequency:
                    file.write(f"{word}: {frequency}회\n")
                else:
                    break
        
        return True
    except Exception as e:
        print(f"파일 저장 오류: {e}")
        return False


def print_analysis_result(analysis):
    """
    분석 결과를 화면에 출력하는 함수
    
    Args:
        analysis (dict): analyze_text_file 함수의 결과
    """
    print("=== 파일 분석 결과 ===")
    print(f"총 줄 수: {analysis['total_lines']}")
    print(f"총 단어 수: {analysis['total_words']}")
    
    print("\n각 줄의 단어 수:")
    for i, word_count in enumerate(analysis['words_per_line'], 1):
        print(f"{i}번째 줄: {word_count}개")
    
    print("\n가장 많이 나타난 단어:")
    if analysis['word_frequencies']:
        max_frequency = analysis['word_frequencies'][0][1]
        for word, frequency in analysis['word_frequencies']:
            if frequency == max_frequency:
                print(f"{word}: {frequency}회")
            else:
                break
    
    print("\n모든 단어 빈도 (상위 10개):")
    for word, frequency in analysis['word_frequencies'][:10]:
        print(f"{word}: {frequency}회")


def test_with_sample_file():
    """
    샘플 파일로 테스트하는 함수
    """
    print("=== 테스트: input.txt 파일 분석 ===")
    
    input_file = "input.txt"
    output_file = "output.txt"
    
    # 파일 분석
    analysis = analyze_text_file(input_file)
    
    if analysis is None:
        print("파일 분석에 실패했습니다.")
        return
    
    # 결과 화면 출력
    print_analysis_result(analysis)
    
    # 결과 파일 저장
    if write_analysis_result(analysis, output_file):
        print(f"\n분석 결과가 '{output_file}' 파일에 저장되었습니다.")
    else:
        print("\n파일 저장에 실패했습니다.")


def main():
    """
    메인 함수 - 사용자 입력을 받아 파일 처리 수행
    """
    print("텍스트 파일 처리 프로그램")
    print("========================")
    
    try:
        input_file = input("분석할 파일명을 입력하세요 (기본값: input.txt): ").strip()
        if not input_file:
            input_file = "input.txt"
        
        output_file = input("결과를 저장할 파일명을 입력하세요 (기본값: output.txt): ").strip()
        if not output_file:
            output_file = "output.txt"
        
        # 입력 파일 존재 확인
        if not os.path.exists(input_file):
            print(f"오류: '{input_file}' 파일이 존재하지 않습니다.")
            return
        
        print(f"\n'{input_file}' 파일을 분석 중...")
        
        # 파일 분석
        analysis = analyze_text_file(input_file)
        
        if analysis is None:
            print("파일 분석에 실패했습니다.")
            return
        
        # 결과 화면 출력
        print_analysis_result(analysis)
        
        # 결과 파일 저장
        if write_analysis_result(analysis, output_file):
            print(f"\n분석 결과가 '{output_file}' 파일에 저장되었습니다.")
        else:
            print("\n파일 저장에 실패했습니다.")
            
    except KeyboardInterrupt:
        print("\n프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"예상치 못한 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    # 테스트 케이스 실행
    test_with_sample_file()
    
    print("\n" + "="*50 + "\n")
    
    # 대화형 모드 실행
    main() 