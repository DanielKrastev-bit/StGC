# StGC - Shkolo Schedule to Google Calendar

StGC is a Python-based tool that automates scraping class schedules from Shkolo.bg and storing them in Google Calendar as events. The project now uses Firefox (GeckoDriver) for web automation.

## Features

- **Automated Login:** Logs into Shkolo.bg using your credentials.
- **Schedule Scraping:** Fetches the weekly schedule for a specific period.
- **Headless Mode:** Runs the browser in headless mode for seamless automation.
- **Google Calendar Integration:** Saves schedules as calendar events.
- **Class Grouping:** Consecutive classes with continuous time intervals are merged into a single event.
- **Vacation Event Scheduling:** Automatically schedules vacation events (using gray color) on workdays between the last school day and the next valid date.
- **Error Handling:** Safely manages errors and ensures resources are cleaned up after execution.

## Prerequisites

- **Python 3.x**
- **Selenium:** Install with `pip install selenium`
- **Firefox:** Make sure Firefox is installed on your system.
- **GeckoDriver:** [Download GeckoDriver](https://github.com/mozilla/geckodriver/releases) and ensure it’s in your system's `PATH` (or update the path in your script).
- **Google API Setup:** Configure the Google Calendar API. You'll need a `credentials.json` file (used for authentication) generated via the Google API Console.

## Setup

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/DanielKrastev-bit/StGC.git
   cd StGC
   ```

2. **Create a Virtual Environment**

   ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
3. **Then install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```
4. **Install GeckoDriver::**
Download and place the GeckoDriver executable in a directory included in your system's PATH or update the driver path in your script accordingly.

## Usage

1. **Adjust Week Variable:**
    Update the week variable in the script (or implement an automatic calculation) to match the current week.

2. **Run the Script:**
    ```bash
    python shkolo_scraper.py
    ```
    Schedule Output:
    The schedule for the specified week is saved as events in Google Calendar. Vacation blocks (if detected) are automatically scheduled on the appropriate workdays.