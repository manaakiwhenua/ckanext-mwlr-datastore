document.querySelectorAll(".review-form").forEach(function(form) {
  const reviewType = form.querySelector("[name='review_type']");
  const approvalType = form.querySelector("[name='approval_type']");
  const rejectionReason = form.querySelector("[name='rejection_reason']");
  const reviewWarning = form.querySelector(".review-warning");

  function checkReviewType() {
    if (!reviewWarning) return; // quit early if the element doesn't exist
    
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

  function retrieveRejectionReasons(reviewTypeValue) {
    if (rejectionReason) {
      // make an API action call to grab the rejection reasons for the selected review type
      var apiUrl = "/api/3/action/retrieve_rejection_reasons?review_type=" + reviewTypeValue;

      fetch(apiUrl)
        .then(response => response.json())
        .then(data => {

          // reset rejection reason, if selected, and repopulate with conditional reasons
          rejectionReason.innerHTML = "";
          rejectionReason.appendChild(new Option("Select reason", ""));

          Object.entries(data.result).forEach(([value, text]) => {
            let option = document.createElement("option");
            option.value = value;
            option.textContent = text;
            rejectionReason.appendChild(option);
          });

        })
        .catch(error => {
          console.error("Error fetching rejection reasons:", error);
        });
      }
  }

  checkReviewType();

  if (reviewType) {
    reviewType.addEventListener("change", function() {
      checkReviewType();
      retrieveRejectionReasons(reviewType.value);
    });
  }

  if (approvalType) {
    approvalType.addEventListener("change", checkReviewType);
  }
});