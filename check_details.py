import google.generativeai as genai

def load_api_key():
    with open('API_key.txt', 'r') as f:
        for line in f:
            if line.startswith('API Key:'):
                return line.split('API Key:')[1].strip()
    return None

api_key = load_api_key()
genai.configure(api_key=api_key)

print(f"{'Modellnavn':<40} | {'Input-grense':<15} | {'Beskrivelse'}")
print("-" * 100)

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        # Prøver å hente ut tokens/grenser
        input_limit = m.input_token_limit if hasattr(m, 'input_token_limit') else "Ukjent"
        print(f"{m.name:<40} | {str(input_limit):<15} | {m.description[:50]}...")
