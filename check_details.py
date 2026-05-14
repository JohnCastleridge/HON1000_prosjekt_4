from google import genai

def load_api_key():
    try:
        with open('API_key.txt', 'r') as f:
            for line in f:
                if line.startswith('API Key:'):
                    return line.split('API Key:')[1].strip()
    except:
        import os
        return os.environ.get("GEMINI_API_KEY")
    return None

api_key = load_api_key()
client = genai.Client(api_key=api_key)

print(f"{'Modellnavn':<40} | {'Input-grense':<15} | {'Output-grense':<15}")
print("-" * 80)

for m in client.models.list():
    # Sjekker hvilke attributter som faktisk finnes
    input_limit = getattr(m, 'input_token_limit', 'Ukjent')
    output_limit = getattr(m, 'output_token_limit', 'Ukjent')
    
    # Vi er mest interessert i Gemini-modellene
    if "gemini" in m.name.lower():
        print(f"{m.name:<40} | {str(input_limit):<15} | {str(output_limit):<15}")
