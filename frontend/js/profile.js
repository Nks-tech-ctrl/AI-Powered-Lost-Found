import { updateCurrentUser } from "./auth.js";
import { hydrateCurrentUser } from "./current-user.js";

hydrateCurrentUser();

document.querySelector("[data-profile-form]")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const status = document.querySelector("[data-profile-save-status]");
  const submitButton = form.querySelector("[type=submit]");
  submitButton.disabled = true;
  status.textContent = "Saving profile…";

  try {
    // TODO: Confirm the profile payload field names with the backend teammate.
    await updateCurrentUser(Object.fromEntries(new FormData(form)));
    status.textContent = "Profile saved.";
    await hydrateCurrentUser();
  } catch (error) {
    status.textContent = "Unable to save profile. Please try again when the service is available.";
    console.warn("Unable to save the current user profile.", error);
  } finally {
    submitButton.disabled = false;
  }
});
