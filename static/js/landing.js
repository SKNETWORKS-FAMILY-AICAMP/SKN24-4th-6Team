(function () {
  'use strict';

  const prefersReduced =
    window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ──────────────────────────────────────────────
  // 상단 내비게이션 — 스크롤 시 보더 / 배경 강화
  // ──────────────────────────────────────────────
  const nav = document.querySelector('.site-nav');
  if (nav) {
    const onScroll = () => {
      nav.classList.toggle('is-scrolled', window.scrollY > 8);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // ──────────────────────────────────────────────
  // 스무스 스크롤 (앵커 링크)
  // ──────────────────────────────────────────────
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href');
      if (!id || id === '#') return;
      const target = document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      const top =
        target.getBoundingClientRect().top + window.scrollY - 76;
      window.scrollTo({
        top,
        behavior: prefersReduced ? 'auto' : 'smooth',
      });
    });
  });

  // ──────────────────────────────────────────────
  // 스크롤 진입 애니메이션 (transitions.dev 스타일)
  //  · .reveal — 단일 요소 페이드+업
  //  · .reveal-stagger — 자식 요소 순차 노출
  // ──────────────────────────────────────────────
  const observe = (selector) => {
    const els = document.querySelectorAll(selector);
    if (!els.length) return;
    if (!('IntersectionObserver' in window)) {
      els.forEach((el) => el.classList.add('is-visible'));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        });
      },
      { threshold: 0.15, rootMargin: '0px 0px -8% 0px' }
    );
    els.forEach((el) => io.observe(el));
  };

  observe('.reveal');
  observe('.reveal-stagger');

  // 히어로는 마운트 직후 트리거 (스크롤 없이도 재생)
  const hero = document.querySelector('.hero');
  if (hero) {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => hero.classList.add('is-visible'));
    });
  }

  // ──────────────────────────────────────────────
  // 카운터 — Problem 섹션 75.1% 카운트업
  // ──────────────────────────────────────────────
  const counters = document.querySelectorAll('[data-count]');
  if (counters.length) {
    const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

    const animate = (el) => {
      const end = parseFloat(el.dataset.count);
      const decimals = parseInt(el.dataset.decimals || '0', 10);
      const duration = parseInt(el.dataset.duration || '1600', 10);

      if (prefersReduced || isNaN(end)) {
        el.textContent = end.toFixed(decimals);
        return;
      }

      const start = performance.now();
      const tick = (now) => {
        const t = Math.min(1, (now - start) / duration);
        const v = end * easeOutCubic(t);
        el.textContent = v.toFixed(decimals);
        if (t < 1) requestAnimationFrame(tick);
        else el.textContent = end.toFixed(decimals);
      };
      requestAnimationFrame(tick);
    };

    if ('IntersectionObserver' in window) {
      const cio = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            animate(entry.target);
            cio.unobserve(entry.target);
          });
        },
        { threshold: 0.5 }
      );
      counters.forEach((el) => cio.observe(el));
    } else {
      counters.forEach(animate);
    }
  }
})();
