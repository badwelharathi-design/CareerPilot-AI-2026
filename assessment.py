# assessment.py

from typing import Dict, List


# Skills used by CareerPilot-AI
ASSESSMENT_SKILLS = [
    "Programming",
    "Data Structures",
    "OOP",
    "DBMS",
    "Git",
    "Problem Solving",
    "HTML",
    "CSS",
    "JavaScript",
    "React",
    "Excel",
    "SQL",
    "Statistics",
    "Power BI",
    "Python",
    "Data Visualization",
    "Machine Learning",
    "Pandas",
    "ETL",
    "Databases",
    "Cloud",
    "Apache Spark",
    "Deep Learning",
    "TensorFlow",
    "PyTorch",
    "Mathematics",
    "Networking",
    "Linux",
    "Cybersecurity",
    "Cryptography",
    "Ethical Hacking",
    "Security Tools",
    "AWS",
    "Azure",
    "Docker",
    "Cloud Computing",
    "Kubernetes",
    "CI/CD",
    "Business Analysis",
    "Communication",
    "Figma",
    "UI Design",
    "UX Research",
    "Prototyping",
    "Graphic Design",
    "Database Administration",
    "Backup and Recovery",
    "Database Security"
]


def validate_skill_level(level):
    """Keep skill level between 0 and 100."""
    try:
        level = float(level)
    except (TypeError, ValueError):
        return 0

    return max(0, min(100, level))


def create_assessment(skill_levels: Dict[str, float]):
    """
    Convert user's assessment answers into
    normalized skill data.

    Example:
        {
            "Python": 80,
            "SQL": 70,
            "Excel": 90
        }
    """
    assessment = {}
    for skill in ASSESSMENT_SKILLS:
        assessment[skill] = validate_skill_level(skill_levels.get(skill, 0))
    return assessment