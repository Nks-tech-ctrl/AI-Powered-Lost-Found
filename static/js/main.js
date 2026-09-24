document.addEventListener('DOMContentLoaded', () => {
  const navbar = document.getElementById('navbar');
  const mobileToggle = document.getElementById('mobile-menu-toggle');
  const mobileMenu = document.getElementById('mobile-menu');
  const menuIcon = document.getElementById('menu-icon');

  window.addEventListener('scroll', () => {
    if (window.scrollY > 20) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  });

  if (mobileToggle && mobileMenu) {
    mobileToggle.addEventListener('click', () => {
      const isExpanded = mobileToggle.getAttribute('aria-expanded') === 'true';
      mobileToggle.setAttribute('aria-expanded', !isExpanded);
      mobileMenu.classList.toggle('hidden');
      if (menuIcon) {
        menuIcon.className = isExpanded ? 'fa-solid fa-bars text-xl' : 'fa-solid fa-xmark text-xl';
      }
    });
  }

  const mobileLinks = document.querySelectorAll('.mobile-nav-link');
  mobileLinks.forEach(link => {
    link.addEventListener('click', () => {
      if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
        mobileMenu.classList.add('hidden');
        if (mobileToggle) mobileToggle.setAttribute('aria-expanded', 'false');
        if (menuIcon) menuIcon.className = 'fa-solid fa-bars text-xl';
      }
    });
  });

  const revealElements = document.querySelectorAll('.reveal-elem');
  const observerOptions = {
    threshold: 0.12,
    rootMargin: '0px 0px -40px 0px'
  };

  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  revealElements.forEach(el => revealObserver.observe(el));

  const statsSection = document.getElementById('stats');
  const counters = document.querySelectorAll('.stat-counter');
  let animated = false;

  function runCounters() {
    if (animated) return;
    animated = true;

    counters.forEach(counter => {
      const target = +counter.getAttribute('data-target');
      const format = counter.getAttribute('data-format');
      const duration = 1800;
      const startTime = performance.now();

      function update(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = Math.floor(easeOut * target);

        if (format === 'k') {
          counter.textContent = current.toLocaleString();
        } else {
          counter.textContent = current;
        }

        if (progress < 1) {
          requestAnimationFrame(update);
        } else {
          if (format === 'k') {
            counter.textContent = target.toLocaleString();
          } else {
            counter.textContent = target;
          }
        }
      }

      requestAnimationFrame(update);
    });
  }

  if (statsSection) {
    const statsObserver = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        runCounters();
        statsObserver.unobserve(statsSection);
      }
    }, { threshold: 0.2 });
    statsObserver.observe(statsSection);
  }

  const runDemoBtn = document.getElementById('run-demo-match-btn');
  const scanningState = document.getElementById('ai-scanning-state');
  const resultsContainer = document.getElementById('ai-results-container');
  const scanningStepText = document.getElementById('scanning-step-text');
  const demoBtnText = document.getElementById('demo-btn-text');
  const demoBtnIcon = document.getElementById('demo-btn-icon');
  const demoProgressCircle = document.getElementById('demo-progress-circle');
  const demoPercentageText = document.getElementById('demo-percentage-text');
  const demoClaimBtn = document.getElementById('demo-claim-btn');

  if (runDemoBtn) {
    runDemoBtn.addEventListener('click', () => {
      runDemoBtn.disabled = true;
      demoBtnText.textContent = 'Analyzing...';
      demoBtnIcon.className = 'fa-solid fa-circle-notch fa-spin';

      resultsContainer.classList.add('hidden');
      scanningState.classList.remove('hidden');

      const steps = [
        'Extracting multimodal vision embeddings...',
        'Matching color histogram & silhouette vectors...',
        'Calculating geospatial transit corridors...',
        'Evaluating semantic taxonomy overlap...',
        'Aggregating neural confidence score...'
      ];

      let stepIndex = 0;
      scanningStepText.textContent = steps[0];

      const stepInterval = setInterval(() => {
        stepIndex++;
        if (stepIndex < steps.length) {
          scanningStepText.textContent = steps[stepIndex];
        } else {
          clearInterval(stepInterval);
          scanningState.classList.add('hidden');
          resultsContainer.classList.remove('hidden');

          if (demoProgressCircle) {
            demoProgressCircle.style.strokeDashoffset = '251.2';
            setTimeout(() => {
              demoProgressCircle.style.strokeDashoffset = '15.07';
            }, 50);
          }

          let count = 0;
          const counterInterval = setInterval(() => {
            count += 2;
            if (count >= 94) {
              count = 94;
              clearInterval(counterInterval);
            }
            demoPercentageText.textContent = count + '%';
          }, 20);

          runDemoBtn.disabled = false;
          demoBtnText.textContent = 'Re-run Demo Match';
          demoBtnIcon.className = 'fa-solid fa-rotate-right';

          showToast('Demo AI Match Complete: 94% confidence match discovered!', 'success');
        }
      }, 450);
    });
  }

  if (demoClaimBtn) {
    demoClaimBtn.addEventListener('click', () => {
      openDetailsModal({
        title: 'Found: Matte Black Commuter Backpack',
        type: 'Found',
        location: 'South Concourse Information Desk',
        date: 'Reported 3 hours ago',
        desc: 'Matte black water-resistant commuter backpack with 15-inch laptop sleeve and distinct yellow paracord zipper pull. Matches reported lost backpack.',
        image: 'images/backpack.jpg'
      });
    });
  }

  const heroQuickMatchBtn = document.getElementById('hero-quick-match-demo-btn');
  if (heroQuickMatchBtn) {
    heroQuickMatchBtn.addEventListener('click', () => {
      const aiSection = document.getElementById('ai-matching');
      if (aiSection) {
        aiSection.scrollIntoView({ behavior: 'smooth' });
        if (runDemoBtn) {
          setTimeout(() => runDemoBtn.click(), 600);
        }
      }
    });
  }

  const filterBtns = document.querySelectorAll('.filter-tab-btn');
  const itemCards = document.querySelectorAll('.item-card');
  const noItemsMatch = document.getElementById('no-items-match');
  const resetFilterBtn = document.getElementById('reset-filter-btn');

  function applyFilter(filter) {
    let visibleCount = 0;

    filterBtns.forEach(btn => {
      const btnFilter = btn.getAttribute('data-filter');
      if (btnFilter === filter) {
        btn.classList.add('bg-white', 'text-navy', 'shadow-sm');
        btn.classList.remove('text-slate-600');
      } else {
        btn.classList.remove('bg-white', 'text-navy', 'shadow-sm');
        btn.classList.add('text-slate-600');
      }
    });

    itemCards.forEach(card => {
      const cardType = card.getAttribute('data-type');
      const isRecent = card.getAttribute('data-recent') === 'true';

      let show = false;
      if (filter === 'all') {
        show = true;
      } else if (filter === 'lost' && cardType === 'lost') {
        show = true;
      } else if (filter === 'found' && cardType === 'found') {
        show = true;
      } else if (filter === 'recent' && isRecent) {
        show = true;
      }

      if (show) {
        card.style.display = 'flex';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });

    if (visibleCount === 0) {
      if (noItemsMatch) noItemsMatch.classList.remove('hidden');
    } else {
      if (noItemsMatch) noItemsMatch.classList.add('hidden');
    }
  }

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const filter = btn.getAttribute('data-filter');
      applyFilter(filter);
    });
  });

  if (resetFilterBtn) {
    resetFilterBtn.addEventListener('click', () => {
      applyFilter('all');
    });
  }

  const reportModal = document.getElementById('report-modal');
  const detailsModal = document.getElementById('details-modal');

  const openReportButtons = [
    document.getElementById('hero-report-lost-btn'),
    document.getElementById('hero-found-item-btn'),
    document.getElementById('nav-get-started-btn'),
    document.getElementById('mobile-start-btn'),
    document.getElementById('cta-lost-btn'),
    document.getElementById('cta-found-btn')
  ];

  function openReportModal(defaultType = 'lost') {
    if (!reportModal) return;
    const radios = reportModal.querySelectorAll('input[name="report_type"]');
    radios.forEach(radio => {
      radio.checked = (radio.value === defaultType);
    });
    reportModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  }

  function closeReportModal() {
    if (!reportModal) return;
    reportModal.classList.add('hidden');
    document.body.style.overflow = '';
  }

  openReportButtons.forEach(btn => {
    if (btn) {
      btn.addEventListener('click', () => {
        const isFoundBtn = btn.id && btn.id.includes('found');
        openReportModal(isFoundBtn ? 'found' : 'lost');
      });
    }
  });

  const closeReportModalBtn = document.getElementById('close-report-modal-btn');
  const cancelReportBtn = document.getElementById('cancel-report-btn');
  if (closeReportModalBtn) closeReportModalBtn.addEventListener('click', closeReportModal);
  if (cancelReportBtn) cancelReportBtn.addEventListener('click', closeReportModal);

  const reportForm = document.getElementById('report-form');
  if (reportForm) {
    reportForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const title = document.getElementById('form-item-title').value;
      closeReportModal();
      reportForm.reset();
      showToast(`Report for "${title}" successfully cataloged! AI scanning initiated.`, 'success');
    });
  }

  const detailsTitle = document.getElementById('details-title');
  const detailsBadge = document.getElementById('details-badge');
  const detailsMeta = document.getElementById('details-meta');
  const detailsDescription = document.getElementById('details-description');
  const detailsImage = document.getElementById('details-image');
  const closeDetailsModalBtn = document.getElementById('close-details-modal-btn');
  const closeDetailsBtnAction = document.getElementById('close-details-btn-action');
  const initiateClaimBtn = document.getElementById('initiate-claim-btn');

  function openDetailsModal(itemData) {
    if (!detailsModal) return;
    detailsTitle.textContent = itemData.title;
    detailsBadge.textContent = itemData.type + ' Item';
    if (itemData.type.toLowerCase() === 'lost') {
      detailsBadge.className = 'px-2.5 py-1 text-xs font-bold uppercase rounded-md bg-rose-500 text-white';
    } else {
      detailsBadge.className = 'px-2.5 py-1 text-xs font-bold uppercase rounded-md bg-emerald-500 text-white';
    }
    detailsMeta.textContent = `${itemData.location} · ${itemData.date}`;
    detailsDescription.textContent = itemData.desc;
    if (detailsImage && itemData.image) {
      detailsImage.src = itemData.image;
      detailsImage.alt = itemData.title;
    }
    detailsModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  }

  function closeDetailsModal() {
    if (!detailsModal) return;
    detailsModal.classList.add('hidden');
    document.body.style.overflow = '';
  }

  if (closeDetailsModalBtn) closeDetailsModalBtn.addEventListener('click', closeDetailsModal);
  if (closeDetailsBtnAction) closeDetailsBtnAction.addEventListener('click', closeDetailsModal);

  if (initiateClaimBtn) {
    initiateClaimBtn.addEventListener('click', () => {
      closeDetailsModal();
      showToast('Verification initiated: Please check your registered email for claim security steps.', 'info');
    });
  }

  const viewItemButtons = document.querySelectorAll('.view-item-btn');
  viewItemButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      openDetailsModal({
        title: btn.getAttribute('data-item'),
        type: btn.getAttribute('data-type'),
        location: btn.getAttribute('data-location'),
        date: btn.getAttribute('data-date'),
        desc: btn.getAttribute('data-desc'),
        image: btn.getAttribute('data-image')
      });
    });
  });

  window.addEventListener('click', (e) => {
    if (e.target === reportModal) closeReportModal();
    if (e.target === detailsModal) closeDetailsModal();
  });

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeReportModal();
      closeDetailsModal();
    }
  });

  const navLoginBtn = document.getElementById('nav-login-btn');
  const mobileLoginBtn = document.getElementById('mobile-login-btn');
  const navGetStartedBtn = document.getElementById('nav-get-started-btn');
  const browseAllBtn = document.getElementById('browse-all-btn');
  const learnSafetyBtn = document.getElementById('learn-safety-btn');
  const footerContactLink = document.getElementById('footer-contact-link');

  if (navLoginBtn) navLoginBtn.addEventListener('click', () => window.location.href = 'pages/login.html');
  if (mobileLoginBtn) mobileLoginBtn.addEventListener('click', () => window.location.href = 'pages/login.html');
  if (navGetStartedBtn) navGetStartedBtn.addEventListener('click', () => window.location.href = 'pages/register.html');
  if (browseAllBtn) browseAllBtn.addEventListener('click', () => window.location.href = 'pages/search.html');
  if (learnSafetyBtn) learnSafetyBtn.addEventListener('click', () => {
    const safetySec = document.getElementById('safety');
    if (safetySec) safetySec.scrollIntoView({ behavior: 'smooth' });
  });
  if (footerContactLink) footerContactLink.addEventListener('click', (e) => {
    e.preventDefault();
    showToast('Support desk contact: support@findback.org', 'info');
  });

  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-xl border text-xs font-semibold max-w-sm transition-all duration-300 transform translate-y-4 opacity-0';

    if (type === 'success') {
      toast.className += ' bg-slate-900 text-white border-slate-700';
      toast.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-400 text-sm"></i><span>${message}</span>`;
    } else {
      toast.className += ' bg-white text-navy border-slate-200 shadow-slate-900/10';
      toast.innerHTML = `<i class="fa-solid fa-circle-info text-primary text-sm"></i><span>${message}</span>`;
    }

    container.appendChild(toast);

    requestAnimationFrame(() => {
      toast.classList.remove('translate-y-4', 'opacity-0');
    });

    setTimeout(() => {
      toast.classList.add('opacity-0', 'translate-y-2');
      setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 300);
    }, 4000);
  }
});
