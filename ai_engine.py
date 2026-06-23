import requests
import json

# Predefined prompt presets
PRESETS = [
    {
        "name": "Executive Summary & Key Takeaways",
        "description": "Create an executive summary and bullet points of key findings.",
        "system_prompt": (
            "You are a professional research assistant. Analyze the provided web page content and "
            "generate an executive summary (3-5 sentences) followed by a bulleted list of the "
            "most important takeaways and insights. Keep the tone professional, objective, and concise."
        )
    },
    {
        "name": "Structured FAQ (Q&A)",
        "description": "Restructure content into a clear list of questions and answers.",
        "system_prompt": (
            "You are an expert editor and educator. Read the web page text and restructure the core information "
            "into a structured Q&A (Frequently Asked Questions) format. Formulate logical questions that readers "
            "would have, and answer them accurately using only the information available in the text."
        )
    },
    {
        "name": "Data & Info Extractor",
        "description": "Extract pricing, contacts, key people, and dates into a structured list.",
        "system_prompt": (
            "You are a precise data extraction specialist. Read the web page content and extract the following: "
            "1. Contact Information (emails, phone numbers, addresses, social profiles)\n"
            "2. Pricing, costs, or subscription plans\n"
            "3. Key people mentioned (names, titles, organizations)\n"
            "4. Important dates or deadlines\n"
            "Present this information in clean markdown tables or organized bulleted lists. If any category "
            "is not found in the text, list it as 'Not specified in content'."
        )
    },
    {
        "name": "Clean Markdown Document",
        "description": "Clean and re-format the raw text into a beautifully structured Markdown file.",
        "system_prompt": (
            "You are a skilled technical writer. Read the raw scraped text of this website and restructure "
            "it into a clean, beautifully formatted Markdown document. Establish a logical hierarchy with H1, "
            "H2, and H3 headers. Clean up punctuation, rewrite awkward formatting, use code blocks for code "
            "snippets, blockquotes for quotes, and bold text for emphasis. Strip away any remainder of navigation, "
            "footer, or ads text."
        )
    },
    {
        "name": "Custom Action...",
        "description": "Write a custom instruction for the AI.",
        "system_prompt": ""
    }
]

def call_gemini(api_key: str, model: str, system_prompt: str, prompt: str) -> tuple[bool, str]:
    """
    Calls the Google Gemini REST API.
    Returns (success_boolean, response_text).
    """
    if not api_key:
        return False, "Error: Gemini API Key is missing. Please enter it in the settings."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }

    # Construct standard payload with systemInstruction
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    
    if system_prompt:
        payload["systemInstruction"] = {
            "parts": [
                {"text": system_prompt}
            ]
        }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        # Check if successful
        if response.status_code != 200:
            # Let's try to parse the error message
            try:
                err_data = response.json()
                err_msg = err_data.get('error', {}).get('message', response.text)
                return False, f"API Error (HTTP {response.status_code}): {err_msg}"
            except Exception:
                return False, f"API Error (HTTP {response.status_code}): {response.text}"

        res_data = response.json()
        
        # Check if block exists
        candidates = res_data.get('candidates', [])
        if not candidates:
            return False, f"Error: No candidates returned. Full response: {json.dumps(res_data)}"
            
        content = candidates[0].get('content', {})
        parts = content.get('parts', [])
        if not parts:
            # Check if block/finishReason was safety
            finish_reason = candidates[0].get('finishReason')
            return False, f"Error: Content generation stopped. Reason: {finish_reason}"

        text = parts[0].get('text', '')
        return True, text

    except requests.exceptions.Timeout:
        return False, "Error: Connection to Gemini API timed out."
    except Exception as e:
        return False, f"Error calling Gemini API: {str(e)}"

def call_ollama(ollama_url: str, model: str, system_prompt: str, prompt: str) -> tuple[bool, str]:
    """
    Calls the local Ollama API.
    Returns (success_boolean, response_text).
    """
    if not ollama_url:
        ollama_url = "http://localhost:11434"
        
    url = f"{ollama_url.rstrip('/')}/api/generate"
    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    if system_prompt:
        payload["system"] = system_prompt

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        if response.status_code != 200:
            try:
                err_data = response.json()
                if 'error' in err_data:
                    return False, f"Ollama Error: {err_data['error']}"
            except Exception:
                pass
            return False, f"Ollama Error (HTTP {response.status_code}): {response.text}"

        res_data = response.json()
        text = res_data.get('response', '')
        return True, text

    except requests.exceptions.Timeout:
        return False, f"Error: Connection to Ollama at {ollama_url} timed out. Is Ollama running?"
    except requests.exceptions.ConnectionError:
        return False, f"Error: Could not connect to Ollama at {ollama_url}. Please ensure Ollama is installed and running."
    except Exception as e:
        return False, f"Error calling Ollama API: {str(e)}"

def get_ollama_models(ollama_url: str) -> list[str]:
    """
    Fetches the list of installed Ollama models from the local service.
    """
    if not ollama_url:
        ollama_url = "http://localhost:11434"
        
    url = f"{ollama_url.rstrip('/')}/api/tags"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            return models
    except Exception:
        pass
    return []
