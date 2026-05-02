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

// .active 클래스를 제거해 모달을 숨기고, 배경 스크롤을 복구
function closeModal(id) {
  document.getElementById(id).classList.remove('active');
  document.body.style.overflow = '';
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
