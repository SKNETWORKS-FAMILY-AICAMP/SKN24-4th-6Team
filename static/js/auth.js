function getCsrf() {
  return document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '';
}

async function api(method, url, data) {
  return fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
    credentials: 'same-origin',
    body: data ? JSON.stringify(data) : undefined,
  });
}

// ════════════════════════════════════
//  로그인
// ════════════════════════════════════
document.getElementById('loginForm').onsubmit = async e => {
  e.preventDefault();
  document.getElementById('loginEmailErr').textContent = '';
  document.getElementById('loginPwErr').textContent = '';

  const res = await api('POST', '/api/users/login/', {
    email: document.getElementById('loginEmail').value,
    password: document.getElementById('loginPw').value,
  });

  if (res.ok) {
    location.href = '/';
  } else {
    const data = await res.json();
    document.getElementById('loginEmailErr').textContent = data.error ?? '이메일 또는 비밀번호를 확인해주세요.';
  }
};

// ════════════════════════════════════
//  회원가입
// ════════════════════════════════════
let signupTimerIv;

function startSignupTimer() {
  let secs = 180;
  clearInterval(signupTimerIv);
  const el = document.getElementById('signupTimer');
  el.textContent = '3:00';
  signupTimerIv = setInterval(() => {
    secs--;
    el.textContent = `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}`;
    if (secs <= 0) { clearInterval(signupTimerIv); el.textContent = '0:00'; }
  }, 1000);
}

async function signupSendCode() {
  document.getElementById('signupEmailErr').textContent = '';
  const res = await api('POST', '/api/users/email/send/', {
    email: document.getElementById('signupEmail').value,
    purpose: 'SIGNUP',
  });
  if (res.ok) {
    document.getElementById('signupSendBtn').disabled = true;
    document.getElementById('signupCode').disabled = false;
    document.getElementById('signupVerifyBtn').disabled = false;
    startSignupTimer();
  } else {
    const data = await res.json();
    document.getElementById('signupEmailErr').textContent =
      data.errors?.email?.[0] ?? data.errors?.non_field_errors?.[0] ?? '오류가 발생했습니다.';
  }
}

async function signupVerifyCode() {
  document.getElementById('signupCodeErr').textContent = '';
  const res = await api('POST', '/api/users/email/verify/', {
    email: document.getElementById('signupEmail').value,
    code: document.getElementById('signupCode').value,
    purpose: 'SIGNUP',
  });
  if (res.ok) {
    clearInterval(signupTimerIv);
    document.getElementById('signupCode').disabled = true;
    document.getElementById('signupVerifyBtn').disabled = true;
    document.getElementById('signupEmail').disabled = true;
    document.getElementById('signupPw').disabled = false;
    document.getElementById('signupPw2').disabled = false;
    document.getElementById('signupNickname').disabled = false;
    document.getElementById('signupBtn').disabled = false;
    document.getElementById('signupTimer').textContent = '✓';
  } else {
    const data = await res.json();
    document.getElementById('signupCodeErr').textContent =
      data.errors?.code?.[0] ?? '인증코드가 일치하지 않습니다.';
  }
}

async function signup() {
  ['signupPwErr', 'signupPw2Err', 'signupNickErr'].forEach(id => {
    document.getElementById(id).textContent = '';
  });
  const res = await api('POST', '/api/users/signup/', {
    email: document.getElementById('signupEmail').value,
    nickname: document.getElementById('signupNickname').value,
    password: document.getElementById('signupPw').value,
    password_confirm: document.getElementById('signupPw2').value,
  });
  if (res.ok) {
    alert('회원가입이 완료되었습니다. 로그인 해주세요.');
    closeModal('signupModal');
    openModal('loginModal');
  } else {
    const data = await res.json();
    if (data.errors) {
      document.getElementById('signupPwErr').textContent = data.errors.password?.[0] ?? '';
      document.getElementById('signupPw2Err').textContent = data.errors.password_confirm?.[0] ?? '';
      document.getElementById('signupNickErr').textContent = data.errors.nickname?.[0] ?? '';
    }
  }
}

// ════════════════════════════════════
//  비밀번호 재설정
// ════════════════════════════════════
let resetTimerIv;

function startResetTimer() {
  let secs = 180;
  clearInterval(resetTimerIv);
  const el = document.getElementById('resetTimer');
  el.textContent = '3:00';
  resetTimerIv = setInterval(() => {
    secs--;
    el.textContent = `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}`;
    if (secs <= 0) { clearInterval(resetTimerIv); el.textContent = '0:00'; }
  }, 1000);
}

async function resetSendCode() {
  document.getElementById('resetEmailErr').textContent = '';
  const res = await api('POST', '/api/users/email/send/', {
    email: document.getElementById('resetEmail').value,
    purpose: 'RESET',
  });
  if (res.ok) {
    document.getElementById('resetSendBtn').disabled = true;
    document.getElementById('resetCode').disabled = false;
    document.getElementById('resetVerifyBtn').disabled = false;
    startResetTimer();
  } else {
    const data = await res.json();
    document.getElementById('resetEmailErr').textContent =
      data.errors?.email?.[0] ?? data.errors?.non_field_errors?.[0] ?? '오류가 발생했습니다.';
  }
}

async function resetVerifyCode() {
  document.getElementById('resetCodeErr').textContent = '';
  const res = await api('POST', '/api/users/email/verify/', {
    email: document.getElementById('resetEmail').value,
    code: document.getElementById('resetCode').value,
    purpose: 'RESET',
  });
  if (res.ok) {
    clearInterval(resetTimerIv);
    document.getElementById('resetCode').disabled = true;
    document.getElementById('resetVerifyBtn').disabled = true;
    document.getElementById('resetEmail').disabled = true;
    document.getElementById('resetPw').disabled = false;
    document.getElementById('resetPw2').disabled = false;
    document.getElementById('resetBtn').disabled = false;
    document.getElementById('resetTimer').textContent = '✓';
  } else {
    const data = await res.json();
    document.getElementById('resetCodeErr').textContent =
      data.errors?.code?.[0] ?? '인증코드가 일치하지 않습니다.';
  }
}

async function resetPw() {
  ['resetPwErr', 'resetPw2Err'].forEach(id => {
    document.getElementById(id).textContent = '';
  });
  const res = await api('POST', '/api/users/password/reset/', {
    email: document.getElementById('resetEmail').value,
    password: document.getElementById('resetPw').value,
    password_confirm: document.getElementById('resetPw2').value,
  });
  if (res.ok) {
    alert('비밀번호가 변경되었습니다. 다시 로그인 해주세요.');
    closeModal('resetModal');
    openModal('loginModal');
  } else {
    const data = await res.json();
    if (data.errors) {
      document.getElementById('resetPwErr').textContent = data.errors.password?.[0] ?? '';
      document.getElementById('resetPw2Err').textContent = data.errors.password_confirm?.[0] ?? '';
    }
  }
}
