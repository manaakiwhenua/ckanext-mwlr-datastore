document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector("form.dataset-form")
  if (!form) return;

  const REVIEW_CHECKBOX_SUFFIX = "_review_required";
  const SCHEMING_PREFIX = "field-";
  const REVIEW_NOTES_SUFFIX = "_review_notes";

  function updateReviewCommentBoxVisibility() {
    let checkboxes = form.querySelectorAll(`input[type="checkbox"][name$="${REVIEW_CHECKBOX_SUFFIX}"]`);

    checkboxes.forEach(checkbox => {
      const reviewType = checkbox.name.replace(REVIEW_CHECKBOX_SUFFIX, "");
      const reviewNote = document.getElementById(`${SCHEMING_PREFIX}${reviewType}${REVIEW_NOTES_SUFFIX}`);
      const reviewNoteGroup = reviewNote ? reviewNote.closest(".form-group") : null;
      if (reviewNoteGroup) {
        reviewNoteGroup.classList.toggle("d-none", !checkbox.checked);
        // Clear the review note if the checkbox is unchecked to prevent stale data being submitted
        if (!checkbox.checked) {
          reviewNote.value = "";
        }
      }
    });
  }

  updateReviewCommentBoxVisibility();  // Initial check on page load
  form.querySelectorAll(`input[type="checkbox"][name$="${REVIEW_CHECKBOX_SUFFIX}"]`).forEach(checkbox => {
    checkbox.addEventListener("change", updateReviewCommentBoxVisibility);
  });
});