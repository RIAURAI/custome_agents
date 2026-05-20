// ── Sidebar toggle ──────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const toggle  = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");

  // Create backdrop for mobile overlay
  const backdrop = document.createElement("div");
  backdrop.className = "sb-backdrop";
  document.body.appendChild(backdrop);

  const mq = window.matchMedia("(max-width: 991.98px)");

  function openSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove("collapsed");
    if (mq.matches) backdrop.classList.add("active");
  }
  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.add("collapsed");
    backdrop.classList.remove("active");
  }

  if (toggle && sidebar) {
    toggle.addEventListener("click", () => {
      sidebar.classList.contains("collapsed") ? openSidebar() : closeSidebar();
    });
  }

  // Tap backdrop → close
  backdrop.addEventListener("click", closeSidebar);

  // Auto-collapse on resize to mobile; remove backdrop when going back to desktop
  function handleBreakpoint(e) {
    if (e.matches) { closeSidebar(); }
    else            { backdrop.classList.remove("active"); }
  }
  handleBreakpoint(mq);  // run immediately on page load
  mq.addEventListener("change", handleBreakpoint);

  // Auto-dismiss alerts after 5 s
  document.querySelectorAll(".alert").forEach(el => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert.close();
    }, 5000);
  });
});

// ── AI Assistant inline fetch ────────────────────────────────────────────────
function runAI(type, text, csrfToken) {
  const btn = document.getElementById("ai-btn");
  const box = document.getElementById("ai-response-box");
  const content = document.getElementById("ai-content");
  if (!btn || !box || !content) return;

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Thinking…';

  fetch("/ai/ask/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify({ type, text }),
  })
    .then(r => r.json())
    .then(data => {
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
