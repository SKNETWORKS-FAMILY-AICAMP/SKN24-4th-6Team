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
    credentials: "same-origin",
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
   URL 동기화 헬퍼
   - id 가 null 이면 /chat/ 로, 아니면 /chat/{id}/ 로 push
   - 이미 같은 경로면 push 하지 않음 (중복 history 방지)
─────────────────────────────── */
function pushChatUrl(id) {
  const target = id ? `/chat/${id}/` : "/chat/";
  if (window.location.pathname !== target) {
    window.history.pushState(id ? { chatroomId: id } : {}, "", target);
  }
}

/* ───────────────────────────────
   초기 화면으로 리셋
   - currentChatroomId 를 null 로, 메시지/활성표시 초기화 후 welcome 화면 표시
   - pushHistory=true 면 URL 도 /chat/ 로 push
─────────────────────────────── */
function resetToWelcome({ pushHistory = true } = {}) {
  currentChatroomId = null;
  chatMessages.innerHTML = "";
  showWelcomeArea();

  chatroomList.querySelectorAll(".chatroom-item").forEach(el => {
    el.classList.remove("chatroom-item--active");
  });

  if (pushHistory) pushChatUrl(null);
}

/* ───────────────────────────────
   새 채팅방 생성
   - POST /api/v1/chatrooms (빈 body) 후 그 채팅방을 열어 URL 동기화
─────────────────────────────── */
// TODO: 채팅방 생성 시 title 도 같이 보내도록 API 수정 후 body 업데이트
async function createChatroom() {
  if (getChatroomCount() >= 10) {
    modalLimitOverlay.classList.add("modal-overlay--visible");
    return;
  }

  try {
    const data = await apiFetch("/api/v1/chatrooms", {
      method: "POST",
      body: JSON.stringify({}),
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
async function openChatroom(id, { pushHistory = true } = {}) {
  currentChatroomId = id;

  if (pushHistory) pushChatUrl(id);

  // 사이드바 활성 상태 변경
  chatroomList.querySelectorAll(".chatroom-item").forEach(el => {
    el.classList.toggle("chatroom-item--active", el.dataset.id === id);
  });

  // 메시지 영역 초기화
  chatMessages.innerHTML = "";

  try {
    const data = await apiFetch(`/api/v1/chatrooms/${id}`);

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
   브라우저 뒤로/앞으로 이동 처리
─────────────────────────────── */
window.addEventListener("popstate", (event) => {
  const id = event.state?.chatroomId;
  if (id) {
    openChatroom(id, { pushHistory: false });
  } else {
    resetToWelcome({ pushHistory: false });
  }
});

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
      const data = await apiFetch("/api/v1/chatrooms", {
        method: "POST",
        body: JSON.stringify({}),
      });
      addChatroomToSidebar(data.chatroom_id, data.title || content.slice(0, 30));
      currentChatroomId = data.chatroom_id;
      setActiveChat(data.chatroom_id);
      pushChatUrl(data.chatroom_id);
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

  let assistantBubble = null;
  let assistantText = "";
  let errored = false;

  try {
    const res = await fetch(`/api/v1/chatrooms/${currentChatroomId}/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
        Accept: "text/event-stream",
      },
      body: JSON.stringify({ content }),
    });

    if (!res.ok || !res.body) {
      throw new Error(`HTTP ${res.status}`);
    }

    await consumeSse(res.body, (event, data) => {
      if (event === "token") {
        if (!assistantBubble) {
          removeLoadingBubble();
          assistantBubble = appendAssistantStreamingBubble();
        }
        const delta = (data && data.delta) || "";
        assistantText += delta;
        assistantBubble.textContent = assistantText;
        chatMessages.scrollTop = chatMessages.scrollHeight;
      } else if (event === "error") {
        errored = true;
      }
    });

    if (errored) {
      removeLoadingBubble();
      if (assistantBubble) {
        assistantBubble.textContent = "죄송합니다. AI 서버 응답을 받지 못했습니다.";
      } else {
        appendMessage("assistant", "죄송합니다. AI 서버 응답을 받지 못했습니다.");
      }
    }

    // 사이드바 채팅방 제목 갱신 (첫 메시지 기준)
    updateChatroomTitle(currentChatroomId, content.slice(0, 30));
  } catch (e) {
    removeLoadingBubble();
    appendMessage(
      "assistant",
      "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
    );
    console.error("메시지 전송 실패:", e);
  } finally {
    isLoading = false;
  }
}

/* ───────────────────────────────
   SSE 소비 헬퍼
─────────────────────────────── */
async function consumeSse(stream, onEvent) {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sep;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      const parsed = parseSseFrame(raw);
      if (parsed.event) {
        let data = {};
        try { data = parsed.data ? JSON.parse(parsed.data) : {}; } catch { /* ignore */ }
        onEvent(parsed.event, data);
      }
    }
  }
}

function parseSseFrame(frame) {
  let event = null;
  const dataLines = [];
  for (const line of frame.split("\n")) {
    if (line.startsWith(":")) continue;
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).replace(/^ /, ""));
  }
  return { event, data: dataLines.join("\n") };
}

/* ───────────────────────────────
   스트리밍용 어시스턴트 버블
─────────────────────────────── */
function appendAssistantStreamingBubble() {
  const div = document.createElement("div");
  div.className = "message message--assistant";
  div.innerHTML = `
    <img class="message__avatar" src="/static/images/logo.png" alt="아이고 청년">
    <div class="message__bubble"></div>
  `;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return div.querySelector(".message__bubble");
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
    await apiFetch(`/api/v1/chatrooms/${pendingDeleteId}`, { method: "DELETE" });

    const item = chatroomList.querySelector(`.chatroom-item[data-id="${pendingDeleteId}"]`);
    if (item) item.remove();

    if (currentChatroomId === pendingDeleteId) {
      resetToWelcome();
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

// 페이지 로드 시 활성 채팅방 자동 열기 (URL 에 chatroom_id 가 있는 경우)
const activeItem = chatroomList.querySelector(".chatroom-item--active");
if (activeItem) {
  openChatroom(activeItem.dataset.id, { pushHistory: false });
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
