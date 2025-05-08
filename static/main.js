document.addEventListener("DOMContentLoaded", () => {
    const plateOutputField = document.getElementById("plate-output");
    const detectionList = document.getElementById("detection-list");
    const MAX_DISPLAY_ITEMS = 10; // Maximum number of detections to display
    let detectionHistory = [];

    // Function to update the latest detection
    function updateLatestDetection(plate) {
        if (plate && plate !== "Invalid Plate") {
            plateOutputField.textContent = plate;
            
            // Add to detection history
            const timestamp = new Date().toLocaleTimeString();
            detectionHistory.unshift({ plate, timestamp });
            
            // Keep only the last MAX_DISPLAY_ITEMS
            if (detectionHistory.length > MAX_DISPLAY_ITEMS) {
                detectionHistory.pop();
            }
            
            // Update the detection list
            updateDetectionList();
        }
    }

    // Function to update the detection list
    function updateDetectionList() {
        detectionList.innerHTML = detectionHistory.map(item => 
            `<li>${item.plate} - ${item.timestamp}</li>`
        ).join('');
    }

    // Function to fetch the latest plate
    function fetchLatestPlate() {
        fetch("/get_latest_plate")
            .then(response => response.json())
            .then(data => {
                if (data.formatted_plate) {
                    updateLatestDetection(data.formatted_plate);
                }
            })
            .catch(error => console.error("Error fetching latest plate:", error));
    }

    // Fetch latest plate every 5 seconds
    setInterval(fetchLatestPlate, 5000);
});

window.onload = function() {
    // Hide the loading screen after the page loads
    document.getElementById('loading-screen').style.display = 'none';
};