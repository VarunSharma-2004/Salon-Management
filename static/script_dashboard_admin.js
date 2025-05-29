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
                appointmentList.appendChild(listItem);
            });
        })
        .catch(error => console.error("Error fetching appointments:", error));
}*/

async function fetchAppointments() {
    try {
        const response = await fetch(`/appointments`);
        if (!response.ok) throw new Error("Failed to fetch appointments");

        const appointments = await response.json();
        const list = document.getElementById("appointments-list");
        list.innerHTML = "";

        if (appointments.length === 0) {
            list.innerHTML = "<li>No appointments available.</li>";
            return;
        }

        appointments.forEach(appointment => {
            const li = document.createElement("li");
            li.innerHTML = `${appointment.service} for User ID ${appointment.user_id} on ${appointment.date} at ${appointment.time} - Status: ${appointment.status}`;

            if (appointment.status === "Booked") {
                const acceptBtn = document.createElement("button");
                acceptBtn.textContent = "Accept";
                acceptBtn.onclick = () => updateStatus(appointment.id, "Accepted");

                const declineBtn = document.createElement("button");
                declineBtn.textContent = "Decline";
                declineBtn.onclick = () => updateStatus(appointment.id, "Declined");

                li.appendChild(acceptBtn);
                li.appendChild(declineBtn);
            }

            list.appendChild(li);
        });
    } catch (error) {
        console.error("Error:", error);
    }
}

async function updateStatus(appointmentId, newStatus) {
    try {
        const response = await fetch(`/appointments/${appointmentId}/status`, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ status: newStatus })
        });

        if (!response.ok) throw new Error("Failed to update status");

        alert(`Appointment ${newStatus}`);
        await fetchAppointments();
    } catch (error) {
        console.error("Error updating status:", error);
        alert("Error updating status");
    }
}


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
