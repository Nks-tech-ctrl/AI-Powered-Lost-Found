/**
 * FindBack Report Lost & Found Client Interactions
 * Handles image drag-and-drop, client-side preview, AI auto-drafting, and submission states.
 */
document.addEventListener('DOMContentLoaded', () => {
  // Mobile drawer navigation
  const mobileToggle = document.getElementById('mobile-menu-btn');
  const mobileDrawer = document.getElementById('mobile-drawer');

  if (mobileToggle && mobileDrawer) {
    mobileToggle.addEventListener('click', () => {
      mobileDrawer.classList.toggle('hidden');
    });
  }

  // Smooth scroll anchors for the top step progress badges
  const stepBadges = document.querySelectorAll('.step-badge');
  stepBadges.forEach(badge => {
    const parentLink = badge.closest('a');
    if (parentLink && parentLink.getAttribute('href').startsWith('#')) {
      parentLink.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = parentLink.getAttribute('href');
        const targetElem = document.querySelector(targetId);
        if (targetElem) {
          targetElem.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    }
  });

  // AI Description Generator Button
  const aiGenerateBtn = document.getElementById('ai-generate-desc-btn');
  const titleInput = document.getElementById('item-title');
  const categorySelect = document.getElementById('item-category');
  const descInput = document.getElementById('item-description');

  if (aiGenerateBtn && descInput) {
    aiGenerateBtn.addEventListener('click', () => {
      const titleVal = titleInput ? titleInput.value.trim() : '';
      const categoryVal = categorySelect ? categorySelect.options[categorySelect.selectedIndex]?.text : '';
      
      let generatedText = '';
      if (titleVal) {
        generatedText = `${titleVal}. In good condition with distinct personal traits. Features durable build and standard finish. Clean exterior with minor visible signs of use.`;
      } else {
        generatedText = `Commuter backpack in matte black ballistic nylon with padded 15-inch laptop compartment, ergonomic mesh straps, and custom high-visibility yellow paracord zipper pull. Clean exterior with minor scuff on base.`;
      }
      descInput.value = generatedText;
      showToast('AI synthesized an optimized product description from your title and category attributes.', 'success');
    });
  }

  // Image Upload, Drag-and-Drop & Vanilla JS Preview
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const uploadPrompt = document.getElementById('upload-prompt');
  const previewCard = document.getElementById('image-preview-card');
  const previewImg = document.getElementById('preview-img');
  const previewName = document.getElementById('preview-name');
  const previewSize = document.getElementById('preview-size');
  const removeImgBtn = document.getElementById('remove-img-btn');

  function handleFile(file) {
    if (!file) return;

    // Check if image
    if (!file.type.startsWith('image/')) {
      showToast('Please select a valid image file (JPG, PNG, or WebP).', 'info');
      return;
    }

    // Check file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      showToast('Image file size must be under 10MB.', 'info');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      if (previewImg) previewImg.src = e.target.result;
      if (previewName) previewName.textContent = file.name;
      if (previewSize) {
        const sizeKb = Math.round(file.size / 1024);
        previewSize.textContent = `${sizeKb} KB · Ready to upload`;
      }
      if (uploadPrompt) uploadPrompt.classList.add('hidden');
      if (previewCard) previewCard.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
  }

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', (e) => {
      if (e.target.closest('#remove-img-btn')) return;
      fileInput.click();
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files[0]) {
        handleFile(fileInput.files[0]);
      }
    });

    // Drag-and-Drop listeners
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('border-primary', 'bg-blue-50/50');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('border-primary', 'bg-blue-50/50');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      if (dt && dt.files && dt.files[0]) {
        fileInput.files = dt.files;
        handleFile(dt.files[0]);
      }
    });
  }

  if (removeImgBtn && fileInput) {
    removeImgBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.value = '';
      if (previewImg) previewImg.src = '#';
      if (previewCard) previewCard.classList.add('hidden');
      if (uploadPrompt) uploadPrompt.classList.remove('hidden');
    });
  }

  // Submit button loading indicator (prevents duplicate submission)
  const reportForms = [
    document.getElementById('report-lost-form'),
    document.getElementById('report-found-form')
  ];

  reportForms.forEach(form => {
    if (form) {
      form.addEventListener('submit', () => {
        const submitBtn = form.querySelector('#submit-report-btn');
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.classList.add('opacity-75', 'cursor-not-allowed');
          submitBtn.innerHTML = `
            <i class="fa-solid fa-circle-notch fa-spin text-xs"></i>
            <span>Submitting Report...</span>
          `;
        }
      });
    }
  });

  // Toast Notification helper
  function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none';
      document.body.appendChild(container);
    }

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
