"use strict";

/* ══════════════════════════════
   유틸
══════════════════════════════ */
function getMpCsrf() {
  const c = document.cookie.split(";").find(s => s.trim().startsWith("csrftoken="));
  return c ? decodeURIComponent(c.split("=")[1]) : "";
}

async function mpFetch(url, options = {}) {
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getMpCsrf(),
      ...(options.headers || {}),
    },
    ...options,
  });
  let data = null;
  try { data = await res.json(); } catch {}
  return { ok: res.ok, status: res.status, data };
}

/* ══════════════════════════════
   DOM
══════════════════════════════ */
const btnProfile        = document.getElementById("btnProfile");

const modalSelfVerify   = document.getElementById("modalSelfVerify");
const verifyPasswordEl  = document.getElementById("verifyPassword");
const verifyErrEl       = document.getElementById("verifyErr");
const btnVerifyConfirm  = document.getElementById("btnVerifyConfirm");
const btnVerifyCancel   = document.getElementById("btnVerifyCancel");

const modalMypage       = document.getElementById("modalMypage");
const mypageAvatarEl    = document.getElementById("mypageAvatar");
const mypageNicknameEl  = document.getElementById("mypageNickname");
const mypageEmailEl     = document.getElementById("mypageEmail");
const mypageEditForm    = document.getElementById("mypageEditForm");
const newNicknameEl     = document.getElementById("newNickname");
const newPasswordEl     = document.getElementById("newPassword");
const confirmPasswordEl = document.getElementById("confirmPassword");
const btnMypageSubmit   = document.getElementById("btnMypageSubmit");
const btnOpenWithdraw   = document.getElementById("btnOpenWithdraw");

const modalWithdraw        = document.getElementById("modalWithdraw");
const btnWithdrawConfirm   = document.getElementById("btnWithdrawConfirm");
const btnWithdrawCancel    = document.getElementById("btnWithdrawCancel");

/* ══════════════════════════════
   모달 헬퍼
══════════════════════════════ */
function showModal(el) { el.classList.add("modal-overlay--visible"); }
function hideModal(el) { el.classList.remove("modal-overlay--visible"); }

/* ══════════════════════════════
   유효성 검사
══════════════════════════════ */
function validateNickname(v) {
  if (!v) return null;
  if (v.length < 2 || v.length > 6) return "닉네임은 2~6자로 입력해주세요.";
  if (!/^[가-힣a-zA-Z0-9]+$/.test(v)) return "한글, 영문, 숫자만 사용 가능합니다.";
  return null;
}

function validatePassword(v) {
  if (!v) return null;
  if (v.length < 8 || v.length > 16) return "비밀번호는 8~16자로 입력해주세요.";
  let cnt = 0;
  if (/[a-zA-Z]/.test(v)) cnt++;
  if (/[0-9]/.test(v))    cnt++;
  if (/[^a-zA-Z0-9]/.test(v)) cnt++;
  if (cnt < 2) return "영문, 숫자, 특수문자 중 2종 이상 포함해주세요.";
  return null;
}

function clearMypageErrors() {
  document.getElementById("newNicknameErr").textContent  = "";
  document.getElementById("newPasswordErr").textContent  = "";
  document.getElementById("confirmPasswordErr").textContent = "";
}

/* ══════════════════════════════
   본인인증 모달
══════════════════════════════ */
btnProfile.addEventListener("click", () => {
  verifyPasswordEl.value  = "";
  verifyErrEl.textContent = "";
  showModal(modalSelfVerify);
  setTimeout(() => verifyPasswordEl.focus(), 80);
});

btnVerifyCancel.addEventListener("click", () => hideModal(modalSelfVerify));

verifyPasswordEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter") btnVerifyConfirm.click();
});

btnVerifyConfirm.addEventListener("click", async () => {
  const pw = verifyPasswordEl.value;
  verifyErrEl.textContent = "";

  if (!pw) {
    verifyErrEl.textContent = "비밀번호를 입력해주세요.";
    return;
  }

  btnVerifyConfirm.disabled = true;
  const { ok, status } = await mpFetch("/api/v1/me/verify/", {
    method: "POST",
    body: JSON.stringify({ password: pw }),
  });
  btnVerifyConfirm.disabled = false;

  if (ok) {
    hideModal(modalSelfVerify);
    await loadMypageData();
    showModal(modalMypage);
  } else if (status === 401) {
    verifyErrEl.textContent = "비밀번호가 일치하지 않습니다.";
  } else {
    verifyErrEl.textContent = "오류가 발생했습니다. 다시 시도해주세요.";
  }
});

