document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('search-input');
  const searchClearBtn = document.getElementById('search-clear-btn');
  const typeBtns = document.querySelectorAll('.filter-type-btn');
  const categorySelect = document.getElementById('filter-category');
  const locationSelect = document.getElementById('filter-location');
  const sortSelect = document.getElementById('filter-sort');
  const tagBtns = document.querySelectorAll('.tag-btn');
  const clearFiltersBtn = document.getElementById('clear-filters-btn');
  
  const cards = document.querySelectorAll('.item-card');
  const resultsGrid = document.getElementById('results-grid');
  const emptyState = document.getElementById('empty-state');
  const resultsCount = document.getElementById('results-count');

  let currentType = 'all';

  function filterItems() {
    const query = searchInput ? searchInput.value.trim().toLowerCase() : '';
    const selectedCategory = categorySelect ? categorySelect.value : 'all';
    const selectedLocation = locationSelect ? locationSelect.value : 'all';
    let visibleCount = 0;

    cards.forEach(card => {
      const cardType = card.getAttribute('data-status');
      const cardCategory = card.getAttribute('data-category');
      const cardLocation = card.getAttribute('data-location');
      const cardText = card.innerText.toLowerCase();

      const matchesType = (currentType === 'all' || cardType === currentType);
      const matchesCategory = (selectedCategory === 'all' || cardCategory === selectedCategory);
      const matchesLocation = (selectedLocation === 'all' || cardLocation === selectedLocation);
      const matchesQuery = (!query || cardText.includes(query));

      if (matchesType && matchesCategory && matchesLocation && matchesQuery) {
        card.classList.remove('hidden');
        visibleCount++;
      } else {
        card.classList.add('hidden');
      }
    });

    if (resultsCount) resultsCount.textContent = visibleCount;
    if (searchClearBtn) searchClearBtn.classList.toggle('hidden', query.length === 0);

    if (visibleCount === 0) {
      if (resultsGrid) resultsGrid.classList.add('hidden');
      if (emptyState) emptyState.classList.remove('hidden');
    } else {
      if (resultsGrid) resultsGrid.classList.remove('hidden');
      if (emptyState) emptyState.classList.add('hidden');
    }
  }

  if (searchInput) {
    searchInput.addEventListener('input', filterItems);
  }
  if (searchClearBtn) {
    searchClearBtn.addEventListener('click', () => {
      searchInput.value = '';
      filterItems();
    });
  }

  typeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      typeBtns.forEach(b => {
        b.className = 'filter-type-btn px-3 py-1.5 rounded-lg text-xs font-bold text-slate-600 hover:text-navy transition-all';
      });
      btn.className = 'filter-type-btn px-3 py-1.5 rounded-lg text-xs font-bold transition-all bg-white text-navy shadow-xs';
      currentType = btn.getAttribute('data-type');
      filterItems();
    });
  });

  if (categorySelect) categorySelect.addEventListener('change', filterItems);
  if (locationSelect) locationSelect.addEventListener('change', filterItems);

  tagBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      if (searchInput) searchInput.value = btn.innerText;
      filterItems();
    });
  });

  if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener('click', () => {
      if (searchInput) searchInput.value = '';
      if (categorySelect) categorySelect.value = 'all';
      if (locationSelect) locationSelect.value = 'all';
      if (typeBtns.length > 0) typeBtns[0].click();
      filterItems();
    });
  }
});
