"use strict";

/* ───────────────────────────────
   DOM
─────────────────────────────── */
const btnNewChat       = document.getElementById("btnNewChat");
const btnSend          = document.getElementById("btnSend");
const btnUpload        = document.getElementById("btnUpload");
const chatInput        = document.getElementById("chatInput");
const chatMessages     = document.getElementById("chatMessages");
const chatWelcome      = document.getElementById("chatWelcome");
const chatroomList     = document.getElementById("chatroomList");

const modalOverlay      = document.getElementById("modalOverlay");
const modalConfirm      = document.getElementById("modalConfirm");
const modalCancel       = document.getElementById("modalCancel");
const modalLimitOverlay = document.getElementById("modalLimitOverlay");
const modalLimitConfirm = document.getElementById("modalLimitConfirm");

// 업로드 모달
const modalUpload        = document.getElementById("modalUpload");
const uploadArea         = document.getElementById("uploadArea");
const fileInput          = document.getElementById("fileInput");
const modalUploadConfirm = document.getElementById("modalUploadConfirm");
const modalUploadCancel  = document.getElementById("modalUploadCancel");

// 우측 사이드바
const contractSidebar = document.getElementById("contractSidebar");
const btnCloseSidebar = document.getElementById("btnCloseSidebar");

/* ───────────────────────────────
   State
─────────────────────────────── */
let currentChatroomId = null;   // 현재 열려 있는 채팅방 UUID
let pendingDeleteId   = null;   // 삭제 대기 중인 채팅방 UUID
let isLoading         = false;  // AI 응답 대기 중 여부
let uploadedFile      = null;   // 업로드된 계약서 파일

/* ───────────────────────────────
   CSRF 유틸
─────────────────────────────── */
function getCsrfToken() {
  const cookie = document.cookie.split(";").find(c => c.trim().startsWith("csrftoken="));
  return cookie ? cookie.split("=")[1] : "";
}

async function apiFetch(url, options = {}) {
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
      ...(options.headers || {}),
    },
    ...options,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/* ───────────────────────────────
   채팅방 목록 카운트 갱신
─────────────────────────────── */
function getChatroomCount() {
  return chatroomList.querySelectorAll(".chatroom-item").length;
}

/* ───────────────────────────────
   새 채팅방 생성
─────────────────────────────── */
async function createChatroom() {
  if (getChatroomCount() >= 10) {
    modalLimitOverlay.classList.add("modal-overlay--visible");
    return;
  }

  try {
    const data = await apiFetch("/chat/chatrooms", {
      method: "POST",
      body: JSON.stringify({ title: "" }),
    });
    addChatroomToSidebar(data.chatroom_id, data.title || "새 채팅");
    await openChatroom(data.chatroom_id);
  } catch (e) {
    console.error("채팅방 생성 실패:", e);
  }
}

/* ───────────────────────────────
   사이드바에 채팅방 항목 추가
─────────────────────────────── */
function addChatroomToSidebar(id, title) {
  // 빈 상태 메시지 제거
  const emptyEl = chatroomList.querySelector(".chatroom-list__empty");
  if (emptyEl) emptyEl.remove();

  const li = document.createElement("li");
  li.className = "chatroom-item";
  li.dataset.id = id;
  li.innerHTML = `
    <span class="chatroom-item__title">${escapeHtml(title)}</span>
    <button class="chatroom-item__menu" data-id="${id}">···</button>
  `;
  li.addEventListener("click", (e) => {
    if (e.target.classList.contains("chatroom-item__menu")) return;
    openChatroom(id);
  });
  li.querySelector(".chatroom-item__menu").addEventListener("click", (e) => {
    e.stopPropagation();
    openDeleteModal(id);
  });
  chatroomList.prepend(li);
}

/* ───────────────────────────────
   채팅방 열기 (메시지 목록 로드)
─────────────────────────────── */
async function openChatroom(id) {
  currentChatroomId = id;

  // 사이드바 활성 상태 변경
  chatroomList.querySelectorAll(".chatroom-item").forEach(el => {
    el.classList.toggle("chatroom-item--active", el.dataset.id === id);
  });

  // 메시지 영역 초기화
  chatMessages.innerHTML = "";

  try {
    const data = await apiFetch(`/chat/chatrooms/${id}`);

    if (data.chats && data.chats.length > 0) {
      showMessagesArea();
      data.chats.forEach(chat => appendMessage(chat.role, chat.content));
    } else {
      showWelcomeArea();
    }
  } catch (e) {
    console.error("채팅방 로드 실패:", e);
  }
}

/* ───────────────────────────────
   화면 전환
─────────────────────────────── */
function showWelcomeArea() {
  chatWelcome.style.display = "flex";
  chatMessages.classList.remove("chat-messages--visible");
}

function showMessagesArea() {
  chatWelcome.style.display = "none";
  chatMessages.classList.add("chat-messages--visible");
}

