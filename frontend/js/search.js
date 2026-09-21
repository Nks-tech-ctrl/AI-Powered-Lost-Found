const emptyState = document.querySelector("[data-empty-state]");
const results = document.querySelector("[data-results]");
document.querySelector("[data-search-form]")?.addEventListener("submit", (event) => {
  event.preventDefault();
  // TODO: Query the backend and render returned report results.
  const query = new FormData(event.currentTarget).get("query")?.trim();
  if (query?.toLowerCase() === "none") {
    results?.classList.add("hidden");
    emptyState?.classList.remove("hidden");
  } else {
    results?.classList.remove("hidden");
    emptyState?.classList.add("hidden");
  }
});
