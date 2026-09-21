import { getCurrentUser } from "./auth.js";

function fullName(user) {
  return user.name || [user.firstName, user.lastName].filter(Boolean).join(" ");
}

function initials(user) {
  return fullName(user).split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
}

function setText(selector, value) {
  document.querySelectorAll(selector).forEach((element) => { element.textContent = value; });
}

function setField(field, value) {
  document.querySelectorAll(`[data-user-field="${field}"]`).forEach((input) => { input.value = value || ""; });
}

function setStatistic(statistics, name) {
  const aliases = {
    lostReports: ["lostReports", "lost_reports", "lostItems"],
    foundReports: ["foundReports", "found_reports", "foundItems"],
    matches: ["potentialMatches", "potential_matches", "matches"],
    claims: ["activeClaims", "active_claims", "claims"],
  };
  const value = aliases[name].map((key) => statistics?.[key]).find((item) => item !== undefined && item !== null);
  setText(`[data-user-stat="${name}"]`, value ?? "—");
}

function setAvatar(user) {
  document.querySelectorAll("[data-user-avatar]").forEach((container) => {
    const image = container.querySelector("[data-user-avatar-image]");
    const fallback = container.querySelector("[data-user-avatar-fallback]");
    if (image && user.avatarUrl) {
      image.src = user.avatarUrl;
      image.alt = fullName(user) ? `${fullName(user)}'s avatar` : "Account avatar";
      image.classList.remove("hidden");
      fallback?.classList.add("hidden");
    } else if (fallback) {
      fallback.textContent = initials(user) || "";
      fallback.classList.remove("hidden");
    }
  });
}

export async function hydrateCurrentUser() {
  try {
    const user = await getCurrentUser();
    const name = fullName(user);
    const greeting = user.firstName ? `Good morning, ${user.firstName}` : "Good morning";

    setText("[data-user-name]", name);
    setText("[data-user-greeting]", greeting);
    setField("firstName", user.firstName);
    setField("lastName", user.lastName);
    setField("email", user.email);
    setField("phone", user.phone);
    setAvatar(user);
    ["lostReports", "foundReports", "matches", "claims"].forEach((stat) => setStatistic(user.statistics, stat));
    setText("[data-current-user-state]", "");
    return user;
  } catch (error) {
    // A blank configuration or unauthenticated session must not display a made-up person.
    setText("[data-current-user-state]", "Account details will appear when your authenticated session is available.");
    console.warn("Unable to load the current user.", error);
    return null;
  }
}
