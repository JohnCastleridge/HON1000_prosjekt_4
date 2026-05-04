import google.generativeai as genai

def load_api_key():
    with open('API_key.txt', 'r') as f:
        for line in f:
            if line.startswith('API Key:'):
                return line.split('API Key:')[1].strip()
    return None

api_key = load_api_key()
genai.configure(api_key=api_key)

print("Tilgjengelige modeller:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
