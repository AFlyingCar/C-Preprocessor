#!/usr/bin/env python3

import os, sys, re

DELIMITERS = " (){}[]\t\n!@#$%^&*-=+\\|,./<>?~`'\""
DELIMITER_REGEX = r"(\s+|\)|\(|\,|\.|;|{|}|##|#)"

macros = { "__FILE__" : "",
           "__LINE__" : "0",
           "__DATE__" : "",
           "__TIME__" : "",
           "__STDC__" : "",
           "__OBJC__" : "0",
           "__cplusplus" : "0",
           "__ASSEMBLER__" : "",
           "__STDC_HOSTED__" : "",
           "__STDC_VERSION__" : "",
         }
# "NAME" : (["param1", "param2", ...], "value")
macroFunctions = {
                 }

includeDirs = [ "/usr/include/",
                "/usr/lib/gcc/x86_64-linux-gnu/4.8/include/"
              ]

def getMacroValue(valueOrMacro, extraMacros = {}):
    if valueOrMacro.strip() in macros:
        ret = getMacroValue(macros[valueOrMacro.strip()], extraMacros).strip()
        return ret
    elif valueOrMacro.strip() in extraMacros:
        ret = getMacroValue(extraMacros[valueOrMacro.strip()], extraMacros).strip()
        return ret
    else:
        return valueOrMacro.strip()

def isMacroAFunc(macro, extraMacros = {}):
    return macro in macroFunctions or (macro in extraMacros and type(extraMacros[macro]) == tuple)

def defined(macro, extraMacros = {}):
    return macro in macros or macro in macroFunctions or macro in extraMacros

def isFloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def getNumOperands(operator):
    if operator in '!~' or operator == "defined" or operator == "not": return 1
    else: return 2

def isoperator(token):
    return (token == "&&" or token == "||" or token == ">=" or
            token == "and" or token == "or" or token == "not" or
            token == "<=" or token == "==" or token == "!=" or
            token == ">>" or token == "<<" or token in "!~+-<>&|^*/%()" or
            token == "defined")

def getPrecedence(operator):
    if operator == "defined":
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
    elif operator in "()":
        return 99
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
    s = re.compile(r'(\s+|\S+|\d+|\W+|\(|\))')
    all = s.findall(expression)
    all2 = []
    x = 0
    while x < len(all):
        i = all[x]
        if i.strip():
            if i == "defined":
                all2.append('defined')
            elif i.startswith('defined'):
                all[x] = ''
                all.insert(x, i[7:])
                all.insert(x, i[:7])
                continue
            elif i == '!':
                all2.append('!')
            elif i.startswith('!'):
                all[x] = ''
                all.insert(x, i[1:])
                all.insert(x, '!')
                continue
            elif i == '(':
                all2.append('(')
            elif i == ')':
                all2.append(')')
            elif i.startswith('('):
                all[x] = ''
                all.insert(x, i[1:])
                all.insert(x, '(')
                continue
            elif i.endswith(')'):
                all[x] = ''
                all.insert(x, ')')
                all.insert(x, i[:-1])
                continue
            elif i == '':
                pass
            else:
                all2.append(i)
        x += 1
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

        if token not in "()" and isoperator(token):
            while (operatorstack and
                   (getPrecedence(operatorstack[-1]) <= getPrecedence(token)) and
                   (getAssociativity(operatorstack[-1]) == "left")):
                # print "Adding operator '" + operatorstack[-1] + "' (precedence %d) to output."%getPrecedence(operatorstack[-1])
                outputqueue.append(operatorstack.pop())
            # print "Adding '" + token + "' (precedence %d) to operator stack"%getPrecedence(token)
            operatorstack.append(token)
        elif token == "(":
            # print "Adding operator '" + token + "' to operator stack"
            operatorstack.append(token)
        elif token == ")":
            while operatorstack and operatorstack[-1] != "(":
                # print "Adding operator '" + operatorstack[-1] + "' to output"
                outputqueue.append(operatorstack.pop())
            # print outputqueue
            operatorstack.pop()
        elif not isoperator(token):
            # print "Adding operand '" + token + "' to output"
            outputqueue.append(token)
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
    polishNotation = parseExpression(expression)
    valuesStack = []
    # print "EVALUATE"
    for token in polishNotation:
        if isoperator(token):
            operator = token

            if operator == "&&": operator = "and"
            elif operator == "||": operator = "or"
            elif operator == "!": operator = "not"

            # print operator

            result = ""
            if getNumOperands(operator) == 2:
                rightoperand = getMacroValue(str(valuesStack.pop()))
                leftoperand = getMacroValue(str(valuesStack.pop()))

                result = eval(leftoperand + ' ' + operator + ' ' + rightoperand)
            else:
                # print valuesStack
                operand = str(valuesStack.pop())
                if operator == "defined":
                    result = defined(operand)
                else:
                    result = eval(operator + ' ' + getMacroValue(operand))

            valuesStack.append(result)
        else:
            # print token
            valuesStack.append(token)

    if len(valuesStack) != 1:
        print "Malformed expression!"
        return 0

    return valuesStack[0]

