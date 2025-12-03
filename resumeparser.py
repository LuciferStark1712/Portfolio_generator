import os
import json
from groq import Groq
from PyPDF2 import PdfReader
import docx
from pdf2image import convert_from_path
import pytesseract

# ✅ Initialize Groq client
# Set this in your environment: GROQ_API_KEY=your_key_here
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def ocr_pdf(file_path):
    text = ""
    images = convert_from_path(file_path)

    for img in images:
        text += pytesseract.image_to_string(img)

    return text.strip(), len(images)


def extract_text_from_pdf(file_path):
    """
    Returns (text, page_count)
    """
    text = ""
    page_count = 0

    with open(file_path, "rb") as f:
        reader = PdfReader(f)
        for page in reader.pages:
            page_count += 1
            extracted = page.extract_text()
            if extracted:
                text += extracted

    text = text.strip()

    # If still no text, try OCR
    if not text:
        print("⚠ No text found! Using OCR...")
        text, page_count = ocr_pdf(file_path)

    return text, page_count


def extract_text_from_docx(file_path):
    """
    Returns (text, page_count)
    For DOCX we just assume 1 page.
    """
    doc = docx.Document(file_path)
    text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    return text, 1


def compute_ats_score(parsed, text, page_count):
    """
    Compute a simple ATS-style score (0–100) based on parsed fields.
    Returns (ats_score_int, detail_dict)
    """
    score = 0
    total = 0
    details = {}

    def add(label, condition, weight):
        nonlocal score, total
        total += weight
        details[label] = bool(condition)
        if condition:
            score += weight

    def has(value):
        return bool(value and str(value).strip())

    # Basic contact info
    add("has_name", has(parsed.get("name")), 10)
    add("has_email", has(parsed.get("email")), 10)
    add("has_phone", has(parsed.get("phone")), 5)

    # Core sections (expecting lists from the model)
    education = parsed.get("education") or []
    skills = parsed.get("skills") or []
    projects = parsed.get("projects") or []
    experience = parsed.get("experience") or []
    achievements = parsed.get("achievements") or []

    add("has_education", len(education) > 0, 10)
    add("has_skills", len(skills) > 0, 20)
    add("has_projects", len(projects) > 0, 10)
    add("has_experience", len(experience) > 0, 20)
    add("has_achievements", len(achievements) > 0, 5)
    add("has_objective", has(parsed.get("objective")), 5)

    # Format / length heuristics
    add("length_ok_pages", page_count <= 2, 3)

    words = text.split()
    add("length_ok_words", len(words) >= 250, 2)  # at least some substance

    if total == 0:
        return 0, details

    ats_score = round(score * 100 / total)
    return ats_score, details


def ats_extractor(file_path):
    # Extract text based on file type
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf":
        text, page_count = extract_text_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        text, page_count = extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload PDF or DOCX.")

    # Prompt for the model
    system_prompt = (
        "You are an ATS resume parser. "
        "Extract all details from the resume and output in valid JSON ONLY. "
        "Do NOT include markdown, explanations, or extra text. "
        "The JSON should strictly follow this format:\n\n"
        "{\n"
        '  \"name\": \"string\",\n'
        '  \"email\": \"string\",\n'
        '  \"phone\": \"string\",\n'
        '  \"education\": [\"list of degrees and institutions\"],\n'
        '  \"skills\": [\"list of skills\"],\n'
        '  \"projects\": [\"list of key projects with brief details\"],\n'
        '  \"experience\": [\"list of work experiences if available\"],\n'
        '  \"achievements\": [\"list of awards or achievements\"],\n'
        '  \"objective\": \"career objective text\"\n'
        "}"
    )

    # Call Groq API
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        temperature=0.0,
    )

    raw_output = response.choices[0].message.content.strip()

    # Parse JSON safely
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError:
        # Try cleaning if model adds extra text
        json_str = raw_output[raw_output.find("{"): raw_output.rfind("}") + 1]
        data = json.loads(json_str)

    # ✅ Compute ATS score + ideal score + details
    ats_score, ats_details = compute_ats_score(data, text, page_count)
    ideal_score = 90  # you can tune this later

    # Attach to the parsed JSON so you can use it directly in templates
    data["ats_score"] = ats_score
    data["ideal_score"] = ideal_score
    data["ats_details"] = ats_details
    data["raw_text"] = text
    data["page_count"] = page_count

    return data
