document.querySelectorAll(".review-form").forEach(function(form) {
  const reviewType = form.querySelector("[name='review_type']");
  const approvalType = form.querySelector("[name='approval_type']");
  const reviewWarning = form.querySelector(".review-warning");

  function checkReviewType() {
    const reviewSelected = reviewType && reviewType.value;
    const approvalSelected = approvalType && approvalType.value;

    if (!reviewSelected) {
      if (reviewWarning) reviewWarning.classList.remove("d-none");
    } else if (approvalType && !approvalSelected) {
      if (reviewWarning) reviewWarning.classList.remove("d-none");
    } else {
      if (reviewWarning) reviewWarning.classList.add("d-none");
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