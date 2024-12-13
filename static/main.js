document.addEventListener("DOMContentLoaded", () => {
    const plateOutputField = document.getElementById("plate-output");
    const approveButton = document.getElementById("approve-button");
    const editButton = document.getElementById("edit-button");
    const searchResultDiv = document.getElementById("search-result");

    // Allow editing the detected license plate
    editButton.addEventListener("click", () => {
        plateOutputField.removeAttribute("readonly");
        plateOutputField.focus();
    });

    // Approve and search the license plate
    approveButton.addEventListener("click", () => {
        const plateValue = plateOutputField.value.trim();
        if (!plateValue) {
            alert("License plate field is empty.");
            return;
        }
    
        // Show a loading message
        searchResultDiv.innerHTML = `<p class="loading">Searching...</p>`;
    
        // Search for license plate details in the database
        fetch("/search", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ plate_output: plateValue }),
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    searchResultDiv.innerHTML = `<p class="error">${data.error}</p>`;
                } else {
                    searchResultDiv.innerHTML = `
                        <p><strong>نام:</strong> ${data.name}</p>
                        <p><strong>نام خانوادگی:</strong> ${data.name2}</p>
                        <p><strong>کد ملی:</strong> ${data.national_code}</p>
                    `;
                }
            })
            .catch(error => {
                console.error("Error fetching search result:", error);
                searchResultDiv.innerHTML = `<p class="error">An error occurred. Please try again.</p>`;
            });
    });

    // Example: Simulate a license plate detection update (to be replaced with live updates)
    function updatePlateOutput(plate) {
        plateOutputField.value = plate;
        plateOutputField.setAttribute("readonly", "true");
    }

    // Simulated example; replace with real-time detection logic
    setInterval(() => {
        updatePlateOutput("REDP"); // Example detected plate
    }, 20000); // Updates every 5 seconds
});


window.onload = function() {
    // Hide the loading screen after the page loads
    document.getElementById('loading-screen').style.display = 'none';
  };  

  function fetchLatestPlate() {
    fetch("/get_latest_plate")
        .then(response => response.json())
        .then(data => {
            const plateOutputField = document.getElementById("plate-output");
            if (data.formatted_plate && data.formatted_plate !== "Invalid Plate") {
                plateOutputField.value = data.formatted_plate;
                plateOutputField.setAttribute("readonly", "true"); // فیلد فقط خواندنی شود
            }
        })
        .catch(error => console.error("Error fetching latest plate:", error));
}


setInterval(fetchLatestPlate, 5000);
