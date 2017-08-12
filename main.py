#!/usr/bin/env python3
from __future__ import print_function

import os, sys, re

DELIMITERS = " (){}[]\t\n!@#$%^&*-=+\\|,./<>?~`'\""
DELIMITER_REGEX = r"(\s+|\)|\(|\,|\.|;|{|}|##|#)"

macros = { "__FILE__" : "",
           "__LINE__" : "1",
           "__DATE__" : "",
           "__TIME__" : "",
           "__STDC__" : "",
           "__OBJC__" : "0",
           "__COUNTER__" : "0",
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

def getCurrentLine():
    return macros["__LINE__"]

def getMacroValue(valueOrMacro, extraMacros = {}):
    # Special case for __COUNTER__
    if valueOrMacro.strip() == "__COUNTER__":
        macros["__COUNTER__"] = str(int(macros["__COUNTER__"]) + 1)
        return macros["__COUNTER__"]

    if valueOrMacro.strip() in extraMacros:
        # ret = getMacroValue(extraMacros[valueOrMacro.strip()], extraMacros).strip()
        return extraMacros[valueOrMacro.strip()] #ret
    elif valueOrMacro.strip() in macros:
        # ret = getMacroValue(macros[valueOrMacro.strip()], extraMacros).strip()
        return macros[valueOrMacro.strip()] #ret
    else:
        return valueOrMacro.strip()

def isMacroAFunc(macro, extraMacros = {}):
    return macro in macroFunctions or (macro in extraMacros and type(extraMacros[macro]) == tuple)

# Overriding the macros list and the macro functions list is possible
def defined(macro, extraMacros = {}, macroList = macros, functions = macroFunctions):
    return macro in macroList or macro in functions or macro in extraMacros

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
    tokens = tokenize(expression)

    outputqueue = []
    operatorstack = []

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token not in "()" and isoperator(token):
            while (operatorstack and
                   (getPrecedence(operatorstack[-1]) <= getPrecedence(token)) and
                   (getAssociativity(operatorstack[-1]) == "left")):
                outputqueue.append(operatorstack.pop())
            operatorstack.append(token)
        elif token == "(":
            operatorstack.append(token)
        elif token == ")":
            while operatorstack and operatorstack[-1] != "(":
                outputqueue.append(operatorstack.pop())
            operatorstack.pop()
        elif not isoperator(token):
            outputqueue.append(token)
        else:
            outputqueue.append(token)

        i += 1

    if "(" in operatorstack:
        print("mismatched parethesis!")
        return []

    while operatorstack:
        outputqueue.append(operatorstack.pop())

    return outputqueue

def evaluateExpression(expression):
    polishNotation = parseExpression(expression)
    valuesStack = []
    for token in polishNotation:
        if isoperator(token):
            operator = token

            if operator == "&&": operator = "and"
            elif operator == "||": operator = "or"
            elif operator == "!": operator = "not"

            result = ""
            if getNumOperands(operator) == 2:
                rightoperand = getMacroValue(str(valuesStack.pop()))
                leftoperand = getMacroValue(str(valuesStack.pop()))

                result = eval(leftoperand + ' ' + operator + ' ' + rightoperand)
            else:
                operand = str(valuesStack.pop())
                if operator == "defined":
                    result = defined(operand)
                else:
                    result = eval(operator + ' ' + getMacroValue(operand))

            valuesStack.append(result)
        else:
            valuesStack.append(token)

    if len(valuesStack) != 1:
        print("Malformed expression!")
        return 0

    return valuesStack[0]

def stringify(token):
    return '"' + token + '"'

def expandMacroFunc(funcName, paramsList, extraMacros = {}):
    realParamsList = paramsList

    funcParams, replaceValue = macroFunctions[funcName]

    if(len(funcParams) == len(realParamsList) or (funcParams[-1] == "..." and len(realParamsList) >= (len(funcParams) - 1))):
        if funcParams[-1] != "...":
            for i in range(len(funcParams)):
                extraMacros[funcParams[i]] = realParamsList[i]
        else:
            for i in range(len(funcParams) - 1):
                extraMacros[funcParams[i]] = realParamsList[i]
            vaName = funcParams[-1][:-3]
            if vaName == '': vaName = "__VA_ARGS__"

            extraMacros[vaName] = ", ".join(realParamsList[len(funcParams) - 1:])
    else:
        print("Invalid number of parameters")
        sys.exit(1)

    return replaceValue

def performTokenOperations(tokens):
    i = 0
    while i < len(tokens):
        token = tokens[i]

        if i + 2 < len(tokens) and tokens[i + 1] == "##":
            tokens[i] = tokens[i] + tokens[i + 2]
            tokens[i + 1] = ''
            tokens[i + 2] = ''
        elif token == "#" and i + 1 < len(tokens):
            tokens[i] = '"' + tokens[i + 1] + '"'
            tokens[i + 1] = ''

        i += 1

    return tokens

def macroizeLine(line, extraMacros = {}):
    tokenized = [t for t in re.split(DELIMITER_REGEX, line) if len(t.strip()) != 0]

    i = 0

    while i < len(tokenized):
        token = tokenized[i]

        if defined(token):
            if isMacroAFunc(token):
                params, value = macroFunctions[token]

                # Remove the opening parenthesis
                tokenized[i + 1] = ''

                # Grab each individual parameter as a token
                c = i + 2
                givenParamsTokens = []
                while tokenized[c] != ")":
                    givenParamsTokens.append(tokenized[c])
                    tokenized[c] = ''
                    c += 1
                tokenized[c] = ''

                # Combine the parameters tokens and break them apart again based on commas
                givenParams = [y.strip() for y in ' '.join(givenParamsTokens).split(',')]

                if len(params) != len(givenParams):
                    if params[-1].endswith("..."):
                        vaName = params[-1][:-3]
                        if vaName == '': vaName = '__VA_ARGS__'

                        givenParams = givenParams[:len(params) - 1] + [', '.join(givenParams[len(params):])]
                    else:
                        print("Invalid number of parameters.")
                        sys.exit(1)

                paramMap = dict(zip(params, givenParams))

                ret = expandMacroFunc(token, givenParams)

                rtokens = [t for t in re.split(DELIMITER_REGEX, ret) if len(t.strip()) != 0]

                # Prescanning
                # Expand only the parameters
                c = 0
                while(c < len(rtokens)):
                    # print rtokens[c]
                    if defined(rtokens[c], paramMap, macros, {}):
                        rtokens[c] = getMacroValue(rtokens[c], paramMap)
                    c += 1

                rtokens = performTokenOperations(rtokens)

                # Expand only the parameters again
                c = 0
                while(c < len(rtokens)):
                    if defined(rtokens[c], paramMap, macros, {}):
                        rtokens[c] = getMacroValue(rtokens[c], paramMap)
                        continue
                    c += 1

                tokenized[i] = ''
                tokenized[i:i] = rtokens

                continue
            else:
                tokenized[i] = getMacroValue(token, extraMacros)

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

def perror(error, filename, line, linenum, column):
    print("%s:%d:%d: error: %s"%(filename, linenum, column, error), file=sys.stderr)
    if line != "":
        print(" %s"%line, file=sys.stderr)
    if column > 0:
        print((" "*column) + "^", file=sys.stderr)
    sys.exit(1)

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

    i = 1
    for line in processedLines:
        print("%d : %s"%(i, line))
        i += 1

def includeStatement(nodirective, i, lines, oldFilename):
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
            column = (lines[i].index('<') if nodirective.startswith('<') else linex[i].index('"')) + 1
            perror("No such file or directory found `%s`"%filename, oldFilename, lines[i], i, column)

    lines[i] = ""

    with open(fullFilename, 'r') as f:
        processedLines = process(fullFilename, f.read().split('\n'))

        n = 0
        while n < len(processedLines):
            lines.insert(i + n, processedLines[n])
            n += 1

        i += n - 1

    return i

def ifStatement(cond, i, lines, filename, lastIf, skipAll = False):
    if cond:
        remove = False
        blockcomment = False

        while i < len(lines):
            removeLine = False

            line = lines[i].strip()

            # Process comments first
            if blockcomment:
                if '*/' in line:
                    line = line[line.find('*/') + 2:]
                    blockcomment = False
                else:
                    macros["__LINE__"] = str(int(macros["__LINE__"]) + 1)

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

            if line.startswith("#"):
                directive, nodirective = getDirectiveAndNoDirective(line)
                removeLine = True
            else:
                directive, nodirective = ["",""]

            if directive == "if":
                lines[i] = ""
                i = ifStatement(bool(int(evaluateExpression(nodirective))), i + 1, lines, filename, line)
                continue
            elif directive == "ifndef":
                lines[i] = ""
                i = ifStatement(nodirective not in macros, i + 1, lines, filename, line)
                continue
            elif directive == "else" or directive == "elif":
                remove = True
            elif directive == "endif":
                lines[i] = ""
                return i + 1
            elif directive == "include":
                # lines[i] = ""
                oldLineNum = getCurrentLine()
                oldFilename = getMacroValue("__FILE__")
                i += includeStatement(nodirective, i, lines, filename)
                macros["__FILE__"] = oldFilename
                macros["__LINE__"] = str(oldLineNum)
                removeLine = True
            elif directive == "line":
                doLineDirective(nodirective)
            elif directive == "undef":
                lines[i] = ""
                undefineMacro(nodirective)
                removeLine = True
            elif directive == "ifdef":
                lines[i] = ""
                i = ifStatement(nodirective in macros, i + 1, lines, filename, line)
                removeLine = True
            elif directive == "define":
                defineMacro(nodirective)
                removeLine = True
            elif directive == "error":
                doErrorDirective(line, filename, i, nodirective)

            if remove or removeLine:
                line = ""

            # Don't increase the line count if it was just changed.
            if directive != "line":
                macros["__LINE__"] = str(int(macros["__LINE__"]) + 1)

            lines[i] = macroizeLine(line)
            i += 1
    else:
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith("#"):
                directive, nodirective = getDirectiveAndNoDirective(line)
                removeLine = True
            else:
                directive, nodirective = ["",""]

            if directive == "if" or directive == "ifdef" or directive == "ifndef":
                lines[i] = ""
                i = ifStatement(False, i + 1, lines, filename, lastIf, True)
                continue
            elif directive == "else":
                if not skipAll:
                    lines[i] = ""
                    i = ifStatement(True, i + 1, lines, filename, lastIf)
                    return i
            elif directive == "elif":
                if not skipAll:
                    lines[i] = ""
                    i = ifStatement(bool(int(evaluateExpression(nodirective))), i + 1, lines, filename, lastIf)
                    return i
            elif directive == "endif":
                lines[i] = ""
                return i + 1

            lines[i] = ""

            macros["__LINE__"] = str(int(macros["__LINE__"]) + 1)

            i += 1

    if i >= len(lines):
        perror("Missing matching endif.", filename, lastIf, i - 1, 1)

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

def doLineDirective(nodirective):
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
            print("Invalid line digit-sequence specifier.")
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
        print("Undefined macro %s"%macro)
        sys.exit(1)

def doErrorDirective(line, filename, linenum, nodirective):
    perror(nodirective, filename, line, linenum, 1)

def process(filename, lines):
    global macros
    print("Processing %s"%filename)

    macros["__FILE__"] = filename
    macros["__LINE__"] = "1"


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
            # getCurrentLine() # This will increase the line counter by one
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
                i = ifStatement(bool(int(evaluateExpression(nodirective))), i + 1, lines, filename, line)

            if directive == "define":
                defineMacro(nodirective)
            elif directive == "undef":
                undefineMacro(nodirective)
            elif directive == "ifdef":
                lines[i] = ""
                i = ifStatement(nodirective in macros, i + 1, lines, filename)
            elif directive == "ifndef":
                lines[i] = ""
                i = ifStatement(nodirective not in macros, i + 1, lines, filename)
            elif directive == "include":
                oldFilename = filename
                oldLineNum = getMacroValue("__LINE__")
                i = includeStatement(nodirective, i, lines, filename) + 1
                macros["__FILE__"] = oldFilename
                macros["__LINE__"] = oldLineNum
            elif directive == "line":
                doLineDirective(nodirective)
            elif directive == "error":
                doErrorDirective(line, filename, i, nodirective)

            line = ""

        line = macroizeLine(line)

        lines[i] = line
        i += 1

        macros["__LINE__"] = str(int(macros["__LINE__"]) + 1)

    print("Done processing %s"%filename)

    return lines

if __name__ == "__main__":
    main()

