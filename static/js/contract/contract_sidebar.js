// contract_sidebar.js

// ── chat-header 높이를 CSS 변수로 설정 ──
function syncSidebarTop() {
  const header = document.querySelector('.chat-header');
  if (header) {
    const height = header.getBoundingClientRect().height;
    document.documentElement.style.setProperty('--chat-header-height', height + 'px');
  }
}

// 페이지 로드 시 + 창 크기 변경 시 실행
document.addEventListener('DOMContentLoaded', syncSidebarTop);
window.addEventListener('resize', syncSidebarTop);

// ── 초기화: 페이지 로드 시 계약서 정보 조회 ──
document.addEventListener('DOMContentLoaded', () => {
  const chatroomId = getChatroomId();
  if (chatroomId) loadContractInfo(chatroomId);
});

// ── upload_modal.js에서 발행하는 contractUpdated 이벤트 수신 ──
document.addEventListener('contractUpdated', (e) => {
  renderSidebar(e.detail);
});

// ── 계약서 정보 조회 ──
async function loadContractInfo(chatroomId) {
  try {
    const response = await fetch(`/contract/${chatroomId}/`, {
      headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    const data = await response.json();
    if (data.success) {
      renderSidebar(data);
    } else {
      hideSidebar();
    }
  } catch (err) {
    hideSidebar();
  }
}

// ── 사이드바 렌더링 ──
function renderSidebar(data) {
  const { contract, property_info } = data;

  // 계약서 정보
  document.getElementById('contractFileName').textContent = contract.title || '-';
  const sizeMB = contract.size ? (contract.size / (1024 * 1024)).toFixed(1) + 'MB' : '';
  document.getElementById('contractFileSize').textContent = sizeMB;

  // 매물 정보
  document.getElementById('viewLocation').textContent = property_info.location || '-';
  document.getElementById('viewDeposit').textContent = property_info.deposit ? `${property_info.deposit.toLocaleString()}만원` : '-';
  document.getElementById('viewMonthRent').textContent = property_info.month_rent ? `${property_info.month_rent.toLocaleString()}만원 / 월` : '-';
  document.getElementById('viewHouseCost').textContent = property_info.house_cost || '-';

  // 임대차 기간
  if (property_info.start_date && property_info.end_date) {
    document.getElementById('viewPeriod').textContent = `${property_info.start_date} ~ ${property_info.end_date}`;
  } else {
    document.getElementById('viewPeriod').textContent = '-';
  }

  // 특약 정보
  document.getElementById('viewSpecialTerms').textContent = contract.content || '-';

  showContent();
}

// ── 상태 전환 ──

// 계약서 없는 채팅방: 탭 버튼도 숨기고 완전히 비활성화
function hideSidebar() {
  const sidebar = document.getElementById('contractSidebar');
  const tab = document.getElementById('sidebarTab');
  sidebar.classList.add('collapsed');
  tab.style.display = 'none';
}

// 계약서 있는 채팅방: 접힌 상태 + 탭 버튼 표시 (바로 펼치지 않음)
function showContent() {
  document.getElementById('sidebarEmpty').style.display = 'none';
  document.getElementById('sidebarContent').style.display = '';
  // 탭 버튼 활성화 (접힌 채로 대기)
  document.getElementById('sidebarTab').style.display = '';
}

// 탭 버튼 클릭 → 사이드바 펼침
function openSidebar() {
  document.getElementById('contractSidebar').classList.remove('collapsed');
}

// X 버튼 클릭 → 사이드바 접힘 (탭 버튼은 유지)
function closeSidebar() {
  document.getElementById('contractSidebar').classList.add('collapsed');
}

// ── 매물 정보 수정 ──
function togglePropertyEdit() {
  const btn = document.getElementById('propertyEditBtn');
  const isEditing = btn.textContent === '저장';

  if (isEditing) {
    // 저장 버튼 클릭 시 폼 submit 트리거
    document.getElementById('propertyForm').requestSubmit();
    return;
  }

  // 수정 모드 진입: value 표시 → input 전환
  const fields = ['Location', 'Deposit', 'MonthRent', 'HouseCost'];
  fields.forEach(f => {
    document.getElementById('view' + f).classList.add('hidden');
    document.getElementById('edit' + f).classList.remove('hidden');
    document.getElementById('edit' + f).value =
      document.getElementById('view' + f).textContent.replace('-', '').replace(/[^0-9a-zA-Zㄱ-힣\s.*~\/()-]/g, '') || '';
  });

  // 보증금, 월세는 숫자만
  document.getElementById('editDeposit').value =
    document.getElementById('viewDeposit').textContent.replace(/[^0-9]/g, '');
  document.getElementById('editMonthRent').value =
    document.getElementById('viewMonthRent').textContent.replace(/[^0-9]/g, '');

  // 임대차 기간 날짜 파싱
  document.getElementById('viewPeriod').classList.add('hidden');
  document.getElementById('editPeriodWrap').classList.remove('hidden');
  const period = document.getElementById('viewPeriod').textContent;
  if (period.includes('~')) {
    const [start, end] = period.split('~').map(s => s.trim());
    document.getElementById('editStartDate').value = start;
    document.getElementById('editEndDate').value = end;
  }

  btn.textContent = '저장';
}

function cancelPropertyEdit() {
  const fields = ['Location', 'Deposit', 'MonthRent', 'HouseCost'];
  fields.forEach(f => {
    document.getElementById('view' + f).classList.remove('hidden');
    document.getElementById('edit' + f).classList.add('hidden');
  });
  document.getElementById('viewPeriod').classList.remove('hidden');
  document.getElementById('editPeriodWrap').classList.add('hidden');
  document.getElementById('propertyEditBtn').textContent = '수정';
}

async function savePropertyInfo(e) {
  e.preventDefault();
  const chatroomId = getChatroomId();

  const body = new URLSearchParams({
    location:   document.getElementById('editLocation').value,
    start_date: document.getElementById('editStartDate').value,
    end_date:   document.getElementById('editEndDate').value,
    deposit:    document.getElementById('editDeposit').value,
    month_rent: document.getElementById('editMonthRent').value,
    house_cost: document.getElementById('editHouseCost').value,
  });

  try {
    const response = await fetch(`/contract/${chatroomId}/property/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body,
    });
    const data = await response.json();
    if (data.success) {
      loadContractInfo(chatroomId);
      cancelPropertyEdit();
    } else {
      alert(data.message || '저장에 실패했습니다.');
    }
  } catch (err) {
    alert('서버 오류가 발생했습니다.');
  }
}

// ── 특약 정보 수정 ──
function toggleSpecialEdit() {
  const btn = document.getElementById('specialEditBtn');
  const el = document.getElementById('viewSpecialTerms');
  const isEditing = btn.textContent === '저장';

  if (isEditing) {
    saveSpecialTerms();
    return;
  }

  // 수정 모드 진입: contenteditable 활성화
  if (el.textContent === '-') el.textContent = '';
  el.contentEditable = 'true';
  el.focus();
  // 커서를 텍스트 끝으로 이동
  const range = document.createRange();
  range.selectNodeContents(el);
  range.collapse(false);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  btn.textContent = '저장';
}

function cancelSpecialEdit() {
  const el = document.getElementById('viewSpecialTerms');
  el.contentEditable = 'false';
  if (!el.textContent.trim()) el.textContent = '-';
  document.getElementById('specialEditBtn').textContent = '수정';
}

async function saveSpecialTerms() {
  const chatroomId = getChatroomId();
  const el = document.getElementById('viewSpecialTerms');
  const content = el.textContent.trim();

  const body = new URLSearchParams({ content });

  try {
    const response = await fetch(`/contract/${chatroomId}/terms/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body,
    });
    const data = await response.json();
    if (data.success) {
      loadContractInfo(chatroomId);
      cancelSpecialEdit();
    } else {
      alert(data.message || '저장에 실패했습니다.');
    }
  } catch (err) {
    alert('서버 오류가 발생했습니다.');
  }
}

// ── 유틸 ──
function getChatroomId() {
  const parts = window.location.pathname.split('/').filter(Boolean);
  return parts[1] || '';
}

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}