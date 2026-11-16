"""Checks for notion_sync.py. Run with: python3 -m unittest discover .github/scripts"""

import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

import notion_sync

MON = date(2026, 11, 16)
TUE = date(2026, 11, 17)


class Decide(unittest.TestCase):
    def test_nothing_submitted_changes_nothing(self):
        self.assertEqual(notion_sync.decide("To do", None, None), {})

    def test_first_submission_solves_the_row(self):
        expected = {"Status": "Solved", "Last attempt": MON}
        self.assertEqual(notion_sync.decide("To do", None, MON), expected)

    def test_a_submission_already_recorded_changes_nothing(self):
        self.assertEqual(notion_sync.decide("Solved", MON, MON), {})
        self.assertEqual(notion_sync.decide("Redo in 1 day", MON, MON), {})

    def test_a_redo_on_time_moves_one_step(self):
        expected = {"Status": "Redo in 1 week", "Last attempt": TUE}
        self.assertEqual(notion_sync.decide("Redo in 1 day", MON, TUE), expected)
        expected = {"Status": "Redo in 3 weeks", "Last attempt": date(2026, 11, 23)}
        self.assertEqual(notion_sync.decide("Redo in 1 week", MON, date(2026, 11, 23)), expected)
        expected = {"Status": "Solved", "Last attempt": date(2026, 12, 7)}
        self.assertEqual(notion_sync.decide("Redo in 3 weeks", MON, date(2026, 12, 7)), expected)

    def test_a_redo_before_it_is_due_is_left_alone(self):
        self.assertEqual(notion_sync.decide("Redo in 1 week", MON, date(2026, 11, 22)), {})
        self.assertEqual(notion_sync.decide("Redo in 3 weeks", MON, date(2026, 12, 6)), {})

    def test_marked_for_redo_before_the_first_attempt_was_seen(self):
        self.assertEqual(notion_sync.decide("Redo in 1 day", None, MON), {"Last attempt": MON})

    def test_solving_again_only_moves_the_date(self):
        self.assertEqual(notion_sync.decide("Solved", MON, TUE), {"Last attempt": TUE})


class ProblemIn(unittest.TestCase):
    def test_takes_the_name_from_a_neetcode_address(self):
        link = "https://neetcode.io/problems/two-integer-sum/question?list=blind75"
        self.assertEqual(notion_sync.problem_in(link), "two-integer-sum")
        self.assertEqual(
            notion_sync.problem_in("https://neetcode.io/problems/sort-colors"), "sort-colors"
        )

    def test_another_site_or_no_link_gives_nothing(self):
        link = "https://leetcode.com/problems/delete-node-in-a-linked-list/"
        self.assertEqual(notion_sync.problem_in(link), "")
        self.assertEqual(notion_sync.problem_in(""), "")
        self.assertEqual(notion_sync.problem_in(None), "")


class Submitted(unittest.TestCase):
    """Against a real, throwaway git repository laid out the way NeetCode lays this one out."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.repo = Path(self.folder.name)
        self.git("init", "--quiet", "--initial-branch=main")
        self.commit("README.md", "2026-11-16T07:40:53+00:00")

    def tearDown(self):
        self.folder.cleanup()

    def git(self, *words, when=None):
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com")
        env.update(GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")
        if when:
            env.update(GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
        subprocess.run(["git", "-C", str(self.repo), *words], check=True, env=env)

    def commit(self, path, when, remove=False):
        file = self.repo / path
        if remove:
            file.unlink()
        else:
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(when)
        self.git("add", "--all")
        self.git("commit", "--quiet", "--message", path, when=when)

    def test_the_newest_submission_of_each_problem(self):
        topic = "Data Structures & Algorithms"
        self.commit(f"{topic}/two-integer-sum/submission-0.py", "2026-11-16T10:00:00+00:00")
        self.commit(f"{topic}/is-anagram/submission-0.py", "2026-11-16T11:00:00+00:00")
        self.commit(f"{topic}/two-integer-sum/submission-1.py", "2026-11-18T09:00:00+00:00")
        expected = {"two-integer-sum": date(2026, 11, 18), "is-anagram": MON}
        self.assertEqual(notion_sync.submitted(str(self.repo)), expected)

    def test_the_day_is_the_day_in_israel(self):
        path = "Data Structures & Algorithms/is-anagram/submission-0.py"
        self.commit(path, "2026-11-16T22:30:00+00:00")  # half past midnight in Israel
        self.assertEqual(notion_sync.submitted(str(self.repo)), {"is-anagram": TUE})

    def test_a_removed_submission_and_other_files_do_not_count(self):
        path = "Data Structures & Algorithms/is-anagram/submission-0.py"
        self.commit(path, "2026-11-16T10:00:00+00:00")
        self.commit(path, "2026-11-20T10:00:00+00:00", remove=True)
        self.commit(".github/scripts/notion_sync.py", "2026-11-21T10:00:00+00:00")
        self.assertEqual(notion_sync.submitted(str(self.repo)), {"is-anagram": MON})


class Sync(unittest.TestCase):
    """The whole run, with Notion replaced by a list of rows."""

    def setUp(self):
        self.written = []
        self.pages = [
            page(
                "a", "Two Sum", "https://neetcode.io/problems/two-integer-sum/question?list=blind75"
            ),
            page(
                "b",
                "Valid Anagram",
                "https://neetcode.io/problems/is-anagram",
                "Redo in 1 day",
                "2026-11-16",
            ),
            page("c", "Delete Node", "https://leetcode.com/problems/delete-node-in-a-linked-list/"),
            page("d", "Implement memcpy", None),
        ]
        self.real_call = notion_sync.call
        notion_sync.call = self.call

    def tearDown(self):
        notion_sync.call = self.real_call

    def call(self, method, path, body=None):
        if method == "POST":
            return {"results": self.pages, "has_more": False}
        self.written.append((path, body))
        return {}

    def test_records_what_is_new_and_names_what_is_not_in_the_plan(self):
        days = {"two-integer-sum": MON, "is-anagram": TUE, "binary-search": MON}
        lines = notion_sync.sync(days)
        self.assertEqual(
            lines,
            [
                "Two Sum: To do -> Solved, last attempt 2026-11-16",
                "Valid Anagram: Redo in 1 day -> Redo in 1 week, last attempt 2026-11-17",
                "binary-search: not in the plan, left alone",
            ],
        )
        first = {"Status": {"status": {"name": "Solved"}}}
        first["Last attempt"] = {"date": {"start": "2026-11-16"}}
        self.assertEqual(self.written[0], ("/pages/a", {"properties": first}))
        self.assertEqual(len(self.written), 2)

    def test_a_dry_run_writes_nothing(self):
        lines = notion_sync.sync({"two-integer-sum": MON}, dry_run=True)
        self.assertEqual(lines, ["Two Sum: To do -> Solved, last attempt 2026-11-16"])
        self.assertEqual(self.written, [])


def page(page_id, problem, link, status="To do", last=None):
    return {
        "id": page_id,
        "properties": {
            "Problem": {"title": [{"plain_text": problem}]},
            "Link": {"url": link},
            "Status": {"status": {"name": status}},
            "Last attempt": {"date": {"start": last} if last else None},
        },
    }


if __name__ == "__main__":
    unittest.main()
