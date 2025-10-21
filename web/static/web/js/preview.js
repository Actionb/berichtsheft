/* Take the form data and open a preview page of the final PDF. */

document.addEventListener("DOMContentLoaded", function () {
    const btn = document.getElementById("preview");
    btn.addEventListener("click", function () {
        const form = document.querySelector("form");
        const data = new FormData(form);
        data.delete("csrfmiddlewaretoken");
        const queryString = new URLSearchParams(data).toString();
        const previewUrl = btn.getAttribute("data-preview-url");
        window.open(previewUrl + "?" + queryString, "_blank");
    });
});