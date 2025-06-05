# this little script coverts the SQL code to C code.
# doing this allows easy conversion from SQL shell to something that'll compile in C.
# doing this also allows complicated unit tests.

# TODO: Improve docs.

"""
Some things it does right:
1.  Return code are checked after every exec, so breakpoints can be set at exit_if_not_ok.
2.  In the case of SELECT(), it allows pretty prints. For example, consider a table with name (int) and age (str).
    Suppose there is str "Select name, age from <table>". In the SQL file, enter something like
        -- .SQL2C_select (text, 0, name_used_in_printf), (int, 1, age_used_in_printf)
        SELECT name, age from <table>
    The generated code will correctly use sqlite3's get column functions based on the types entered.\
"""

from typing import Dict, List, NamedTuple, Optional, Tuple, Union
import re

VAR_RETURN_CODE =   "rc"
VAR_ERR_MSG     =   "errMsg"
VAR_DB          =   "db"
VAR_STMT        =   "stmt"


VAR_DECLS = [
    f"sqlite3 *{VAR_DB};",
    f"char *{VAR_ERR_MSG};",
    f"sqlite3_stmt *{VAR_STMT};",
    f"int {VAR_RETURN_CODE};"
]

READ_SPEC_TICKER_RE = r'\((text|int), (\d+), ([a-z]+)\)'

HEADERS = """
#include <stdio.h>
#include <stdlib.h>
#include "sqlite3.h"
"""

MAIN_START  = "int main() {"
MAIN_END    = "}"

OPEN_TICKER         = ".open"
COMMENT_TICKER      = "--"
READ_SPEC_TICKER    = ".SQL2C_select"
# TODO: Implement logic for using prepare ticker when I've more time.
USE_PREPARE_TICKER  = ".SQL2C_prepare"

BLANK   =   "\n"

EXIT_ON_ERROR_FUNC = """
void exit_if_not_ok(int rc, char *zErrMsg, int correct_code){
    if (rc != correct_code){
        printf("Error msg: %s\\n", zErrMsg);
        exit(rc);
    }
}
"""

EXIT_ON_ERROR_CALL  = f"exit_if_not_ok({VAR_RETURN_CODE}, {VAR_ERR_MSG}, SQLITE_OK);"
EXIT_ON_DONE_CALL   = f"exit_if_not_ok({VAR_RETURN_CODE}, {VAR_ERR_MSG}, SQLITE_DONE);"

class CDefs(NamedTuple):
    # the value can be an int or str.
    # if the value is a str, then it gets put in double quotes.
    value: Union[str, int]

    def get_pretty_value(self):
        stred = str(self.value) if isinstance(self.value, int) else ("\"" + self.value + "\"")
        return stred
    
    def prefix(self) -> Optional[str]:
        # this can be overriden.
        return "TEMP"
    
    def canonicalize(self, context: Dict[str, int]) -> List[str]:
        prefix = self.prefix()
        context[prefix] = context.get(prefix, 0) + 1
        return [f"#define {prefix}_{context[prefix]} {self.get_pretty_value()}"]

def assign(lhs: str, rhs: str) -> str:
    return f"{lhs}\t={rhs}"

class CSQLiteOpen(NamedTuple):
    value: str

    def canonicalize(self, context: Dict[str, int]) -> List[str]:
        sqlite_open = f"sqlite3_open(\"{self.value}\", &{VAR_DB});"
        return [
            assign(VAR_RETURN_CODE, sqlite_open),
            EXIT_ON_ERROR_CALL
        ]

class CSQLitePrepare(NamedTuple):
    sql_to_prepare : str

    def canonicalize(self, context: Dict[str, int]) -> List[str]:
        sqlite_prepare = f"sqlite3_prepare_v2({VAR_DB}, \"{self.sql_to_prepare}\", -1, &{VAR_STMT}, NULL);"
        return [
            assign(VAR_RETURN_CODE, sqlite_prepare),
            EXIT_ON_ERROR_CALL
        ]

class CSimpleStr(NamedTuple):
    stmts: List[str]

    def canonicalize(self, context: Dict[str, int]) -> List[str]:
        return self.stmts

class CSQLiteExec(NamedTuple):
    stmt_to_exec: str

    def canonicalize(self, context: Dict[str, int]) -> List[str]:
        sqlite_exec = f"sqlite3_exec({VAR_DB}, \"{self.stmt_to_exec}\", NULL, NULL, &{VAR_ERR_MSG});"
        return [
            assign(VAR_RETURN_CODE, sqlite_exec), 
            EXIT_ON_ERROR_CALL
        ]

# if the next line is a read operation, then this comment contains
# specs on how to parse it.
def parse_comment(lines: List[str], index: int):
    line = lines[index-1]
    cmt_index = line.index(COMMENT_TICKER)
    line = line[cmt_index+len(COMMENT_TICKER):].strip()
    if (line.startswith(READ_SPEC_TICKER)):
        return parse_read_comment_and_select(line, lines, index)
    # In this case, there is nothing to parse more, and this is just a comment.
    return [], index, []

# If we're doing reads, we follow the prepare interface.
def parse_read_comment_and_select(line: str, lines: List[str], index: int):
    comment_line = line
    sql_line = lines[index]
    # We've already parsed this statement here.
    index += 1
    prepared = CSQLitePrepare(sql_line.strip())
    # The comment line is of format
    # -- .SQL2C_select (text|int, 1, varname), (text|int, 2, varname) .... (text|int, index, varname)
    matches: List[Tuple[str, int, str]] = re.findall(READ_SPEC_TICKER_RE, comment_line)
    while_start = f"while ( ({assign(VAR_RETURN_CODE, f'sqlite3_step({VAR_STMT})')}) == SQLITE_ROW ) " + "{"
    print_items_str = [f"{var_name}: {'%s' if var_type == 'text' else '%d'}" for (var_type, _, var_name) in matches]
    print_values_str = [f"sqlite3_column_{var_type}({VAR_STMT}, {var_index})" for (var_type, var_index, _) in matches]
    printf_call = f"printf(\"{', '.join(print_items_str)}\\n\", {','.join(print_values_str)});"
    while_end = "}"
    
    while_node = CSimpleStr([while_start, printf_call, while_end, f"sqlite3_finalize({VAR_STMT});"])
    return [prepared, while_node, CSimpleStr([EXIT_ON_DONE_CALL])], index, []


def parse_exec(line: str, index: int):
    return [
        CSQLiteExec(line)
    ], index, []
    

# Parses a line, and returns the next line to parse.
# Importantly, also returns if some "global" members (like functions)
# that need to be added.
def parse_line(lines: List[str], index: int):
    line = lines[index].strip()
    # return the next index to parse.
    # sometimes, we'd parse two lines together (comments)
    index += 1
    if line.startswith(OPEN_TICKER):
        file_name = line.split()[1]
        return [CSQLiteOpen(file_name)], index, []
    
    if line.startswith(COMMENT_TICKER):
        return parse_comment(lines, index)
    
    # Now, we just exec whatever this sql statement is.
    return parse_exec(line, index)

def perform_parse(lines: List[str]) -> List[str]:
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if len(lines) > 0]

    index = 0
    nodes = []
    funcs = []

    while index < len(lines):
        new_nodes, index, new_funcs = parse_line(lines, index)
        nodes = [*nodes, *new_nodes]
        funcs = [*funcs, *new_funcs]

    file = [HEADERS, EXIT_ON_ERROR_FUNC, *VAR_DECLS, MAIN_START]


    for node in nodes:
        file.extend(node.canonicalize(None))
        file.extend(BLANK)
    
    file.append(MAIN_END)
    return file

