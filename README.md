# SQLite Code Gen

A little script that generates C code for SQLite3 from .SQL file. Most of the C code writing used in SQLite3 application gets repetitive. 

Consider example below. Suppose the following SQL needs to be coded for SQLite3 in C:

```
.open test_mem_2025_06_05.db
PRAGMA journal_mode=WAL;
DROP TABLE IF EXISTS sample_table;
CREATE TABLE sample_table (id INTEGER PRIMARY KEY, name TEXT, age INTEGER);
INSERT INTO sample_table (name, age) VALUES ('Alice', 25);
Select name, age from sample_table;
Select 'Starting a transaction!';
begin transaction;
update sample_table set age = 90;
Select 'Read in transaction';
Select name, age from sample_table;
rollback;
Select 'Rollback transaction result:';
Select name, age from sample_table;
```

This will usually involve a lot of hand copy-pasted C code. To automatically generate C code for it, first augment the "select" queries like below. The augment is required for proper arguments in printf.

```
.open test_mem_2025_06_05.db
PRAGMA journal_mode=WAL;
DROP TABLE IF EXISTS sample_table;
CREATE TABLE sample_table (id INTEGER PRIMARY KEY, name TEXT, age INTEGER);
INSERT INTO sample_table (name, age) VALUES ('Alice', 25);
-- .SQL2C_select (text, 0, name), (int, 1, age)
Select name, age from sample_table;
-- .SQL2C_select (text, 0, msg)
Select 'Starting a transaction!';
begin transaction;
update sample_table set age = 90;
-- .SQL2C_select (text, 0, msg)
Select 'Read in transaction';
-- .SQL2C_select (text, 0, name), (int, 1, age)
Select name, age from sample_table;
rollback;
-- .SQL2C_select (text, 0, msg)
Select 'Rollback transaction result:';
-- .SQL2C_select (text, 0, name), (int, 1, age)
Select name, age from sample_table;
```

Then, invoke the script (with an optional flag of `-f` to perform in-place `clang-format`)
```
python3 -m sqlite_code_gen -i <input.sql> -o <output.c>
```

The resulting output is:

```

#include "sqlite3.h"
#include <stdio.h>
#include <stdlib.h>

void exit_if_not_ok(int rc, char *zErrMsg, int correct_code) {
  if (rc != correct_code) {
    printf("Error msg: %s\n", zErrMsg);
    exit(rc);
  }
}

sqlite3 *db;
char *errMsg;
sqlite3_stmt *stmt;
int rc;
int main() {
  rc = sqlite3_open("test_mem_2025_06_05.db", &db);
  exit_if_not_ok(rc, errMsg, SQLITE_OK);

  rc = sqlite3_exec(db, "PRAGMA journal_mode=WAL;", NULL, NULL, &errMsg);
  exit_if_not_ok(rc, errMsg, SQLITE_OK);

  rc = sqlite3_exec(db, "DROP TABLE IF EXISTS sample_table;", NULL, NULL,
                    &errMsg);
  exit_if_not_ok(rc, errMsg, SQLITE_OK);

  rc = sqlite3_exec(db,
                    "CREATE TABLE sample_table (id INTEGER PRIMARY KEY, name "
                    "TEXT, age INTEGER);",
                    NULL, NULL, &errMsg);
  exit_if_not_ok(rc, errMsg, SQLITE_OK);

  rc = sqlite3_exec(
      db, "INSERT INTO sample_table (name, age) VALUES ('Alice', 25);", NULL,
      NULL, &errMsg);
  exit_if_not_ok(rc, errMsg, SQLITE_OK);

  rc = sqlite3_prepare_v2(db, "Select name, age from sample_table;", -1, &stmt,
                          NULL);
  exit_if_not_ok(rc, errMsg, SQLITE_OK);

  while ((rc = sqlite3_step(stmt)) == SQLITE_ROW) {
    printf("name: %s, age: %d\n", sqlite3_column_text(stmt, 0),
           sqlite3_column_int(stmt, 1));
  }
  sqlite3_finalize(stmt);

  exit_if_not_ok(rc, errMsg, SQLITE_DONE);

  rc = sqlite3_prepare_v2(db, "Select 'Starting a transaction!';", -1, &stmt,
                          NULL);
  exit_if_not_ok(rc, errMsg, SQLITE_OK);

  while ((rc = sqlite3_step(stmt)) == SQLITE_ROW) {
    printf("msg: %s\n", sqlite3_column_text(stmt, 0));
  }
  sqlite3_finalize(stmt);

  exit_if_not_ok(rc, errMsg, SQLITE_DONE);

  rc = sqlite3_exec(db, "begin transaction;", NULL, NULL, &errMsg);
  exit_if_not_ok(rc, errMsg, SQLITE_OK);

  rc = sqlite3_exec(db, "update sample_table set age = 90;", NULL, NULL,
                    &errMsg);
  exit_if_not_ok(rc, errMsg, SQLITE_OK);

  rc = sqlite3_prepare_v2(db, "Select 'Read in transaction';", -1, &stmt, NULL);
  exit_if_not_ok(rc, errMsg, SQLITE_OK);

  while ((rc = sqlite3_step(stmt)) == SQLITE_ROW) {
    printf("msg: %s\n", sqlite3_column_text(stmt, 0));
  }
  sqlite3_finalize(stmt);

  exit_if_not_ok(rc, errMsg, SQLITE_DONE);

  rc = sqlite3_prepare_v2(db, "Select name, age from sample_table;", -1, &stmt,
                          NULL);
  exit_if_not_ok(rc, errMsg, SQLITE_OK);

  while ((rc = sqlite3_step(stmt)) == SQLITE_ROW) {
    printf("name: %s, age: %d\n", sqlite3_column_text(stmt, 0),
           sqlite3_column_int(stmt, 1));
  }
  sqlite3_finalize(stmt);

  exit_if_not_ok(rc, errMsg, SQLITE_DONE);

  rc = sqlite3_exec(db, "rollback;", NULL, NULL, &errMsg);
  exit_if_not_ok(rc, errMsg, SQLITE_OK);

  rc = sqlite3_prepare_v2(db, "Select 'Rollback transaction result:';", -1,
                          &stmt, NULL);
  exit_if_not_ok(rc, errMsg, SQLITE_OK);

  while ((rc = sqlite3_step(stmt)) == SQLITE_ROW) {
    printf("msg: %s\n", sqlite3_column_text(stmt, 0));
  }
  sqlite3_finalize(stmt);

  exit_if_not_ok(rc, errMsg, SQLITE_DONE);

  rc = sqlite3_prepare_v2(db, "Select name, age from sample_table;", -1, &stmt,
                          NULL);
  exit_if_not_ok(rc, errMsg, SQLITE_OK);

  while ((rc = sqlite3_step(stmt)) == SQLITE_ROW) {
    printf("name: %s, age: %d\n", sqlite3_column_text(stmt, 0),
           sqlite3_column_int(stmt, 1));
  }
  sqlite3_finalize(stmt);

  exit_if_not_ok(rc, errMsg, SQLITE_DONE);
}
```

## Installation

To install, run 

```
pip install -e .
```
