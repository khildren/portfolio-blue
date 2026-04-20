/*************************/
/*      Contact Js       */
/*************************/

document.addEventListener('DOMContentLoaded', () => {
    const form = document.forms["myForm"];

    if (!form) return;

    const errorMsg = document.getElementById("error-msg");
    const responseDiv = document.getElementById("simple-msg");

    form.onsubmit = async function (e) {
        e.preventDefault();

        // Collect form values
        const name = form["name"]?.value.trim();
        const email = form["email"]?.value.trim();
        const comments = form["comments"]?.value.trim();

        // Reset error
        errorMsg.style.opacity = 0;
        errorMsg.innerHTML = "";
        responseDiv.innerHTML = "";

        // Basic client-side validation
        if (!name) return showError("*Please enter a Name*");
        if (!email) return showError("*Please enter an Email*");
        if (!comments) return showError("*Please enter a Comments*");

        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

            const formData = new URLSearchParams();
            formData.append("name", name);
            formData.append("email", email);
            formData.append("comments", comments);

            const response = await fetch("/contactus", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRF-TOKEN": csrfToken
                },
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                responseDiv.innerHTML = result.message;
                form.reset(); // clear form fields
            } else {
                showError(result.message || "Something went wrong.");
            }

        } catch (error) {
            console.error("An unexpected error occurred:", error);
            showError("An unexpected error occurred. Please try again later.");
        }
    };

    function showError(msg) {
        errorMsg.innerHTML = `<div class='alert alert-warning error_message'>${msg}</div>`;
        fadeIn(errorMsg);
        return false;
    }

    function fadeIn(element) {
        let opacity = 0;
        element.style.opacity = opacity;
        const interval = setInterval(() => {
            if (opacity < 1) {
                opacity += 0.1;
                element.style.opacity = opacity;
            } else {
                clearInterval(interval);
            }
        }, 50);
    }
});