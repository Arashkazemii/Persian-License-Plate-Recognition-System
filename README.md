# License Plate Recognition and Persian OCR Application

## Overview

This repository showcases a robust **License Plate Recognition** and **OCR (Optical Character Recognition)** system tailored for Persian license plates. The project combines advanced deep learning techniques and a user-friendly web interface to detect and recognize license plates captured from security checkpoints or scale cameras.

---

## Features

- **License Plate Detection:**
  - Utilizes a custom-trained YOLOv5 model for accurate plate detection.
  - Tested on a diverse dataset for robust performance.

- **Persian License Plate OCR:**
  - Custom-trained OCR model specifically for Persian characters and numbers.
  - Handles Persian character mapping to ensure correct outputs.

- **Web Application:**
  - Built using Flask, providing an intuitive interface for users.
  - Includes login/logout functionality and database search integration.

- **Database Integration:**
  - Connects to an Oracle database to retrieve information based on detected license plates.

- **Dockerized Environment:**
  - Simplifies deployment with Docker and Docker Compose.

---

## Project Structure

```
version0.2/
├── models/
│   ├── ocr.pt                  # Trained OCR model
│   ├── plate_detector.pt       # Trained plate detection model
├── static/
│   ├── login.css               # Styling for login page
│   ├── main.css                # Styling for main page
│   ├── main.js                 # Client-side JavaScript
├── templates/
│   ├── login.html              # Login page template
│   ├── main.html               # Main page template
├── .env                        # Environment variables (not included for security)
├── app.py                      # Flask application
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Docker container setup
├── requirements.txt            # Python dependencies
```

---

## How It Works

### Workflow:
1. **License Plate Detection:**
   - Input images or video streams are processed using the YOLOv5 plate detection model.
   - Detected license plate regions are cropped for OCR.

2. **OCR for Persian Plates:**
   - The OCR model recognizes Persian characters and numbers from the cropped images.
   - Outputs are formatted based on Persian license plate structure.

3. **Database Search:**
   - Recognized license plate numbers are searched in an Oracle database to retrieve associated details.

### Character Mapping:
The OCR system incorporates a mapping layer to convert model outputs into Persian characters and digits accurately.

---

## Installation and Setup

### Prerequisites:
- Python 3.8+
- Docker and Docker Compose
- Oracle Database (for the optional database search feature)

### Steps:
1. **Clone the repository:**
   ```bash
   git clone https://github.com/Arashkazemii/License-Plate-Recognition-and-Persian-OCR-Application.git
   cd License-Plate-Recognition-and-Persian-OCR-Application
   ```

2. **Set up environment variables:**
   - Create a `.env` file based on the following template:
     ```env
     SECRET_KEY=your_secret_key
     DB_USER=your_db_username
     DB_PASSWORD=your_db_password
     DB_DSN=your_db_dsn
     USER_1_USERNAME=admin
     USER_1_PASSWORD=password
     USER_2_USERNAME=security
     USER_2_PASSWORD=admin
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Docker Setup (Optional):**
   - Build and run using Docker Compose:
     ```bash
     docker-compose up --build
     ```

---

## Usage

1. **Access the Application:**
   - Visit `http://localhost:5000` in your web browser.

2. **Login:**
   - Use the credentials defined in the `.env` file to log in.

3. **Stream Video Feed:**
   - The application processes the input RTSP stream and displays detected license plates with OCR results in real-time.

4. **Search Database:**
   - Input a detected license plate to query the Oracle database for related information.

---

## Screenshots

### Login Page:
![alt text](images/login-page.png)

### Main Interface:
![alt text](images/main-page.png)

---

## Limitations
- The models included are optimized for Persian license plates only.
- Real-time performance depends on the hardware and input stream quality.

---

## Disclaimer
The models, code, and assets in this repository are provided **for demonstration purposes only**. Any use outside of viewing this repository requires explicit written permission from the author.

---

## Contact
For inquiries or collaborations, feel free to contact me:
- **Email:** kazemiarash09@gmail.com
- **GitHub:** [GitHub profile](https://github.com/Arashkazemii)