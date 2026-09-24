document.addEventListener('DOMContentLoaded', () => {
  const rows = document.querySelectorAll('.claim-row');
  const title = document.getElementById('timeline-title');
  const badge = document.getElementById('timeline-status-badge');
  const hubBtn = document.getElementById('contact-hub-btn');

  const claimData = {
    c801: {
      title: 'Claim #C-801: Matte Black Backpack',
      status: 'UNDER REVIEW',
      statusClass: 'px-2.5 py-1 rounded text-xs font-bold uppercase bg-indigo/10 text-indigo border border-indigo/20'
    },
    c744: {
      title: 'Claim #C-744: Blue Wireless Earbuds',
      status: 'VERIFIED',
      statusClass: 'px-2.5 py-1 rounded text-xs font-bold uppercase bg-emerald-50 text-emerald-700 border border-emerald-200'
    },
    c690: {
      title: 'Claim #C-690: Silver Chronograph Watch',
      status: 'COMPLETED',
      statusClass: 'px-2.5 py-1 rounded text-xs font-bold uppercase bg-slate-100 text-slate-700 border border-slate-200'
    }
  };

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
