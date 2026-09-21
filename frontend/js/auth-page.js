import { login, register } from "./auth.js";

const form = document.querySelector("[data-auth-form]");

if (form) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const mode = form.dataset.authForm;
    const status = document.querySelector("[data-auth-status]");
    const submitButton = form.querySelector("[type=submit]");
    const values = Object.fromEntries(new FormData(form));

    if (mode === "register" && values.password !== values.confirmPassword) {
      status.textContent = "Passwords do not match.";
      return;
    }

    submitButton.disabled = true;
    status.textContent = mode === "login" ? "Signing in…" : "Creating your account…";

    try {
      // TODO: Map the form payload to the backend's agreed authentication contract.
      if (mode === "login") await login(values);
      if (mode === "register") await register(values);
      // The dashboard loads identity independently from the authenticated backend session.
      window.location.assign("dashboard.html");
    } catch (error) {
      status.textContent = "Authentication is unavailable. Please try again when the service is configured.";
      console.warn("Authentication request failed.", error);
    } finally {
      submitButton.disabled = false;
    }
  });
}
