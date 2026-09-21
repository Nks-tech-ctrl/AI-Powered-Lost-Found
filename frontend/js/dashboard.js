import { hydrateCurrentUser } from "./current-user.js";

document.querySelectorAll("[data-sidebar-link]").forEach((link) => {
  link.addEventListener("click", () => document.querySelectorAll("[data-sidebar-link]").forEach((item) => item.classList.remove("bg-blue-50", "text-blue-700")));
});

hydrateCurrentUser();
