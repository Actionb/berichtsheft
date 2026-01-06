// Mark a Nachweis object as finished/completed.

/*
 * Return the CSRF token.
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

/*
 * Return the "finish" list action button for a specific Nachweis object id.
 */
function getFinishButton(pk) {
    return document.querySelector(`button.finish-btn[data-obj-id="${pk}"]`);
}

/*
 * Return the results row for a specific Nachweis object id that is being marked as finished.
 */
function getFinishRow(pk) {
    return getFinishButton(pk).closest("tr");
}

/*
 * Return the URL for the "finish" action endpoint.
 */
function getFinishUrl() {
    return document.getElementById("confirmFinish").dataset.finishUrl
}

/*
 * Send a request to the server to mark the Nachweis with the given id as finished.
 */
function confirmFinish(pk, eingereichtBei) {
    fetch(getFinishUrl(), {
        method: "POST",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: new URLSearchParams({ pk: pk, eingereicht_bei: eingereichtBei })
    })
        .then(response => {
            if (response.ok) {
                response.json().then(data => {
                    // Update the results table:
                    const row = getFinishRow(pk);
                    if (row) {
                        const checkmark = '<i class="bi bi-check-circle fs-4 text-success"></i>';
                        row.querySelector(".td-fertig").innerHTML = checkmark;
                        row.querySelector(".td-unterschrieben").innerHTML = checkmark;
                        row.querySelector(".td-eingereicht_bei").textContent = data.eingereicht_bei;
                    }
                });
            } else {
                console.log(`Error marking Nachweis ${pk} as finished: ${response.statusText}`);
            }
        });

}

document.addEventListener("DOMContentLoaded", function () {
    // The modal contains fields for setting the "eingereicht_bei" value
    const modal = document.getElementById("finishModal");
    const modalBody = modal.querySelector(".modal-body");

    // Do not show the modal if the Nachweis already has a value for "eingereicht_bei"
    modal.addEventListener("show.bs.modal", (event) => {
        modal.pk = event.relatedTarget.dataset.objId;  // event.relatedTarget is the list action button that was pressed
        const eingereichtBei = getFinishRow(modal.pk).querySelector(".td-eingereicht_bei").textContent;
        if (eingereichtBei) {
            event.preventDefault();
            confirmFinish(modal.pk, eingereichtBei);
        }
    });

    // Handle modal confirmation.
    document.getElementById("confirmFinish").addEventListener("click", () => {
        const input = modalBody.querySelector("input[name='eingereicht_bei']");
        const select = modalBody.querySelector("select[name='eingereicht_bei']");
        if (modal.pk) {
            confirmFinish(modal.pk, input.value || select.value);
            bootstrap.Modal.getInstance(modal).hide();

            // Add a success message
            const messageContainer = document.querySelector("#messages-container");
            if (messageContainer) {
                messageContainer.insertAdjacentHTML(
                    "beforeend",
                    `<div class="alert alert-dismissible alert-success" role="alert">
                        Nachweis erfolgreich abgeschlossen.
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>`
                );
            }
        }
    });

})