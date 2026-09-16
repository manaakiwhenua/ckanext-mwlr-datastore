document.querySelectorAll(".review-form").forEach(function(form) {
  const reviewTypes = form.querySelectorAll("[name='review_types']");
  const approvalOutcome = form.querySelector("[name='approval_outcome']");
  const approvalConditions = form.querySelector(".approval-conditions");
  const rejectionReasons = form.querySelectorAll("[name='rejection_reasons']");
  const rejectionReasonsParentDiv = form.querySelector("#rejection_reason_checkbox_parent");
  const reviewWarning = form.querySelector(".review-warning");

  function checkDisplayOfReviewWarning() {
    if (!reviewWarning) return; // quit early if the element doesn't exist
    
    const reviewSelected = reviewTypes.length > 0 && Array.from(reviewTypes).some(rt => rt.checked); // check if at least one review type is selected

    if (!reviewSelected) {
      reviewWarning.classList.remove("d-none");
    } else {
      reviewWarning.classList.add("d-none");
    }
  }

  function updateRejectionReasons(reviewTypeValue) {
    if (rejectionReasons.length > 0) {
      // make an API action call to grab the rejection reasons for the selected review type
      var apiUrl = "/api/3/action/retrieve_rejection_reasons?review_types=" + reviewTypeValue;

      fetch(apiUrl)
        .then(response => response.json())
        .then(data => {

          rejectionReasonsParentDiv.innerHTML = ""; // Clear existing options
          Object.entries(data.result).forEach(([value, text]) => {
            const checkboxDiv = document.createElement("div");
            const checkboxInput = document.createElement("input");
            const checkboxLabel = document.createElement("label");

            checkboxDiv.classList.add("form-check");
            checkboxInput.classList.add("form-check-input");
            checkboxInput.type = "checkbox";
            checkboxInput.name = "rejection_reasons";
            checkboxInput.id = `rejection_reason_${value}`;
            checkboxInput.value = value;

            checkboxLabel.classList.add("form-check-label", "multi-select-reasons");
            checkboxLabel.htmlFor = `rejection_reason_${value}`;
            checkboxLabel.textContent = text;

            checkboxDiv.appendChild(checkboxInput)
            checkboxDiv.appendChild(checkboxLabel)

            rejectionReasonsParentDiv.appendChild(checkboxDiv);
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

  checkDisplayOfReviewWarning();

  // Attach the handler to each reviewType input
  if (reviewTypes.length > 0) {
    reviewTypes.forEach(function(rt) {
      rt.addEventListener("change", handleReviewTypeChange);
    });
  }

  if (approvalOutcome) {
    approvalOutcome.addEventListener("change", toggleApprovalDescriptionVisibility);
  }

  function handleReviewTypeChange() {
    checkDisplayOfReviewWarning();
    const selectedReviewTypes = getSelectedReviewTypes();
    updateRejectionReasons(selectedReviewTypes.join(","));
  }
  
  function getSelectedReviewTypes() {
    return Array.from(reviewTypes)
      .filter(rt => rt.checked)
      .map(rt => rt.value);
  }
});
