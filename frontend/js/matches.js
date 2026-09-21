document.querySelectorAll("[data-match-details]").forEach((button) => {
  button.addEventListener("click", () => {
    // TODO: Navigate to the selected backend-backed match detail.
    window.location.href = "item-details.html";
  });
});
