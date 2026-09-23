document.addEventListener('DOMContentLoaded', () => {
  let currentStep = 1;
  const totalSteps = 4;

  const stepTabs = document.querySelectorAll('.step-tab');
  const stepPanels = document.querySelectorAll('.step-panel');
  const prevBtn = document.getElementById('prev-step-btn');
  const nextBtn = document.getElementById('next-step-btn');
  const submitBtn = document.getElementById('submit-report-btn');
  const saveDraftBtn = document.getElementById('save-draft-btn');
  const reportLostForm = document.getElementById('report-lost-form');
  const reportFoundForm = document.getElementById('report-found-form');
  const mobileToggle = document.getElementById('mobile-menu-btn');
  const mobileDrawer = document.getElementById('mobile-drawer');
  const aiGenerateBtn = document.getElementById('ai-generate-desc-btn');
  const descInput = document.getElementById('item-description');

  if (mobileToggle && mobileDrawer) {
    mobileToggle.addEventListener('click', () => {
      mobileDrawer.classList.toggle('hidden');
    });
  }

  function updateStepUI(step) {
    currentStep = step;

    stepPanels.forEach((panel, idx) => {
      if (idx + 1 === step) {
        panel.classList.remove('hidden');
      } else {
        panel.classList.add('hidden');
      }
    });

    stepTabs.forEach((tab) => {
      const tabStep = parseInt(tab.getAttribute('data-step'));
      const badge = tab.querySelector('.step-badge');
      const title = tab.querySelector('span:last-child');
      const isFound = reportFoundForm !== null;
      const activeColor = isFound ? 'bg-emerald-600' : 'bg-primary';

      if (tabStep === step) {
        badge.className = `step-badge w-8 h-8 rounded-full ${activeColor} text-white text-xs font-bold flex items-center justify-center shadow-md`;
        title.className = 'text-[11px] sm:text-xs font-bold text-navy mt-1.5 block';
      } else if (tabStep < step) {
        badge.className = 'step-badge w-8 h-8 rounded-full bg-emerald-500 text-white text-xs font-bold flex items-center justify-center';
        badge.innerHTML = '<i class="fa-solid fa-check"></i>';
        title.className = 'text-[11px] sm:text-xs font-semibold text-slate-600 mt-1.5 block';
      } else {
        badge.className = 'step-badge w-8 h-8 rounded-full bg-slate-100 text-slate-500 text-xs font-bold flex items-center justify-center';
        badge.textContent = `0${tabStep}`;
        title.className = 'text-[11px] sm:text-xs font-semibold text-slate-400 mt-1.5 block';
      }
    });

    if (step === 1) {
      if (prevBtn) prevBtn.classList.add('hidden');
    } else {
      if (prevBtn) prevBtn.classList.remove('hidden');
    }

    if (step === totalSteps) {
      if (nextBtn) nextBtn.classList.add('hidden');
      if (submitBtn) submitBtn.classList.remove('hidden');
    } else {
      if (nextBtn) nextBtn.classList.remove('hidden');
      if (submitBtn) submitBtn.classList.add('hidden');
    }
  }

  stepTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = parseInt(tab.getAttribute('data-step'));
      updateStepUI(target);
    });
  });

  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      if (currentStep < totalSteps) updateStepUI(currentStep + 1);
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      if (currentStep > 1) updateStepUI(currentStep - 1);
    });
  }

  if (saveDraftBtn) {
    saveDraftBtn.addEventListener('click', () => {
      showToast('Draft report saved to your local session.', 'info');
    });
  }

  if (aiGenerateBtn && descInput) {
    aiGenerateBtn.addEventListener('click', () => {
      descInput.value = 'Commuter backpack in matte black ballistic nylon with padded 15-inch laptop compartment, ergonomic mesh straps, and custom high-visibility yellow paracord zipper pull. Clean exterior with minor scuff on base.';
      showToast('AI synthesized an optimized product description from your title and category attributes.', 'success');
    });
  }

  if (reportLostForm) {
    reportLostForm.addEventListener('submit', (e) => {
      e.preventDefault();
      showToast('Report submitted! AI matching engine initiated...', 'success');
      setTimeout(() => {
        window.location.href = 'matches.html';
      }, 1200);
    });
  }

  if (reportFoundForm) {
    reportFoundForm.addEventListener('submit', (e) => {
      e.preventDefault();
      showToast('Found report submitted! Scanning registered lost items for instant matches...', 'success');
      setTimeout(() => {
        window.location.href = 'matches.html';
      }, 1200);
    });
  }

  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-xl border text-xs font-semibold max-w-sm transition-all duration-300 transform translate-y-4 opacity-0 bg-white';

    if (type === 'success') {
      toast.classList.add('border-emerald-200', 'text-slate-800');
      toast.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-500 text-sm"></i><span>${message}</span>`;
    } else {
      toast.classList.add('border-blue-200', 'text-slate-800');
      toast.innerHTML = `<i class="fa-solid fa-circle-info text-primary text-sm"></i><span>${message}</span>`;
    }

    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.remove('translate-y-4', 'opacity-0'));
    setTimeout(() => {
      toast.classList.add('translate-y-4', 'opacity-0');
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }
});
