# FYPDP 2026: People's Choice Award

A web-based voting application developed for the FYPDP 2026 event to manage the "People's Choice Award". This system allows attendees to vote for their favorite studies and allows administrators to manage the polling status in real-time.

## Features

- **Public Voting:** Users can select their preferred study from various categories via a user-friendly form.
- **Live Results:** Real-time visualization of vote counts and percentages for each study.
- **Admin Dashboard:**
  - Toggle voting status (Start/Stop Voting).
  - Reset poll data.
  - Secure login protection.
- **Responsive Design:** Built with a custom base style for consistent viewing across devices.

## Project Structure

- **templates/**: Jinja2 HTML templates.
  - `base.html`: Landing page entry point.
  - `poll.html`: The main voting form where users select studies.
  - `results.html`: Displays current vote standings with progress bars.
  - `admin_login.html`: Login page for administrators.
  - `admin_dashboard.html`: Control panel for poll management (Open/Close poll, Reset DB).
- **static/**: Static assets.
  - `css/base_style.css`: Application styling.
  - `images/`: Contains project logos (e.g., `FYPDP_Logo.png`).

## Technologies Used

- **Backend:** Python (Flask)
- **Frontend:** HTML5, CSS3, JavaScript
- **Templating:** Jinja2

## Setup and Usage

1. **Prerequisites:**
   - Python 3.x installed.
   - Flask installed (`pip install flask`).

2. **Running the Application:**
   Run your main Flask entry file (e.g., `app.py`):
   ```bash
   python app.py
   ```

*Note:* This project is to be strictly used for the FYPDP 2026 event. Unauthorized use is strictly prohibited.