/* ══════════════════════════════
   내정보 모달 — 데이터 로드
══════════════════════════════ */
async function loadMypageData() {
  const { ok, data } = await mpFetch("/api/v1/me/");
  if (!ok || !data) return;

  const { nickname, email } = data;
  mypageAvatarEl.textContent   = (nickname || "?")[0].toUpperCase();
  mypageNicknameEl.textContent = nickname || "";
  mypageEmailEl.textContent    = email    || "";

  newNicknameEl.placeholder = nickname || "";
  newNicknameEl.value       = "";
  newPasswordEl.value       = "";
  confirmPasswordEl.value   = "";
  btnMypageSubmit.disabled  = true;
  clearMypageErrors();
}

/* ── 수정하기 버튼 활성/비활성 ── */
function checkMypageChanged() {
  const hasNick    = newNicknameEl.value.trim().length > 0;
  const hasPw      = newPasswordEl.value.length > 0;
  const hasConfirm = confirmPasswordEl.value.length > 0;
  btnMypageSubmit.disabled = !(hasNick || (hasPw && hasConfirm));
}

newNicknameEl.addEventListener("input", checkMypageChanged);
newPasswordEl.addEventListener("input", checkMypageChanged);
confirmPasswordEl.addEventListener("input", checkMypageChanged);

/* ── 수정하기 제출 ── */
mypageEditForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearMypageErrors();

  const nickname   = newNicknameEl.value.trim();
  const pw         = newPasswordEl.value;
  const confirmPw  = confirmPasswordEl.value;

  const nicknameErr = validateNickname(nickname);
  if (nicknameErr) {
    document.getElementById("newNicknameErr").textContent = nicknameErr;
    return;
  }

  if (pw || confirmPw) {
    const pwErr = validatePassword(pw);
    if (pwErr) {
      document.getElementById("newPasswordErr").textContent = pwErr;
      return;
    }
    if (pw !== confirmPw) {
      document.getElementById("confirmPasswordErr").textContent = "비밀번호가 일치하지 않습니다.";
      return;
    }
  }

  const payload = {};
  if (nickname) payload.nickname = nickname;
  if (pw) { payload.password = pw; payload.password_confirm = confirmPw; }

  btnMypageSubmit.disabled = true;
  const { ok, data } = await mpFetch("/api/v1/me/", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  btnMypageSubmit.disabled = false;

  if (ok) {
    const changed = data?.changed || [];
    if (changed.includes("password")) {
      window.location.href = "/login/";
    } else {
      window.location.reload();
    }
    return;
  }

  const errs = data?.errors || {};
  if (errs.nickname)         document.getElementById("newNicknameErr").textContent  = errs.nickname[0];
  if (errs.password)         document.getElementById("newPasswordErr").textContent  = errs.password[0];
  if (errs.password_confirm) document.getElementById("confirmPasswordErr").textContent = errs.password_confirm[0];
  if (!errs.nickname && !errs.password && !errs.password_confirm) {
    alert("오류가 발생했습니다. 다시 시도해주세요.");
  }
});

/* ══════════════════════════════
   탈퇴 모달
══════════════════════════════ */
btnOpenWithdraw.addEventListener("click", () => showModal(modalWithdraw));

btnWithdrawCancel.addEventListener("click", () => hideModal(modalWithdraw));

btnWithdrawConfirm.addEventListener("click", async () => {
  btnWithdrawConfirm.disabled = true;
  const { ok, status } = await mpFetch("/api/v1/me/", { method: "DELETE" });
  if (ok || status === 204) {
    window.location.href = "/";
  } else {
    btnWithdrawConfirm.disabled = false;
    alert("오류가 발생했습니다. 다시 시도해주세요.");
  }
});

/* ══════════════════════════════
   모달 바깥 클릭 시 닫기
══════════════════════════════ */
[modalSelfVerify, modalMypage, modalWithdraw].forEach(modal => {
  modal.addEventListener("click", (e) => {
    if (e.target === modal) hideModal(modal);
  });
});
