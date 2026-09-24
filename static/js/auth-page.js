document.addEventListener('DOMContentLoaded', () => {
  const togglePasswordBtn = document.getElementById('toggle-password');
  const passwordInput = document.getElementById('password');
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  const emailInput = document.getElementById('email');
  const emailError = document.getElementById('email-error');
  const passwordError = document.getElementById('password-error');
  const submitBtn = document.getElementById('submit-btn');
  const btnText = document.getElementById('btn-text');
  const btnSpinner = document.getElementById('btn-spinner');
  const forgotPasswordBtn = document.getElementById('forgot-password-btn');
  const googleAuthBtn = document.getElementById('google-auth-btn');
  const googleSignupBtn = document.getElementById('google-signup-btn');

  const fullnameInput = document.getElementById('fullname');
  const termsCheckbox = document.getElementById('terms-agree');
  const nameError = document.getElementById('name-error');
  const termsError = document.getElementById('terms-error');
  const strengthText = document.getElementById('strength-text');
  const bar1 = document.getElementById('bar-1');
  const bar2 = document.getElementById('bar-2');
  const bar3 = document.getElementById('bar-3');

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

  if (forgotPasswordBtn) {
    forgotPasswordBtn.addEventListener('click', () => {
      showToast('Password recovery instructions sent to registered email address.', 'info');
    });
  }

  if (googleAuthBtn) {
    googleAuthBtn.addEventListener('click', () => {
      showToast('Google OAuth simulated — redirecting to FindBack Dashboard...', 'info');
      setTimeout(() => {
        window.location.href = 'dashboard.html';
      }, 1000);
    });
  }

  if (googleSignupBtn) {
    googleSignupBtn.addEventListener('click', () => {
      showToast('Google OAuth simulated — creating account and redirecting...', 'info');
      setTimeout(() => {
        window.location.href = 'dashboard.html';
      }, 1000);
    });
  }

  if (passwordInput && strengthText && bar1 && bar2 && bar3) {
    passwordInput.addEventListener('input', () => {
      const val = passwordInput.value;
      let score = 0;
      if (val.length >= 6) score++;
      if (val.length >= 8 && /[A-Z]/.test(val) && /[0-9]/.test(val)) score++;
      if (val.length >= 10 && /[^A-Za-z0-9]/.test(val)) score++;

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

  if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      let isValid = true;

      const emailVal = emailInput ? emailInput.value.trim() : '';
      if (!emailVal || !emailVal.includes('@') || !emailVal.includes('.')) {
        if (emailError) emailError.classList.remove('hidden');
        if (emailInput) emailInput.classList.add('border-rose-400');
        isValid = false;
      } else {
        if (emailError) emailError.classList.add('hidden');
        if (emailInput) emailInput.classList.remove('border-rose-400');
      }

      const passVal = passwordInput ? passwordInput.value : '';
      if (!passVal || passVal.length < 6) {
        if (passwordError) passwordError.classList.remove('hidden');
        if (passwordInput) passwordInput.classList.add('border-rose-400');
        isValid = false;
      } else {
        if (passwordError) passwordError.classList.add('hidden');
        if (passwordInput) passwordInput.classList.remove('border-rose-400');
      }

      if (!isValid) return;

      if (submitBtn) submitBtn.disabled = true;
      if (btnText) btnText.textContent = 'Verifying...';
      if (btnSpinner) btnSpinner.classList.remove('hidden');

      setTimeout(() => {
        showToast('Sign-in successful! Welcome back, Abhishek.', 'success');
        setTimeout(() => {
          window.location.href = 'dashboard.html';
        }, 800);
      }, 900);
    });
  }

  if (registerForm) {
    registerForm.addEventListener('submit', (e) => {
      e.preventDefault();
      let isValid = true;

      if (fullnameInput && !fullnameInput.value.trim()) {
        if (nameError) nameError.classList.remove('hidden');
        fullnameInput.classList.add('border-rose-400');
        isValid = false;
      } else if (fullnameInput) {
        if (nameError) nameError.classList.add('hidden');
        fullnameInput.classList.remove('border-rose-400');
      }

      const emailVal = emailInput ? emailInput.value.trim() : '';
      if (!emailVal || !emailVal.includes('@') || !emailVal.includes('.')) {
        if (emailError) emailError.classList.remove('hidden');
        if (emailInput) emailInput.classList.add('border-rose-400');
        isValid = false;
      } else if (emailInput) {
        if (emailError) emailError.classList.add('hidden');
        emailInput.classList.remove('border-rose-400');
      }

      if (passwordInput && (!passwordInput.value || passwordInput.value.length < 8)) {
        if (passwordError) passwordError.classList.remove('hidden');
        passwordInput.classList.add('border-rose-400');
        isValid = false;
      } else if (passwordInput) {
        if (passwordError) passwordError.classList.add('hidden');
        passwordInput.classList.remove('border-rose-400');
      }

      if (termsCheckbox && !termsCheckbox.checked) {
        if (termsError) termsError.classList.remove('hidden');
        isValid = false;
      } else if (termsError) {
        termsError.classList.add('hidden');
      }

      if (!isValid) return;

      if (submitBtn) submitBtn.disabled = true;
      if (btnText) btnText.textContent = 'Creating account...';
      if (btnSpinner) btnSpinner.classList.remove('hidden');

      setTimeout(() => {
        showToast('Account created successfully! Welcome to FindBack.', 'success');
        setTimeout(() => {
          window.location.href = 'dashboard.html';
        }, 800);
      }, 1000);
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
    } else if (type === 'error') {
      toast.classList.add('border-rose-200', 'text-slate-800');
      toast.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-rose-500 text-sm"></i><span>${message}</span>`;
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
