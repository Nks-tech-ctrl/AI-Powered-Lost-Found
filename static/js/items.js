document.addEventListener('DOMContentLoaded', () => {
  const mainImg = document.getElementById('main-item-img');

  const thumbBtns = document.querySelectorAll('.thumb-btn');
  thumbBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      thumbBtns.forEach(b => {
        b.classList.remove('border-primary');
        b.classList.add('border-slate-200', 'opacity-70');
      });
      btn.classList.add('border-primary');
      btn.classList.remove('opacity-70', 'border-slate-200');
      if (mainImg) mainImg.src = btn.getAttribute('data-src');
    });
  });

  const claimBtn = document.getElementById('claim-item-btn');
  const claimModal = document.getElementById('claim-modal');
  const closeClaimBtn = document.getElementById('close-claim-modal');
  const cancelClaimBtn = document.getElementById('cancel-claim-btn');
  const submitClaimBtn = document.getElementById('submit-claim-btn');
  const contactBtn = document.getElementById('contact-reporter-btn');
  const flagBtn = document.getElementById('flag-btn');

  if (claimBtn && claimModal) {
    claimBtn.addEventListener('click', () => claimModal.classList.remove('hidden'));
  }
  if (closeClaimBtn && claimModal) {
    closeClaimBtn.addEventListener('click', () => claimModal.classList.add('hidden'));
  }
  if (cancelClaimBtn && claimModal) {
    cancelClaimBtn.addEventListener('click', () => claimModal.classList.add('hidden'));
  }
  if (submitClaimBtn && claimModal) {
    submitClaimBtn.addEventListener('click', () => {
      claimModal.classList.add('hidden');
      showToast('Ownership claim submitted! Redirecting to Claims tracking center...', 'success');
      setTimeout(() => {
        window.location.href = '/claims/';
      }, 1200);
    });
  }

  if (contactBtn) {
    contactBtn.addEventListener('click', () => {
      showToast('Proxy message relay opened: Your identity remains anonymous.', 'info');
    });
  }

  if (flagBtn) {
    flagBtn.addEventListener('click', () => {
      showToast('Report submitted for moderator review.', 'info');
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
