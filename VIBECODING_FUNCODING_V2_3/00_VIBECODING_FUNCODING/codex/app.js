// 앱 상태
const state = {
    records: [],
    isLoading: false,
    editingRecordId: null,
    isEditSubmitting: false
};

// DOM 요소
const elements = {
    recordInput: document.getElementById('record-input'),
    saveButton: document.getElementById('save-button'),
    recordsList: document.getElementById('records-list'),
    loadingState: document.getElementById('loading-state'),
    emptyState: document.getElementById('empty-state'),
    totalCount: document.getElementById('total-count'),
    weekCount: document.getElementById('week-count'),
    toast: document.getElementById('toast'),
    toastMessage: document.getElementById('toast-message'),
    editModal: document.getElementById('edit-modal'),
    editInput: document.getElementById('edit-input'),
    updateRecordButton: document.getElementById('update-record-button'),
    cancelEditButton: document.getElementById('cancel-edit'),
    closeEditButton: document.getElementById('close-edit')
};

// 토스트 알림 표시
function showToast(message, duration = 3000) {
    elements.toastMessage.textContent = message;
    elements.toast.classList.remove('hidden');
    elements.toast.classList.add('fade-in');

    setTimeout(() => {
        elements.toast.classList.add('hidden');
        elements.toast.classList.remove('fade-in');
    }, duration);
}

// 날짜 포맷팅
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '방금 전';
    if (minutes < 60) return `${minutes}분 전`;
    if (hours < 24) return `${hours}시간 전`;
    if (days < 7) return `${days}일 전`;

    const month = date.getMonth() + 1;
    const day = date.getDate();
    return `${month}월 ${day}일`;
}

// 이번 주 시작 날짜 가져오기
function getWeekStart() {
    const now = new Date();
    const day = now.getDay();
    const diff = now.getDate() - day;
    return new Date(now.setDate(diff));
}

// 통계 업데이트
function updateStats() {
    const total = state.records.length;
    const weekStart = getWeekStart();
    const weekRecords = state.records.filter(r => new Date(r.createdAt) >= weekStart);

    elements.totalCount.textContent = `${total}개`;
    elements.weekCount.textContent = `${weekRecords.length}개`;
}

// 기록 렌더링
function renderRecords() {
    if (state.records.length === 0) {
        elements.recordsList.classList.add('hidden');
        elements.emptyState.classList.remove('hidden');
        return;
    }

    elements.emptyState.classList.add('hidden');
    elements.recordsList.classList.remove('hidden');

    elements.recordsList.innerHTML = state.records
        .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
        .map(record => `
            <div class="toss-card bg-white rounded-2xl shadow-sm p-5 fade-in" data-id="${record.id}">
                <div class="flex justify-between items-start mb-2">
                    <p class="text-sm text-gray-500">${formatDate(record.createdAt)}</p>
                    <div class="flex items-center gap-2">
                        <button
                            onclick="openEditModal('${record.id}')"
                            class="text-gray-400 hover:text-blue-500 transition-colors text-sm font-medium">
                            수정
                        </button>
                        <button
                            onclick="deleteRecord('${record.id}')"
                            class="text-gray-400 hover:text-red-500 transition-colors">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                        </button>
                    </div>
                </div>
                <p class="text-gray-900 leading-relaxed whitespace-pre-wrap">${escapeHtml(record.content)}</p>
            </div>
        `).join('');
}

// HTML 이스케이프
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 로딩 상태 토글
function setLoading(loading) {
    state.isLoading = loading;

    if (loading) {
        elements.saveButton.disabled = true;
        elements.saveButton.innerHTML = '<div class="loading-spinner mx-auto"></div>';
        elements.loadingState.classList.remove('hidden');
    } else {
        elements.saveButton.disabled = false;
        elements.saveButton.innerHTML = '<span>기록하기</span>';
        elements.loadingState.classList.add('hidden');
    }
}

