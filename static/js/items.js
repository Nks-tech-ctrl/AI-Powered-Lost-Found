document.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  const itemId = urlParams.get('id') || 'backpack';

  const mainImg = document.getElementById('main-item-img');
  const detailTitle = document.getElementById('detail-title');
  const detailCategory = document.getElementById('detail-category');
  const detailDesc = document.getElementById('detail-desc');
  const statusBadge = document.getElementById('item-status-badge');
  const statusText = document.getElementById('item-status-text');
  const categoryBadge = document.getElementById('item-category-badge');

  const catalog = {
    backpack: {
      title: 'Matte Black Commuter Backpack with 15" Sleeve',
      category: 'Bags & Luggage',
      status: 'LOST',
      image: '../images/backpack.jpg',
      desc: 'Water-resistant commuter backpack with 15-inch laptop sleeve and distinct yellow paracord zipper pull. Contains university notebooks.'
    },
    earbuds: {
      title: 'Blue Wireless Earbuds in Charging Case',
      category: 'Electronics',
      status: 'FOUND',
      image: '../images/earbuds.jpg',
      desc: 'Navy blue charging case with golden hinge accent. Found left on a corner booth at downtown cafe.'
    },
    watch: {
      title: 'Silver Chronograph Watch with Blue Sunburst Dial',
      category: 'Jewelry & Watches',
      status: 'LOST',
      image: '../images/watch.jpg',
      desc: 'Stainless steel mesh strap with blue sunburst dial. Heirloom gift with back casing engraving.'
    },
    id_card: {
      title: 'Student ID Card (State University)',
      category: 'Documents',
      status: 'FOUND',
      image: '../images/id_card.jpg',
      desc: 'Clear lanyard badge holder with university magnetic keycard. Identity protected for privacy.'
    },
    keys: {
      title: 'House Keys with Leather Fob',
      category: 'Keys',
      status: 'LOST',
      image: '../images/keys.jpg',
      desc: 'Set of 3 brass house keys attached to a distinctive tan stitched leather keychain fob.'
    },
    wallet: {
      title: 'Brown Bi-Fold Leather Wallet',
      category: 'Wallets',
      status: 'FOUND',
      image: '../images/wallet.jpg',
      desc: 'Distressed vintage brown leather wallet. Handed over to terminal security desk for safe cataloging.'
    }
  };

  if (catalog[itemId]) {
    const item = catalog[itemId];
    if (mainImg) mainImg.src = item.image;
    if (detailTitle) detailTitle.textContent = item.title;
    if (detailCategory) detailCategory.textContent = item.category;
    if (categoryBadge) categoryBadge.textContent = item.category;
    if (detailDesc) detailDesc.textContent = item.desc;
    if (statusText) statusText.textContent = item.status;

    if (item.status === 'FOUND' && statusBadge) {
      statusBadge.className = 'absolute top-4 left-4 px-3 py-1 text-xs font-bold uppercase rounded-lg bg-emerald-500 text-white shadow-md flex items-center gap-1.5';
    }
  }

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
