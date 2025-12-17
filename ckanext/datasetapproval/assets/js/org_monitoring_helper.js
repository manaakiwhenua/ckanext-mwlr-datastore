console.log("org monitoring helper loaded");
var org_selected = document.getElementById("field-organizations");
var submit_button = document.getElementById("submitButton");
console.log("submit button:", submit_button);
var selected_org = org_selected.value;
console.log("selected org: " + selected_org);
//check_is_user_admin(selected_org);

org_selected.addEventListener("DOMContentLoaded", function() {
    var selected_org = org_selected.value;
    console.log("selected org changed to: " + selected_org);
    //check_is_user_admin(selected_org);
});


org_selected.addEventListener("change", function() {
    var selected_org = org_selected.value;
    console.log("selected org changed to: " + selected_org);
    //check_is_user_admin(selected_org);
});

async function check_is_user_admin(org_id) {
    const apiUrl = `/api/3/action/check_user_admin?org_id=${org_id}`;

    try {
        const response = await fetch(apiUrl);
        const data = await response.json();
        console.log("Admin check response:", data);
        if (!data.success) {
            throw new Error("API call unsuccessful");
        } 
        if (submit_button) {
            submit_button.hidden = !!data.result.is_user_admin;
        }
    } catch (error) {
        console.error("Error fetching admin details:", error);
    }
}