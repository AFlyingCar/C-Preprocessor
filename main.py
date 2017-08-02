#!/usr/bin/env python3

import os, sys, re

DELIMITERS = " (){}[]\t\n!@#$%^&*-=+\\|,./<>?~`'\""
DELIMITER_REGEX = "(\t| |\(|\))+"

macros = {}

includeDirs = [ "/usr/include/",
                "/usr/lib/gcc/x86_64-linux-gnu/4.8/include/"
              ]

def defined(MACRO):
    return MACRO in macros

def isFloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def isoperator(token):
    return (token == "&&" or token == "||" or token == ">=" or
            token == "<=" or token == "==" or token == "!=" or
            token == ">>" or token == "<<" or token in "!~+-<>&|^*/%()")

def getPrecedence(operator):
    if operator in "()":
        return 1
    elif operator in "!~":
        return 2
    elif operator in "*/%":
        return 3
    elif operator in "+-":
        return 4
    elif operator == "<<" or operator == ">>":
        return 5
    elif operator == "<=" or operator == ">=" or operator in "<>":
        return 6
    elif operator == "==" or operator == "!=":
        return 7
    elif operator == "&":
        return 8
    elif operator == "^":
        return 9
    elif operator == "|":
        return 10
    elif operator == "&&":
        return 11
    elif operator == "||":
        return 12
    else:
        return -1

def getAssociativity(operator):
    if (operator == "&&" or operator == "||" or operator == ">=" or
        operator == "<=" or operator == "==" or operator == "!=" or
        operator == ">>" or operator == "<<" or operator in "!~+-<>&|^*/%()"):
        return "left"
    else:
        return "right"

def tokenize(expression):
    s = re.compile(r'(\s+|\S+|\d+|\W+)')
    all = s.findall(expression)
    all2 = []
    for i in all:
        if i.strip():
            if i.startswith('defined'):
                all2.append(i)
            elif i.startswith('('):
                all2.append('(')
                all2.append(i[1:])
            elif i.endswith(')'):
                all2.append(i[:-1])
                all2.append(')')
            else:
                all2.append(i)
    return all2

# The shunting yard algorithm
def parseExpression(expression):
    # print expression
    # tokens = [i for i in re.split(r'(\d+|\W+)', expression) if i]
    tokens = tokenize(expression)

    outputqueue = []
    operatorstack = []

    # print tokens

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token.startswith('defined'):
            macro = token.strip().split('(')[1][:-1].rstrip()
            token = str(int(defined(macro)))

        if token in macros:
            token = macros[token]

        if token.isdigit():
            # print "Adding '" + token + "' to output"
            outputqueue.append(token)
        elif token not in "()" and isoperator(token):
            while (operatorstack and
                   (getPrecedence(operatorstack[-1]) >= getPrecedence(token)) and
                   (getAssociativity(operatorstack[-1]) == "left")):
                # print "Adding '" + operatorstack[-1] + "' to output."
                outputqueue.append(operatorstack.pop())
            # print "Adding '" + token + "' to operator stack"
            operatorstack.append(token)
        elif token == "(":
            # print "Adding '" + token + "' to operator stack"
            operatorstack.append(token)
        elif token == ")":
            while operatorstack and operatorstack[-1] != "(":
                # print "Adding '" + operatorstack[-1] + "' to output"
                outputqueue.append(operatorstack.pop())
            operatorstack.pop()
        else:
            # print "Adding '" + token + "' to output"
            outputqueue.append(token)

        i += 1

    if "(" in operatorstack:
        print "mismatched parethesis!"
        return []

    while operatorstack:
        outputqueue.append(operatorstack.pop())

    # print outputqueue

    return outputqueue

def evaluateExpression(expression):
    # print "EVALUATE"
    polishNotation = parseExpression(expression)
    valuesStack = []
    for token in polishNotation:
        # print valuesStack
        if token.isdigit() or isFloat(token):
            valuesStack.append(token)
        else:
            operator = token

            if operator == "&&": operator = "and"
            elif operator == "||": operator = "or"

            rightoperand = str(valuesStack.pop())
            leftoperand = str(valuesStack.pop())

            result = eval(leftoperand + ' ' + operator + ' ' + rightoperand)
            valuesStack.append(result)

    if len(valuesStack) != 1:
        print "Malformed expression!"
        return 0

    return valuesStack[0]

def macroizeLine(line):
    tokenized = [t for t in re.split(DELIMITER_REGEX, line) if len(t.strip()) != 0]

    atleast = 0
    stringing = False
    for token in tokenized:
        # Don't replace in strings
        if "\"" in token or "'" in token:
            if stringing:
                stringing = False
            else:
                stringing = True
            continue

        if token in macros:
            # Do this because python doesn't have a way to replace a string based solely on position+range
            line = macros[token].join((line[:line.find(token, atleast)], line[line.find(token, atleast) + len(token):]))
        atleast += len(token)

    return line


def getWord(line):
    match = re.match(r'^\s*(\w+)', line)
    if match != None:
        return str(match.groups()[0])
    else:
        return None

def getDirectiveAndNoDirective(line):
    nosharp = line[1:].lstrip()
    c = 0
    while c < len(nosharp):
        if nosharp[c] in DELIMITERS:
            break
        c += 1
    return nosharp[:c], nosharp[c:].lstrip()

