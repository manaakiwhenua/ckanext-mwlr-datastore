console.log("package form helpers loaded")

// here can monitor the form as see if anything except the visibility has changed


// button by default should simply state "Submit for review" unless "chosen_visibility" is updated (AND dataset is in approved state) 
// then should be "Update Visibility"

// if any other field is updated button should move back to "Submit for review"

document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form.dataset-form")
    const publishingStatus = form.querySelector("#field-publishing_status");
    console.log("publishing status: ", publishingStatus.value)
    const submitButton = form.querySelector("#submitButton");
    console.log("submit button text: ", submitButton)
    const chosen_visibility = "chosen_visibility"
    const bypassReview = document.getElementById("bypass-review-flag");
    console.log("visibility", bypassReview)

    if (!form || !submitButton || publishingStatus.value !== "approved" || !bypassReview) return; // guard clause
    console.log("made it here: ");
    function getFormState() {
        const formData = new FormData(form);
        const state = {};

        for (const [key, value] of formData.entries()) {
            if (key === "save" || key === "submit_check") continue; // don't compare the submit button values
            if(!state[key]) {
                state[key] = [];
            }

            state[key].push(value)
        }
        return state;
    }

    const originalState = getFormState(form);
    console.log("original form state: ", originalState)

    function normalize(value) {
        return JSON.stringify(value || []);
    }

    function determineSubmitLogic() {
        const currentState = getFormState(form);
        var visibilityChanged = false;
        //grab all fields that have been altered that aren't the chosen_visibility or bypass review flag
        const changedFields = Object.keys(currentState).filter((key) => {
            if (key === "chosen_visibility"){
                visibilityChanged = JSON.stringify(currentState[key]) !== JSON.stringify(originalState[key])
            }
            if (key !== "chosen_visibility" && key !== "bypass_review") {
                return JSON.stringify(currentState[key]) !== JSON.stringify(originalState[key])
            }
        });

        // if no fields where changed and visibility was changed
        if (changedFields.length === 0 && visibilityChanged) {
            submitButton.textContent = "Update visibility";
            bypassReview.value = "true";

        } else {
            submitButton.textContent = "Submit for Review";
            bypassReview.value = "false";
        }


    }

    form.addEventListener("input", determineSubmitLogic);
    form.addEventListener("change", determineSubmitLogic);
})
