// Mark a Nachweis object as finished/completed.

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

document.addEventListener("DOMContentLoaded", function () {
    const confirmButtons = document.querySelectorAll(".confirm-finish-btn");
    confirmButtons.forEach(button => {
        button.addEventListener("click", function () {
            // Handle the finish action for the specific row
            const url = this.dataset.finishUrl;
            const modalBody = button.closest(".modal-content").querySelector(".modal-body");
            const form = modalBody.querySelector("form");
            
            const input = modalBody.querySelector("input[name='eingereicht_bei']");
            const select = modalBody.querySelector("select[name='eingereicht_bei']");
            let eingereichtBei = "";
            if (input && select) {
                eingereichtBei = input.value || select.value;
            }
            if (url) {
                fetch(url, {
                    method: "POST",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "X-CSRFToken": getCookie("csrftoken")
                    },
                    body: new URLSearchParams({ eingereicht_bei: eingereichtBei })
                })
                    .then(response => {
                        // TODO: take the value for "eingereicht_bei" from the response and insert it into the table
                        if (response.ok) {
                            response.json().then(data => {
                                // Update the table:
                                const row = button.closest("tr");
                                row.querySelector(".td-eingereicht_bei").textContent = data.eingereicht_bei;
                                row.querySelector(".td-finish").textContent = "Fertiggestellt";
                                row.querySelector(".td-unterschrieben").textContent = "Ja";

                                // Close the modal
                                const modal = button.closest(".modal");
                                if (modal) {
                                    const modalInstance = bootstrap.Modal.getInstance(modal);
                                    modalInstance.hide();
                                }

                                // Add a success message
                                const messageContainer = document.querySelector("#messages-container");
                                if (messageContainer) {
                                    messageContainer.insertAdjacentHTML("beforeend", `<div class="alert alert-dismissible alert-success" role="alert">
                            Nachweis erfolgreich abgeschlossen.
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>`);
                                }

                            });
                        } else {
                            // Handle error
                        }
                    });
            }
        });
    });
})