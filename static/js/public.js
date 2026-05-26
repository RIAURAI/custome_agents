/* ── public.js — WorkHub marketing interactions v2 ──────────────────────── */
(function () {
  'use strict';

  /* ── Navbar scroll ───────────────────────────────────────────────────── */
  const nav = document.querySelector('.pub-nav');
  if (nav) {
    const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ── Mobile burger ───────────────────────────────────────────────────── */
  const burger = document.querySelector('.nav-burger');
  const drawer = document.querySelector('.nav-drawer');
  if (burger && drawer) {
    burger.addEventListener('click', () => {
      burger.classList.toggle('open');
      drawer.classList.toggle('open');
    });
    drawer.querySelectorAll('a').forEach(a =>
      a.addEventListener('click', () => {
        burger.classList.remove('open');
        drawer.classList.remove('open');
      })
    );
  }

  /* ── Scroll reveal ───────────────────────────────────────────────────── */
  const revealObs = new IntersectionObserver(
    entries => entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('visible'); revealObs.unobserve(e.target); }
    }),
    { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
  );
  document.querySelectorAll('.reveal').forEach(el => revealObs.observe(el));

  /* ── Animated counters ───────────────────────────────────────────────── */
  function animateCount(el, target, suffix, duration) {
    const start = performance.now();
    const isFloat = target % 1 !== 0;
    const step = ts => {
      const p = Math.min((ts - start) / duration, 1);
      const ease = 1 - Math.pow(1 - p, 3);
      const val = ease * target;
      el.textContent = (isFloat ? val.toFixed(1) : Math.floor(val)).toLocaleString() + suffix;
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }
  const counterObs = new IntersectionObserver(
    entries => entries.forEach(e => {
      if (e.isIntersecting) {
        const el = e.target;
        animateCount(el, parseFloat(el.dataset.count), el.dataset.suffix || '', parseInt(el.dataset.dur || '1800', 10));
        counterObs.unobserve(el);
      }
    }),
    { threshold: 0.4 }
  );
  document.querySelectorAll('[data-count]').forEach(el => counterObs.observe(el));

  /* ── Active nav highlight ────────────────────────────────────────────── */
  const path = window.location.pathname;
  document.querySelectorAll('.nav-links a, .nav-drawer a').forEach(a => {
    const href = a.getAttribute('href');
    if (href === path || (href !== '/' && path.startsWith(href))) a.classList.add('active');
  });

  /* ── Marquee duplicate for infinite scroll ───────────────────────────── */
  const track = document.querySelector('.marquee-track');
  if (track) {
    track.innerHTML += track.innerHTML;
  }

  /* ── Interactive feature showcase ───────────────────────────────────── */
  document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.fshow-tab');
    const panels = document.querySelectorAll('.fp-panel');
    if (!tabs.length || !panels.length) return;

    const CYCLE_MS = 4500;
    let autoTimer = null;
    let current = 0;
    let paused = false;

    function triggerAnims(panel) {
      panel.querySelectorAll('.anim-slide-in, .anim-typewriter').forEach(el => {
        el.style.animation = 'none';
        void el.offsetWidth;
        el.style.animation = '';
      });
    }

    function activate(idx) {
      // Deactivate all
      tabs.forEach((t, i) => {
        const isActive = i === idx;
        t.classList.toggle('active', isActive);
        const bar = t.querySelector('.ft-bar');
        if (bar) {
          bar.style.cssText = 'transition:none;width:0%';
          if (isActive) {
            requestAnimationFrame(() => requestAnimationFrame(() => {
              bar.style.cssText = `transition:width ${CYCLE_MS}ms linear;width:100%`;
            }));
          }
        }
      });
      panels.forEach((p, i) => {
        const wasActive = p.classList.contains('active');
        p.classList.toggle('active', i === idx);
        if (i === idx && !wasActive) triggerAnims(p);
      });
      current = idx;
    }

    function startAuto() {
      clearInterval(autoTimer);
      autoTimer = setInterval(() => {
        if (!paused) activate((current + 1) % tabs.length);
      }, CYCLE_MS);
    }

    // Click on tabs
    tabs.forEach((tab, idx) => {
      tab.addEventListener('click', function(e) {
        // Don't trigger if clicking a link inside an already-active tab
        if (e.target.closest('a') && tab.classList.contains('active')) return;
        activate(idx);
        startAuto(); // restart cycle from this tab
      });
    });

    // Pause auto-cycle while hovering
    const wrap = document.querySelector('.fshow-wrap');
    if (wrap) {
      wrap.addEventListener('mouseenter', () => { paused = true; });
      wrap.addEventListener('mouseleave', () => { paused = false; });
    }

    activate(0);
    startAuto();
  });

})();
