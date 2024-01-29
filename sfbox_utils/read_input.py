import pathlib

from typing import List
from typing import Union

from enum import Enum, auto

from .utils import try_cast_to_numeric, ld_to_dl

class ParseError(ValueError):
    pass


class InputLineType(Enum):
    empty = auto()
    comment = auto()
    block_separator = auto()
    statement = auto()
    invalid = auto()

def get_line_type(line : str) -> str:
    """Check the line for type
    possible variants
    -empty line ""
    -comment "comment"
    -start keyword "start"
    -parameter-value statement "param_value"

    Args:
        line (str): line to check

    Returns:
        str: linetype
    """
    if (line == ''):
        return InputLineType.empty
    if line.startswith(('//', '#')):
        return InputLineType.comment
    #if ('/' in line) or ('#' in line):
    #    return InputLineType.comment
    if (line == 'start'):
        return InputLineType.block_separator
    if ':' in line:
        if line.count(":") != 3:
            return InputLineType.invalid
        return InputLineType.statement
    return InputLineType.invalid

def parse_statement(
        line : str,
        parse_all_keywords = False,
        new_sep = ":",
        replace_spaces = " ",
        convert_to = try_cast_to_numeric,
        to_dict = False,
        ):
    """Parses statement type : type_title : parameter_name : parameter_value
    to a tuple or a dict {(type, type_title, parameter_name) : parameter_value}.

    Examples:
        parse_all_keywords = True
    'lat : 2G : gradients : 2' -> ('lat', '2G', 'gradients', 2)
        parse_all_keywords = True, to_dict = true
    'lat : 2G : gradients : 2' -> {'lat', '2G', 'gradients' : 2}
        parse_all_keywords = False, to_dict = true, new_sep = '.'
    'lat : 2G : gradients : 2' -> {'lat.2G.gradients' : 2}

    Args:
        line (str): line to parse
        parse_all_keywords (bool, optional): Whether to split first three keywords to tuple or leave it as a string. Defaults to False.
        new_sep (str, optional): Replaces old separator ':' to the given. Defaults to ":".
        replace_spaces (str, optional): Replace all spaces. Defaults to "".
        convert_to (_type_, optional): Tries to apply a conversion function. Defaults to None.
        to_dict (bool, optional): Save result as a dict, otherwise as a tuple. Defaults to False.

    Raises:
        ParseError: Failed to parse, no separators between keywords were found
        ParseError: Failed to parse, not enough keywords in the line

    Returns:
        tuple|dict: parsed to a tuple or a dict statement
    """

    if ":" not in line:
        raise ParseError("Can not parse the line no separator found")

    if line.count(":") != 3:
        raise ParseError("Must be at 3 keywords and value")

    type_, type_title, parameter_name, parameter_value = [l.strip() for l in line.split(sep = ":")]

    if convert_to is not None:
        parameter_value=convert_to(parameter_value)

    if not(parse_all_keywords):
        parameter = new_sep.join(
            [
                word.replace(" ", replace_spaces) for word in [
                    type_, type_title, parameter_name
                    ]
            ]
        )
        if to_dict:
            return {parameter : parameter_value}
        else:
            return parameter, parameter_value
    if to_dict:
        return {(type_, type_title, parameter_name) : parameter_value}
    else:
        return type_, type_title, parameter_name, parameter_value

def parse_block(lines : Union[List[str], str], to_dict=True, **kwargs):
    if isinstance(lines, str):
        lines = [line.strip() for line in lines.split("\n")]
    
    parsed_lines = [parse_statement(line, to_dict = False, **kwargs) for line in lines]

    if to_dict:
            #parsed_lines = dict((key, val) for k in parsed_lines for key, val in k.items())
            parsed_lines_dict = {}
            for line in parsed_lines:
                key, val = line
                if key not in parsed_lines_dict:
                    parsed_lines_dict[key] = val
                else:
                    #print(f"'{key}' is already found")
                    old_val = parsed_lines_dict[key]
                    if not isinstance(old_val, list): old_val = [old_val]
                    old_val.append(val)
                    parsed_lines_dict[key] = old_val
            parsed_lines = parsed_lines_dict

    return parsed_lines

def parse_file(
        file : Union[str, pathlib.Path],
        compact = False,
        **kwargs):
    f = open(file)
    blocks = []
    lines = []
    while line := f.readline():
        #remove everything after // and #
        line = line.split("#")[0]
        line = line.partition("//")[0]
        line = line.rstrip('\r\n')

        line_type = get_line_type(line)
        if line_type == InputLineType.comment or line_type == InputLineType.empty:
            pass
        elif line_type == InputLineType.block_separator:
            parsed_lines = parse_block(lines, **kwargs)
            blocks.append(parsed_lines)
            lines = []
        elif line_type == InputLineType.statement:
            lines.append(line)
    if lines:
        parsed_lines = parse_block(lines, **kwargs)
        blocks.append(parsed_lines)
        lines = []
    f.close()
    if compact:
        blocks = ld_to_dl(blocks)
    return blocks
#%%
