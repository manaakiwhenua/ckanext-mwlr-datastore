document.querySelectorAll(".review-form").forEach(function(form) {
  const reviewType = form.querySelector("[name='review_type']");
  const approvalOutcome = form.querySelector("[name='approval_outcome']");
  const approvalConditions = form.querySelector(".approval-conditions");
  const rejectionReason = form.querySelector("[name='rejection_reason']");
  const reviewWarning = form.querySelector(".review-warning");

  function checkReviewType() {
    if (!reviewWarning) return; // quit early if the element doesn't exist
    
    const reviewSelected = reviewType && reviewType.value;

    if (!reviewSelected) {
      reviewWarning.classList.remove("d-none");
    } else {
      reviewWarning.classList.add("d-none");
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

  function toggleApprovalDescriptionVisibility() {
    if (!approvalOutcome || !approvalConditions) return;

    if (approvalOutcome.value === "conditional") {
      approvalConditions.classList.remove("d-none");
    } else {
      approvalConditions.classList.add("d-none");
    }
  }

  checkReviewType();

  if (reviewType) {
    reviewType.addEventListener("change", function() {
      checkReviewType();
      retrieveRejectionReasons(reviewType.value);
    });
  }

  if (approvalOutcome) {
    approvalOutcome.addEventListener("change", toggleApprovalDescriptionVisibility);
  }
});