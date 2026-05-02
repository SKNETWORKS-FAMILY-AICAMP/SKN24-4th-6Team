// contract_sidebar.js

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
      showEmpty();
    }
  } catch (err) {
    showEmpty();
  }
}

// ── 사이드바 렌더링 ──
function renderSidebar(data) {
  const { contract, property_info } = data;

  // 계약서 정보
  document.getElementById('contractFileName').textContent = contract.title || '-';

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
function showEmpty() {
  document.getElementById('sidebarEmpty').style.display = '';
  document.getElementById('sidebarContent').style.display = 'none';
}

function showContent() {
  document.getElementById('sidebarEmpty').style.display = 'none';
  document.getElementById('sidebarContent').style.display = '';
}

// ── 매물 정보 수정 ──
function togglePropertyEdit() {
  const view = document.getElementById('propertyView');
  const form = document.getElementById('propertyEditForm');
  const btn  = document.getElementById('propertyEditBtn');

  // 현재 값을 폼에 채우기
  document.getElementById('editLocation').value   = document.getElementById('viewLocation').textContent.replace('-', '');
  document.getElementById('editDeposit').value    = document.getElementById('viewDeposit').textContent.replace(/[^0-9]/g, '');
  document.getElementById('editMonthRent').value  = document.getElementById('viewMonthRent').textContent.replace(/[^0-9]/g, '');
  document.getElementById('editHouseCost').value  = document.getElementById('viewHouseCost').textContent.replace('-', '');

  // 날짜 파싱
  const period = document.getElementById('viewPeriod').textContent;
  if (period.includes('~')) {
    const [start, end] = period.split('~').map(s => s.trim());
    document.getElementById('editStartDate').value = start;
    document.getElementById('editEndDate').value   = end;
  }

  view.classList.add('hidden');
  form.classList.remove('hidden');
  btn.textContent = '';
}

function cancelPropertyEdit() {
  document.getElementById('propertyView').classList.remove('hidden');
  document.getElementById('propertyEditForm').classList.add('hidden');
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
  const view = document.getElementById('specialView');
  const form = document.getElementById('specialEditForm');
  const btn  = document.getElementById('specialEditBtn');

  document.getElementById('editSpecialTerms').value = document.getElementById('viewSpecialTerms').textContent.replace('-', '');

  view.classList.add('hidden');
  form.classList.remove('hidden');
  btn.textContent = '';
}

function cancelSpecialEdit() {
  document.getElementById('specialView').classList.remove('hidden');
  document.getElementById('specialEditForm').classList.add('hidden');
  document.getElementById('specialEditBtn').textContent = '수정';
}

async function saveSpecialTerms(e) {
  e.preventDefault();
  const chatroomId = getChatroomId();

  const body = new URLSearchParams({
    content: document.getElementById('editSpecialTerms').value,
  });

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
