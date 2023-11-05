import unittest
from datetime import datetime
from notepy.notes import Note


class TestNote(unittest.TestCase):
    def setUp(self):
        self.title = "The quick brown fox jumps over the lazy dog"
        self.author = "Anonymous"
        self.date = "2023-10-19T19:30:01"
        self.zk_id = '3e804e0062ecdba15ee1dd655385c8b8'
        self.tags = "#test,#unittest,#zettelkasten"
        self.metadata = {'title': self.title,
                         'author': self.author,
                         'date': self.date,
                         'zk_id': self.zk_id,
                         'tags': self.tags}
        self.frontmatter = f"---\ntitle: {self.title}\nauthor: {self.author}\ndate: {self.date}\nzk_id: {self.zk_id}\ntags: {self.tags}\n---"

    def test_generate_frontmatter(self):
        """
        Test whether the generated frontmatter is
        correct given a set metadata
        """
        generated_frontmatter = Note._generate_frontmatter(self.metadata)
        self.assertEqual(generated_frontmatter, self.frontmatter)


if __name__ == "__main__":
    unittest.main()
