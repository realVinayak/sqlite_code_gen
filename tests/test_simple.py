from sqlite_code_gen import perform_parse
import unittest


class TestCodeGen(unittest.TestCase):

    def test_simple_code_gen(self):
        with open("tests/static/test_simple.sql") as in_sql_f:
            in_sql = in_sql_f.readlines()

        with open("tests/static/test_simple.c") as out_expected_f:
            out_expected = out_expected_f.read()

        returned = perform_parse(in_sql)
        self.assertEqual("\n".join(returned).strip(), out_expected.strip())