def stringify(token):
    return '"' + token + '"'

def macroizeLine(line, extraMacros = {}):
    tokenized = [t for t in re.split(DELIMITER_REGEX, line) if len(t.strip()) != 0]

    print tokenized

    i = 0
    stringing = False
    while i < len(tokenized):
        token = tokenized[i]
        # Don't replace in strings
        if "\"" in token or "'" in token:
            if stringing:
                stringing = False
            else:
                stringing = True
            continue

        if not stringing:
            print token

            if defined(token, extraMacros):
                if isMacroAFunc(token, extraMacros):
                    params, value = macroFunctions[token]
                    print params
                    print value
                    numParams = len(params)

                    i += 2
                    start = i
                    givenParamsTokens = []
                    while tokenized[i] != ")":
                        givenParamsTokens.append(tokenized[i])
                        i += 1

                    givenParams = [y.strip() for y in ' '.join(givenParamsTokens).split(',')]

                    if len(params) == len(givenParams):
                        print givenParams

                        passableValues = dict(extraMacros, **dict(zip(params, givenParams)))
                        result = macroizeLine(value, passableValues)
                        print result

                else:
                    tokenized[i] = getMacroValue(token, extraMacros)

            if token == '##':
                if i != 0 and i + 1 < len(tokenized):
                    tokenized[i] = getMacroValue(tokenized[i - 1], extraMacros) + getMacroValue(tokenized[i + 1], extraMacros)
                    tokenized[i - 1] = ''
                    tokenized[i + 1] = ''
                else:
                    print "Stray '##' in the program"
                    sys.exit(1)
        i += 1

    return ' '.join(tokenized)


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

    i = 0
    for line in processedLines:
        print i, ":", line
        i += 1

def includeStatement(nodirective, i, lines):
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

        # lines.insert(i + n, "#line " + str(i))
        i += n - 1

    return i

def ifStatement(cond, i, lines, skipAll = False):
    if cond:
        remove = False
        blockcomment = False

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

            directive, nodirective = getDirectiveAndNoDirective(line)

            if directive == "if":
                lines[i] = ""
                i = ifStatement(bool(int(evaluateExpression(nodirective))), i + 1, lines)
                continue
            elif directive == "ifndef":
                lines[i] = ""
                i = ifStatement(nodirective not in macros, i + 1, lines)
                continue
            elif directive == "else" or directive == "elif":
                remove = True
            elif directive == "endif":
                lines[i] = ""
                return i + 1
            elif directive == "include":
                lines[i] = ""
                oldFilename = getMacroValue("__FILE__")
                i += includeStatement(nodirective, i, lines)
                macros["__FILE__"] = oldFilename
                continue
            elif directive == "ifdef":
                lines[i] = ""
                i = ifStatement(nodirective in macros, i + 1, lines)
                continue
            elif directive == "define":
                lines[i] = ""
                defineMacro(nodirective)
                continue

            if remove:
                line = ""

            lines[i] = line
            i += 1
    else:
        while i < len(lines):
            line = lines[i].strip()
            directive, nodirective = getDirectiveAndNoDirective(line)
            if directive == "if" or directive == "ifdef" or directive == "ifndef":
                lines[i] = ""
                i = ifStatement(False, i + 1, lines, True)
                continue
            elif directive == "else":
                if not skipAll:
                    lines[i] = ""
                    i = ifStatement(True, i + 1, lines)
                    return i
            elif directive == "elif":
                if not skipAll:
                    lines[i] = ""
                    i = ifStatement(bool(int(evaluateExpression(nodirective))), i + 1, lines)
                    return i
            elif directive == "endif":
                print "endif"
                lines[i] = ""
                return i + 1

            lines[i] = ""

            i += 1

    if i >= len(lines):
        print "Mismatched endifs"
        sys.exit(1)

    return i

