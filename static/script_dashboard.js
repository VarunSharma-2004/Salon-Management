document.addEventListener("DOMContentLoaded", async () => {
    const userId = localStorage.getItem("user_id");
    if (!userId) {
        window.location.href = "login.html";
        return;
    }
    
    await fetchServices();
    await fetchAppointments();
});

async function fetchServices() {
    const servicesList = document.getElementById("services-list");
    const serviceSelect = document.getElementById("service-select");

    try {
        const response = await fetch("http://127.0.0.1:5000/services");
        if (!response.ok) {
            throw new Error("Failed to fetch services");
        }
        
        const services = await response.json();
        servicesList.innerHTML = "";
        serviceSelect.innerHTML = "";

        services.forEach(service => {
            const li = document.createElement("li");
            li.textContent = `${service.name} - Rs. ${service.price} (${service.duration})`;
            servicesList.appendChild(li);
            
            const option = document.createElement("option");
            option.value = service.id;
            option.textContent = `${service.name} (${service.duration})`;
            serviceSelect.appendChild(option);
        });
    } catch (error) {
        console.error("Error fetching services:", error);
        servicesList.innerHTML = "<li>Error loading services. Please try again later.</li>";
    }
}

async function fetchAppointments() {
    const userId = localStorage.getItem("user_id");
    if (!userId) return;

    try {
        const response = await fetch(`http://127.0.0.1:5000/appointments/${userId}`);
        if (!response.ok) {
            throw new Error("Failed to fetch appointments");
        }

        const appointments = await response.json();
        const appointmentsList = document.getElementById("appointments-list");
        appointmentsList.innerHTML = "";

        if (appointments.length === 0) {
            appointmentsList.innerHTML = "<li>No appointments booked.</li>";
            return;
        }

        appointments.forEach(appointment => {
            const serviceName = appointment.service || "Unknown Service";  // Fixes the issue

            const li = document.createElement("li");
            li.textContent = `${serviceName} on ${appointment.date} at ${appointment.time}`;

            const deleteButton = document.createElement("button");
            deleteButton.textContent = "Delete";
            deleteButton.classList.add("delete-btn");
            deleteButton.onclick = () => deleteAppointment(appointment.id);

            li.appendChild(deleteButton);
            appointmentsList.appendChild(li);
        });
    } catch (error) {
        console.error("Error fetching appointments:", error);
    }
}
async function bookAppointment() {
    const userId = localStorage.getItem("user_id");
    if (!userId) {
        alert("User not logged in. Please log in again.");
        window.location.href = "login.html";
        return;
    }

    const serviceId = document.getElementById("service-select").value;
    const date = document.getElementById("appointment-date").value;
    const time = document.getElementById("appointment-time").value;

    if (!serviceId || !date || !time) {
        alert("Please select a service, date, and time.");
        return;
    }

    const selectedDateTime = new Date(`${date}T${time}`);
    const currentDateTime = new Date();

    if (selectedDateTime < currentDateTime) {
        alert("You cannot book an appointment in the past. Please select a valid date and time.");
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:5000/appointments", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: userId,
                service_id: serviceId,
                date: date,
                time: time
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Failed to book appointment");
        }

        alert("Appointment booked successfully!");
        await fetchAppointments();
    } catch (error) {
        console.error("Error booking appointment:", error);
        alert(error.message); // Show the error from backend
    }
}

async function deleteAppointment(appointmentId) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/appointments/${appointmentId}`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error("Failed to delete appointment");
        }

        alert("Appointment deleted successfully!");
        await fetchAppointments();
    } catch (error) {
        console.error("Error deleting appointment:", error);
        alert("Error deleting appointment. Please try again.");
    }
}

document.getElementById("book-appointment-btn").addEventListener("click", bookAppointment);

function logout() {
    localStorage.removeItem("user_id");
    window.location.href = "login.html";
}
