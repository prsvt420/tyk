from typing import Callable

from locust import HttpUser, constant, task
from locust.clients import ResponseContextManager
from locust.exception import ResponseError, StopUser

ORIGINAL_URL: str = "https://yandex.ru/"
REQUEST_TIMEOUT_SECONDS: float = 5.0


def _get_created_short_code(response: ResponseContextManager) -> str:
    """Validate a creation response and return its short code."""
    if response.status_code != 201:
        raise ResponseError("Expected HTTP 201.")

    try:
        response_body: object = response.json()
    except ValueError as error:
        raise ResponseError("Expected a JSON response.") from error

    if not isinstance(response_body, dict):
        raise ResponseError("Expected a JSON object.")

    short_code: object = response_body.get("short_code")
    if not isinstance(short_code, str) or not short_code:
        raise ResponseError("Expected a non-empty short code.")

    return short_code


class CreateShortLinkUser(HttpUser):
    """Measure requests handled by the short link router."""

    wait_time: Callable[..., float] = constant(0)

    @task
    def create_short_link(self) -> None:
        """Create a short link and validate the response."""
        response: ResponseContextManager = self.client.post(
            url="/api/v1/short-links",
            json={"original_url": ORIGINAL_URL, "expires_at": None},
            allow_redirects=False,
            catch_response=True,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        with response:
            _get_created_short_code(response=response)


class RedirectShortLinkUser(HttpUser):
    """Measure requests handled by the short link redirect router."""

    wait_time: Callable[..., float] = constant(0)
    _redirect_path: str

    def on_start(self) -> None:
        """Create a short link for this user's redirect requests."""
        response: ResponseContextManager = self.client.post(
            url="/api/v1/short-links",
            name="/api/v1/short-links (setup)",
            json={"original_url": ORIGINAL_URL, "expires_at": None},
            allow_redirects=False,
            catch_response=True,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        short_code: str | None = None

        with response:
            short_code = _get_created_short_code(response=response)

        if short_code is None:
            raise StopUser("Could not prepare a short link for redirects.")

        self._redirect_path: str = f"/r/{short_code}"

    @task
    def redirect_short_link(self) -> None:
        """Request the short link and validate the redirect target."""
        response: ResponseContextManager = self.client.get(
            url=self._redirect_path,
            name="/r/{short_code}",
            allow_redirects=False,
            catch_response=True,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        with response:
            if response.status_code != 307:
                raise ResponseError("Expected HTTP 307.")
            if response.headers.get("Location") != ORIGINAL_URL:
                raise ResponseError("Unexpected redirect target.")
