import ast
p = r'd:\peaches\automation_tools\resume_tailor.py'
try:
    s = open(p, 'r', encoding='utf-8').read()
    ast.parse(s)
    print('AST OK')
except SyntaxError as e:
    print('SyntaxError', e)
    print('Error at:', e.lineno, e.offset)
    L = s.splitlines()
    for i in range(max(0,e.lineno-5), min(len(L), e.lineno+5)):
        print(i+1, L[i])
