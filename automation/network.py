from playwright.sync_api import BrowserContext, Error, Route

from automation.policy import PolicyViolation, check_url


def install_request_guard(context: BrowserContext) -> list[str]:
    blocked_requests: list[str] = []

    def handle_request(route: Route) -> None:
        request = route.request

        try:
            check_url(request.url)

            if request.method != "GET":
                raise PolicyViolation("Only GET requests are allowed.")

        except (PolicyViolation, ValueError) as error:
            blocked_requests.append(str(error))
            route.abort("blockedbyclient")
            return

        try:
            response = route.fetch(
                max_redirects=0,
                max_retries=0,
                timeout=5000,
            )
        except Error:
            route.abort("failed")
            return

        try:
            if 300 <= response.status < 400:
                blocked_requests.append("HTTP redirects are blocked.")
                route.abort("blockedbyclient")
                return

            route.fulfill(response=response)

        finally:
            response.dispose()

    context.route("**/*", handle_request)
    return blocked_requests