def main():
    global includeDirs

    if(len(sys.argv) < 2):
        print("Invalid number of arguments. Must specify a filename.")
        sys.exit(1)

    for arg in sys.argv[1:-1]:
        if arg.startswith('-I'):
            incdir = arg[2:] + ('/' if not arg.endswith('/') else "")
            if incdir not in includeDirs:
                includeDirs.append(incdir)


    filename = sys.argv[len(sys.argv) - 1]

    lines = []
    with open(filename, 'r') as f:
        lines = f.read().split('\n')

    processedLines = process(filename, lines)

    for line in processedLines:
        print line

def process(filename, lines):
    print "Processing " + filename

    global macros

    #TODO: Convert ifndef and ifdef statements to `if defined` statements

    blockcomment = False
    skippingToNextElse = False
    i = 0
    lineNum = 0
    while i < len(lines):
        line = lines[i].strip()

        # Process comments first
        if blockcomment:
            if '*/' in line:
                line = line[line.find('*/') + 2:]
                blockcomment = False
            else:
                lines[i] = ""
                i += 1
                continue

        while line.endswith('\\'):
            i += 1
            # Remove the \ character before concatenating
            line = line[:-1] + lines[i].strip()
            lines[i - 1] = ""

        if '//' in line:
            line = line[:line.find('//')]
        if '/*' in line:
            line = line[:line.find('/*')]
            blockcomment = True


        if line.startswith('#'):
            directive, nodirective = getDirectiveAndNoDirective(line)

            if directive == "define":
                c = 0
                while c < len(nodirective):
                    if nodirective[c] in DELIMITERS:
                        break
                    c += 1


                macro = nodirective[:c]

                value = nodirective[c:]

                # TODO: Handle macro functions

                macros[macro] = value

            elif directive == "ifdef":
                c = 0
                while c < len(nodirective):
                    if nodirective[c] in DELIMITERS:
                        break
                    c += 1

                macro = nodirective[:c]

                if macro not in macros:
                    line = ""
                    while i < len(lines):
                        if(getDirectiveAndNoDirective(lines[i])[0] == "endif"):
                            break
                        lines[i] = ""
                        i += 1
                    lines[i] = ""

            elif directive == "ifndef":
                c = 0
                while c < len(nodirective):
                    if nodirective[c] in DELIMITERS:
                        break
                    c += 1

                macro = nodirective[:c]

                if macro in macros:
                    line = ""
                    while i < len(lines):
                        if(getDirectiveAndNoDirective(lines[i])[0] == "endif"):
                            break
                        lines[i] = ""
                        i += 1
                    lines[i] = ""

            elif directive == "include":
                filename = nodirective[1:].split('>' if nodirective.startswith('<') else '"', 1)[0]
                fullFilename = None

                if nodirective.startswith('<'):
                    for inc in includeDirs:
                        if os.path.exists(os.path.join(inc, filename)):
                            fullFilename = os.path.join(inc, filename)
                            break

                if fullFilename == None:
                    if os.path.exists(os.path.join(".", filename)):
                        fullFilename = os.path.join(".", filename)
                        break
                    else:
                        print "No such file or directory found: " + filename
                        sys.exit(1)

                lines[i] = ""

                with open(fullFilename, 'r') as f:
                    processedLines = process(fullFilename, f.read().split('\n'))

                    n = 0
                    while n < len(processedLines):
                        lines.insert(i + n, processedLines[n])
                        n += 1

                    lines.insert(i + n, "#line " + str(i))
                    i += n

            elif directive == "if":
                # expression = nodirective
                expression_result = evaluateExpression(nodirective)
                print "RESULT = " + str(expression_result)

                if not bool(int(expression_result)):
                    skippingToNextElse = True
                    line = ""
                    while i < len(lines):
                        directive = getDirectiveAndNoDirective(lines[i])[0]
                        if(directive == "endif" or directive == "elif" or
                           directive == "else"):
                            break
                        lines[i] = ""
                        i += 1
                    lines[i] = ""

            elif directive == "elif":
                if skippingToNextElse:
                    skippingToNextElse = False
                    # expression = nodirective
                    expression_result = evaluateExpression(nodirective)
                    print "RESULT = " + str(expression_result)

                    if not bool(int(expression_result)):
                        skippingToNextElse = True
                        line = ""
                        while i < len(lines):
                            if(getDirectiveAndNoDirective(lines[i])[0] == "endif"):
                                break
                            lines[i] = ""
                            i += 1
                        lines[i] = ""
                else:
                    line = ""
                    while i < len(lines):
                        if(getDirectiveAndNoDirective(lines[i])[0] == "endif"):
                            break
                        lines[i] = ""
                        i += 1
                    lines[i] = ""

            elif directive == "else":
                if not skippingToNextElse:
                    line = ""
                    while i < len(lines):
                        if(getDirectiveAndNoDirective(lines[i])[0] == "endif"):
                            break
                        lines[i] = ""
                        i += 1
                    lines[i] = ""

            line = ""

        line = macroizeLine(line)

        lines[i] = line
        # print i, ": " + line
        i += 1
        lineNum += 1

    return lines

if __name__ == "__main__":
    main()

