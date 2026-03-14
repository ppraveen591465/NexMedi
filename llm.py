import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Create client
client = genai.Client(api_key=API_KEY)

# Pick a multimodal model that can handle PDFs/images (example name, adjust to your access).
MODEL_NAME = "gemini-3-flash-preview"  # or gemini-2.0-flash / gemini-1.5-flash etc.

BASE_SYSTEM_PROMPT = (
    "You are a medical explanation assistant.\n"
    "You read patient lab reports and explain them in safe, simple language.\n"
    "You never diagnose specific diseases or prescribe treatment.\n"
    "Always clearly say this is not medical advice and they must consult a doctor.\n"
)

def build_prompt(lab_text: str, mode: str) -> str:
    # Novelty 2: explanation mode
    style_line = (
        "Provide explanations in normal medical language.\n"
        if mode == "medical"
        else "Explain everything like I am 12 years old, using very simple words.\n"
    )

    # Novelty 1 & 3: risk level + follow-up questions
    instructions = (
        "Analyze the lab report.\n"
        "1) List key abnormal and important values.\n"
        "2) Explain each in simple language.\n"
        "3) Assign an overall health risk level: Normal, Monitor, or Critical, "
        "and show it with symbols like 🟢, 🟡, 🔴.\n"
        "4) Say if a doctor visit is recommended (yes/no, in neutral language).\n"
        "5) Suggest 3–5 follow-up questions the patient can ask their doctor.\n"
    )

    return (
        BASE_SYSTEM_PROMPT
        + style_line
        + instructions
        + "\nHere is the lab report text:\n"
        + lab_text
    )

def summarize_from_text(lab_text: str, mode: str) -> str:
    if not lab_text.strip():
        return "No lab text found. Please upload a report or paste values."

    prompt = build_prompt(lab_text, mode)

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"[Gemini text error] {e}"

def summarize_from_file(file_path: str, mime_type: str, mode: str) -> str:
    """
    Send local PDF/image bytes + prompt to Gemini in one request.[web:48][web:71]
    """
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        prompt = (
            BASE_SYSTEM_PROMPT
            + (
                "Provide explanations in normal medical language.\n"
                if mode == "medical"
                else "Explain everything like I am 12 years old, using very simple words.\n"
            )
            + "Analyze this lab report document and:\n"
              "1) List key abnormal and important values.\n"
              "2) Explain them simply.\n"
              "3) Assign overall risk level: Normal, Monitor, or Critical, with symbols 🟢, 🟡, 🔴.\n"
              "4) Say if a doctor visit is recommended.\n"
              "5) Suggest 3–5 follow-up questions for the doctor.\n"
        )

        # Document understanding: send bytes as a Part plus prompt text.[web:48][web:71]
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                prompt,
            ],
        )
        return response.text
    except Exception as e:
        return f"[Gemini file error] {e}"
