document.addEventListener("DOMContentLoaded", () => {
  const jobSelect = document.getElementById("job_id");
  const customFields = document.getElementById("custom_job");
  function toggleCustom() {
    customFields.style.display = jobSelect.value === "custom" ? "block" : "none";
  }
  if (jobSelect) {
    jobSelect.addEventListener("change", toggleCustom);
    toggleCustom();
  }
});
