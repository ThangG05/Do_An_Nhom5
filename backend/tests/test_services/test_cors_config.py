import unittest

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from src.config import Settings


class CorsConfigTests(unittest.TestCase):
    @staticmethod
    def _client(*, local_dev: bool) -> TestClient:
        config = Settings(
            _env_file=None,
            CORS_ORIGINS="http://localhost:3000",
            CORS_ALLOW_LOCAL_DEV_ORIGINS=local_dev,
        )
        app = FastAPI()
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.cors_origins,
            allow_origin_regex=config.cors_origin_regex,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        return TestClient(app)

    @staticmethod
    def _preflight(client: TestClient, origin: str):
        return client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,x-hvnh-client",
            },
        )

    def test_flutter_web_random_local_port_is_allowed_in_dev(self) -> None:
        response = self._preflight(self._client(local_dev=True), "http://localhost:54321")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:54321")

    def test_arbitrary_remote_origin_stays_blocked(self) -> None:
        response = self._preflight(self._client(local_dev=True), "http://example.com:54321")
        self.assertEqual(response.status_code, 400)

    def test_local_random_port_is_blocked_without_dev_opt_in(self) -> None:
        response = self._preflight(self._client(local_dev=False), "http://localhost:54321")
        self.assertEqual(response.status_code, 400)
