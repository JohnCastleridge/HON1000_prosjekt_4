import os
from google import genai

# Finn nøkkelen slik app.py gjør det
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key or api_key.strip() == "":
    try:
        with open('API_key.txt', 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if 'API Key:' in content:
                api_key = content.split('API Key:')[1].strip()
            else:
                api_key = content
    except:
        pass

print(f"Tester nøkkel: {api_key[:10]}...{api_key[-5:]}")

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model='gemini-flash-lite-latest',
        contents="Hei, fungerer du?"
    )
    print("SVAR FRA GEMINI:", response.text)
except Exception as e:
    print("FEIL:", str(e))
