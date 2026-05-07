import 'package:flutter/material.dart';
import '../models/todo.dart';

class TodoItem extends StatefulWidget {
  final Todo todo;
  final VoidCallback onTap;
  final VoidCallback onLongPress;
  final VoidCallback onDelete;

  const TodoItem({
    super.key,
    required this.todo,
    required this.onTap,
    required this.onLongPress,
    required this.onDelete,
  });

  @override
  State<TodoItem> createState() => _TodoItemState();
}

class _TodoItemState extends State<TodoItem> with TickerProviderStateMixin {
  late AnimationController _slideController;
  late AnimationController _scaleController;
  late AnimationController _rippleController;
  late Animation<Offset> _slideAnimation;
  late Animation<double> _scaleAnimation;
  late Animation<double> _rippleAnimation;

  @override
  void initState() {
    super.initState();
    _slideController = AnimationController(
      duration: const Duration(milliseconds: 400),
      vsync: this,
    );
    _scaleController = AnimationController(
      duration: const Duration(milliseconds: 150),
      vsync: this,
    );
    _rippleController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    _slideAnimation =
        Tween<Offset>(begin: const Offset(1.2, 0.0), end: Offset.zero).animate(
          CurvedAnimation(parent: _slideController, curve: Curves.elasticOut),
        );

    _scaleAnimation = Tween<double>(begin: 1.0, end: 0.97).animate(
      CurvedAnimation(parent: _scaleController, curve: Curves.easeInOut),
    );

    _rippleAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _rippleController, curve: Curves.easeOut),
    );

    _slideController.forward();
  }

  @override
  void dispose() {
    _slideController.dispose();
    _scaleController.dispose();
    _rippleController.dispose();
    super.dispose();
  }

  void _handleTapDown(TapDownDetails details) {
    _scaleController.forward();
    _rippleController.forward();
  }

  void _handleTapUp(TapUpDetails details) {
    _scaleController.reverse();
    _rippleController.reverse();
  }

  void _handleTapCancel() {
    _scaleController.reverse();
    _rippleController.reverse();
  }

  @override
  Widget build(BuildContext context) {
    return SlideTransition(
      position: _slideAnimation,
      child: ScaleTransition(
        scale: _scaleAnimation,
        child: Dismissible(
          key: Key(widget.todo.id),
          direction: DismissDirection.endToStart,
          onDismissed: (direction) {
            widget.onDelete();
          },
          background: Container(
            margin: const EdgeInsets.only(left: 12),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.red.shade300, Colors.red.shade500],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: Colors.red.withValues(alpha: 0.3),
                  blurRadius: 8,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                Container(
                  margin: const EdgeInsets.only(right: 24),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.delete_outline, color: Colors.white, size: 24),
                      SizedBox(height: 4),
                      Text(
                        '삭제',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          child: GestureDetector(
            onTapDown: _handleTapDown,
            onTapUp: _handleTapUp,
            onTapCancel: _handleTapCancel,
            onTap: widget.onTap,
            onLongPress: widget.onLongPress,
            child: Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.white, Colors.grey.shade50],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: _getBorderColor(), width: 1.5),
                boxShadow: [
                  BoxShadow(
                    color: _getStatusColor().withValues(alpha: 0.15),
                    blurRadius: 8,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 상태 인디케이터
                  Container(
                    width: 28,
                    height: 28,
                    decoration: BoxDecoration(
                      gradient: widget.todo.status == TodoStatus.completed
                          ? LinearGradient(
                              colors: [
                                _getStatusColor(),
                                _getStatusColor().withValues(alpha: 0.8),
                              ],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            )
                          : null,
                      color: widget.todo.status != TodoStatus.completed
                          ? Colors.white
                          : null,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: _getStatusColor(), width: 2.5),
                      boxShadow: [
                        BoxShadow(
                          color: _getStatusColor().withValues(alpha: 0.3),
                          blurRadius: 6,
                          offset: const Offset(0, 3),
                        ),
                      ],
                    ),
                    child: widget.todo.status == TodoStatus.completed
                        ? const Icon(Icons.check, color: Colors.white, size: 18)
                        : widget.todo.status == TodoStatus.onHold
                        ? Container(
                            margin: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: _getStatusColor(),
                              borderRadius: BorderRadius.circular(4),
                            ),
                          )
                        : AnimatedBuilder(
                            animation: _rippleAnimation,
                            builder: (context, child) {
                              return Container(
                                margin: EdgeInsets.all(
                                  8 - _rippleAnimation.value * 2,
                                ),
                                decoration: BoxDecoration(
                                  color: _getStatusColor().withValues(
                                    alpha: _rippleAnimation.value * 0.3,
                                  ),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                              );
                            },
                          ),
                  ),
                  const SizedBox(width: 20),
                  // 할일 내용
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // 제목
                        Text(
                          widget.todo.title,
                          style: TextStyle(
                            fontSize: 17,
                            fontWeight: FontWeight.w600,
                            color: _getTextColor(),
                            decoration:
                                widget.todo.status == TodoStatus.completed
                                ? TextDecoration.lineThrough
                                : TextDecoration.none,
                            decorationColor: _getTextColor(),
                            decorationThickness: 2,
                            height: 1.3,
                          ),
                        ),
                        // 설명
                        if (widget.todo.description != null &&
                            widget.todo.description!.isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 6),
                            child: Text(
                              widget.todo.description!,
                              style: TextStyle(
                                fontSize: 15,
                                color: _getDescriptionColor(),
                                decoration:
                                    widget.todo.status == TodoStatus.completed
                                    ? TextDecoration.lineThrough
                                    : TextDecoration.none,
                                decorationColor: _getDescriptionColor(),
                                height: 1.4,
                              ),
                              maxLines: 3,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        // 메타데이터
                        Padding(
                          padding: const EdgeInsets.only(top: 16),
                          child: Row(
                            children: [
                              // 시간 정보
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 10,
                                  vertical: 6,
                                ),
                                decoration: BoxDecoration(
                                  gradient: LinearGradient(
                                    colors: [
                                      Colors.grey.shade100,
                                      Colors.grey.shade200,
                                    ],
                                    begin: Alignment.topLeft,
                                    end: Alignment.bottomRight,
                                  ),
                                  borderRadius: BorderRadius.circular(10),
                                  border: Border.all(
                                    color: Colors.grey.shade300,
                                    width: 0.5,
                                  ),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(
                                      Icons.schedule,
                                      size: 14,
                                      color: Colors.grey.shade600,
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      _formatDate(widget.todo.createdAt),
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: Colors.grey.shade600,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 12),
                              // 상태 뱃지
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 10,
                                  vertical: 6,
                                ),
                                decoration: BoxDecoration(
                                  gradient: LinearGradient(
                                    colors: [
                                      _getStatusColor().withValues(alpha: 0.1),
                                      _getStatusColor().withValues(alpha: 0.2),
                                    ],
                                    begin: Alignment.topLeft,
                                    end: Alignment.bottomRight,
                                  ),
                                  borderRadius: BorderRadius.circular(10),
                                  border: Border.all(
                                    color: _getStatusColor().withValues(
                                      alpha: 0.3,
                                    ),
                                    width: 0.5,
                                  ),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Container(
                                      width: 8,
                                      height: 8,
                                      decoration: BoxDecoration(
                                        gradient: LinearGradient(
                                          colors: [
                                            _getStatusColor(),
                                            _getStatusColor().withValues(
                                              alpha: 0.8,
                                            ),
                                          ],
                                          begin: Alignment.topLeft,
                                          end: Alignment.bottomRight,
                                        ),
                                        borderRadius: BorderRadius.circular(4),
                                        boxShadow: [
                                          BoxShadow(
                                            color: _getStatusColor().withValues(
                                              alpha: 0.4,
                                            ),
                                            blurRadius: 3,
                                            offset: const Offset(0, 1),
                                          ),
                                        ],
                                      ),
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      _getStatusText(),
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: _getStatusColor(),
                                        fontWeight: FontWeight.w700,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const Spacer(),
                              // 수정 아이콘
                              GestureDetector(
                                onTap: widget.onLongPress,
                                child: Container(
                                  padding: const EdgeInsets.all(8),
                                  decoration: BoxDecoration(
                                    gradient: LinearGradient(
                                      colors: [
                                        Colors.grey.shade100,
                                        Colors.grey.shade200,
                                      ],
                                      begin: Alignment.topLeft,
                                      end: Alignment.bottomRight,
                                    ),
                                    borderRadius: BorderRadius.circular(8),
                                    border: Border.all(
                                      color: Colors.grey.shade300,
                                      width: 0.5,
                                    ),
                                  ),
                                  child: Icon(
                                    Icons.edit_note,
                                    size: 16,
                                    color: Colors.grey.shade600,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Color _getStatusColor() {
    switch (widget.todo.status) {
      case TodoStatus.pending:
        return Colors.blue.shade500;
      case TodoStatus.onHold:
        return Colors.orange.shade500;
      case TodoStatus.completed:
        return Colors.green.shade500;
    }
  }

  Color _getBorderColor() {
    switch (widget.todo.status) {
      case TodoStatus.pending:
        return Colors.blue.withValues(alpha: 0.25);
      case TodoStatus.onHold:
        return Colors.orange.withValues(alpha: 0.25);
      case TodoStatus.completed:
        return Colors.green.withValues(alpha: 0.25);
    }
  }

  Color _getTextColor() {
    switch (widget.todo.status) {
      case TodoStatus.pending:
        return Colors.black87;
      case TodoStatus.onHold:
        return Colors.orange.shade800;
      case TodoStatus.completed:
        return Colors.grey.shade500;
    }
  }

  Color _getDescriptionColor() {
    switch (widget.todo.status) {
      case TodoStatus.pending:
        return Colors.grey.shade600;
      case TodoStatus.onHold:
        return Colors.orange.shade600;
      case TodoStatus.completed:
        return Colors.grey.shade400;
    }
  }

  String _getStatusText() {
    switch (widget.todo.status) {
      case TodoStatus.pending:
        return '대기';
      case TodoStatus.onHold:
        return '보류';
      case TodoStatus.completed:
        return '완료';
    }
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);

    if (difference.inDays == 0) {
      if (difference.inHours == 0) {
        if (difference.inMinutes == 0) {
          return '방금 전';
        }
        return '${difference.inMinutes}분 전';
      }
      return '${difference.inHours}시간 전';
    } else if (difference.inDays == 1) {
      return '어제';
    } else if (difference.inDays < 7) {
      return '${difference.inDays}일 전';
    } else if (difference.inDays < 30) {
      return '${(difference.inDays / 7).floor()}주 전';
    } else {
      return '${date.month}/${date.day}';
    }
  }
}
