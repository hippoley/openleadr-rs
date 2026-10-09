import pathlib
import tempfile
import unittest

from verify_junit import audit

GOOD = """<testsuites><testsuite>
<testcase name="external_vtn_can_list_programs_without_local_database" time="0.01"/>
<testcase name="external_vtn_can_list_events_without_local_database" time="0.01"/>
</testsuite></testsuites>"""

class JUnitOracleTests(unittest.TestCase):
    def check(self, xml):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "junit.xml"
            path.write_text(xml, encoding="utf-8")
            return audit(path)

    def test_good(self):
        result = self.check(GOOD)
        self.assertEqual(result["case_count"], 2)
        self.assertFalse(result["verified_closed"])

    def test_missing_case_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            self.check(GOOD.replace('<testcase name="external_vtn_can_list_events_without_local_database" time="0.01"/>', ""))

    def test_skipped_is_not_a_pass(self):
        with self.assertRaisesRegex(ValueError, "skipped"):
            self.check(GOOD.replace('time="0.01"/>', 'time="0.01"><skipped/></testcase>', 1))

    def test_failed_is_not_a_pass(self):
        with self.assertRaisesRegex(ValueError, "failure"):
            self.check(GOOD.replace('time="0.01"/>', 'time="0.01"><failure/></testcase>', 1))

    def test_duplicate_is_not_a_pass(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.check(GOOD.replace("</testsuite>", '<testcase name="external_vtn_can_list_programs_without_local_database" time="0.01"/></testsuite>'))

if __name__ == "__main__":
    unittest.main()
