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
const btnToggleSidebar = document.getElementById("btnToggleSidebar");
const chatTitle        = document.getElementById("chatTitle");

const modalOverlay      = document.getElementById("modalOverlay");
const modalConfirm      = document.getElementById("modalConfirm");
const modalCancel       = document.getElementById("modalCancel");
const modalLimitOverlay = document.getElementById("modalLimitOverlay");
const modalLimitConfirm = document.getElementById("modalLimitConfirm");

// 로그아웃 모달
const btnLogout          = document.getElementById("btnLogout");
const modalLogoutOverlay = document.getElementById("modalLogoutOverlay");
const modalLogoutConfirm = document.getElementById("modalLogoutConfirm");
const modalLogoutCancel  = document.getElementById("modalLogoutCancel");

/* ───────────────────────────────
   State
─────────────────────────────── */
let currentChatroomId = null;   // 현재 열려 있는 채팅방 UUID
let pendingDeleteId   = null;   // 삭제 대기 중인 채팅방 UUID
let isLoading         = false;  // AI 응답 대기 중 여부

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

  // 응답이 비어있으면 null 반환 (DELETE 요청의 경우)
  if (res.status === 204 || res.headers.get('content-length') === '0') {
    return null;
  }

  return res.json();
}

/* ───────────────────────────────
   채팅방 목록 카운트 갱신
─────────────────────────────── */
function getChatroomCount() {
  return chatroomList.querySelectorAll(".chatroom-item").length;
}

// 모든 드롭다운 닫기
function closeAllDropdowns() {
  document.querySelectorAll(".chatroom-item__dropdown").forEach(dropdown => {
    dropdown.classList.remove("chatroom-item__dropdown--visible");
  });
}

// 다른 곳 클릭 시 드롭다운 닫기
document.addEventListener("click", (e) => {
  if (!e.target.closest(".chatroom-item__menu-wrapper")) {
    closeAllDropdowns();
  }
});

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
   채팅방 수 실시간 업데이트
   - 대화 (n/10)에서 n
