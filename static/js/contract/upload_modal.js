// upload_modal.js

const MAX_SIZE = 5 * 1024 * 1024; // 5MB

const fileInput       = document.getElementById('fileInput');
const dropzone        = document.getElementById('dropzone');
const uploadProgress  = document.getElementById('uploadProgress');
const sizeError       = document.getElementById('sizeError');
const analyzing       = document.getElementById('analyzing');
const saveBtn         = document.getElementById('saveBtn');
const cancelBtn       = document.getElementById('cancelBtn');
const reselectBtn     = document.getElementById('reselectBtn');
const progressBar     = document.getElementById('progressBar');
const progressLabel   = document.getElementById('progressLabel');

let selectedFile = null;

// 드롭존 원본 HTML 저장 (초기화 시 복구용)
const dropzoneOriginalHTML = dropzone.innerHTML;

// ── 드래그앤드롭 ──
dropzone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropzone.classList.add('drag-over');
});
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

// ── 파일 선택 ──
fileInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) handleFile(file);
});

// ── 버튼 이벤트 ──
saveBtn.addEventListener('click', startUpload);
cancelBtn.addEventListener('click', closeModal);
reselectBtn.addEventListener('click', resetToDropzone);

// ── 파일 검증 ──
function handleFile(file) {
  if (!file.name.endsWith('.pdf')) {
    alert('PDF 파일만 업로드 가능합니다.');
    return;
  }
  if (file.size > MAX_SIZE) {
    showState('sizeError');
    return;
  }
  selectedFile = file;
  saveBtn.disabled = false;
  document.getElementById('uploadFileName').textContent = file.name;
  document.getElementById('analyzeFileName').textContent = file.name;

  // 드롭존 UI → 파일 선택 완료 상태로 변경
  const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
  dropzone.innerHTML = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"
      style="width:40px;height:40px;color:var(--color-primary);margin:0 auto 12px;display:block;">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
      <path d="M14 2v6h6"/>
    </svg>
    <div style="font-size:15px;font-weight:600;color:var(--color-fg);margin-bottom:4px;">${file.name}</div>
    <div style="font-size:13px;color:var(--color-fg-muted);margin-bottom:10px;">${sizeMB}MB</div>
    <div style="font-size:13px;color:var(--color-accent);font-weight:500;">✓ 업로드 준비 완료</div>
    <div style="font-size:12px;color:var(--color-fg-muted);margin-top:8px;">다른 파일을 선택하려면 클릭하세요</div>
    <input type="file" id="fileInput" accept=".pdf"
      style="position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%;">
  `;

  // 새로 생성된 fileInput에 이벤트 재등록
  document.getElementById('fileInput').addEventListener('change', (e) => {
    const newFile = e.target.files[0];
    if (newFile) handleFile(newFile);
  });
}

// ── 업로드 시작 ──
function startUpload() {
  if (!selectedFile) return;
  showState('uploadProgress');
  saveBtn.disabled = true;

  // 진행 바 애니메이션 (업로드 시뮬레이션)
  let progress = 0;
  const interval = setInterval(() => {
    progress += 10;
    progressBar.style.width = progress + '%';
    progressLabel.textContent = `업로드 중... ${progress}%`;
    if (progress >= 100) {
      clearInterval(interval);
      progressLabel.textContent = '업로드 완료!';
      // analyzing 화면은 API 성공 후에만 표시 → uploadToServer에서 처리
      uploadToServer(selectedFile);
    }
  }, 150);
}

// ── Django API 호출 ──
async function uploadToServer(file) {
  const chatroomId = getChatroomId();
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(`/contract/${chatroomId}/upload/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') },
      body: formData,
    });
    const data = await response.json();

    if (data.success) {
      // API 성공 → 4-5 분석 중 화면 표시
      showState('analyzing');
      setTimeout(() => {
        closeModal();
        refreshContractInfo(chatroomId);
      }, 2000);
    } else {
      // API 실패 → 드롭존으로 초기화
      alert(data.message || '업로드에 실패했습니다.');
      resetToDropzone();
    }
  } catch (err) {
    // 서버 오류 → 드롭존으로 초기화
    alert('서버 오류가 발생했습니다.');
    resetToDropzone();
  }
}

// ── 상태 전환 ──
function showState(state) {
  dropzone.style.display       = 'none';
  uploadProgress.classList.remove('show');
  sizeError.classList.remove('show');
  analyzing.classList.remove('show');

  if (state === 'dropzone') {
    dropzone.style.display = '';
  } else if (state === 'uploadProgress') {
    uploadProgress.classList.add('show');
  } else if (state === 'sizeError') {
    sizeError.classList.add('show');
  } else if (state === 'analyzing') {
    analyzing.classList.add('show');
  }
}

// ── 초기화 ──
function resetToDropzone() {
  selectedFile = null;
  saveBtn.disabled = true;
  progressBar.style.width = '0%';
  // 드롭존 원본 HTML 복구
  dropzone.innerHTML = dropzoneOriginalHTML;
  // fileInput 이벤트 재등록
  document.getElementById('fileInput').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleFile(file);
  });
  showState('dropzone');
}

// ── 모달 열기 (외부에서 호출) ──
function openUploadModal() {
  document.getElementById('uploadModalOverlay').classList.add('modal-overlay--visible');
}

// ── 모달 닫기 ──
function closeModal() {
  document.getElementById('uploadModalOverlay').classList.remove('modal-overlay--visible');
  resetToDropzone();
}

// ── 계약서 정보 갱신 (우측 바) ──
function refreshContractInfo(chatroomId) {
  fetch(`/contract/${chatroomId}/`)
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        document.dispatchEvent(new CustomEvent('contractUpdated', { detail: data }));
      }
    });
}

// ── 유틸 ──
function getChatroomId() {
  // URL 구조: /threads/{chatroom_id}/ 에서 추출
  const parts = window.location.pathname.split('/').filter(Boolean);
  return parts[1] || '';
}

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}
