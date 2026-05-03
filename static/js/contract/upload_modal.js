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
  uploadToServer(selectedFile);
}

// ── Django API 호출 (XHR progress 연동) ──
function uploadToServer(file) {
  const chatroomId = getChatroomId();
  const formData = new FormData();
  formData.append('file', file);

  const xhr = new XMLHttpRequest();

  // 실제 업로드 진행률 연동
  xhr.upload.addEventListener('progress', (e) => {
    if (e.lengthComputable) {
      const percent = Math.round((e.loaded / e.total) * 100);
      progressBar.style.width = percent + '%';
    }
  });

  xhr.addEventListener('load', () => {
    try {
      const data = JSON.parse(xhr.responseText);
      if (data.success) {
        document.getElementById('analyzeFileName').textContent =
          document.getElementById('uploadFileName').textContent;
        showState('analyzing');

        if (data.low_confidence) {
          document.getElementById('analyzeWarning').style.display = '';
        }

        // Step2(OCR) 완료 → Step3(추출) 진행 중으로 전환
        setStep2Done();

        // 1초 후 Step3(추출) 완료로 전환
        setTimeout(() => {
          setStep3Done();
          // 완료 표시 잠깐 보여주고 모달 닫기
          setTimeout(() => {
            closeModal();
            refreshContractInfo(chatroomId);
          }, 800);
        }, 1000);
      } else {
        alert(data.message || '업로드에 실패했습니다.');
        resetToDropzone();
      }
    } catch {
      alert('서버 오류가 발생했습니다.');
      resetToDropzone();
    }
  });

  xhr.addEventListener('error', () => {
    alert('서버 오류가 발생했습니다.');
    resetToDropzone();
  });

  xhr.open('POST', `/contract/${chatroomId}/upload/`);
  xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
  xhr.send(formData);
}

// ── 스텝 전환 헬퍼 ──
function setStep2Done() {
  // Step2: 진행 중 → 완료
  const step2 = document.getElementById('step2');
  step2.querySelector('.step-badge').className = 'step-badge done';
  step2.querySelector('.step-badge').textContent = '✓';
  step2.querySelector('.step-status').className = 'step-status done';
  step2.querySelector('.step-status').textContent = '완료';

  // Step3: 대기 → 진행 중
  const step3 = document.getElementById('step3');
  step3.querySelector('.step-badge').className = 'step-badge active';
  step3.querySelector('.step-badge').textContent = '3';
  const status3 = document.createElement('span');
  status3.className = 'step-status active';
  status3.innerHTML = '<span class="spinner"></span>진행 중';
  step3.appendChild(status3);
}

function setStep3Done() {
  // Step3: 진행 중 → 완료
  const step3 = document.getElementById('step3');
  step3.querySelector('.step-badge').className = 'step-badge done';
  step3.querySelector('.step-badge').textContent = '✓';
  const status3 = step3.querySelector('.step-status');
  if (status3) {
    status3.className = 'step-status done';
    status3.textContent = '완료';
  } else {
    const newStatus = document.createElement('span');
    newStatus.className = 'step-status done';
    newStatus.textContent = '완료';
    step3.appendChild(newStatus);
  }
}

// ── 상태 전환 ──
function showState(state) {
  const notice = document.querySelector('.upload-notice');
  const footer = document.getElementById('modalFooter');

  // 모두 초기화
  dropzone.style.display = 'none';
  uploadProgress.classList.remove('show');
  sizeError.classList.remove('show');
  analyzing.classList.remove('show');
  notice.style.display = 'none';
  footer.style.display = 'none';

  if (state === 'dropzone') {
    dropzone.style.display = '';
    notice.style.display = '';
    footer.style.display = '';
  } else if (state === 'uploadProgress') {
    uploadProgress.classList.add('show');
  } else if (state === 'sizeError') {
    sizeError.classList.add('show');
    // 푸터, 안내문구 모두 숨김 → "다시 선택" 버튼만 표시
  } else if (state === 'analyzing') {
    analyzing.classList.add('show');
  }
}

// ── 초기화 ──
function resetToDropzone() {
  selectedFile = null;
  saveBtn.disabled = true;
  progressBar.style.width = '0%';
  document.getElementById('analyzeProgressBar').style.width = '0%';
  document.getElementById('analyzeWarning').style.display = 'none';
  // 스텝 상태 초기화
  const step2 = document.getElementById('step2');
  step2.querySelector('.step-badge').className = 'step-badge active';
  step2.querySelector('.step-badge').textContent = '2';
  step2.querySelector('.step-status').className = 'step-status active';
  step2.querySelector('.step-status').innerHTML = '<span class="spinner"></span>진행 중';
  const step3 = document.getElementById('step3');
  step3.querySelector('.step-badge').className = 'step-badge pending';
  step3.querySelector('.step-badge').textContent = '3';
  const step3Status = step3.querySelector('.step-status');
  if (step3Status) step3Status.remove();
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
