from google import genai

def load_api_key():
    with open('API_key.txt', 'r') as f:
        for line in f:
            if line.startswith('API Key:'):
                return line.split('API Key:')[1].strip()
    return None

api_key = load_api_key()
client = genai.Client(api_key=api_key)

print("Tilgjengelige modeller:")
for m in client.models.list():
    print(f"Name: {m.name}")
    # print(f"Attributes: {dir(m)}") # DEBUG
