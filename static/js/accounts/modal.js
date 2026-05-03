/**
 * modal.js — 모달 열기/닫기 공통 유틸리티
 *
 * 사용법:
 *   openModal('loginModal')   // id가 loginModal인 모달 열기
 *   closeModal('loginModal')  // id가 loginModal인 모달 닫기
 *
 * HTML 구조:
 *   <div class="modal-overlay" id="loginModal">
 *     <div class="modal-card">
 *       <button class="modal-close" onclick="closeModal('loginModal')">×</button>
 *       <!-- 내용 -->
 *     </div>
 *   </div>
 *
 * 닫기 방법: × 버튼 클릭 / 배경(오버레이) 클릭 / ESC 키
 */

// .active 클래스를 추가해 모달을 표시하고, 배경 스크롤을 막음
function openModal(id) {
  document.getElementById(id).classList.add('active');
  document.body.style.overflow = 'hidden';
}

// .active 클래스를 제거해 모달을 숨기고, 배경 스크롤을 복구 + 내용 초기화
function closeModal(id) {
  document.getElementById(id).classList.remove('active');
  document.body.style.overflow = '';
  _resetModalContent(id);
}

function _clearVals(ids) {
  ids.forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
}

function _clearErrs(ids) {
  ids.forEach(id => { const el = document.getElementById(id); if (el) el.textContent = ''; });
}

function _setDisabled(ids, disabled) {
  ids.forEach(id => { const el = document.getElementById(id); if (el) el.disabled = disabled; });
}

function _resetModalContent(id) {
  if (id === 'loginModal') {
    _clearVals(['loginEmail', 'loginPw']);
    _clearErrs(['loginEmailErr', 'loginPwErr']);

  } else if (id === 'signupModal') {
    _clearVals(['signupEmail', 'signupCode', 'signupPw', 'signupPw2', 'signupNickname']);
    _clearErrs(['signupEmailErr', 'signupCodeErr', 'signupPwErr', 'signupPw2Err', 'signupNickErr']);
    // 타이머 표시 초기화 (백엔드 타이머는 계속 유효)
    const signupTimer = document.getElementById('signupTimer');
    if (signupTimer) signupTimer.textContent = '';
    // 입력 단계 초기화
    _setDisabled(['signupEmail'], false);
    _setDisabled(['signupCode', 'signupPw', 'signupPw2', 'signupNickname'], true);
    _setDisabled(['signupSendBtn'], false);
    _setDisabled(['signupVerifyBtn', 'signupBtn'], true);

  } else if (id === 'termsModal') {
    ['termsPrivacy', 'termsAI'].forEach(cid => {
      const el = document.getElementById(cid);
      if (el) el.checked = false;
    });
    const nextBtn = document.getElementById('termsNextBtn');
    if (nextBtn) nextBtn.disabled = true;

  } else if (id === 'resetModal') {
    _clearVals(['resetEmail', 'resetCode', 'resetPw', 'resetPw2']);
    _clearErrs(['resetEmailErr', 'resetCodeErr', 'resetPwErr', 'resetPw2Err']);
    // 타이머 표시 초기화 (백엔드 타이머는 계속 유효)
    const resetTimer = document.getElementById('resetTimer');
    if (resetTimer) resetTimer.textContent = '';
    // 입력 단계 초기화
    _setDisabled(['resetEmail'], false);
    _setDisabled(['resetCode', 'resetPw', 'resetPw2'], true);
    _setDisabled(['resetSendBtn'], false);
    _setDisabled(['resetVerifyBtn', 'resetBtn'], true);
  }
}

// 오버레이(배경) 클릭 시 닫기 — 카드 내부 클릭은 무시
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) closeModal(overlay.id);
  });
});

// ESC 키로 현재 열려 있는 모달 모두 닫기
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.active').forEach(m => closeModal(m.id));
  }
});

// ── 약관 동의 모달 ──

// 필수 항목 두 가지 모두 체크해야 다음 버튼 활성화
function checkTerms() {
  document.getElementById('termsNextBtn').disabled =
    !document.getElementById('termsPrivacy').checked ||
    !document.getElementById('termsAI').checked;
}

// 모달 닫을 때 체크박스 초기화
function closeTermsModal() {
  closeModal('termsModal');
}