// 기록 불러오기
async function loadRecords() {
    try {
        setLoading(true);
        const response = await fetch('/api/records');

        if (!response.ok) {
            throw new Error('기록을 불러오는데 실패했습니다');
        }

        const data = await response.json();
        state.records = data.records || [];
        renderRecords();
        updateStats();
    } catch (error) {
        console.error('Error loading records:', error);
        showToast('기록을 불러오는데 실패했습니다');
        state.records = [];
        renderRecords();
    } finally {
        setLoading(false);
    }
}

// 기록 저장
async function saveRecord() {
    const content = elements.recordInput.value.trim();

    if (!content) {
        showToast('내용을 입력해주세요');
        elements.recordInput.focus();
        return;
    }

    try {
        setLoading(true);

        const response = await fetch('/api/records', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content })
        });

        if (!response.ok) {
            throw new Error('기록 저장에 실패했습니다');
        }

        const data = await response.json();

        // 새 기록 추가
        state.records.unshift(data.record);
        elements.recordInput.value = '';

        renderRecords();
        updateStats();
        showToast('✅ 기록했어요!');

    } catch (error) {
        console.error('Error saving record:', error);
        showToast('기록 저장에 실패했습니다');
    } finally {
        setLoading(false);
    }
}

// 기록 삭제
async function deleteRecord(id) {
    if (!confirm('이 기록을 삭제하시겠어요?')) {
        return;
    }

    try {
        const response = await fetch(`/api/records/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('기록 삭제에 실패했습니다');
        }

        state.records = state.records.filter(r => r.id !== id);
        renderRecords();
        updateStats();
        showToast('🗑️ 삭제했어요');

    } catch (error) {
        console.error('Error deleting record:', error);
        showToast('삭제에 실패했습니다');
    }
}

// 수정 모달 열기
function openEditModal(id) {
    const target = state.records.find(r => r.id === id);

    if (!target) {
        showToast('기록을 찾을 수 없습니다');
        return;
    }

    state.editingRecordId = id;
    elements.editInput.value = target.content;
    elements.editModal.classList.remove('hidden');
    elements.editInput.focus();
}

// 수정 모달 닫기
function closeEditModal() {
    state.editingRecordId = null;
    elements.editInput.value = '';
    elements.editModal.classList.add('hidden');
    setEditLoading(false);
}

// 수정 로딩 상태
function setEditLoading(loading) {
    state.isEditSubmitting = loading;

    if (loading) {
        elements.updateRecordButton.disabled = true;
        elements.updateRecordButton.innerHTML = '<div class="loading-spinner mx-auto"></div>';
    } else {
        elements.updateRecordButton.disabled = false;
        elements.updateRecordButton.innerHTML = '수정 완료';
    }
}

// 기록 수정
async function updateRecord() {
    if (!state.editingRecordId) {
        return;
    }

    const content = elements.editInput.value.trim();

    if (!content) {
        showToast('내용을 입력해주세요');
        elements.editInput.focus();
        return;
    }

    try {
        setEditLoading(true);
        const response = await fetch(`/api/records/${state.editingRecordId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content })
        });

        if (!response.ok) {
            throw new Error('기록 수정에 실패했습니다');
        }

        const data = await response.json();
        const updatedRecord = data.record;

        state.records = state.records.map(record =>
            record.id === updatedRecord.id ? updatedRecord : record
        );

        renderRecords();
        closeEditModal();
        showToast('✏️ 수정했어요');
    } catch (error) {
        console.error('Error updating record:', error);
        showToast('수정에 실패했습니다');
    } finally {
        setEditLoading(false);
    }
}

// 전역 함수로 노출 (HTML onclick에서 사용)
window.deleteRecord = deleteRecord;
window.openEditModal = openEditModal;

// 이벤트 리스너
elements.saveButton.addEventListener('click', saveRecord);
elements.updateRecordButton.addEventListener('click', updateRecord);
elements.cancelEditButton.addEventListener('click', closeEditModal);
elements.closeEditButton.addEventListener('click', closeEditModal);

elements.recordInput.addEventListener('keydown', (e) => {
    // Cmd/Ctrl + Enter로 저장
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        saveRecord();
    }
});

// 앱 초기화
document.addEventListener('DOMContentLoaded', () => {
    loadRecords();
});
