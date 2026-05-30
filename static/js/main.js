// ══════════════════════════════════════════════════════════════════════════
// WorkHub — Main JS
// Sidebar collapse/expand, mobile drawer, group toggles
// ══════════════════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
  const sidebar      = document.getElementById("sidebar");
  const toggleBtn    = document.getElementById("sidebarToggle");
  const backdrop     = document.getElementById("sidebarBackdrop");
  const STORAGE_KEY  = "wh-sidebar-collapsed";
  const mq           = window.matchMedia("(max-width: 1023px)");

  if (!sidebar) return;

  // ── Restore saved state (desktop only) ─────────────────────────────────
  if (!mq.matches && localStorage.getItem(STORAGE_KEY) === "1") {
    sidebar.classList.add("collapsed");
  }

  // ── Toggle handler ─────────────────────────────────────────────────────
  function toggleSidebar() {
    if (mq.matches) {
      // Mobile: slide drawer in/out
      const isOpen = sidebar.classList.contains("mobile-open");
      sidebar.classList.toggle("mobile-open", !isOpen);
      if (backdrop) backdrop.classList.toggle("active", !isOpen);
    } else {
      // Desktop: collapse/expand
      sidebar.classList.toggle("collapsed");
      localStorage.setItem(
        STORAGE_KEY,
        sidebar.classList.contains("collapsed") ? "1" : "0"
      );
    }
  }

  if (toggleBtn)   toggleBtn.addEventListener("click", toggleSidebar);

  // ── Backdrop click → close mobile drawer ───────────────────────────────
  if (backdrop) {
    backdrop.addEventListener("click", () => {
      sidebar.classList.remove("mobile-open");
      backdrop.classList.remove("active");
    });
  }

  // ── Handle resize ──────────────────────────────────────────────────────
  mq.addEventListener("change", (e) => {
    sidebar.classList.remove("mobile-open");
    if (backdrop) backdrop.classList.remove("active");

    if (!e.matches) {
      // Switched to desktop — restore saved state
      if (localStorage.getItem(STORAGE_KEY) === "1") {
        sidebar.classList.add("collapsed");
      } else {
        sidebar.classList.remove("collapsed");
      }
    }
  });

  // ── Sidebar group expand/collapse ──────────────────────────────────────
  document.querySelectorAll(".sb-group-toggle").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      btn.closest(".sb-group").classList.toggle("expanded");
    });
  });

  // ── Auto-dismiss alerts after 5s ───────────────────────────────────────
  document.querySelectorAll(".alert").forEach((el) => {
    setTimeout(() => {
      try {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
        if (bsAlert) bsAlert.close();
      } catch (_) {
        el.style.display = "none";
      }
    }, 5000);
  });
});

// ══════════════════════════════════════════════════════════════════════════
// AI Assistant inline fetch
// ══════════════════════════════════════════════════════════════════════════
function runAI(type, text, csrfToken) {
  const btn = document.getElementById("ai-btn");
  const box = document.getElementById("ai-response-box");
  const content = document.getElementById("ai-content");
  if (!btn || !box || !content) return;

  btn.disabled = true;
  btn.innerHTML =
    '<span class="spinner-border spinner-border-sm me-2"></span>Thinking…';

  fetch("/ai/ask/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify({ type, text }),
  })
    .then((r) => r.json())
    .then((data) => {
      content.textContent = data.result || data.error || "No response";
      box.classList.remove("d-none");
    })
    .catch(() => {
      content.textContent = "Something went wrong. Please try again.";
      box.classList.remove("d-none");
    })
    .finally(() => {
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-robot me-2"></i>AI Summarize / Reply';
    });
}
