import os
import sys
from google import genai

def get_api_key():
    """Henter API-nøkkel fra miljøvariabel eller fil."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        try:
            if os.path.exists("API_key.txt"):
                with open("API_key.txt", "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    return content.split("API Key:")[1].strip() if "API Key:" in content else content
        except Exception:
            pass
    return key

def troubleshoot():
    print("--- Gemini API Feilsøking ---")
    
    api_key = get_api_key()
    if not api_key:
        print("FEIL: Fant ingen API-nøkkel i GEMINI_API_KEY eller API_key.txt")
        return

    print(f"Nøkkel funnet: {api_key[:5]}...{api_key[-5:]}")
    
    try:
        client = genai.Client(api_key=api_key)
        
        print("\n1. Tester tilkobling og henter modeller...")
        models = list(client.models.list())
        print(f"Suksess! Fant {len(models)} tilgjengelige modeller.")
        
        print("\n2. Tester tekstgenerering med 'gemini-flash-lite-latest'...")
        response = client.models.generate_content(
            model='gemini-flash-lite-latest',
            contents="Dette er en test. Svar kun med ordet 'OK'."
        )
        print(f"Svar fra AI: {response.text.strip()}")
        
        print("\n--- Alt ser ut til å fungere! ---")
        
    except Exception as e:
        error_msg = str(e)
        print(f"\nFEIL oppstod: {error_msg}")
        if "503" in error_msg:
            print("Tips: Gemini API har for stor pågang akkurat nå. Vent noen minutter og prøv igjen.")
        elif "429" in error_msg:
            print("Tips: Du har nådd kvotegrensen din (Rate Limit). Vent litt før du prøver igjen.")
        elif "401" in error_msg or "403" in error_msg:
            print("Tips: API-nøkkelen din er ugyldig eller har ikke tilgang.")

if __name__ == "__main__":
    troubleshoot()