/* ───────────────────────────────
   메시지 렌더링
─────────────────────────────── */
function appendMessage(role, content) {
  const div = document.createElement("div");
  div.className = `message message--${role}`;

  if (role === "assistant") {
    div.innerHTML = `
      <img class="message__avatar" src="/static/images/logo.png" alt="아이고 청년">
      <div class="message__bubble">${escapeHtml(content)}</div>
    `;
  } else {
    div.innerHTML = `<div class="message__bubble">${escapeHtml(content)}</div>`;
  }

  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

/* ───────────────────────────────
   로딩 버블
─────────────────────────────── */
function showLoadingBubble() {
  const div = document.createElement("div");
  div.className = "message message--assistant";
  div.id = "loadingBubble";
  div.innerHTML = `
    <img class="message__avatar" src="/static/images/logo.png" alt="아이고 청년">
    <div class="message__bubble message__bubble--loading">
      <span></span><span></span><span></span>
    </div>
  `;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeLoadingBubble() {
  const bubble = document.getElementById("loadingBubble");
  if (bubble) bubble.remove();
}

/* ───────────────────────────────
   메시지 전송
─────────────────────────────── */
async function sendMessage() {
  const content = chatInput.value.trim();
  if (!content || isLoading) return;

  // 채팅방이 없으면 먼저 생성
  if (!currentChatroomId) {
    if (getChatroomCount() >= 10) {
      modalLimitOverlay.classList.add("modal-overlay--visible");
      return;
    }
    try {
      const data = await apiFetch("/chat/chatrooms", {
        method: "POST",
        body: JSON.stringify({ title: content.slice(0, 30) }),
      });
      addChatroomToSidebar(data.chatroom_id, data.title || content.slice(0, 30));
      currentChatroomId = data.chatroom_id;
      setActiveChat(data.chatroom_id);
    } catch (e) {
      console.error("채팅방 생성 실패:", e);
      return;
    }
  }

  isLoading = true;
  chatInput.value = "";
  chatInput.style.height = "auto";
  btnSend.disabled = true;

  showMessagesArea();
  appendMessage("user", content);
  showLoadingBubble();

  try {
    const data = await apiFetch(`/chat/chatrooms/${currentChatroomId}/chats`, {
      method: "POST",
      body: JSON.stringify({ content }),
    });
    removeLoadingBubble();
    appendMessage("assistant", data.content);

    // 사이드바 채팅방 제목 갱신 (첫 메시지 기준)
    updateChatroomTitle(currentChatroomId, content.slice(0, 30));
  } catch (e) {
    removeLoadingBubble();
    appendMessage("assistant", "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
    console.error("메시지 전송 실패:", e);
  } finally {
    isLoading = false;
  }
}

/* ───────────────────────────────
   사이드바 채팅방 제목 갱신
─────────────────────────────── */
function updateChatroomTitle(id, title) {
  const item = chatroomList.querySelector(`.chatroom-item[data-id="${id}"]`);
  if (item) {
    const titleEl = item.querySelector(".chatroom-item__title");
    if (titleEl && titleEl.textContent === "새 채팅") {
      titleEl.textContent = title;
    }
  }
}

/* ───────────────────────────────
   활성 채팅방 표시
─────────────────────────────── */
function setActiveChat(id) {
  chatroomList.querySelectorAll(".chatroom-item").forEach(el => {
    el.classList.toggle("chatroom-item--active", el.dataset.id === id);
  });
}

/* ───────────────────────────────
   채팅방 삭제
─────────────────────────────── */
function openDeleteModal(id) {
  pendingDeleteId = id;
  modalOverlay.classList.add("modal-overlay--visible");
}

async function deleteChatroom() {
  if (!pendingDeleteId) return;
  try {
    await apiFetch(`/chat/chatrooms/${pendingDeleteId}`, { method: "DELETE" });

    const item = chatroomList.querySelector(`.chatroom-item[data-id="${pendingDeleteId}"]`);
    if (item) item.remove();

    if (currentChatroomId === pendingDeleteId) {
      currentChatroomId = null;
      chatMessages.innerHTML = "";
      showWelcomeArea();
    }

    // 목록이 비었으면 빈 상태 메시지 표시
    if (getChatroomCount() === 0) {
      const li = document.createElement("li");
      li.className = "chatroom-list__empty";
      li.textContent = "대화 내역이 없습니다.";
      chatroomList.appendChild(li);
    }
  } catch (e) {
    console.error("채팅방 삭제 실패:", e);
  } finally {
    pendingDeleteId = null;
    modalOverlay.classList.remove("modal-overlay--visible");
  }
}

/* ───────────────────────────────
   XSS 방지
─────────────────────────────── */
function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/* ───────────────────────────────
   textarea 자동 높이
─────────────────────────────── */
chatInput.addEventListener("input", () => {
  chatInput.style.height = "auto";
  chatInput.style.height = Math.min(chatInput.scrollHeight, 160) + "px";
  btnSend.disabled = chatInput.value.trim() === "";
});

/* ───────────────────────────────
   Enter 키 전송 (Shift+Enter 줄바꿈)
─────────────────────────────── */
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    if (!btnSend.disabled) sendMessage();
  }
});