def defineMacro(nodirective):
    c = 0
    while c < len(nodirective):
        if nodirective[c] in DELIMITERS:
            break
        c += 1

    macro = nodirective[:c]

    value = getMacroValue(nodirective[c:])

    if value.startswith('('):
        rawParams = ""
        realValue = ""
        paramsList = []

        c = 0
        while c < len(value):
            if value[c] == ')':
                break
            c += 1

        rawParams = value[1:c]
        realValue = value[c + 1:].strip()

        paramsList = [p.strip() for p in rawParams.split(',')]

        macroFunctions[macro] = (paramsList, realValue)
    else:
        macros[macro] = value

def undefineMacro(nodirective):
    c = 0
    while c < len(nodirective):
        if nodirective[c] in DELIMITERS:
            break
        c += 1

    macro = nodirective[:c]

    if macro in macros:
        macros.pop(macro, None)
    elif macro in macroFunctions:
        macroFunctions.pop(macro, None)
    else:
        print "Undefined macro " + macro
        sys.exit(1)

def process(filename, lines):
    global macros
    print "Processing " + filename

    macros["__FILE__"] = filename


    #TODO: Convert ifndef and ifdef statements to `if defined` statements

    blockcomment = False

    depth = 0
    lastDepth = 0
    ifFailure = False
    
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
            macros["__LINE__"] = str(int(macros["__LINE__"]) + 1)
            # Remove the \ character before concatenating
            line = line[:-1] + lines[i].strip()
            lines[i - 1] = ""

        if '//' in line:
            line = line[:line.find('//')]
        if '/*' in line:
            line = line[:line.find('/*')]
            blockcomment = True

        # line = handleStringConcatenation(line)

        if line.startswith('#'):
            directive, nodirective = getDirectiveAndNoDirective(line)

            if directive == "if":
                lines[i] = ""
                i = ifStatement(bool(int(evaluateExpression(nodirective))), i + 1, lines)

            if directive == "define":
                defineMacro(nodirective)
            elif directive == "undef":
                undefineMacro(nodirective)
            elif directive == "ifdef":
                lines[i] = ""
                i = ifStatement(nodirective in macros, i + 1, lines)
            elif directive == "ifndef":
                lines[i] = ""
                i = ifStatement(nodirective not in macros, i + 1, lines)
            elif directive == "include":
                oldFilename = filename
                i = includeStatement(nodirective, i, lines) + 1
                macros["__FILE__"] = oldFilename
            elif directive == "line":
                num = ""
                c = 0
                while c < len(nodirective):
                    if nodirective[c] not in DELIMITERS:
                        num += nodirective[c]
                    else:
                        break
                    c += 1

                num = num.strip()
                value = num

                if not num.isdigit():
                    value = getMacroValue(num)
                    if not value.isdigit():
                        print "Invalid line digit-sequence specifier."
                        sys.exit(1)

                scharseq = ""
                gettingscharseq = False
                while c < len(nodirective):
                    if nodirective[c] == '"':
                        if gettingscharseq: break

                        gettingscharseq = True
                    else:
                        if gettingscharseq:
                            scharseq += nodirective[c]
                    c += 1

                if scharseq != "":
                    filename = scharseq
                macros["__LINE__"] = str(int(value))

            line = ""

        line = macroizeLine(line)

        lines[i] = line
        i += 1

        macros["__LINE__"] = str(int(macros["__LINE__"]) + 1)

    print "Done processing " + filename

    return lines

if __name__ == "__main__":
    main()

