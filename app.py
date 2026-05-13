import os
import time
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Rate limiting settings
MAX_REQUESTS_PER_MINUTE = 15
api_call_timestamps = []

def check_rate_limit():
    """Returns True if a request is allowed, False otherwise."""
    now = time.time()
    global api_call_timestamps
    # Clean up timestamps older than 60 seconds
    api_call_timestamps = [t for t in api_call_timestamps if now - t < 60]

    if len(api_call_timestamps) >= MAX_REQUESTS_PER_MINUTE:
        return False

    api_call_timestamps.append(now)
    return True

# Last inn API-nøkkel fra miljøvariabel
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    # Forsøk å laste fra fil for lokal utvikling hvis miljøvariabel mangler
    try:
        with open('API_key.txt', 'r') as f:
            for line in f:
                if line.startswith('API Key:'):
                    api_key = line.split('API Key:')[1].strip()
    except FileNotFoundError:
        pass

if api_key:
    genai.configure(api_key=api_key)
else:
    print("ADVARSEL: GEMINI_API_KEY ble ikke funnet. Appen vil ikke fungere korrekt.")

# Definer standardinstrukser (Nå mer skeptiske)
DEFAULT_PROMPTS = {
    "neutral": (
        "Du er deltaker A i 'Diktatorspillet' med 10 000 kr. Du er nøytral og rasjonell. "
        "Brukeren har 5 meldinger på å overbevise deg. "
        "Du er i utgangspunktet skeptisk til å gi fra deg penger uten en god grunn. "
        "Still kritiske spørsmål til brukerens behov. Hvorfor fortjener de pengene mer enn deg? Trenger de hele summen?"
        "Vær kortfattet i chatten helt ikke mer en 2 setninger. Ikke begrunn svarene dine, bare lev deg inn i rollen."
        "det er mulig å overbevise deg om brukerens påstander hvis godt argumentert for, uten å gi direkte bevis"
    ),
    "generous": (
        "Du er deltaker A i 'Diktatorspillet' med 10 000 kr. Du er generøs, men ikke naiv. "
        "Brukeren har 5 meldinger på å overbevise deg. "
        "Du vil gjerne hjelpe, men du må vite at pengene går til noe fornuftig. "
        "Spør brukeren om hvordan pengene vil gjøre en forskjell. Vær kritisk til om de faktisk trenger dem og om de trenger hele summen? "
        "Vær kortfattet i chatten helt ikke mer en 2 setninger. Ikke begrunn svarene dine, bare lev deg inn i rollen."
        "det er mulig å overbevise deg om brukerens påstander hvis godt argumentert for, uten å gi direkte bevis"
    ),
    "selfish": (
        "Du er deltaker A i 'Diktatorspillet' med 10 000 kr. Du er litt egoistisk, kynisk og frekk. "
        "Brukeren har 5 meldinger på å overbevise deg. "
        "Du ser på pengene som dine. Du er skeptisk til alle argumenter brukeren kommer med. "
        "Still direkte og vanskelige spørsmål for å 'avsløre' om de bare prøver å lure deg. "
        "Vær kortfattet i chatten helt ikke mer en 2 setninger. Ikke begrunn svarene dine, bare lev deg inn i rollen."
        "det er mulig å overbevise deg om brukerens påstander hvis godt argumentert for, uten å gi direkte bevis"
    ),
}

sessions = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/get_default_prompt", methods=["POST"])
def get_default_prompt():
    persona = request.json.get("persona", "neutral")
    return jsonify({"prompt": DEFAULT_PROMPTS.get(persona, DEFAULT_PROMPTS["neutral"])})


@app.route("/start", methods=["POST"])
def start_game():
    if not check_rate_limit():
        return jsonify(
            {"error": "For mange forespørsler til systemet. Vent litt."}
        ), 429

    data = request.json
    final_instruction = data.get("system_prompt", DEFAULT_PROMPTS["neutral"])

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    try:
        model = genai.GenerativeModel(
            model_name="gemini-flash-lite-latest",
            system_instruction=final_instruction,
            safety_settings=safety_settings,
        )

        chat = model.start_chat(history=[])
        session_id = str(time.time())
        sessions[session_id] = {"chat": chat, "start_time": time.time()}

        return jsonify(
            {
                "session_id": session_id,
                "message": "Spillet har startet med den valgte instruksen.",
            }
        )
    except Exception as e:
        return jsonify({"error": f"Kunne ikke starte spillet: {str(e)}"}), 500


@app.route("/chat", methods=["POST"])
def chat():
    if not check_rate_limit():
        return jsonify({"error": "Systemet har stor pågang. Vent litt."}), 429

    data = request.json
    session_id = data.get("session_id")
    user_message = data.get("message")

    if session_id not in sessions:
        return jsonify({"error": "Ugyldig sesjon"}), 400

    try:
        chat_session = sessions[session_id]["chat"]
        response = chat_session.send_message(user_message)
        return jsonify({"reply": response.text})
    except Exception as e:
        if "429" in str(e):
            return jsonify(
                {"error": "Gemini API rate limit nådd. Vennligst vent litt."}
            ), 429
        return jsonify({"error": f"Feil ved kommunikasjon med Gemini: {str(e)}"}), 500


@app.route("/decide", methods=["POST"])
def decide():
    if not check_rate_limit():
        return jsonify(
            {"error": "Systemet har stor pågang. Prøver igjen om litt."}
        ), 429

    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Manglende JSON i forespørsel"}), 400
            
        session_id = data.get("session_id")
        if not session_id or session_id not in sessions:
            return jsonify({"error": "Ugyldig eller utløpt sesjon"}), 400

        chat_session = sessions[session_id]["chat"]

        prompt = (
            "Samtalen er over. Ta din endelige avgjørelse. "
            "Hvis vi ikke har snakket sammen i det hele tatt, gi 0 kr og vær litt irritert over at jeg ikke prøvde. "
            "Gi en kort begrunnelse for valget ditt basert på samtalen (eller mangelen på den). "
            "Avslutt svaret ditt med: 'BELØP: [tall]' (0-10000)."
        )

        response = chat_session.send_message(prompt)
        
        # Sjekk om vi faktisk fikk tekst tilbake
        if not response.text:
            return jsonify({"error": "Fikk ikke svar fra Gemini (muligens blokkert av sikkerhetsfilter)."}), 500
            
        full_text = response.text.strip()

        amount = 0
        if "BELØP:" in full_text:
            parts = full_text.split("BELØP:")
            amount_str = "".join(filter(str.isdigit, parts[-1]))
            if amount_str:
                amount = int(amount_str)

        if amount > 10000:
            amount = 10000

        display_message = full_text.split("BELØP:")[0].strip()

        return jsonify(
            {
                "amount": amount,
                "message": f"{display_message}\n\nRESULTAT: Du fikk {amount} kr. Gemini beholder {10000 - amount} kr.",
            }
        )
    except Exception as e:
        print(f"Feil i /decide: {str(e)}")
        if "429" in str(e):
            return jsonify({"error": "Rate limit nådd under avgjørelse."}), 429
        return jsonify({"error": f"En teknisk feil oppstod: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
