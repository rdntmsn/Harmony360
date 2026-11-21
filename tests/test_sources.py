import io
import unittest
from urllib.error import HTTPError, URLError

from harmony360_orchestration.sources import MAX_BYTES, OfficialGitHubClient, SourceUnavailable


class Response(io.BytesIO):
    url = "https://api.github.com/"


class Opener:
    def __init__(self, values):
        self.values = iter(values)

    def open(self, request, timeout):
        value = next(self.values)
        if isinstance(value, BaseException):
            raise value
        return Response(value)


class SourceTests(unittest.TestCase):
    def client(self, values):
        client = OfficialGitHubClient(token="")
        client.opener = Opener(values)
        return client

    def test_empty_advisory_list_is_a_successful_fetch(self):
        self.assertEqual(self.client([b"[]", b"[]"]).fetch().advisories, ())

    def test_advisory_permission_failure_is_not_empty(self):
        error = HTTPError("https://api.github.com", 403, "secret-body", {}, None)
        with self.assertRaisesRegex(SourceUnavailable, "HTTP 403"):
            self.client([b"[]", error]).fetch()

    def test_rejects_duplicate_keys_nonfinite_and_wrong_shape(self):
        for data in (b'{"a":1,"a":2}', b'[NaN]', b'[1e999]', b'{}', b'[1]'):
            with self.subTest(data=data), self.assertRaises(SourceUnavailable):
                self.client([data]).fetch()

    def test_size_limit_and_network_errors_are_explicit(self):
        for value in (b" " * (MAX_BYTES + 1), URLError("connection failed")):
            with self.assertRaises(SourceUnavailable):
                self.client([value]).fetch()

    def test_pagination_reads_next_page(self):
        row = b'{"id":1}'
        page = b"[" + b",".join([row]*100) + b"]"
        client = self.client([page, b'[{"id":2}]', b"[]"])
        self.assertEqual(len(client.fetch().releases), 101)


if __name__ == "__main__":
    unittest.main()

