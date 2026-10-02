import json

from playwright.sync_api import sync_playwright

from automation.observation import observe_page

def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)

        try:
            context = browser.new_context()
            page = context.new_page()
            page.set_default_timeout(5000)

            page.goto("http://127.0.0.1:8000")

            while True:
                observation = observe_page(page)
                print(json.dumps(observation, indent=2))

                command = input(
                    "\nNavigate in the browser, then press Enter "
                    "to observe again. Type q to quit: "
                )

                if command.strip().lower() == "q":
                    break

        finally:
            browser.close()


if __name__ == "__main__":
    main()