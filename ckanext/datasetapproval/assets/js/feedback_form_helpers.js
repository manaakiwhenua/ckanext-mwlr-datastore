console.log("feedback_form_helpers.js loaded");

document.querySelectorAll(".review-form").forEach(function(form) {
  const reviewType = form.querySelector("[name='review_type']");
  const approvalType = form.querySelector("[name='approval_type']");
  const rejectWarning = form.querySelector(".reject-review-warning");
  const approveWarning = form.querySelector(".approve-review-warning");

  function checkReviewType() {
    const reviewSelected = reviewType && reviewType.value;
    const approvalSelected = approvalType && approvalType.value;

    if (!reviewSelected) {
      if (rejectWarning) rejectWarning.classList.remove("d-none");
      if (approveWarning) approveWarning.classList.remove("d-none");
    } else if (approvalType && !approvalSelected) {
      if (rejectWarning) rejectWarning.classList.add("d-none");
      if (approveWarning) approveWarning.classList.remove("d-none");
    } else {
      if (rejectWarning) rejectWarning.classList.add("d-none");
      if (approveWarning) approveWarning.classList.add("d-none");
    }
  }

  checkReviewType();

  if (reviewType) {
    reviewType.addEventListener("change", checkReviewType);
  }

  if (approvalType) {
    approvalType.addEventListener("change", checkReviewType);
  }
});