document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector("form.dataset-form")
  if (!form) return;

  function syncVisibility() {
    // Find all fields that have conditional visibility rules
    let dependentFields = form.querySelectorAll("[data-conditional-visibility-controller]");
    
    dependentFields.forEach(field => {
      const visibilityControllerName = field.dataset.conditionalVisibilityController;
      const controller = form.querySelector(`[name="${visibilityControllerName}"]`);
      if (!controller) return;

      const controllerHasMatchingValue = controller.value === field.dataset.conditionalVisibilityValue; // For non-checkbox controller fields (e.g. a select dropdown), check if the controller field value matches the value that triggers visibility
      const visible = controller.type === "checkbox" ? controller.checked : controllerHasMatchingValue;

      const group = field.closest(".form-group");
      if (group) {
        group.classList.toggle("d-none", !visible);
        if (!visible) field.value = ""; // Clear the value of hidden fields to prevent stale data from being submitted
      }
    });
  }

  syncVisibility();  // Initial check on page load

  // Add change event listeners to all controls that affect field visibility
  form.querySelectorAll("[data-conditional-visibility-controller]").forEach(conditionalVisibilityField => {
    const visibilityControllerName = conditionalVisibilityField.dataset.conditionalVisibilityController;
    const controller = form.querySelector(`[name="${visibilityControllerName}"]`);
    if (controller) {
      controller.addEventListener("change", syncVisibility);
    }
  });
});