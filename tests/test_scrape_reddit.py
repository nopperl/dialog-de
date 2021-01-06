import unittest

from reddit.scrape_reddit import is_ama_submission, is_proper_comment, has_proper_text


class TestScrapeReddit(unittest.TestCase):
    def test_is_ama_submission(self):
        ama_flair = "ama"
        sub = {"amaFlairs": ama_flair}
        submission = {"link_flair_text": ama_flair}
        self.assertTrue(is_ama_submission(submission, sub))
        submission = {"link_flair_text": "somethingelse", "title": "[AMA] i am a test"}
        self.assertFalse(is_ama_submission(submission, sub))
        sub = {"allowAMAInOtherFlairs": True}
        self.assertTrue(is_ama_submission(submission, sub))
        submission["title"] = "AMA - i am a test"
        self.assertTrue(is_ama_submission(submission, sub))
        submission["title"] = "i am a test - AMA"
        self.assertTrue(is_ama_submission(submission, sub))

    def test_is_proper_comment(self):
        comment = {
            "data": {
                "author": "test",
                "body": "text",
                "depth": 4,
                "score": 10,
                "replies": {"data": {"children": []}},
            }
        }
        self.assertTrue(is_proper_comment(comment))
        comment["data"]["depth"] = 0
        self.assertFalse(is_proper_comment(comment))
        comment["data"]["replies"] = {"data": {"children": [{"data": None}]}}
        self.assertTrue(is_proper_comment(comment))

    def test_has_proper_text(self):
        post = {"text": "This is a [link](http://example.com)", "text_html": 'This is a &lt;a href=\"http://example.com\"&gt;link&lt;a&gt;'}
        self.assertFalse(has_proper_text(post["text"], post["text_html"]))
        self.assertFalse(has_proper_text(""))
        self.assertFalse(has_proper_text("[deleted]"))
        self.assertFalse(has_proper_text("RAAAAAGE"))


if __name__ == "__main__":
    unittest.main()
