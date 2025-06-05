
#include <stdio.h>
#include <stdlib.h>
#include "sqlite3.h"


void exit_if_not_ok(int rc, char *zErrMsg, int correct_code){
    if (rc != correct_code){
        printf("Error msg: %s\n", zErrMsg);
        exit(rc);
    }
}

sqlite3 *db;
char *errMsg;
sqlite3_stmt *stmt;
int rc;
int main() {
rc	=sqlite3_open("test_mem_2025_06_05.db", &db);
exit_if_not_ok(rc, errMsg, SQLITE_OK);


rc	=sqlite3_exec(db, "PRAGMA journal_mode=WAL;", NULL, NULL, &errMsg);
exit_if_not_ok(rc, errMsg, SQLITE_OK);


rc	=sqlite3_exec(db, "DROP TABLE IF EXISTS sample_table;", NULL, NULL, &errMsg);
exit_if_not_ok(rc, errMsg, SQLITE_OK);


rc	=sqlite3_exec(db, "CREATE TABLE sample_table (id INTEGER PRIMARY KEY, name TEXT, age INTEGER);", NULL, NULL, &errMsg);
exit_if_not_ok(rc, errMsg, SQLITE_OK);


rc	=sqlite3_exec(db, "INSERT INTO sample_table (name, age) VALUES ('Alice', 25);", NULL, NULL, &errMsg);
exit_if_not_ok(rc, errMsg, SQLITE_OK);


rc	=sqlite3_prepare_v2(db, "Select name, age from sample_table;", -1, &stmt, NULL);
exit_if_not_ok(rc, errMsg, SQLITE_OK);


while ( (rc	=sqlite3_step(stmt)) == SQLITE_ROW ) {
printf("name: %s, age: %d\n", sqlite3_column_text(stmt, 0),sqlite3_column_int(stmt, 1));
}
sqlite3_finalize(stmt);


exit_if_not_ok(rc, errMsg, SQLITE_DONE);


rc	=sqlite3_prepare_v2(db, "Select 'Starting a transaction!';", -1, &stmt, NULL);
exit_if_not_ok(rc, errMsg, SQLITE_OK);


while ( (rc	=sqlite3_step(stmt)) == SQLITE_ROW ) {
printf("msg: %s\n", sqlite3_column_text(stmt, 0));
}
sqlite3_finalize(stmt);


exit_if_not_ok(rc, errMsg, SQLITE_DONE);


rc	=sqlite3_exec(db, "begin transaction;", NULL, NULL, &errMsg);
exit_if_not_ok(rc, errMsg, SQLITE_OK);


rc	=sqlite3_exec(db, "update sample_table set age = 90;", NULL, NULL, &errMsg);
exit_if_not_ok(rc, errMsg, SQLITE_OK);


rc	=sqlite3_prepare_v2(db, "Select 'Read in transaction';", -1, &stmt, NULL);
exit_if_not_ok(rc, errMsg, SQLITE_OK);


while ( (rc	=sqlite3_step(stmt)) == SQLITE_ROW ) {
printf("msg: %s\n", sqlite3_column_text(stmt, 0));
}
sqlite3_finalize(stmt);


exit_if_not_ok(rc, errMsg, SQLITE_DONE);


rc	=sqlite3_prepare_v2(db, "Select name, age from sample_table;", -1, &stmt, NULL);
exit_if_not_ok(rc, errMsg, SQLITE_OK);


while ( (rc	=sqlite3_step(stmt)) == SQLITE_ROW ) {
printf("name: %s, age: %d\n", sqlite3_column_text(stmt, 0),sqlite3_column_int(stmt, 1));
}
sqlite3_finalize(stmt);


exit_if_not_ok(rc, errMsg, SQLITE_DONE);


rc	=sqlite3_exec(db, "rollback;", NULL, NULL, &errMsg);
exit_if_not_ok(rc, errMsg, SQLITE_OK);


rc	=sqlite3_prepare_v2(db, "Select 'Rollback transaction result:';", -1, &stmt, NULL);
exit_if_not_ok(rc, errMsg, SQLITE_OK);


while ( (rc	=sqlite3_step(stmt)) == SQLITE_ROW ) {
printf("msg: %s\n", sqlite3_column_text(stmt, 0));
}
sqlite3_finalize(stmt);


exit_if_not_ok(rc, errMsg, SQLITE_DONE);


rc	=sqlite3_prepare_v2(db, "Select name, age from sample_table;", -1, &stmt, NULL);
exit_if_not_ok(rc, errMsg, SQLITE_OK);


while ( (rc	=sqlite3_step(stmt)) == SQLITE_ROW ) {
printf("name: %s, age: %d\n", sqlite3_column_text(stmt, 0),sqlite3_column_int(stmt, 1));
}
sqlite3_finalize(stmt);


exit_if_not_ok(rc, errMsg, SQLITE_DONE);


}