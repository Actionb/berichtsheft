/*
Prompt the user for a confirmation before deleting an item.
*/

document.addEventListener("DOMContentLoaded", function () {
    const deleteBtn = document.getElementById("delete-btn");
    if (deleteBtn) {
        deleteBtn.addEventListener("click", function (event) {
            // TODO: use a modal for this?
            if (!confirm("Sind Sie sicher, dass Sie dieses Objekt löschen möchten?")) {
                event.preventDefault();
            }
        });
    }
})