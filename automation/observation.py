from playwright.sync_api import Page


def observe_page(page: Page) -> dict[str, str]:
    title = page.title()
    snapshot = page.locator("body").aria_snapshot()
    url = page.url

    return {
        "url": url,
        "title": title,
        "snapshot": snapshot,
    }