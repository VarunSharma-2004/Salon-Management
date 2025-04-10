document.addEventListener("DOMContentLoaded", () => {
    document.querySelector(".register").addEventListener("click", register);
});

async function register() {
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    if (!name || !email || !password) {
        showMessage("All fields are required!", "error");
        return;
    }

    try {
        const response = await fetch("/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, password })
        });

        const result = await response.json();
        console.log("Server Response:", result); // Debugging

        if (response.ok) {
            showMessage("Registration successful! Redirecting to login...", "success");

            setTimeout(() => {
                window.location.href = "/"; // Change path if needed
            }, 2000);
        } else {
            showMessage(result.error || "Registration failed. Try again!", "error");
        }
    } catch (error) {
        console.error("Fetch Error:", error);
        showMessage("Server error. Please try again later.", "error");
    }
}

function showMessage(message, type) {
    const msgElement = document.getElementById("message");
    msgElement.textContent = message;
    msgElement.style.color = type === "success" ? "green" : "red";
}
