var org_selected = document.getElementById("field-organizations");
var submit_button = document.getElementById("submitButton");
var save_button = document.getElementById("saveButton");
var update_button = document.getElementById("updateButton");
var selected_org = org_selected.value;
check_is_user_admin(selected_org);

// handle change event on select 2 organization field dropdown
$('#field-organizations').on('change', function() {
    var selected_org = org_selected.value;
    check_is_user_admin(selected_org);
});

async function check_is_user_admin(org_id) {
    const apiUrl = `/api/3/action/check_user_admin?org_id=${org_id}`;

    try {
        const response = await fetch(apiUrl);
        const data = await response.json();
        if (!data.success) {
            throw new Error("API call unsuccessful");
        } 
        if (submit_button) {
            submit_button.hidden = !!data.result.is_user_admin;
        }
        if (save_button) {
            save_button.hidden = !!data.result.is_user_admin;
        }
        if (update_button) {
            update_button.hidden = !data.result.is_user_admin;
        }
    } catch (error) {
        console.error("Error fetching admin details:", error);
    }
}