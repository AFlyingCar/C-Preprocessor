#!/usr/bin/env python



DIRECTIVES = {
        "python"  : HandlePython,
        "if"      : HandleIf,      
        "ifdef"   : HandleIfdef,    # done
        "ifndef"  : HandleIfndef,   # done
        "elif"    : HandleElif,
        "else"    : HandleElse,
        "endif"   : HandleEndif,    # done
        "pragma"  : HandlePython,
        "include" : HandlePython,
        "define"  : HandlePython,
        "undef"   : HandlePython,
        "line"    : HandlePython,
        "error"   : HandlePython,
        "warning" : HandlePython,
        "\\"      : HandleBackslash
}

DEFAULT_MACROS = {
        "__COUNTER__" : 0,
        "__LINE__" : 0,
        "__FILE__" : ""
}

DELIMITERS = [
    " ",
    "<",
    ">",
    "\t",
    "\n",
    "#",
    "\"",
    "'",
    ",",
    "."
]

def skipAheadToDirective(i, fileData, directive):
    for i in range(i, len(fileData)):
        if(fileData[i - 1] == "\n" and fileData[i] == "#"):
            i += 1
            found = ""
            while fileData[i] not in DELIMITERS:
                found += fileData[i]
                if(i >= len(fileData)):
                    error("Reached EOF")
            if(found == directive):
                return i
    error("Could not find %s before EOF.", directive)

    return -1;

def main():
    fileData = ""
    lines = []
    defined = {}
    skippingTo = ""
    i = 0

    lines = fileData.split("\n");

    while(i < len(lines)):
        line = lines[i]

        if(skippingTo != "" and line.endswith("\\")):
            lines[i] += lines.pop(i+1)
            continue

        if(line.startswith("#")):
            directive = line[1:]

            if skippingTo != "":
                if directive.startswith(skippingTo):
                    skippingTo = ""
                else:
                    continue

            if(directive not in DIRECTIVES):
                error("Unknown directive %s"%directive)

            if(directive.startswith("define")):
                argument, value = directive[6:].strip().split(" ")
                defined[argument] = value
            elif(directive.startswith("ifdef")):
                argument = directive[5:].strip()
                if(argument not in defined):
                    skippingTo = "endif"
            elif(directive.startswith("ifndef")):
                argument = directive[6:].strip()
                if(argument in defined):
                    skippingTo = "endif"
            elif(directive.startswith("line")):
                lnum, fname = directive[4:].strip().split(" ")

        for define in defined:
            if(define in line):
                lines[i] = defined[define]

        i += 1

