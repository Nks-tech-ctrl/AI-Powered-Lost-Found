document.addEventListener('DOMContentLoaded', () => {
  const profileForm = document.getElementById('profile-form');
  const changeAvatarBtn = document.getElementById('change-avatar-btn');
  const changePasswordBtn = document.getElementById('change-password-btn');
  const signoutDevicesBtn = document.getElementById('signout-devices-btn');

  if (profileForm) {
    profileForm.addEventListener('submit', (e) => {
      e.preventDefault();
      showToast('Profile information successfully updated.', 'success');
    });
  }

  if (changeAvatarBtn) {
    changeAvatarBtn.addEventListener('click', () => {
      showToast('Avatar selection simulated: Image uploaded.', 'info');
    });
  }

  if (changePasswordBtn) {
    changePasswordBtn.addEventListener('click', () => {
      showToast('Password reset link dispatched to abhishek@example.com.', 'info');
    });
  }

  if (signoutDevicesBtn) {
    signoutDevicesBtn.addEventListener('click', () => {
      showToast('All active secondary sessions revoked.', 'info');
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
