document.addEventListener("DOMContentLoaded", () => {
    const plateOutputField = document.getElementById("plate-output");
    const detectionList = document.getElementById("detection-list");
    const MAX_DISPLAY_ITEMS = 10; // Maximum number of detections to display
    let detectionHistory = [];

    // Tab switching functionality
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and panes
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));

            // Add active class to clicked button and corresponding pane
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });

    // Form submission handlers
    const rtspForm = document.getElementById('rtsp-form');
    const imageForm = document.getElementById('image-form');
    const videoForm = document.getElementById('video-form');

    rtspForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(rtspForm);
        try {
            const response = await fetch('/set_rtsp', {
                method: 'POST',
                body: formData
            });
            if (response.ok) {
                // Refresh video feed
                document.getElementById('video-feed').src = '/video_feed?' + new Date().getTime();
            }
        } catch (error) {
            console.error('Error setting RTSP URL:', error);
        }
    });

    imageForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(imageForm);
        try {
            const response = await fetch('/upload_image', {
                method: 'POST',
                body: formData
            });
            if (response.ok) {
                // Refresh video feed
                document.getElementById('video-feed').src = '/video_feed?' + new Date().getTime();
            }
        } catch (error) {
            console.error('Error uploading image:', error);
        }
    });

    videoForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(videoForm);
        try {
            const response = await fetch('/upload_video', {
                method: 'POST',
                body: formData
            });
            if (response.ok) {
                // Refresh video feed
                document.getElementById('video-feed').src = '/video_feed?' + new Date().getTime();
            }
        } catch (error) {
            console.error('Error uploading video:', error);
        }
    });

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