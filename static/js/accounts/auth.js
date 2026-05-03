function getCsrf() {
  return document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '';
}

async function api(method, url, data) {
  try {
    return await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      credentials: 'same-origin',
      body: data ? JSON.stringify(data) : undefined,
    });
  } catch {
    return new Response(JSON.stringify({ error: '네트워크 오류가 발생했습니다.' }), { status: 503 });
  }
}

// ════════════════════════════════════
//  로그인
// ════════════════════════════════════
document.getElementById('loginForm').onsubmit = async e => {
  e.preventDefault();
  document.getElementById('loginEmailErr').textContent = '';
  document.getElementById('loginPwErr').textContent = '';

  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPw').value;

  if (!email) {
    document.getElementById('loginEmailErr').textContent = '이메일을 입력해주세요.';
    return;
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    document.getElementById('loginEmailErr').textContent = '이메일 형식이 올바르지 않습니다.';
    return;
  }
  if (!password) {
    document.getElementById('loginPwErr').textContent = '비밀번호를 입력해주세요.';
    return;
  }

  const res = await api('POST', '/api/users/login/', { email, password });

  if (res.ok) {
    location.href = '/chat/';
  } else {
    const data = await res.json();
    if (data.field === 'password') {
      document.getElementById('loginPwErr').textContent = data.error;
    } else {
      document.getElementById('loginEmailErr').textContent = data.error;
    }
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
    if (secs <= 0) {
      clearInterval(signupTimerIv);
      el.textContent = '0:00';
      document.getElementById('signupCodeErr').textContent = '인증시간이 만료 되었습니다.';
      document.getElementById('signupVerifyBtn').disabled = true;
      document.getElementById('signupSendBtn').disabled = false;
    }
  }, 1000);
}

async function signupSendCode() {
  document.getElementById('signupEmailErr').textContent = '';
  document.getElementById('signupCodeErr').textContent = '';

  const email = document.getElementById('signupEmail').value.trim();
  if (!email) {
    document.getElementById('signupEmailErr').textContent = '이메일을 입력해주세요.';
    return;
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    document.getElementById('signupEmailErr').textContent = '올바른 이메일 형식을 입력해주세요.';
    return;
  }

  document.getElementById('signupSendBtn').disabled = true;

  const res = await api('POST', '/api/users/email/send/', { email, purpose: 'SIGNUP' });
  if (res.ok) {
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

  const code = document.getElementById('signupCode').value.trim();
  if (!code) {
    document.getElementById('signupCodeErr').textContent = '인증코드를 입력해주세요.';
    return;
  }

  const res = await api('POST', '/api/users/email/verify/', {
    email: document.getElementById('signupEmail').value,
    code,
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
    document.getElementById('signupTimer').textContent = '';
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

  const password = document.getElementById('signupPw').value;
  const password_confirm = document.getElementById('signupPw2').value;
  const nickname = document.getElementById('signupNickname').value.trim();

  if (!password) {
    document.getElementById('signupPwErr').textContent = '비밀번호를 입력해주세요.';
    return;
  }
  const pwHasLetter  = /[a-zA-Z]/.test(password);
  const pwHasNumber  = /[0-9]/.test(password);
  const pwHasSpecial = /[^a-zA-Z0-9]/.test(password);
  if (password.length < 8 || password.length > 16 ||
      [pwHasLetter, pwHasNumber, pwHasSpecial].filter(Boolean).length < 2) {
    document.getElementById('signupPwErr').textContent = '비밀번호 형식이 잘못 되었습니다.';
    return;
  }
  if (!password_confirm) {
    document.getElementById('signupPw2Err').textContent = '비밀번호 확인을 입력해주세요.';
    return;
  }
  if (password !== password_confirm) {
    document.getElementById('signupPw2Err').textContent = '비밀번호가 일치하지 않습니다.';
    return;
  }
  if (!nickname) {
    document.getElementById('signupNickErr').textContent = '닉네임을 입력해주세요.';
    return;
  }

  const res = await api('POST', '/api/users/', {
    email: document.getElementById('signupEmail').value,
    nickname,
    password,
    password_confirm,
  });
  if (res.ok) {
    alert('회원가입이 완료되었습니다.');
    closeModal('signupModal');
    openModal('loginModal');
  } else {
    const data = await res.json();
    if (data.errors) {
      document.getElementById('signupPwErr').textContent = data.errors.password?.[0] ?? '';
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
    if (secs <= 0) {
      clearInterval(resetTimerIv);
      el.textContent = '0:00';
      document.getElementById('resetCodeErr').textContent = '인증시간이 만료 되었습니다.';
      document.getElementById('resetVerifyBtn').disabled = true;
      document.getElementById('resetSendBtn').disabled = false;
    }
  }, 1000);
}

async function resetSendCode() {
  document.getElementById('resetEmailErr').textContent = '';
  document.getElementById('resetCodeErr').textContent = '';

  const email = document.getElementById('resetEmail').value.trim();
  if (!email) {
    document.getElementById('resetEmailErr').textContent = '이메일을 입력해주세요.';
    return;
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    document.getElementById('resetEmailErr').textContent = '올바른 이메일 형식을 입력해주세요.';
    return;
  }

  document.getElementById('resetSendBtn').disabled = true;

  const res = await api('POST', '/api/users/email/send/', { email, purpose: 'RESET' });
  if (res.ok) {
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

  const code = document.getElementById('resetCode').value.trim();
  if (!code) {
    document.getElementById('resetCodeErr').textContent = '인증코드를 입력해주세요.';
    return;
  }

  const res = await api('POST', '/api/users/email/verify/', {
    email: document.getElementById('resetEmail').value,
    code,
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
    document.getElementById('resetTimer').textContent = '';
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

  const password = document.getElementById('resetPw').value;
  const password_confirm = document.getElementById('resetPw2').value;

  if (!password) {
    document.getElementById('resetPwErr').textContent = '비밀번호를 입력해주세요.';
    return;
  }
  const pwHasLetter  = /[a-zA-Z]/.test(password);
  const pwHasNumber  = /[0-9]/.test(password);
  const pwHasSpecial = /[^a-zA-Z0-9]/.test(password);
  if (password.length < 8 || password.length > 16 ||
      [pwHasLetter, pwHasNumber, pwHasSpecial].filter(Boolean).length < 2) {
    document.getElementById('resetPwErr').textContent = '비밀번호 형식이 잘못 되었습니다.';
    return;
  }
  if (!password_confirm) {
    document.getElementById('resetPw2Err').textContent = '비밀번호 확인을 입력해주세요.';
    return;
  }
  if (password !== password_confirm) {
    document.getElementById('resetPw2Err').textContent = '비밀번호가 일치하지 않습니다.';
    return;
  }

  const res = await api('POST', '/api/users/password/reset/', {
    email: document.getElementById('resetEmail').value,
    password,
    password_confirm,
  });
  if (res.ok) {
    alert('비밀번호가 변경되었습니다.');
    closeModal('resetModal');
    openModal('loginModal');
  } else {
    const data = await res.json();
    if (data.errors) {
      document.getElementById('resetPwErr').textContent = data.errors.password?.[0] ?? '';
    }
  }
}
