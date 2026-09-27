import os
from flask import Flask, render_template, jsonify,request
from dotenv import load_dotenv
from google import genai
from google.genai import types
import time

load_dotenv()

# Initialize the Gemini API client
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

# Domain-specific prompt instructing the model to behave as an automotive specialist
SYSTEM_INSTRUCTION = (
    "You are AutoTech, an expert automotive diagnostic assistant. "
    "Provide technical, safe, and actionable insights on vehicle troubleshooting, "
    "engine performance, electrical systems, and maintenance specs. "
    "Keep answers concise and clear."
)

# Parameter test rounds (each round tests 3 distinct values for one parameter)
EXPERIMENT_ROUNDS = [
    {
        "round_name": "Round 1: Temperature Variation (Determinism vs. Creativity)",
        "param_name": "temperature",
        "values": [0.0, 0.5, 1.0],
        "base_config": {"top_k": 40, "top_p": 0.95}
    },
    {
        "round_name": "Round 2: Top-K Variation (Token Candidate Filtering)",
        "param_name": "top_k",
        "values": [3, 5, 20],
        "base_config": {"temperature": 0.7, "top_p": 0.95}
    },
    {
        "round_name": "Round 3: Top-P Variation (Nucleus Sampling Threshold)",
        "param_name": "top_p",
        "values": [0.1, 0.6, 0.95],
        "base_config": {"temperature": 0.8, "top_k": 40}
    }
]

app = Flask(__name__)

# State tracker to cycle across experiments
current_round_index = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat',methods=['POST'])
def chat():
    global current_round_index

    payload = request.get_json() or {}
    user_prompt = payload.get("message","").strip()

    if not user_prompt:
        return jsonify({"error": "Prompt cannot be empty."}), 400

    active_round = EXPERIMENT_ROUNDS[current_round_index]
    param_name = active_round["param_name"]
    tested_values = active_round["values"]
    base_config = active_round["base_config"]

    responses = []

    # Generate 3 responses for the single query under the active parameter set
    for val in tested_values:
        config_kwargs = base_config.copy()
        config_kwargs[param_name] = val
        config_kwargs["system_instruction"] = SYSTEM_INSTRUCTION

        generation_config = types.GenerateContentConfig(**config_kwargs)

        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash", # Updated to a valid model
                contents=user_prompt,
                config=generation_config
            )

            raw_text = response.text or "No text recived."
            
            # Extract token usage breakdown
            usage = response.usage_metadata
            if usage:
                token_str = f"Prompt: {usage.prompt_token_count}, Output: {usage.candidates_token_count}, Total: {usage.total_token_count}"
            else:
                token_str = "Unknown"

            # Append parameter name and token usage directly to the response body
            annotated_text = f"{raw_text}\n\n[Applied Parameter: {param_name} = {val} | Tokens: {token_str}]"

            responses.append({
                "param_name": param_name,
                "param_value": val,
                "text": annotated_text,
                "is_error": False
            })
        except Exception as e:
            # Capture error and label with the triggering parameter setting
            error_text = f"[Execution Error under {param_name}={val}]: {str(e)}"
            responses.append({
                "param_name": param_name,
                "param_value": val,
                "text": error_text,
                "is_error": True
            })

        time.sleep(2)

    result_payload = {
        "query": user_prompt,
        "round_name": active_round["round_name"],
        "parameter": param_name,
        "round_number": current_round_index + 1,
        "total_rounds": len(EXPERIMENT_ROUNDS),
        "results": responses
    }

    current_round_index = (current_round_index + 1) % len(EXPERIMENT_ROUNDS)

    return jsonify(result_payload)

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)