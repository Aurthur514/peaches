# Test snippet
data = "{}"
prompt = f'''You are an expert at writing compelling cover letters. Customize this letter while preserving formatting.
Rules:
- Keep same format/layout
- Highlight relevant experience
- Reference job requirements
- Be enthusiastic but professional
- Be truthful and specific
- Preserve contact info/header

Job:
Title: test
Company: test
Requirements: {data}
Description: test

Template:
test'''

print(prompt)