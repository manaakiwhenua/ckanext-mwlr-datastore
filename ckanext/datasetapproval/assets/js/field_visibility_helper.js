document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector("form.dataset-form")
  if (!form) return;

  function syncVisibility(field) {

      const visibilityControllerName = field.dataset.conditionalVisibilityController;
      const controller = form.querySelector(`[name="${visibilityControllerName}"]`);
      if (!controller) return;

      const controllerHasMatchingValue = String(controller.value).toLowerCase() === field.dataset.conditionalVisibilityValue.toLowerCase(); // For non-checkbox controller fields (e.g. a select dropdown), check if the controller field value matches the value that triggers visibility

      let visible = (controller.type === "checkbox" || controller.type === "radio") ? (controller.checked && controllerHasMatchingValue) : controllerHasMatchingValue;

      const group = field.closest(".form-group");
      if (group) {
        group.classList.toggle("d-none", !visible);
        if (!visible) field.value = ""; // Clear the value of hidden fields to prevent stale data from being submitted
      }
  }

  // Add change event listeners to all controls that affect field visibility
  form.querySelectorAll("[data-conditional-visibility-controller]").forEach(conditionalVisibilityField => {
    const visibilityControllerName = conditionalVisibilityField.dataset.conditionalVisibilityController;
    const controller = form.querySelectorAll(`[name="${visibilityControllerName}"]`); // get all controllers with the same name (e.g. for radio button groups)
    if (controller.length > 0) {
      syncVisibility(conditionalVisibilityField); // Sync visibility on page load 
      controller.forEach(ctrl => {
        ctrl.addEventListener("change", () => syncVisibility(conditionalVisibilityField));
      });
    }
  });
});