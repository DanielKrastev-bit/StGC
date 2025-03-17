import scraper
import remove_events
import send_to_drive


def main():
    scraper.main()
    remove_events.main()
    send_to_drive.main()

# Run the main function
if __name__ == "__main__":
    main()