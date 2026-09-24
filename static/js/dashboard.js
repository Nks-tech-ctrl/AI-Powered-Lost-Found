document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('mobile-sidebar-toggle');
  const drawer = document.getElementById('mobile-sidebar-drawer');

  if (toggle && drawer) {
    toggle.addEventListener('click', () => {
      drawer.classList.toggle('hidden');
    });
  }

  const claimRows = document.querySelectorAll('.claim-row');
  claimRows.forEach(row => {
    row.addEventListener('click', () => {
      const claimId = row.getAttribute('data-claim-id');
      if (claimId) {
        window.location.href = `/claims/?id=${claimId}`;
      }
    });
  });
});
