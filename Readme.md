# Event QR Code Manager

A PyQt5 desktop application for managing event participants using QR codes.  
Load participant data from a CSV file, generate unique QR codes for each participant, scan QR codes using a webcam or a mobile phone camera, and track attendance in real-time.

---

## Features

- Load participant details from a CSV file (must include columns: `Name`, `Passport Number`, `Phone Number`, `Email`)
- Automatically generate unique QR codes for each participant
- Save QR codes as PNG images in a dedicated folder (`qrcodes/`)
- Scan QR codes live via a webcam to mark participants as scanned
- Search participants by Passport Number and view their scan status
- Export updated participant list including QR code filenames and scan status
- Reset scan counts to start fresh for new events
- Supports multiple camera devices connected to your computer
- Stylish UI with custom fonts and background image

---

## Installation

1. Clone this repository or download the source code.  
2. Make sure you have Python 3.7+ installed.  
3. Install dependencies using pip:

```bash
pip install -r requirements.txt
````

4. Place `Orbitron-Regular.ttf` font file and optionally `background.jpg` and `logo.png` in the same directory as the script for better UI styling.

---

## Usage

1. Run the application:

```bash
python gatekeeper.py
```

2. Click **Load CSV** and select your participants CSV file.
   The CSV must contain the following columns:
   `Name`, `Passport Number`, `Phone Number`, `Email`.

3. Click **Generate QR Codes** to create QR images for each participant. These are saved in the `qrcodes/` folder.

4. Connect your webcam or use a mobile phone camera to scan QR codes:

   * Select the desired camera from the dropdown.
   * Click **Start Scan** to begin scanning QR codes live.
   * The app will highlight and mark scanned participants, updating their status.
   * Click **Stop Scan** to stop camera input.

5. You can search for participants by Passport Number using the search box.

6. Export the participant list with scan status and QR code filenames by clicking **Export List w/ QR & Scan**.

7. Reset scan counts with **Reset Count** if needed.

---

## Using a Mobile Phone as a Scanner

You can also use your mobile phone camera as a webcam to scan QR codes with this application by using **DroidCam**:

* Install **DroidCam Client** on your computer:
  [https://www.dev47apps.com/](https://www.dev47apps.com/)

* Install **DroidCam** app on your mobile phone (Android or iOS).

* Connect your phone and computer to the same Wi-Fi network or via USB.

* Launch DroidCam on both devices and connect your phone camera as a webcam on your PC.

* Select **DroidCam** as the camera in the app's camera selector dropdown.

This way, you can scan QR codes using your phone’s camera seamlessly.

---

## CSV File Format Example

| Name       | Passport Number | Phone Number | Email                                       |
| ---------- | --------------- | ------------ | ------------------------------------------- |
| John Smith | A1234567        | 555-1234     | [john@example.com](mailto:john@example.com) |
| Jane Doe   | B9876543        | 555-5678     | [jane@example.com](mailto:jane@example.com) |

---

## Requirements

* Python 3.7 or higher
* Packages (install via `pip install -r requirements.txt`):

  * PyQt5
  * pandas
  * qrcode
  * opencv-python
  * pyzbar

`
