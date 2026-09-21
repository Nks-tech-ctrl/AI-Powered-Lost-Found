import { hydrateCurrentUser } from "./current-user.js";

hydrateCurrentUser();

document.querySelector("[data-profile-form]")?.addEventListener("submit", (event) => {
  event.preventDefault();
  // TODO: Send this FormData to the backend's agreed profile-update endpoint.
});