─────────────────────────────── */
function updateChatroomCount() {
  const count = getChatroomCount();
  const countElement = document.querySelector(".sidebar__section-title");
  if (countElement) {
    countElement.textContent = `대화 (${count}/10)`;
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
    <div class="chatroom-item__menu-wrapper">
      <button class="chatroom-item__menu" data-id="${id}">···</button>
      <div class="chatroom-item__dropdown" data-id="${id}">
        <button class="chatroom-item__delete-btn">
          <img src="/static/images/icons/delete.svg" alt="삭제">
          삭제하기
        </button>
      </div>
    </div>
  `;
  li.addEventListener("click", (e) => {
    if (e.target.closest(".chatroom-item__menu-wrapper")) return;
    openChatroom(id);
  });
  
  // ··· 메뉴 버튼 클릭 시 드롭다운 토글
  const menuBtn = li.querySelector(".chatroom-item__menu");
  const dropdown = li.querySelector(".chatroom-item__dropdown");
  menuBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    closeAllDropdowns();
    dropdown.classList.toggle("chatroom-item__dropdown--visible");
  });
  
  // 삭제하기 버튼 클릭
  const deleteBtn = li.querySelector(".chatroom-item__delete-btn");
  deleteBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    openDeleteModal(id);
    closeAllDropdowns();
  });
  
  chatroomList.prepend(li);
  updateChatroomCount();
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
    
    // 제목 업데이트
    chatTitle.textContent = data.title || "새 채팅";

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
    // DB 저장본은 본문 + '---\n**관련 법령/판례:**\n- [title](url)...' 꼬리가
    // 한 덩어리로 들어 있을 수 있으므로, 본문/출처를 다시 분리해서 표시
    const bodyText = stripReferenceTail(content || "");
    const citations = extractCitationsFromTail(content || "");

    div.innerHTML = `
      <img class="message__avatar" src="/static/img/sub_img.svg" alt="아이고 청년">
      <div class="message__bubble">
        <div class="message__body">${renderMarkdownLite(bodyText)}</div>
        <div class="message__citations" hidden></div>
      </div>
    `;
    const citationsEl = div.querySelector(".message__citations");
    renderCitations(citationsEl, citations);
  } else {
    div.innerHTML = `<div class="message__bubble">${escapeHtml(content)}</div>`;
  }

  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

/* ───────────────────────────────
   저장된 본문에서 '관련 법령/판례:' 꼬리 부분의
   '- [title](url)' 항목들을 citation 배열로 추출
─────────────────────────────── */
function extractCitationsFromTail(content) {
  const m = content.match(REFERENCE_TAIL_RE);
  if (!m) return [];
  const tail = m[0];
  const out = [];
  // - [type] title (url)  또는  - [title](url)  형태 둘 다 대응
  const linkRe = /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g;
  let lm;
  while ((lm = linkRe.exec(tail)) !== null) {
    out.push({ doc_type: "참고", title: lm[1], url: lm[2] });
  }
  return out;
}

/* ───────────────────────────────
   로딩 버블
─────────────────────────────── */
function showLoadingBubble() {
  const div = document.createElement("div");
  div.className = "message message--assistant";
  div.id = "loadingBubble";
  div.innerHTML = `
    <img class="message__avatar" src="/static/img/sub_img.svg" alt="아이고 청년">
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

  let assistantNodes = null;       // { bodyEl, citationsEl } - 본문/출처 두 영역 핸들
  let rawText        = "";          // token 누적 (분리 전 원본)
  let citations      = [];          // citation 이벤트 누적
  let errored        = false;

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
        if (!assistantNodes) {
          removeLoadingBubble();
          assistantNodes = appendAssistantStreamingBubble();
        }
        const delta = (data && data.delta) || "";
        rawText += delta;

        // 마지막 token에 들어오는 '관련 법령/판례:' 마크다운 블록은 본문에서 잘라냄
        // (같은 정보가 citation 이벤트로도 따로 오므로 카드 영역에서만 표출)
        const bodyText = stripReferenceTail(rawText);
        assistantNodes.bodyEl.innerHTML = renderMarkdownLite(bodyText);
        chatMessages.scrollTop = chatMessages.scrollHeight;
      } else if (event === "citation") {
        if (!assistantNodes) {
          removeLoadingBubble();
          assistantNodes = appendAssistantStreamingBubble();
        }
        if (data && (data.title || data.url)) {
          citations.push(data);
          renderCitations(assistantNodes.citationsEl, citations);
          chatMessages.scrollTop = chatMessages.scrollHeight;
        }
      } else if (event === "error") {
        errored = true;
      }
    });

    if (errored) {
      removeLoadingBubble();
      if (assistantNodes) {
        assistantNodes.bodyEl.textContent = "죄송합니다. AI 서버 응답을 받지 못했습니다.";
      } else {
        appendMessage("assistant", "죄송합니다. AI 서버 응답을 받지 못했습니다.");
      }
    }

    // 사이드바 채팅방 제목 갱신 (첫 메시지 기준)
    updateChatroomTitle(currentChatroomId, content.slice(0, 30));
    chatTitle.textContent = content.slice(0, 30);  // 헤더 제목도 업데이트
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
   - 본문(.message__body) + 출처카드(.message__citations) 두 영역으로 분리
─────────────────────────────── */
function appendAssistantStreamingBubble() {
  const div = document.createElement("div");
  div.className = "message message--assistant";
  div.innerHTML = `
    <img class="message__avatar" src="/static/img/sub_img.svg" alt="아이고 청년">
    <div class="message__bubble">
      <div class="message__body"></div>
      <div class="message__citations" hidden></div>
    </div>
  `;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return {
    bodyEl: div.querySelector(".message__body"),
    citationsEl: div.querySelector(".message__citations"),
  };
}

/* ───────────────────────────────
   참고자료 꼬리 제거
   - 마지막 token에 한 덩어리로 오는
     '\n\n---\n**관련 법령/판례:**\n- [...]...' 블록을 잘라냄
   - 같은 정보가 citation 이벤트로도 따로 오므로 본문에서는 제거
─────────────────────────────── */
const REFERENCE_TAIL_RE = /\n+-{3,}\s*\n\s*\*\*\s*관련\s*법령\s*\/\s*판례\s*[:：]?\s*\*\*[\s\S]*$/;

function stripReferenceTail(text) {
  return text.replace(REFERENCE_TAIL_RE, "").trimEnd();
}

