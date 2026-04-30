console.log("package form helpers loaded")

// here can monitor the form as see if anything except the visibility has changed


// button by default should simply state "Submit for review" unless "chosen_visibility" is updated (AND dataset is in approved state) 
// then should be "Update Visibility"

// if any other field is updated button should move back to "Submit for review"

document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form.dataset-form")
    if (!form) return;

    const publishingStatus = form.querySelector("#field-publishing_status");
    const submitButton = form.querySelector("#submitButton");
    const bypassReview = document.getElementById("bypass-review-flag");
    if (!submitButton || publishingStatus.value !== "approved" || !bypassReview) return;

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

    function checkMeaningfulChanges() {
        const currentState = getFormState(form);
        var visibilityChanged;

        //grab all fields that have been altered that aren't the chosen_visibility or bypass review flag
        const meaningfulChanges = Object.keys(currentState).filter((key) => {
            // don't add if visibility change but record this change
            if (key === "chosen_visibility") {
                visibilityChanged = JSON.stringify(currentState[key]) !== JSON.stringify(originalState[key])
            } else {
                if (key !== "bypass_review"){
                    return JSON.stringify(currentState[key]) !== JSON.stringify(originalState[key])
                }
            }
        });

        console.log("meaningful changes: ", meaningfulChanges);

        // if visibility has changed, check if there have been any other changes
        if (visibilityChanged) {
            if (meaningfulChanges.length > 0) {
                bypassReview.value = "false";
            } else {
                bypassReview.value = "true";
            }
            updateFormContent()
        }
    }
    
    function updateFormContent() {
        if (bypassReview.value == "true") {
            submitButton.textContent = "Update Visibility";
        } else {
            submitButton.textContent = "Submit for Review";
        }
    }

    form.addEventListener("input", checkMeaningfulChanges);
    form.addEventListener("change", checkMeaningfulChanges);
    // the tag and license fields are handled with jquery select2 events so needed additional work
    if (window.jQuery) {
        jQuery("[name='license_id']").on("change select2:select select2:unselect", function () {
            console.log("license changed:", jQuery(this).val());
            checkMeaningfulChanges();
        });

        jQuery("[name='tag_string']").on("change select2:select select2:unselect", function () {
            console.log("tags changed:", jQuery(this).val());
            checkMeaningfulChanges();
        });
    }
})
