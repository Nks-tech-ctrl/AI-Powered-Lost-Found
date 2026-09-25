document.addEventListener('DOMContentLoaded', () => {
  // Password visibility toggle for password input
  const togglePasswordBtn = document.getElementById('toggle-password');
  const passwordInput = document.getElementById('password');

  if (togglePasswordBtn && passwordInput) {
    togglePasswordBtn.addEventListener('click', () => {
      const isPassword = passwordInput.getAttribute('type') === 'password';
      passwordInput.setAttribute('type', isPassword ? 'text' : 'password');
      const icon = togglePasswordBtn.querySelector('i');
      if (icon) {
        icon.className = isPassword ? 'fa-regular fa-eye-slash text-xs' : 'fa-regular fa-eye text-xs';
      }
    });
  }

  // Password visibility toggle for confirm_password input
  const toggleConfirmPasswordBtn = document.getElementById('toggle-confirm-password');
  const confirmPasswordInput = document.getElementById('confirm_password');

  if (toggleConfirmPasswordBtn && confirmPasswordInput) {
    toggleConfirmPasswordBtn.addEventListener('click', () => {
      const isPassword = confirmPasswordInput.getAttribute('type') === 'password';
      confirmPasswordInput.setAttribute('type', isPassword ? 'text' : 'password');
      const icon = toggleConfirmPasswordBtn.querySelector('i');
      if (icon) {
        icon.className = isPassword ? 'fa-regular fa-eye-slash text-xs' : 'fa-regular fa-eye text-xs';
      }
    });
  }

  // Password strength meter
  const strengthText = document.getElementById('strength-text');
  const bar1 = document.getElementById('bar-1');
  const bar2 = document.getElementById('bar-2');
  const bar3 = document.getElementById('bar-3');

  if (passwordInput && strengthText && bar1 && bar2 && bar3) {
    passwordInput.addEventListener('input', () => {
      const val = passwordInput.value;
      let score = 0;
      if (val.length >= 8) score++;
      if (/[A-Z]/.test(val) && /[0-9]/.test(val)) score++;
      if (/[^A-Za-z0-9]/.test(val)) score++;

      bar1.className = 'h-full w-1/3 bg-slate-200 transition-colors';
      bar2.className = 'h-full w-1/3 bg-slate-200 transition-colors';
      bar3.className = 'h-full w-1/3 bg-slate-200 transition-colors';

      if (score === 0 && val.length > 0) {
        strengthText.textContent = 'Weak';
        strengthText.className = 'font-bold text-rose-500';
        bar1.className = 'h-full w-1/3 bg-rose-500 transition-colors';
      } else if (score === 1) {
        strengthText.textContent = 'Fair';
        strengthText.className = 'font-bold text-amber-500';
        bar1.className = 'h-full w-1/3 bg-amber-500 transition-colors';
        bar2.className = 'h-full w-1/3 bg-amber-500 transition-colors';
      } else if (score >= 2) {
        strengthText.textContent = 'Strong';
        strengthText.className = 'font-bold text-emerald-600';
        bar1.className = 'h-full w-1/3 bg-emerald-500 transition-colors';
        bar2.className = 'h-full w-1/3 bg-emerald-500 transition-colors';
        bar3.className = 'h-full w-1/3 bg-emerald-500 transition-colors';
      } else {
        strengthText.textContent = 'None';
        strengthText.className = 'font-bold text-slate-400';
      }
    });
  }

  // Handle form submission feedback (loading indicator) without preventing real POST
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  const submitBtn = document.getElementById('submit-btn');
  const btnText = document.getElementById('btn-text');
  const btnSpinner = document.getElementById('btn-spinner');

  if (loginForm) {
    loginForm.addEventListener('submit', () => {
      if (btnText) btnText.textContent = 'Signing in...';
      if (btnSpinner) btnSpinner.classList.remove('hidden');
    });
  }

  if (registerForm) {
    registerForm.addEventListener('submit', () => {
      if (btnText) btnText.textContent = 'Creating account...';
      if (btnSpinner) btnSpinner.classList.remove('hidden');
    });
  }

  // Forgot password button
  const forgotPasswordBtn = document.getElementById('forgot-password-btn');
  if (forgotPasswordBtn) {
    forgotPasswordBtn.addEventListener('click', () => {
      showToast('Password recovery instructions will be sent to your registered email address.', 'info');
    });
  }

  // Google OAuth demo buttons
  const googleAuthBtn = document.getElementById('google-auth-btn');
  const googleSignupBtn = document.getElementById('google-signup-btn');

  if (googleAuthBtn) {
    googleAuthBtn.addEventListener('click', () => {
      showToast('Google OAuth is being configured. Please sign in with your username/password.', 'info');
    });
  }

  if (googleSignupBtn) {
    googleSignupBtn.addEventListener('click', () => {
      showToast('Google OAuth is being configured. Please register with your email below.', 'info');
    });
  }

  function showToast(message, type = 'info') {
    let container = document.getElementById('django-messages-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'django-messages-container';
      container.className = 'fixed top-24 right-6 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-auto transition-all';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'flex items-center gap-3 p-4 rounded-xl shadow-lg border backdrop-blur-md transition-all duration-300 bg-blue-50/95 border-blue-200 text-blue-800';
    toast.innerHTML = `
      <div class="shrink-0 text-base"><i class="fa-solid fa-circle-info text-blue-600"></i></div>
      <div class="flex-1 text-xs font-semibold leading-relaxed">${message}</div>
      <button type="button" onclick="this.parentElement.remove()" class="text-slate-400 hover:text-slate-700 transition-colors">
        <i class="fa-solid fa-xmark text-sm"></i>
      </button>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.5s ease';
      setTimeout(() => toast.remove(), 500);
    }, 4500);
  }
});
