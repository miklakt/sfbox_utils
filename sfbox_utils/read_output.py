import pathlib
from typing import List
from typing import Union
from enum import Enum, auto



from .utils import try_cast_to_numeric, ld_to_dl


class ParseError(ValueError):
    pass


class OutputLineType(Enum):
    empty = auto()
    ignore = auto()
    block_separator = auto()
    statement = auto()
    invalid = auto()
    vector_element = auto()
    vector_name = auto()


def get_line_type(line, raise_error = True):
    line = line.rstrip('\r\n')
    if (line == ''):
        return OutputLineType.empty

    if (line == 'system delimiter'):
        return OutputLineType.block_separator

    if ' : ' in line:
        if ('vector' in line) or ('profile' in line):
            return OutputLineType.vector_name
        else:
            if line.count(":") != 3:
                return OutputLineType.invalid
            return OutputLineType.statement
    line = try_cast_to_numeric(line)
    if isinstance(line, str):
        #failed to convert to number
        return OutputLineType.invalid
    else:
        return OutputLineType.vector_element


def parse_statement(
        line : str,
        parse_all_keywords = False,
        new_sep = ":",
        replace_spaces = " ",
        convert_to = None,
        to_dict = False,
        ):

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


def vector_str_to_float(vector, as_numpy = True):
    v = [float(v_) for v_ in vector]
    if as_numpy:
        import numpy as np
        v = np.array(v, dtype=float)
    return v


def parse_vector(
    vector_name : str,
    vector_elements : List[str],
    parse_all_keywords = False,
    new_sep = ":",
    replace_spaces = " ",
    convert_to = None,
    to_dict = False,
    ):

    type_, type_title, profile_name, profile_type = [l.strip() for l in vector_name.split(sep = ":")]

    if convert_to is not None:
        vector_elements=convert_to(vector_elements)

    if not(parse_all_keywords):
        parameter = new_sep.join(
            [
                word.replace(" ", replace_spaces) for word in [
                    type_, type_title, profile_name, profile_type
                    ]
            ]
        )
        if to_dict:
            return {parameter : vector_elements}
        else:
            return parameter, vector_elements
    if to_dict:
        return {(type_, type_title, profile_name, profile_type) : vector_elements}
    else:
        return type_, type_title, profile_name, profile_type, vector_elements


def parse_file(
        file : Union[str, pathlib.Path],
        convert_vector_to = vector_str_to_float,
        convert_value_to = try_cast_to_numeric,
        compact = True,
        to_dict = True,
        ignore_fields = None, 
        read_fields = None,
        **kwargs):
    if (ignore_fields is not None) and (read_fields is not None):
        raise AttributeError("Can not pass ignore_fields and read_fields at the same time")
    
    def field_to_skip(line_, linetype_):
        if linetype_ is OutputLineType.vector_element: return False
        
        if linetype is OutputLineType.statement:
            line_ = line_.rsplit(":",1)[0]
        line_ = line_.rstrip()
        if (ignore_fields is None) and (read_fields is None):
            return False
        elif (ignore_fields is not None):
            return line_ in ignore_fields
        else:
            return line_ not in read_fields

    __SKIP__ = True

    f = open(file)
    #to collect all calculations in a list
    blocks = []
    #to collect all lines of current block
    lines = []
    #to store vector name
    vector_name = None
    #to collect all vector values
    vector_acc = []
    #reading file line by line
    i=0
    #skip vector flag
    skip_vector = False
    while line := f.readline():
        line = line.rstrip('\r\n')
        i=i+1
        linetype = get_line_type(line)
        skip_field = field_to_skip(line, linetype)

        if linetype == OutputLineType.invalid:
            raise ParseError(f"Invalid expression in line {i}")

        ##Reading vector elements
        if linetype == OutputLineType.vector_element:
            #When we meet vector element, we must have read vector name
            if vector_name is None:
                raise ParseError(f"Vector element is read but no vector name found, line {i}")
            
            if not skip_vector:
                vector_acc.append(line)
            else:
                #we do not need to read vector, 
                #but we indicate we indeed read vector elements
                vector_acc = __SKIP__

        else:
            if vector_acc:
                if not skip_vector:
                    lines.append(parse_vector(vector_name, vector_acc, convert_to=convert_vector_to, to_dict=to_dict, **kwargs))
                vector_name = None
                vector_acc = []
            
            else:
                if vector_name is not None:
                    raise ParseError(f"Vector name must be followed by vector elements, line {i}")

        if linetype == OutputLineType.vector_name:
            vector_name = line
            skip_vector = skip_field

        if linetype == OutputLineType.statement:
            if not skip_field:
                lines.append(parse_statement(line, convert_to=convert_value_to, to_dict=to_dict, **kwargs))

        if linetype == OutputLineType.block_separator:
            if to_dict:
                lines = dict((key, val) for k in lines for key, val in k.items())
            blocks.append(lines)
            lines = []

    if vector_acc:
        lines.append(parse_vector(vector_name, vector_acc, convert_to=convert_vector_to, **kwargs))
        vector_name = None
        vector_acc = []

    if lines:
        blocks.append(lines)

    if compact:
        blocks = ld_to_dl(blocks)
    return blocks