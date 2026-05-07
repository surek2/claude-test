enum TodoStatus {
  pending, // 대기
  onHold, // 보류
  completed, // 완료
}

class Todo {
  final String id;
  final String title;
  final String? description;
  final TodoStatus status;
  final DateTime createdAt;

  Todo({
    required this.id,
    required this.title,
    this.description,
    this.status = TodoStatus.pending,
    required this.createdAt,
  });

  // JSON으로 변환
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'status': status.index,
      'createdAt': createdAt.millisecondsSinceEpoch,
    };
  }

  // JSON에서 Todo 객체 생성
  factory Todo.fromJson(Map<String, dynamic> json) {
    return Todo(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      status: TodoStatus.values[json['status']],
      createdAt: DateTime.fromMillisecondsSinceEpoch(json['createdAt']),
    );
  }

  // 복사본 생성 (상태 변경 시 사용)
  Todo copyWith({
    String? id,
    String? title,
    String? description,
    TodoStatus? status,
    DateTime? createdAt,
  }) {
    return Todo(
      id: id ?? this.id,
      title: title ?? this.title,
      description: description ?? this.description,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}
