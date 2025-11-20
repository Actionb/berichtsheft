/**
 * Hard delete a model instance that is currently in the recycle bin.
 */

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener("DOMContentLoaded", () => {
    const deleteAllButton = document.getElementById("delete-all")
    if (deleteAllButton) {
        deleteAllButton.addEventListener("click", (event) => {
            if (!confirm("Sind Sie sicher, dass Sie alle Objekte löschen möchten?")) {
                event.preventDefault()
            }
        })
    }

    const deleteButtons = document.querySelectorAll(".delete-btn")
    deleteButtons.forEach(button => {
        button.addEventListener("click", (event) => {
            event.preventDefault()
            const url = button.getAttribute("href")
            fetch(url, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCookie("csrftoken")
                }
            }).then(response => {
                if (response.ok) {
                    location.reload()
                } else {
                    alert("Fehler beim Löschen des Objekts.")
                }
            })
        })
    })
})
