document.addEventListener('DOMContentLoaded', () => {
  const rows = document.querySelectorAll('.claim-row');
  const title = document.getElementById('timeline-title');
  const badge = document.getElementById('timeline-status-badge');
  const hubBtn = document.getElementById('contact-hub-btn');

  rows.forEach(row => {
    row.addEventListener('click', () => {
      rows.forEach(r => r.classList.remove('bg-blue-50/40'));
      row.classList.add('bg-blue-50/40');
      const id = row.getAttribute('data-claim-id');
      if (claimData[id] && title && badge) {
        title.textContent = claimData[id].title;
        badge.textContent = claimData[id].status;
        badge.className = claimData[id].statusClass;
      }
    });
  });

  if (hubBtn) {
    hubBtn.addEventListener('click', () => {
      showToast('Inquiry sent to Central Station Custody Desk.', 'info');
    });
  }

  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-xl border text-xs font-semibold max-w-sm transition-all duration-300 transform translate-y-4 opacity-0 bg-white border-blue-200 text-slate-800';
    toast.innerHTML = `<i class="fa-solid fa-circle-check text-primary text-sm"></i><span>${message}</span>`;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.remove('translate-y-4', 'opacity-0'));
    setTimeout(() => {
      toast.classList.add('translate-y-4', 'opacity-0');
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }
});
