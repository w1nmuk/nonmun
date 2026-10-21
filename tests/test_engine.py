import io
import unittest
import urllib.error
import urllib.parse
from unittest.mock import patch

from arxiv_engine import SearchError, create_markdown_content, fetch_arxiv_base


FEED = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry>
<id>http://arxiv.org/abs/1706.03762v1</id>
<title>Attention Is\n All You Need</title>
<summary>A paper\n about attention.</summary>
<author><name>A. Researcher</name></author>
<author><name>B. Researcher</name></author>
</entry></feed>'''
PAPER = {
    'title': 'Attention Is All You Need',
    'authors': 'A. Researcher, B. Researcher',
    'summary': 'A paper about attention.',
    'link': 'https://arxiv.org/abs/1706.03762v1',
}


class EngineTests(unittest.TestCase):
    @patch('arxiv_engine.urllib.request.urlopen')
    def test_search_encodes_query_uses_https_timeout_and_parses_feed(self, open_url):
        open_url.return_value = io.BytesIO(FEED)
        self.assertEqual(fetch_arxiv_base('  graph & 한국어  ', 1), [PAPER])
        request = open_url.call_args.args[0]
        self.assertTrue(request.full_url.startswith('https://export.arxiv.org/api/query?'))
        params = urllib.parse.parse_qs(urllib.parse.urlsplit(request.full_url).query)
        self.assertEqual(params['search_query'], ['all:graph & 한국어'])
        self.assertEqual(params['max_results'], ['1'])
        self.assertEqual(params['sortBy'], ['relevance'])
        self.assertEqual(open_url.call_args.kwargs['timeout'], 15)
        self.assertTrue(open_url.return_value.closed)
        open_url.assert_called_once()

    @patch('arxiv_engine.urllib.request.urlopen')
    def test_invalid_input_makes_no_request(self, open_url):
        for query, count in [(' ', 5), ('graph', 0), ('graph', 11)]:
            with self.subTest(query=query, count=count), self.assertRaises(ValueError):
                fetch_arxiv_base(query, count)
        open_url.assert_not_called()

    @patch('arxiv_engine.urllib.request.urlopen')
    def test_empty_feed_is_a_valid_empty_result(self, open_url):
        open_url.return_value = io.BytesIO(b'<feed xmlns="http://www.w3.org/2005/Atom"/>')
        self.assertEqual(fetch_arxiv_base('no matches'), [])

    @patch('arxiv_engine.urllib.request.urlopen')
    def test_network_errors_are_not_empty_results(self, open_url):
        errors = [
            urllib.error.URLError('unreachable'), TimeoutError(),
            urllib.error.HTTPError('https://export.arxiv.org', 429, 'rate limited', {}, None),
            urllib.error.HTTPError('https://export.arxiv.org', 503, 'unavailable', {}, None),
        ]
        for error in errors:
            with self.subTest(error=type(error).__name__):
                open_url.side_effect = error
                with self.assertRaises(SearchError) as caught:
                    fetch_arxiv_base('graph')
                if isinstance(error, urllib.error.HTTPError):
                    self.assertIn('요청이 많습니다' if error.code == 429 else 'HTTP 503', str(caught.exception))

    @patch('arxiv_engine.urllib.request.urlopen')
    def test_bad_response_and_api_error_raise(self, open_url):
        responses = [
            b'not XML', b'<html/>',
            FEED.replace(b'http://arxiv.org/abs/1706.03762v1', b'http://arxiv.org/api/errors#bad_query'),
            FEED.replace(b'<title>Attention Is\n All You Need</title>', b''),
            FEED.replace(b'http://arxiv.org/abs/1706.03762v1', b'https://example.com/abs/1234'),
        ]
        for response in responses:
            with self.subTest(response=response):
                open_url.return_value = io.BytesIO(response)
                with self.assertRaises(SearchError):
                    fetch_arxiv_base('graph')

    @patch('arxiv_engine.urllib.request.urlopen')
    def test_markdown_export_is_offline_and_preserves_paper_details(self, open_url):
        result = create_markdown_content([PAPER], 'attention')
        self.assertIn("# 'attention' 관련 논문", result)
        for value in PAPER.values():
            self.assertIn(value, result)
        self.assertNotIn('번역 실패', result)
        open_url.assert_not_called()


if __name__ == '__main__':
    unittest.main()
