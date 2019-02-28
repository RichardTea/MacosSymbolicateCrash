import sys
import ntpath
from subprocess import Popen, PIPE, STDOUT
import os

def get_arch_and_base_address(file_path_diag, module_name):
    found_binary = False
    with open(file_path_diag) as f:
        lines = f.readlines()
        for line in lines:
            if found_binary and module_name in line and "0x" in line:
                base_address = None
                arch = None
                words = line.split()
                for index, word in enumerate(words):
                    if index > 0 and words[index - 1] == module_name:
                        print "Found architecture: " + word
                        arch = word
                    if base_address == None and "0x" in word:
                        print "Found base address: " + word
                        base_address = word
                    if arch and base_address:
                        return (arch, base_address)
            elif "Binary Images:" in line:
                found_binary = True

    raise ValueError("Didn't find architecture or base address of module" + module_name)


def get_method_address(line, module):
    if module in line and "0x" in line:
        words = line.split()
        for word in words:
            if "0x" in word:
                word = word.replace('[', '')
                word = word.replace(']', '')
                return word
    return ''


def read_crash(file_path_sym, file_path_diag, output_file_path):
    output_file = open(output_file_path, "w")

    module_name = ntpath.basename(file_path_sym)

    (arch, base_address) = get_arch_and_base_address(file_path_diag, module_name)

    with open(file_path_diag) as f:
        lines = f.readlines()
        for line in lines:
            is_translated = False
            if module_name in line and base_address in line:

                method_address = get_method_address(line, module_name)

                if method_address != "":
                    cmd = 'atos -arch ' + arch + " -o " + file_path_sym + " -l " + base_address + " " + method_address
                    print cmd
                    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
                    atos_output = p.stdout.read()
                    out_line = line.translate(None, "\n") + "   " + atos_output + "\n"
                    output_file.write(out_line)
                    is_translated = True

            if not is_translated:
                output_file.write(line)


arglen = len(sys.argv)

if arglen < 3:
    print 'Missing input - symbolicate.py {xxx.dSYM/Contents/Resources/DWARF/xxx} {file.crash}'

filename = ""

if arglen == 3:
    filename = "symbolicated.crash"
else:
    filename = sys.argv[3]

try:
    os.remove(filename)
except OSError:
    pass

read_crash(sys.argv[1], sys.argv[2], filename)

print 'Symbolicated log to ' + filename
