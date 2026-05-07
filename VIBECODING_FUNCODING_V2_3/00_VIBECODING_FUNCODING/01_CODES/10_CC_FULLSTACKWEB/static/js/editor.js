// Quill.js 에디터 초기화 및 설정
function initializeEditor(editorId, options = {}) {
    const defaultOptions = {
        theme: 'snow',
        modules: {
            toolbar: {
                container: [
                    [{ 'header': [3, false] }], // H3 제목
                    ['bold', 'italic'], // 볼드체, 이탤릭체
                    [{ 'color': [] }, { 'background': [] }], // 글자 색상, 글자 배경색상
                    [{ 'list': 'ordered' }, { 'list': 'bullet' }], // 리스트
                    ['clean'] // 서식 지우기
                ]
            },
            clipboard: {
                matchVisual: false
            }
        },
        placeholder: '내용을 입력해주세요...',
        ...options
    };

    const editor = new Quill(`#${editorId}`, defaultOptions);

    // 이미지 붙여넣기 처리
    editor.root.addEventListener('paste', (e) => {
        const clipboardData = e.clipboardData || window.clipboardData;
        const items = clipboardData.items;

        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            
            if (item.type.indexOf('image') !== -1) {
                e.preventDefault();
                const file = item.getAsFile();
                
                if (file) {
                    const reader = new FileReader();
                    
                    reader.onload = (e) => {
                        const base64 = e.target.result;
                        const range = editor.getSelection(true);
                        editor.insertEmbed(range.index, 'image', base64, 'user');
                        editor.setSelection(range.index + 1, 'silent');
                    };
                    
                    reader.readAsDataURL(file);
                }
            }
        }
    });

    return editor;
}

// 에디터에서 HTML 콘텐츠 가져오기
function getEditorContent(editor) {
    return editor.root.innerHTML;
}

// HTML 콘텐츠를 에디터에 설정하기
function setEditorContent(editor, html) {
    editor.root.innerHTML = html;
}

// 에디터 비우기
function clearEditor(editor) {
    editor.setText('');
}

// 에디터가 비어있는지 확인
function isEditorEmpty(editor) {
    const text = editor.getText().trim();
    return text.length === 0 || text === '\n';
}

// Form 제출 시 에디터 콘텐츠를 hidden input에 복사
function setupFormSubmission(editor, formId, contentFieldName = 'content') {
    const form = document.getElementById(formId);
    if (!form) return;

    // 빈 내용 체크
    form.addEventListener('htmx:before-request', (e) => {
        if (isEditorEmpty(editor)) {
            alert('내용을 입력해주세요.');
            e.preventDefault();
            return;
        }
        
        // hidden input에 content 설정
        const contentInput = document.getElementById(contentFieldName + '-input');
        if (contentInput) {
            contentInput.value = getEditorContent(editor);
        }
    });
    
    // HTMX json-enc와 호환되도록 값 추가
    form.addEventListener('htmx:configRequest', (e) => {
        const content = getEditorContent(editor);
        // JSON 페이로드에 content 추가
        if (e.detail.parameters) {
            e.detail.parameters[contentFieldName] = content;
        }
    });
}

// 전역 사용을 위해 export
window.QuillEditor = {
    initialize: initializeEditor,
    getContent: getEditorContent,
    setContent: setEditorContent,
    clear: clearEditor,
    isEmpty: isEditorEmpty,
    setupForm: setupFormSubmission
};