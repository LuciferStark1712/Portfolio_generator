import os
import uuid
from jinja2 import Template


def normalize_experience(experience_list):
    """
    Experience may come as:
    - list of strings
    - list of dicts
    - empty

    We convert all formats into:
    [{ title, company, years, points }]
    """

    final_exp = []

    if not experience_list:
        return final_exp

    for item in experience_list:
        if isinstance(item, str):
            final_exp.append({
                "title": item,
                "company": "",
                "years": "",
                "points": []
            })

        elif isinstance(item, dict):
            final_exp.append({
                "title": item.get("title", "Experience"),
                "company": item.get("company", ""),
                "years": item.get("years", ""),
                "points": item.get("points", [])
            })

    return final_exp


def normalize_projects(project_list):
    """
    Projects may be list of strings.
    Convert them into:
    [{ name, description }]
    """
    final_projects = []

    if not project_list:
        return final_projects

    for p in project_list:
        if isinstance(p, str):
            final_projects.append({
                "name": p,
                "description": ""
            })
        elif isinstance(p, dict):
            final_projects.append({
                "name": p.get("name", "Project"),
                "description": p.get("description", "")
            })

    return final_projects


def generate_portfolio(data, theme="theme_modern"):
    """
    Generate a modern portfolio based on ATS-parsed resume data.
    Output: generated_sites/<uid>/index.html
    """

    # Create unique ID for the portfolio
    uid = str(uuid.uuid4())[:8]
    output_dir = os.path.join("generated_sites", uid)
    os.makedirs(output_dir, exist_ok=True)

    # Path to new dynamic template
    template_path = os.path.join("templates", theme, "index.html")

    # Load template file
    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    # Extract values safely
    name = data.get("name", "John Doe")
    email = data.get("email", "")
    phone = data.get("phone", "")
    objective = data.get("objective", "Aspiring Software Developer")
    skills = data.get("skills", [])
    location = data.get("location", "India")
    experience = normalize_experience(data.get("experience", []))
    projects = normalize_projects(data.get("projects", []))

    # Render HTML with dynamic resume data
    rendered_html = template.render(
        name=name,
        role=objective,
        summary=objective,
        email=email,
        phone=phone,
        location=location,
        skills=skills,
        experience=experience,
        projects=projects
    )

    # Save generated HTML
    output_file = os.path.join(output_dir, "index.html")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    return uid