/* ───────────────────────────────
   이벤트 바인딩
─────────────────────────────── */
btnNewChat.addEventListener("click", createChatroom);
btnSend.addEventListener("click", sendMessage);

modalConfirm.addEventListener("click", deleteChatroom);
modalCancel.addEventListener("click", () => {
  pendingDeleteId = null;
  modalOverlay.classList.remove("modal-overlay--visible");
});
modalLimitConfirm.addEventListener("click", () => {
  modalLimitOverlay.classList.remove("modal-overlay--visible");
});

// 기존 채팅방 항목에 이벤트 바인딩 (Django 템플릿으로 렌더된 항목들)
chatroomList.querySelectorAll(".chatroom-item").forEach(item => {
  const id = item.dataset.id;
  item.addEventListener("click", (e) => {
    if (e.target.classList.contains("chatroom-item__menu")) return;
    openChatroom(id);
  });
  item.querySelector(".chatroom-item__menu")?.addEventListener("click", (e) => {
    e.stopPropagation();
    openDeleteModal(id);
  });
});

// 페이지 로드 시 활성 채팅방 자동 열기
const activeItem = chatroomList.querySelector(".chatroom-item--active");
if (activeItem) {
  currentChatroomId = activeItem.dataset.id;
}

/* ───────────────────────────────
   계약서 업로드 모달
─────────────────────────────── */
function openUploadModal() {
  modalUpload.classList.add("modal-overlay--visible");
}

function closeUploadModal() {
  modalUpload.classList.remove("modal-overlay--visible");
  fileInput.value = "";
}

// 업로드 영역 클릭
uploadArea.addEventListener("click", () => {
  fileInput.click();
});

// 파일 선택
fileInput.addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (file) {
    if (file.type !== "application/pdf") {
      alert("PDF 파일만 업로드 가능합니다.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      alert("파일 크기는 5MB 이하여야 합니다.");
      return;
    }
    uploadedFile = file;
  }
});

// 드래그 앤 드롭
uploadArea.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadArea.classList.add("upload-area--dragging");
});

uploadArea.addEventListener("dragleave", () => {
  uploadArea.classList.remove("upload-area--dragging");
});

uploadArea.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadArea.classList.remove("upload-area--dragging");
  
  const file = e.dataTransfer.files[0];
  if (file) {
    if (file.type !== "application/pdf") {
      alert("PDF 파일만 업로드 가능합니다.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      alert("파일 크기는 5MB 이하여야 합니다.");
      return;
    }
    uploadedFile = file;
    fileInput.files = e.dataTransfer.files;
  }
});

// 업로드 확인
modalUploadConfirm.addEventListener("click", async () => {
  if (!uploadedFile) {
    alert("파일을 선택해주세요.");
    return;
  }

  // TODO: 실제 업로드 API 연동
  // 현재는 더미 데이터로 우측 사이드바 표시
  showContractSidebar({
    fileName: uploadedFile.name,
    fileSize: `${(uploadedFile.size / 1024 / 1024).toFixed(1)}MB`,
    address: "서울시 ○○구 ○○동 ○○번지",
    period: "2025-03-01 ~ 2027-02-28(2년)",
    deposit: "15,000만원",
    rent: "80만원 / 매월 말일",
    landlord: "박○ 외 1명 (총 1건)",
    specialTerms: [
      "1. 세입자는 입주 가기 전엔 대출을 받지 않는다."
    ]
  });

  closeUploadModal();
});

// 업로드 취소
modalUploadCancel.addEventListener("click", closeUploadModal);

/* ───────────────────────────────
   우측 사이드바 (계약서 정보)
─────────────────────────────── */
function showContractSidebar(data) {
  document.getElementById("fileName").textContent = data.fileName;
  document.getElementById("contractFile").querySelector(".contract-file__size").textContent = data.fileSize;
  document.getElementById("infoAddress").textContent = data.address;
  document.getElementById("infoPeriod").textContent = data.period;
  document.getElementById("infoDeposit").textContent = data.deposit;
  document.getElementById("infoRent").textContent = data.rent;
  document.getElementById("infoLandlord").textContent = data.landlord;

  const specialTermsEl = document.getElementById("specialTerms");
  specialTermsEl.innerHTML = data.specialTerms.map(term => `
    <div class="special-term-item">
      <p class="special-term-text">${escapeHtml(term)}</p>
    </div>
  `).join("");

  contractSidebar.classList.add("contract-sidebar--visible");
}

function hideContractSidebar() {
  contractSidebar.classList.remove("contract-sidebar--visible");
  uploadedFile = null;
}

// 우측 사이드바 닫기
btnCloseSidebar.addEventListener("click", hideContractSidebar);

// 업로드 버튼 클릭
btnUpload.addEventListener("click", openUploadModal);
