document.addEventListener('DOMContentLoaded', () => {
  const dismissBtns = document.querySelectorAll('.dismiss-match-btn');
  const refreshBtn = document.getElementById('refresh-matches-btn');

  dismissBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const matchId = btn.getAttribute('data-id');
      const card = document.querySelector(`.match-card[data-match-id="${matchId}"]`);
      if (card) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(-10px)';
        card.style.transition = 'all 0.3s ease';
        setTimeout(() => {
          card.remove();
          showToast('Match report dismissed from your queue.', 'info');
        }, 300);
      }
    });
  });

  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      showToast('Scanning 4,200+ active search nodes... Catalog is up to date.', 'info');
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