/* ───────────────────────────────
   가벼운 마크다운 변환
   - **굵게** → <strong>, 줄바꿈 → <br> 만 처리
   - 그 외에는 escapeHtml 로 안전하게 출력
─────────────────────────────── */
function renderMarkdownLite(text) {
  if (!text) return "";
  const escaped = escapeHtml(text);
  return escaped
    .replace(/\*\*([^*\n]+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>");
}

/* ───────────────────────────────
   인용(출처) 카드 렌더링
─────────────────────────────── */
function renderCitations(containerEl, citations) {
  if (!citations || citations.length === 0) {
    containerEl.hidden = true;
    containerEl.innerHTML = "";
    return;
  }

  const items = citations.map((c, idx) => {
    const num   = idx + 1;
    const type  = escapeHtml(c.doc_type || "참고");
    const title = escapeHtml(c.title || c.url || "출처");
    const url   = c.url || "#";
    const detail = c.detail ? `<span class="citation__detail">${escapeHtml(c.detail)}</span>` : "";

    if (url && url !== "#") {
      return `
        <li class="citation">
          <span class="citation__num">${num}</span>
          <span class="citation__type">${type}</span>
          <a class="citation__title" href="${escapeAttr(url)}" target="_blank" rel="noopener noreferrer">${title}</a>
          ${detail}
        </li>`;
    }
    return `
      <li class="citation">
        <span class="citation__num">${num}</span>
        <span class="citation__type">${type}</span>
        <span class="citation__title">${title}</span>
        ${detail}
      </li>`;
  }).join("");

  containerEl.innerHTML = `
    <div class="citations__header">출처 · ${citations.length}건</div>
    <ol class="citations__list">${items}</ol>
  `;
  containerEl.hidden = false;
}

/* href/속성용 escape (인용 url 보호) */
function escapeAttr(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
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
    updateChatroomCount();

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

// PDF 업로드 버튼 → Contract 앱의 openUploadModal() 호출
btnUpload.addEventListener("click", () => { openUploadModal(); });

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
    if (e.target.closest(".chatroom-item__menu-wrapper")) return;
    openChatroom(id);
  });
  
  // ··· 메뉴 버튼 클릭 시 드롭다운 토글
  const menuBtn = item.querySelector(".chatroom-item__menu");
  const dropdown = item.querySelector(".chatroom-item__dropdown");
  if (menuBtn && dropdown) {
    menuBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      closeAllDropdowns();
      dropdown.classList.toggle("chatroom-item__dropdown--visible");
    });
  }
  
  // 삭제하기 버튼 클릭
  const deleteBtn = item.querySelector(".chatroom-item__delete-btn");
  if (deleteBtn) {
    deleteBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      openDeleteModal(id);
      closeAllDropdowns();
    });
  }
});

// 페이지 로드 시 활성 채팅방 자동 열기 (URL 에 chatroom_id 가 있는 경우)
const activeItem = chatroomList.querySelector(".chatroom-item--active");
if (activeItem) {
  openChatroom(activeItem.dataset.id, { pushHistory: false });
}

/* ───────────────────────────────
   로그아웃
─────────────────────────────── */
btnLogout.addEventListener("click", (e) => {
  e.preventDefault();
  modalLogoutOverlay.classList.add("modal-overlay--visible");
});

modalLogoutConfirm.addEventListener("click", async () => {
  try {
    // 로그아웃 API 호출
    await fetch("/api/users/logout", {
      method: "POST",
      headers: {
        "X-CSRFToken": getCsrfToken(),
      },
    });
    
    // 로그인 페이지로 이동
    window.location.href = "/login/";
  } catch (e) {
    console.error("로그아웃 실패:", e);
    alert("로그아웃에 실패했습니다. 다시 시도해주세요.");
  }
});

modalLogoutCancel.addEventListener("click", () => {
  modalLogoutOverlay.classList.remove("modal-overlay--visible");
});

// 좌측 사이드바 토글
const sidebar = document.querySelector(".sidebar");
const toggleIcon = document.getElementById("toggleIcon");

btnToggleSidebar.addEventListener("click", () => {
  sidebar.classList.toggle("sidebar--hidden");

  // 아이콘 변경
  if (sidebar.classList.contains("sidebar--hidden")) {
    toggleIcon.src = "/static/images/icons/open.svg";
  } else {
    toggleIcon.src = "/static/images/icons/close.svg";
  }
});