document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector("form.dataset-form")
  if (!form) return;

  function syncVisibility(controller, field, group) {
    if (controller.type === "radio" && controller.checked == false || controller.type === "checkbox" && controller.checked == false) return; // For radio buttons and checkboxes, only proceed if the controller is checked (i.e. active)

    const controllerHasMatchingValue = String(controller.value).toLowerCase() === field.dataset.conditionalVisibilityValue.toLowerCase();

    if (group) {
      group.classList.toggle("d-none", !controllerHasMatchingValue);
      if (!controllerHasMatchingValue) field.value = ""; // Clear the value of hidden fields to prevent stale data from being submitted
    }
  }

  // Add change event listeners to all controls that affect field visibility
  form.querySelectorAll("[data-conditional-visibility-controller]").forEach(conditionalVisibilityField => {
    const group = conditionalVisibilityField.closest(".form-group");

    if (group) { 
      group.classList.add("d-none"); // Hide all conditionally visible fields on page load. This means fields are hidden if the selection is blank (as with a new dataset)
    } 

    const visibilityControllerName = conditionalVisibilityField.dataset.conditionalVisibilityController;
    const controller = form.querySelectorAll(`[name="${visibilityControllerName}"]`); // get all controllers with the same name (e.g. for radio button groups)
    if (controller.length > 0) {
      controller.forEach(ctrl => {
        syncVisibility(ctrl, conditionalVisibilityField, group); // Sync visibility on page load 
        ctrl.addEventListener("change", () => syncVisibility(ctrl, conditionalVisibilityField, group));
      });
    }
  });
});