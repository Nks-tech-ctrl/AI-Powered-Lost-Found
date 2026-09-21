document.querySelectorAll("[data-image-input]").forEach((input) => {
  input.addEventListener("change", () => {
    const label = document.querySelector(`[data-file-name="${input.id}"]`);
    if (label && input.files?.[0]) label.textContent = input.files[0].name;
  });
});

document.querySelectorAll("[data-report-form]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    // TODO: Send new FormData(form) to the backend report endpoint.
  });
});
