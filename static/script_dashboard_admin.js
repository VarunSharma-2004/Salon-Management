document.addEventListener("DOMContentLoaded", () => {
    checkAuth();
    fetchAppointments();
    fetchServices();

    document.getElementById("logout-btn").addEventListener("click", logout);
    document.getElementById("add-service-form").addEventListener("submit", addService);
});

// Check Authentication
function checkAuth() {
    if (localStorage.getItem("authenticated") !== "true") {
        window.location.href = "/adminlogin";
    }
}

// Logout Function
function logout() {
    localStorage.removeItem("authenticated");
    window.location.href = "/adminlogin";
}

/*// Fetch Appointments
function fetchAppointments() {
    fetch("/admin/appointments")
        .then(response => response.json())
        .then(data => {
            console.log("API Response:", data); // Debugging output

            const appointmentList = document.getElementById("appointments-list");
            appointmentList.innerHTML = "";

            data.forEach(appointment => {
                const customerName = appointment.user || "Unknown User"; // Fix for undefined user
                const service = appointment.service || "Unknown Service";
                const date = appointment.date || "No Date";
                const time = appointment.time || "No Time";

                const listItem = document.createElement("li");
                listItem.textContent = `${customerName} - ${service} (${date} at ${time})`;
                <button onclick="updateStatus(${appt.id}, 'Accepted')">Accept</button>
                <button onclick="updateStatus(${appt.id}, 'Declined')">Decline</button>
                appointmentList.appendChild(listItem);
            });
        })
        .catch(error => console.error("Error fetching appointments:", error));
}*/
document.addEventListener("DOMContentLoaded", fetchAppointments);

function fetchAppointments() {
    fetch("/admin/appointments")
        .then(response => response.json())
        .then(data => {
            const list = document.getElementById("appointments-list");
            list.innerHTML = ""; // Clear any old data

            data.forEach(appt => {
                const li = document.createElement("li");
                li.className = "appointment-item";
                li.innerHTML = `
                    <strong>${appt.user}</strong> booked <strong>${appt.service}</strong> 
                    on <strong>${appt.date}</strong> at <strong>${appt.time}</strong> 
                    - Status: <strong>${appt.status}</strong>
                `;
                list.appendChild(li);
            });
        })
        .catch(error => {
            console.error("Error fetching appointments:", error);
        });
}

/*function updateStatus(id, status) {
    fetch(`/admin/appointment/${id}/status`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ status }),
    })
    .then(res => res.json())
    .then(() => fetchAppointments());
}*/

// Fetch Services
function fetchServices() {
    fetch("/admin/services")
        .then(response => response.json())
        .then(data => {
            const serviceList = document.getElementById("services-list");
            serviceList.innerHTML = "";
            data.forEach(service => {
                const listItem = document.createElement("li");
                listItem.innerHTML = `${service.name} - ₹${service.price} 
                    <button onclick="deleteService(${service.id})">Delete</button>`;
                serviceList.appendChild(listItem);
            });
        })
        .catch(error => console.error("Error fetching services:", error));
}

// Add Service
function addService(event) {
    event.preventDefault();
    const serviceName = document.getElementById("service-name").value;
    const price = document.getElementById("service-price").value;
    const duration = document.getElementById("service-duration").value;

    fetch("/admin/services", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: serviceName, price: price, duration: duration })
    })
    .then(response => response.json())
    .then(() => {
        fetchServices();
        document.getElementById("add-service-form").reset();
    })
    .catch(error => console.error("Error adding service:", error));
}

// Delete Service
function deleteService(serviceId) {
    fetch(`/admin/services/${serviceId}`, { method: "DELETE" })
    .then(() => fetchServices())
    .catch(error => console.error("Error deleting service:", error));
}
