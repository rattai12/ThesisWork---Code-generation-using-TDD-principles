import json

# Initialize lists to store the data
texts = []
tests = []
text_and_tests = []

# Read and process the jsonl file
with open('mbpp.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():  # Skip empty lines
            data = json.loads(line)
            if 'text' in data and 'test_list' in data:
                # Store just the text
                texts.append(data['text'])
                
                # Store just the tests
                tests.append(data['test_list'])
                
                # Store text and tests together
                text_and_tests.append({
                    'text': data['text'],
                    'tests': data['test_list']
                })

# Write texts to a file
with open('mbpp_texts.txt', 'w', encoding='utf-8') as f:
    for i, text in enumerate(texts, 1):
        f.write(f"{i}. {text}\n")

# Write tests to a file
with open('mbpp_tests.txt', 'w', encoding='utf-8') as f:
    for i, test_list in enumerate(tests, 1):
        f.write(f"Problem {i}:\n")
        for test in test_list:
            f.write(f"  {test}\n")
        f.write("\n")

# Write combined text and tests to a file
with open('mbpp_text_and_tests.txt', 'w', encoding='utf-8') as f:
    for i, item in enumerate(text_and_tests, 1):
        f.write(f"Problem {i}:\n")
        f.write(f"Description: {item['text']}\n")
        f.write("Tests:\n")
        for test in item['tests']:
            f.write(f"  {test}\n")
        f.write("\n") 