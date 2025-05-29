document.addEventListener("DOMContentLoaded", () => {
    document.querySelector(".login").addEventListener("click", login);
});

async function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    if (!email || !password) {
        showMessage("Please enter email and password!", "error");
        return;
    }

    try {
        const response = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const result = await response.json();
        
        if (response.ok && result.user_id) {
            localStorage.setItem("user_id", result.user_id);
            showMessage("Login successful! Redirecting...", "success");
            setTimeout(() => window.location.href = "/dashboard.html", 1500);
        } else {
            showMessage(result.error || "Login failed. Please try again.", "error");
        }
    } catch (error) {
        showMessage("Server error. Please try again later.", "error");
    }
}

function showMessage(message, type) {
    const msgElement = document.getElementById("message");
    msgElement.textContent = message;
    msgElement.style.color = type === "success" ? "green" : "red";
}
