document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("login-form");
    
    loginForm.addEventListener("submit", (event) => {
        event.preventDefault();
        
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;
        
        if (email === "salon@gmail.com" && password === "Salon@123") {
            localStorage.setItem("authenticated", "true");
            window.location.href = "dashboard_admin.html";
        } else {
            alert("Invalid credentials! Please try again.");
        }
    });
});
