/**
 * mypage.js — 마이페이지 동작 (깡통 단계)
 *
 * 화면설계서 SCR-USER-007 기준
 * - 닉네임 / 비밀번호 / 비밀번호 확인 통합 폼
 * - 수정하기 버튼: 변경사항 없으면 비활성
 * - 탈퇴하기 → 확인 팝업 (6-1)
 *
 * 현재: 깡통 (UI 동작 위주, API 연결은 추후)
 */

document.addEventListener('DOMContentLoaded', () => {

  // ============================================
  // 1. 페이지 로드 시 사용자 정보 가져오기
  // ============================================
  // TODO: 실제 API 연결 시 활성화
  // try {
  //   const res = await api('GET', '/api/users/me/');
  //   if (res.ok) {
  //     const user = await res.json();
  //     document.getElementById('userNickname').textContent = user.nickname;
  //     document.getElementById('userEmail').textContent = user.email;
  //   }
  // } catch (err) {
  //   console.error('사용자 정보 로드 실패:', err);
  // }

  console.log('마이페이지 로드 완료 (깡통 상태)');


  // ============================================
  // 2. 입력 필드 변경 감지 → 수정하기 버튼 활성/비활성
  // ============================================
  const nicknameInput = document.getElementById('newNickname');
  const newPwInput = document.getElementById('newPassword');
  const confirmPwInput = document.getElementById('confirmPassword');
  const submitBtn = document.getElementById('submitEditBtn');

  function checkFormChanged() {
    const hasNickname = nicknameInput.value.trim().length > 0;
    const hasNewPw = newPwInput.value.length > 0;
    const hasConfirmPw = confirmPwInput.value.length > 0;
    submitBtn.disabled = !(hasNickname || (hasNewPw && hasConfirmPw));
  }

  nicknameInput.addEventListener('input', checkFormChanged);
  newPwInput.addEventListener('input', checkFormChanged);
  confirmPwInput.addEventListener('input', checkFormChanged);


  // ============================================
  // 3. 유효성 검사 함수
  // ============================================

  // 닉네임: 한글/영문/숫자 2~6자
  function validateNickname(nickname) {
    if (!nickname) return null;
    if (nickname.length < 2 || nickname.length > 6) {
      return '닉네임은 2~6자로 입력해주세요.';
    }
    const pattern = /^[가-힣a-zA-Z0-9]+$/;
    if (!pattern.test(nickname)) {
      return '한글, 영문, 숫자만 사용 가능합니다.';
    }
    return null;
  }

  // 비밀번호: 영문/숫자/특수문자 중 2종 이상, 8~16자
  function validatePassword(pw) {
    if (!pw) return null;
    if (pw.length < 8 || pw.length > 16) {
      return '비밀번호는 8~16자로 입력해주세요.';
    }
    let typeCount = 0;
    if (/[a-zA-Z]/.test(pw)) typeCount++;
    if (/[0-9]/.test(pw)) typeCount++;
    if (/[^a-zA-Z0-9]/.test(pw)) typeCount++;
    if (typeCount < 2) {
      return '영문, 숫자, 특수문자 중 2종 이상 포함해주세요.';
    }
    return null;
  }


  // ============================================
  // 4. 수정하기 폼 제출
  // ============================================
  document.getElementById('mypageEditForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const nickname = nicknameInput.value.trim();
    const newPw = newPwInput.value;
    const confirmPw = confirmPwInput.value;

    document.getElementById('newNicknameErr').textContent = '';
    document.getElementById('newPasswordErr').textContent = '';
    document.getElementById('confirmPasswordErr').textContent = '';

    const nicknameErr = validateNickname(nickname);
    if (nicknameErr) {
      document.getElementById('newNicknameErr').textContent = nicknameErr;
      return;
    }

    if (newPw || confirmPw) {
      const pwErr = validatePassword(newPw);
      if (pwErr) {
        document.getElementById('newPasswordErr').textContent = pwErr;
        return;
      }
      if (newPw !== confirmPw) {
        document.getElementById('confirmPasswordErr').textContent =
          '비밀번호가 일치하지 않습니다.';
        return;
      }
    }

    const payload = {};
    if (nickname) payload.nickname = nickname;
    if (newPw) payload.password = newPw;

    // TODO: 실제 API 연결 시 활성화
    // const res = await api('PATCH', '/api/users/me/', payload);

    // 깡통 동작 — 임시
    alert('[깡통] 수정 요청\n' + JSON.stringify(payload, null, 2));
  });


  // ============================================
  // 5. 회원 탈퇴 확정 버튼
  // ============================================
  document.getElementById('confirmWithdrawBtn').addEventListener('click', async () => {
    // TODO: 실제 API 연결 시 활성화
    // const res = await api('DELETE', '/api/users/me/');

    // 깡통 동작 — 임시
    alert('[깡통] 회원 탈퇴 요청');
    closeModal('withdrawConfirmModal');
  });


  // ============================================
  // 6. 뒤로가기 버튼 (← 채팅 화면으로)
  // ============================================
  document.getElementById('mypageBackBtn').addEventListener('click', () => {
    // TODO: 실제 라우팅 결정 후 변경
    // window.location.href = '/chat/';

    // 깡통 동작 — 임시
    alert('[깡통] 채팅 화면으로 이동');
  });

});