document.addEventListener("DOMContentLoaded", () => {
    document.querySelector(".register").addEventListener("click", register);
    document.querySelector(".login").addEventListener("click", login);
});

async function register() {
    const name = document.getElementById("name").value;  // FIXED ID
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    if (!name || !email || !password) {
        showMessage("All fields are required!", "error");
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:5000/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, password })
        });

        const result = await response.json();
        if (response.ok) {
            showMessage("Registration successful! Redirecting to login...", "success");
            setTimeout(() => window.location.href = "login.html", 2000);
        } else {
            showMessage(result.error || "Registration failed. Try again!", "error");
        }
    } catch (error) {
        showMessage("Server error. Please try again later.", "error");
    }
}

async function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    if (!email || !password) {
        showMessage("Please enter email and password!", "error");
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:5000/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const result = await response.json();
        
        if (response.ok && result.user_id) {
            localStorage.setItem("user_id", result.user_id);
            showMessage("Login successful! Redirecting...", "success");
            setTimeout(() => window.location.href = "dashboard.html", 1500);
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
