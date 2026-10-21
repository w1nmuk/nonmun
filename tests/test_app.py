from pathlib import Path
import unittest
from unittest.mock import patch

import streamlit as st
from streamlit.testing.v1 import AppTest

from arxiv_engine import SearchError


APP = Path(__file__).resolve().parents[1] / 'app.py'
PAPER = {
    'title': 'A sample paper', 'authors': 'A researcher',
    'summary': 'A sample abstract.', 'link': 'https://arxiv.org/abs/1234.5678',
}


class AppTests(unittest.TestCase):
    def setUp(self):
        st.cache_data.clear()

    @patch('arxiv_engine.fetch_arxiv_base')
    def test_initial_render_and_blank_query_make_no_request(self, fetch):
        app = AppTest.from_file(str(APP)).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.slider), 1)
        app.text_input[0].set_value('   ')
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.warning[0].value, '검색어를 입력해 주세요.')
        fetch.assert_not_called()

    @patch('arxiv_engine.fetch_arxiv_base', return_value=[PAPER])
    def test_search_persists_and_repeated_submission_is_cached(self, fetch):
        app = AppTest.from_file(str(APP)).run()
        app.text_input[0].set_value('  graph  ')
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.expander[0].label, PAPER['title'])
        self.assertIn(PAPER['summary'], [item.value for item in app.text])
        self.assertEqual(len(app.get('download_button')), 1)
        self.assertIn('graph', app.subheader[0].value)
        fetch.assert_called_once_with('graph', max_results=5)
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.expander), 1)
        app.button[0].click().run()
        self.assertFalse(app.exception)
        fetch.assert_called_once()

    @patch('arxiv_engine.fetch_arxiv_base')
    def test_failure_clears_old_results_and_can_be_retried(self, fetch):
        fetch.side_effect = [[PAPER], SearchError('네트워크 연결 실패'), []]
        app = AppTest.from_file(str(APP)).run()
        app.text_input[0].set_value('graph')
        app.button[0].click().run()
        self.assertEqual(len(app.expander), 1)
        app.text_input[0].set_value('other')
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.error[0].value, '네트워크 연결 실패')
        self.assertEqual(len(app.expander), 0)
        self.assertEqual(len(app.get('download_button')), 0)
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.info[0].value, '검색 결과가 없습니다. 다른 검색어를 입력해 주세요.')
        self.assertEqual(fetch.call_count, 3)


if __name__ == '__main__':
    unittest.main()
