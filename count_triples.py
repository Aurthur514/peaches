p='d:/peaches/automation_tools/resume_tailor.py'
s=open(p,'r',encoding='utf-8').read()
print('lines',len(s.splitlines()))
print('count triple double', s.count('"""'))
for i, line in enumerate(s.splitlines(),1):
    if '"""' in line:
        print(i, line)
