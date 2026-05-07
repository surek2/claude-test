import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import 'dart:math';
import '../models/todo.dart';
import '../widgets/todo_item.dart';

enum ViewMode { all, pending, onHold, completed }

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  List<Todo> _todos = [];
  List<Todo> _filteredTodos = [];
  final TextEditingController _textController = TextEditingController();
  final TextEditingController _descriptionController = TextEditingController();
  final TextEditingController _searchController = TextEditingController();
  int _selectedTabIndex = 0;
  ViewMode _currentViewMode = ViewMode.all;
  bool _isSearching = false;
  late AnimationController _fabController;
  late Animation<double> _fabAnimation;

  @override
  void initState() {
    super.initState();
    _loadTodos();
    _searchController.addListener(_onSearchChanged);
    _fabController = AnimationController(
      duration: const Duration(milliseconds: 200),
      vsync: this,
    );
    _fabAnimation = Tween<double>(
      begin: 1.0,
      end: 1.1,
    ).animate(CurvedAnimation(parent: _fabController, curve: Curves.easeInOut));
  }

  void _onSearchChanged() {
    setState(() {
      _filterTodos();
    });
  }

  void _filterTodos() {
    List<Todo> filtered = _todos;

    // 검색 필터 적용
    if (_searchController.text.isNotEmpty) {
      filtered = filtered.where((todo) {
        return todo.title.toLowerCase().contains(
              _searchController.text.toLowerCase(),
            ) ||
            (todo.description != null &&
                todo.description!.toLowerCase().contains(
                  _searchController.text.toLowerCase(),
                ));
      }).toList();
    }

    // 상태 필터 적용
    switch (_currentViewMode) {
      case ViewMode.all:
        break;
      case ViewMode.pending:
        filtered = filtered
            .where((todo) => todo.status == TodoStatus.pending)
            .toList();
        break;
      case ViewMode.onHold:
        filtered = filtered
            .where((todo) => todo.status == TodoStatus.onHold)
            .toList();
        break;
      case ViewMode.completed:
        filtered = filtered
            .where((todo) => todo.status == TodoStatus.completed)
            .toList();
        break;
    }

    _filteredTodos = filtered;
  }

  // SharedPreferences에서 할일 목록 로드
  Future<void> _loadTodos() async {
    final prefs = await SharedPreferences.getInstance();
    final todosJson = prefs.getStringList('todos') ?? [];
    setState(() {
      _todos = todosJson
          .map((json) => Todo.fromJson(jsonDecode(json)))
          .toList()
          .reversed
          .toList();
      _filterTodos();
    });
  }

  // SharedPreferences에 할일 목록 저장
  Future<void> _saveTodos() async {
    final prefs = await SharedPreferences.getInstance();
    final todosJson = _todos.map((todo) => jsonEncode(todo.toJson())).toList();
    await prefs.setStringList('todos', todosJson);
  }

  // 할일 추가
  void _addTodo() {
    _textController.clear();
    _descriptionController.clear();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.red.shade400, Colors.red.shade600],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.add_task, color: Colors.white, size: 20),
            ),
            const SizedBox(width: 12),
            const Text(
              '새 할일 추가',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.grey.shade50, Colors.grey.shade100],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.grey.shade300, width: 1),
              ),
              child: TextField(
                controller: _textController,
                decoration: const InputDecoration(
                  hintText: '할일을 입력하세요',
                  hintStyle: TextStyle(color: Colors.grey),
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.all(16),
                ),
                autofocus: true,
                maxLines: 1,
                style: const TextStyle(fontSize: 16),
              ),
            ),
            const SizedBox(height: 16),
            Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.grey.shade50, Colors.grey.shade100],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.grey.shade300, width: 1),
              ),
              child: TextField(
                controller: _descriptionController,
                decoration: const InputDecoration(
                  hintText: '설명을 입력하세요 (선택사항)',
                  hintStyle: TextStyle(color: Colors.grey),
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.all(16),
                ),
                maxLines: 3,
                style: const TextStyle(fontSize: 14),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(
              '취소',
              style: TextStyle(color: Colors.grey.shade600, fontSize: 16),
            ),
          ),
          ElevatedButton(
            onPressed: () {
              if (_textController.text.trim().isNotEmpty) {
                final newTodo = Todo(
                  id: _generateId(),
                  title: _textController.text.trim(),
                  description: _descriptionController.text.trim().isEmpty
                      ? null
                      : _descriptionController.text.trim(),
                  createdAt: DateTime.now(),
                );
                setState(() {
                  _todos.insert(0, newTodo);
                  _filterTodos();
                });
                _saveTodos();
                Navigator.pop(context);
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red.shade500,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            ),
            child: const Text(
              '추가',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }

  // 할일 상태 변경
  void _toggleTodoStatus(Todo todo) {
    setState(() {
      final index = _todos.indexWhere((t) => t.id == todo.id);
      if (index != -1) {
        TodoStatus newStatus;
        switch (todo.status) {
          case TodoStatus.pending:
            newStatus = TodoStatus.onHold;
            break;
          case TodoStatus.onHold:
            newStatus = TodoStatus.completed;
            break;
          case TodoStatus.completed:
            newStatus = TodoStatus.pending;
            break;
        }
        _todos[index] = todo.copyWith(status: newStatus);
        _filterTodos();
      }
    });
    _saveTodos();
  }

  // 할일 수정
  void _editTodo(Todo todo) {
    _textController.text = todo.title;
    _descriptionController.text = todo.description ?? '';

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.blue.shade400, Colors.blue.shade600],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.edit, color: Colors.white, size: 20),
            ),
            const SizedBox(width: 12),
            const Text(
              '할일 수정',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.grey.shade50, Colors.grey.shade100],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.grey.shade300, width: 1),
              ),
              child: TextField(
                controller: _textController,
                decoration: const InputDecoration(
                  hintText: '할일을 입력하세요',
                  hintStyle: TextStyle(color: Colors.grey),
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.all(16),
                ),
                autofocus: true,
                maxLines: 1,
                style: const TextStyle(fontSize: 16),
              ),
            ),
            const SizedBox(height: 16),
            Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.grey.shade50, Colors.grey.shade100],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.grey.shade300, width: 1),
              ),
              child: TextField(
                controller: _descriptionController,
                decoration: const InputDecoration(
                  hintText: '설명을 입력하세요 (선택사항)',
                  hintStyle: TextStyle(color: Colors.grey),
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.all(16),
                ),
                maxLines: 3,
                style: const TextStyle(fontSize: 14),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(
              '취소',
              style: TextStyle(color: Colors.grey.shade600, fontSize: 16),
            ),
          ),
          TextButton(
            onPressed: () {
              _deleteTodo(todo);
              Navigator.pop(context);
            },
            child: const Text(
              '삭제',
              style: TextStyle(
                color: Colors.red,
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          ElevatedButton(
            onPressed: () {
              if (_textController.text.trim().isNotEmpty) {
                setState(() {
                  final index = _todos.indexWhere((t) => t.id == todo.id);
                  if (index != -1) {
                    _todos[index] = todo.copyWith(
                      title: _textController.text.trim(),
                      description: _descriptionController.text.trim().isEmpty
                          ? null
                          : _descriptionController.text.trim(),
                    );
                    _filterTodos();
                  }
                });
                _saveTodos();
                Navigator.pop(context);
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.blue.shade500,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            ),
            child: const Text(
              '수정',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }

  // 할일 삭제
  void _deleteTodo(Todo todo) {
    setState(() {
      _todos.removeWhere((t) => t.id == todo.id);
      _filterTodos();
    });
    _saveTodos();

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Row(
          children: [
            Icon(Icons.check_circle, color: Colors.white),
            SizedBox(width: 8),
            Text('할일이 삭제되었습니다', style: TextStyle(fontWeight: FontWeight.w500)),
          ],
        ),
        backgroundColor: Colors.red.shade500,
        duration: const Duration(seconds: 2),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.all(16),
      ),
    );
  }

  // 고유 ID 생성
  String _generateId() {
    return DateTime.now().millisecondsSinceEpoch.toString() +
        Random().nextInt(1000).toString();
  }

  // 현재 날짜 포맷
  String _getCurrentDate() {
    final now = DateTime.now();
    final months = [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec',
    ];
    final weekdays = [
      'Monday',
      'Tuesday',
      'Wednesday',
      'Thursday',
      'Friday',
      'Saturday',
      'Sunday',
    ];

    return '${months[now.month - 1]} ${now.day} • ${weekdays[now.weekday - 1]}';
  }

  String _getViewModeTitle() {
    switch (_currentViewMode) {
      case ViewMode.all:
        return 'Today';
      case ViewMode.pending:
        return '대기 중';
      case ViewMode.onHold:
        return '보류';
      case ViewMode.completed:
        return '완료';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      body: SafeArea(
        child: Column(
          children: [
            // 상단 헤더
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.white, Colors.grey.shade50],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
                borderRadius: const BorderRadius.only(
                  bottomLeft: Radius.circular(32),
                  bottomRight: Radius.circular(32),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.08),
                    blurRadius: 16,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 앱 이름과 메뉴
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Container(
                            width: 40,
                            height: 40,
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                colors: [
                                  Colors.red.shade400,
                                  Colors.red.shade600,
                                ],
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                              ),
                              borderRadius: BorderRadius.circular(12),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.red.withValues(alpha: 0.3),
                                  blurRadius: 8,
                                  offset: const Offset(0, 4),
                                ),
                              ],
                            ),
                            child: const Icon(
                              Icons.task_alt,
                              color: Colors.white,
                              size: 22,
                            ),
                          ),
                          const SizedBox(width: 16),
                          const Text(
                            'MyTodo',
                            style: TextStyle(
                              fontSize: 24,
                              fontWeight: FontWeight.bold,
                              color: Colors.black87,
                            ),
                          ),
                        ],
                      ),
                      Container(
                        decoration: BoxDecoration(
                          color: Colors.grey.shade100,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: IconButton(
                          onPressed: () {
                            setState(() {
                              _isSearching = !_isSearching;
                              if (!_isSearching) {
                                _searchController.clear();
                                _filterTodos();
                              }
                            });
                          },
                          icon: Icon(
                            _isSearching ? Icons.close : Icons.search,
                            color: Colors.grey.shade600,
                            size: 20,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  // 검색창
                  if (_isSearching)
                    Container(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [Colors.grey.shade100, Colors.grey.shade200],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: Colors.grey.shade300,
                          width: 1,
                        ),
                      ),
                      child: TextField(
                        controller: _searchController,
                        decoration: const InputDecoration(
                          hintText: '할일 검색...',
                          hintStyle: TextStyle(color: Colors.grey),
                          prefixIcon: Icon(Icons.search, color: Colors.grey),
                          border: InputBorder.none,
                          contentPadding: EdgeInsets.all(16),
                        ),
                        autofocus: true,
                        style: const TextStyle(fontSize: 16),
                      ),
                    ),
                  if (_isSearching) const SizedBox(height: 20),
                  // 현재 뷰와 날짜
                  Text(
                    _getViewModeTitle(),
                    style: const TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Icon(
                        Icons.calendar_today,
                        size: 16,
                        color: Colors.grey.shade600,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        _getCurrentDate(),
                        style: TextStyle(
                          fontSize: 16,
                          color: Colors.grey.shade600,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [Colors.red.shade400, Colors.red.shade500],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.red.withValues(alpha: 0.3),
                              blurRadius: 6,
                              offset: const Offset(0, 2),
                            ),
                          ],
                        ),
                        child: Text(
                          '${_filteredTodos.length}개',
                          style: const TextStyle(
                            fontSize: 12,
                            color: Colors.white,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            // 할일 목록
            Expanded(
              child: _filteredTodos.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            width: 100,
                            height: 100,
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                colors: [
                                  Colors.grey.shade100,
                                  Colors.grey.shade200,
                                ],
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                              ),
                              borderRadius: BorderRadius.circular(50),
                            ),
                            child: Icon(
                              _isSearching ? Icons.search_off : Icons.task_alt,
                              size: 48,
                              color: Colors.grey.shade400,
                            ),
                          ),
                          const SizedBox(height: 24),
                          Text(
                            _isSearching ? '검색 결과가 없습니다' : '할일이 없습니다',
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.w600,
                              color: Colors.grey.shade600,
                            ),
                          ),
                          const SizedBox(height: 12),
                          Text(
                            _isSearching
                                ? '다른 검색어를 시도해보세요'
                                : '+ 버튼을 눌러 새 할일을 추가하세요',
                            style: TextStyle(
                              fontSize: 16,
                              color: Colors.grey.shade500,
                            ),
                          ),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(20),
                      itemCount: _filteredTodos.length,
                      itemBuilder: (context, index) {
                        return Container(
                          margin: const EdgeInsets.only(bottom: 12),
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [Colors.white, Colors.grey.shade50],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            ),
                            borderRadius: BorderRadius.circular(20),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withValues(alpha: 0.08),
                                blurRadius: 12,
                                offset: const Offset(0, 4),
                              ),
                            ],
                          ),
                          child: TodoItem(
                            todo: _filteredTodos[index],
                            onTap: () =>
                                _toggleTodoStatus(_filteredTodos[index]),
                            onLongPress: () => _editTodo(_filteredTodos[index]),
                            onDelete: () => _deleteTodo(_filteredTodos[index]),
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
      // 하단 탭바
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [Colors.white, Colors.grey.shade50],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(32),
            topRight: Radius.circular(32),
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.08),
              blurRadius: 16,
              offset: const Offset(0, -4),
            ),
          ],
        ),
        child: Padding(
          padding: const EdgeInsets.only(top: 8),
          child: BottomNavigationBar(
            currentIndex: _selectedTabIndex,
            onTap: (index) {
              setState(() {
                _selectedTabIndex = index;
                switch (index) {
                  case 0:
                    _currentViewMode = ViewMode.all;
                    break;
                  case 1:
                    _currentViewMode = ViewMode.pending;
                    break;
                  case 2:
                    _currentViewMode = ViewMode.onHold;
                    break;
                  case 3:
                    _currentViewMode = ViewMode.completed;
                    break;
                }
                _filterTodos();
              });
            },
            type: BottomNavigationBarType.fixed,
            selectedItemColor: Colors.red.shade500,
            unselectedItemColor: Colors.grey.shade500,
            backgroundColor: Colors.transparent,
            elevation: 0,
            selectedFontSize: 13,
            unselectedFontSize: 12,
            selectedLabelStyle: const TextStyle(fontWeight: FontWeight.w600),
            unselectedLabelStyle: const TextStyle(fontWeight: FontWeight.w500),
            items: const [
              BottomNavigationBarItem(icon: Icon(Icons.view_list), label: '전체'),
              BottomNavigationBarItem(
                icon: Icon(Icons.pending_actions),
                label: '대기',
              ),
              BottomNavigationBarItem(
                icon: Icon(Icons.pause_circle),
                label: '보류',
              ),
              BottomNavigationBarItem(
                icon: Icon(Icons.check_circle),
                label: '완료',
              ),
            ],
          ),
        ),
      ),
      // 플로팅 액션 버튼
      floatingActionButton: ScaleTransition(
        scale: _fabAnimation,
        child: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [Colors.red.shade400, Colors.red.shade600],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              BoxShadow(
                color: Colors.red.withValues(alpha: 0.4),
                blurRadius: 16,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: FloatingActionButton(
            onPressed: () {
              _fabController.forward().then((_) {
                _fabController.reverse();
              });
              _addTodo();
            },
            backgroundColor: Colors.transparent,
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Icon(Icons.add, color: Colors.white, size: 32),
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _textController.dispose();
    _descriptionController.dispose();
    _searchController.dispose();
    _fabController.dispose();
    super.dispose();
  }
}
