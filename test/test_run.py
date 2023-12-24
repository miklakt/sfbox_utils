# usualy it is what we need
# comment if working directory is different from script directory
import sys, os
os.chdir(sys.path[0])

import sfbox_utils

#read template file and parse it to create a structure to work with
ifile = "template.txt"
input = sfbox_utils.read_input.parse_file(ifile)

# An example change in the input
input[0]["mon:P:chi - C"] = -1.0

# Append sequintial task to the input
input.append({"mon:P:chi - C" : -1.5})

# Executable path has to be set if sfbox is not installed
#sfbox_utils.set_executable_path('/home/ml/Studium/SFBox/sfbox_64')
sfbox_utils.write_input.write_input_file("test_sfbox_file.in", input)

# call sfbox executable 
sfbox_utils.sfbox_call("test_sfbox_file.in")