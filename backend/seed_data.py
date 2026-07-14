"""
Seed data script for the AI-CRM HCP Module.

Populates the database with realistic sample HCPs, Products, and Interactions
for development and demonstration purposes. Safe to re-run — skips seeding
if data already exists.
"""

from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from models import HCP, Interaction, Product
from database import get_db_session


SAMPLE_HCPS = [
    {
        "name": "Dr. Sarah Chen",
        "specialty": "Cardiology",
        "institution": "Massachusetts General Hospital",
        "email": "s.chen@mgh.harvard.edu",
        "phone": "+1-617-555-0101",
        "territory": "Northeast",
        "tier": "KOL",
        "notes": "Key opinion leader in heart failure management. Frequent conference speaker.",
        "npi_number": "1234567890",
        "city": "Boston",
        "state": "Massachusetts",
    },
    {
        "name": "Dr. James Rodriguez",
        "specialty": "Oncology",
        "institution": "MD Anderson Cancer Center",
        "email": "j.rodriguez@mdanderson.org",
        "phone": "+1-713-555-0202",
        "territory": "South",
        "tier": "KOL",
        "notes": "Leading researcher in immunotherapy. Published 50+ papers on checkpoint inhibitors.",
        "npi_number": "2345678901",
        "city": "Houston",
        "state": "Texas",
    },
    {
        "name": "Dr. Emily Watson",
        "specialty": "Endocrinology",
        "institution": "Cleveland Clinic",
        "email": "e.watson@ccf.org",
        "phone": "+1-216-555-0303",
        "territory": "Midwest",
        "tier": "High",
        "notes": "Specialises in Type 2 diabetes and obesity management. Active on clinical trials.",
        "npi_number": "3456789012",
        "city": "Cleveland",
        "state": "Ohio",
    },
    {
        "name": "Dr. Michael Okafor",
        "specialty": "Neurology",
        "institution": "Johns Hopkins Hospital",
        "email": "m.okafor@jhmi.edu",
        "phone": "+1-410-555-0404",
        "territory": "Mid-Atlantic",
        "tier": "High",
        "notes": "Focus on multiple sclerosis and neuroimmunology. Advisory board member.",
        "npi_number": "4567890123",
        "city": "Baltimore",
        "state": "Maryland",
    },
    {
        "name": "Dr. Priya Patel",
        "specialty": "Rheumatology",
        "institution": "Stanford Health Care",
        "email": "p.patel@stanford.edu",
        "phone": "+1-650-555-0505",
        "territory": "West",
        "tier": "Medium",
        "notes": "Interested in biologic therapies for rheumatoid arthritis.",
        "npi_number": "5678901234",
        "city": "Palo Alto",
        "state": "California",
    },
    {
        "name": "Dr. David Kim",
        "specialty": "Pulmonology",
        "institution": "Mayo Clinic",
        "email": "d.kim@mayo.edu",
        "phone": "+1-507-555-0606",
        "territory": "Midwest",
        "tier": "Medium",
        "notes": "COPD specialist. Involved in pulmonary rehab program development.",
        "npi_number": "6789012345",
        "city": "Rochester",
        "state": "Minnesota",
    },
    {
        "name": "Dr. Lisa Nakamura",
        "specialty": "Dermatology",
        "institution": "NYU Langone Health",
        "email": "l.nakamura@nyulangone.org",
        "phone": "+1-212-555-0707",
        "territory": "Northeast",
        "tier": "Medium",
        "notes": "Psoriasis expert. Open to new biologic treatment options.",
        "npi_number": "7890123456",
        "city": "New York",
        "state": "New York",
    },
    {
        "name": "Dr. Robert Thompson",
        "specialty": "Gastroenterology",
        "institution": "Cedars-Sinai Medical Center",
        "email": "r.thompson@csmc.edu",
        "phone": "+1-310-555-0808",
        "territory": "West",
        "tier": "Low",
        "notes": "General GI practice. Potential for IBD product discussions.",
        "npi_number": "8901234567",
        "city": "Los Angeles",
        "state": "California",
    },
    {
        "name": "Dr. Angela Müller",
        "specialty": "Hematology",
        "institution": "Dana-Farber Cancer Institute",
        "email": "a.muller@dfci.harvard.edu",
        "phone": "+1-617-555-0909",
        "territory": "Northeast",
        "tier": "High",
        "notes": "Expert in CAR-T cell therapy. Strong advocate for novel treatment paradigms.",
        "npi_number": "9012345678",
        "city": "Boston",
        "state": "Massachusetts",
    },
    {
        "name": "Dr. Carlos Mendez",
        "specialty": "Cardiology",
        "institution": "Mount Sinai Hospital",
        "email": "c.mendez@mountsinai.org",
        "phone": "+1-212-555-1010",
        "territory": "Northeast",
        "tier": "Low",
        "notes": "Community cardiologist. Mainly uses generic statins.",
        "npi_number": "0123456789",
        "city": "New York",
        "state": "New York",
    },
]

SAMPLE_PRODUCTS = [
    {
        "name": "CardioMax XR",
        "therapeutic_area": "Cardiovascular",
        "description": "Extended-release formulation for chronic heart failure management. Reduces hospitalisation and improves LVEF.",
        "key_messages": [
            "35% reduction in heart failure hospitalisations vs placebo",
            "Once-daily dosing improves patient adherence",
            "Demonstrated safety in elderly patients (>75 years)",
            "Complementary mechanism to standard-of-care RAAS inhibitors",
        ],
        "status": "active",
    },
    {
        "name": "OncoShield",
        "therapeutic_area": "Oncology",
        "description": "Next-generation PD-L1 checkpoint inhibitor with enhanced tumour penetration for solid tumours.",
        "key_messages": [
            "Improved overall survival in NSCLC first-line setting",
            "Favourable safety profile with lower immune-related AE rate",
            "Companion diagnostic available for patient selection",
            "Approved across 5 solid tumour indications",
        ],
        "status": "active",
    },
    {
        "name": "GlucoBalance Pro",
        "therapeutic_area": "Endocrinology",
        "description": "Dual GIP/GLP-1 receptor agonist for Type 2 diabetes with significant weight loss benefit.",
        "key_messages": [
            "Superior HbA1c reduction vs existing GLP-1 RAs",
            "Average 15% body weight reduction in clinical trials",
            "Cardiovascular outcome benefit demonstrated",
            "Weekly subcutaneous injection for convenience",
        ],
        "status": "active",
    },
    {
        "name": "NeuroGuard",
        "therapeutic_area": "Neurology",
        "description": "Anti-CD20 monoclonal antibody for relapsing forms of multiple sclerosis.",
        "key_messages": [
            "Near-complete suppression of new brain lesions",
            "Convenient 6-month IV infusion schedule",
            "Strong long-term safety data (8+ years)",
            "Significant reduction in disability progression",
        ],
        "status": "active",
    },
    {
        "name": "ImmunoFlex",
        "therapeutic_area": "Rheumatology / Dermatology",
        "description": "Selective JAK1 inhibitor for moderate-to-severe rheumatoid arthritis and psoriasis.",
        "key_messages": [
            "Oral alternative to biologic injections",
            "Rapid onset of action within 2 weeks",
            "Dual indication: RA and psoriasis",
            "No requirement for concomitant methotrexate",
        ],
        "status": "pipeline",
    },
]

NOW = datetime.now(timezone.utc)

SAMPLE_INTERACTIONS = [
    {
        "hcp_id": 1,
        "interaction_type": "visit",
        "date": NOW - timedelta(days=5),
        "duration_minutes": 30,
        "summary": "Discussed CardioMax XR phase IV real-world data. Dr. Chen expressed interest in the elderly subgroup analysis.",
        "key_topics": ["heart failure", "real-world evidence", "elderly patients"],
        "products_discussed": ["CardioMax XR"],
        "sentiment": "positive",
        "follow_up_required": True,
        "follow_up_date": NOW + timedelta(days=10),
        "follow_up_notes": "Send elderly subgroup analysis publication. Schedule follow-up call.",
        "logged_by": "Rep: John Miller",
        "raw_notes": "Met with Dr. Chen at MGH. She was very receptive to the new RWE data for CardioMax XR. Particularly keen on data in patients over 75. Wants the publication. Should follow up in 2 weeks.",
        "ai_summary": "Productive in-person visit with KOL Dr. Chen at MGH. Strong interest in CardioMax XR real-world evidence, especially elderly subgroup (>75 years). Action: send publication and schedule follow-up within 2 weeks.",
    },
    {
        "hcp_id": 2,
        "interaction_type": "conference",
        "date": NOW - timedelta(days=15),
        "duration_minutes": 45,
        "summary": "Engaged Dr. Rodriguez at ASCO booth. Discussed OncoShield data in NSCLC and upcoming combination trials.",
        "key_topics": ["NSCLC", "immunotherapy", "combination therapy", "clinical trials"],
        "products_discussed": ["OncoShield"],
        "sentiment": "positive",
        "follow_up_required": True,
        "follow_up_date": NOW + timedelta(days=5),
        "follow_up_notes": "Share combination trial protocol synopsis. Discuss advisory board invitation.",
        "logged_by": "Rep: Maria Santos",
        "raw_notes": "Spoke with Dr. Rodriguez at ASCO. He presented his latest data on checkpoint combinations. Very interested in our OncoShield combo trials. Mentioned he'd consider an advisory board role.",
        "ai_summary": "Met Dr. Rodriguez at ASCO conference. He is enthusiastic about OncoShield combination trial programme. Potential advisory board candidate. Action: share protocol synopsis and extend advisory board invitation.",
    },
    {
        "hcp_id": 3,
        "interaction_type": "call",
        "date": NOW - timedelta(days=3),
        "duration_minutes": 20,
        "summary": "Phone call with Dr. Watson about GlucoBalance Pro formulary inclusion at Cleveland Clinic.",
        "key_topics": ["formulary", "Type 2 diabetes", "payer access", "weight loss"],
        "products_discussed": ["GlucoBalance Pro"],
        "sentiment": "neutral",
        "follow_up_required": True,
        "follow_up_date": NOW + timedelta(days=14),
        "follow_up_notes": "Provide health-economic dossier for P&T committee review.",
        "logged_by": "Rep: John Miller",
        "raw_notes": "Called Dr. Watson. She's pushing for GlucoBalance Pro on the Cleveland Clinic formulary but P&T committee needs more economic data. Requested health-econ dossier.",
        "ai_summary": "Dr. Watson is championing GlucoBalance Pro for Cleveland Clinic formulary. P&T committee requires health-economic evidence. Action: deliver dossier before next committee meeting.",
    },
    {
        "hcp_id": 4,
        "interaction_type": "virtual",
        "date": NOW - timedelta(days=8),
        "duration_minutes": 35,
        "summary": "Virtual meeting with Dr. Okafor on NeuroGuard long-term safety data and patient switching from oral DMTs.",
        "key_topics": ["multiple sclerosis", "long-term safety", "treatment switching", "DMT"],
        "products_discussed": ["NeuroGuard"],
        "sentiment": "positive",
        "follow_up_required": False,
        "follow_up_date": None,
        "follow_up_notes": None,
        "logged_by": "Rep: Sarah Lee",
        "raw_notes": "Virtual meeting with Dr. Okafor. He's already prescribing NeuroGuard and happy with outcomes. Wanted to see long-term safety data beyond 5 years. I shared the 8-year extension study.",
        "ai_summary": "Dr. Okafor is a satisfied NeuroGuard prescriber. Reviewed 8-year extension study safety data. No immediate follow-up required; maintain relationship through periodic check-ins.",
    },
    {
        "hcp_id": 5,
        "interaction_type": "email",
        "date": NOW - timedelta(days=12),
        "duration_minutes": 5,
        "summary": "Emailed Dr. Patel about ImmunoFlex pipeline update and upcoming Phase III readout.",
        "key_topics": ["JAK inhibitor", "rheumatoid arthritis", "pipeline", "Phase III"],
        "products_discussed": ["ImmunoFlex"],
        "sentiment": "neutral",
        "follow_up_required": True,
        "follow_up_date": NOW + timedelta(days=30),
        "follow_up_notes": "Follow up after Phase III data release expected next month.",
        "logged_by": "Rep: Maria Santos",
        "raw_notes": "Sent email update to Dr. Patel re: ImmunoFlex Phase III timeline. She replied acknowledging receipt and said she's watching the data closely.",
        "ai_summary": "Email exchange with Dr. Patel regarding ImmunoFlex Phase III timeline. She is monitoring the data readout closely. Action: follow up after Phase III results are published.",
    },
    {
        "hcp_id": 1,
        "interaction_type": "call",
        "date": NOW - timedelta(days=30),
        "duration_minutes": 15,
        "summary": "Introductory call with Dr. Chen about CardioMax XR clinical trial programme.",
        "key_topics": ["clinical trials", "heart failure", "introduction"],
        "products_discussed": ["CardioMax XR"],
        "sentiment": "positive",
        "follow_up_required": True,
        "follow_up_date": NOW - timedelta(days=10),
        "follow_up_notes": "Schedule in-person visit at MGH.",
        "logged_by": "Rep: John Miller",
        "raw_notes": "First call with Dr. Chen. She knows about CardioMax XR from literature. Very interested in discussing further. Set up in-person visit.",
        "ai_summary": "Initial outreach to KOL Dr. Chen was very well received. She has existing awareness of CardioMax XR from publications. Strong engagement potential. Action: arrange in-person visit at MGH.",
    },
    {
        "hcp_id": 6,
        "interaction_type": "visit",
        "date": NOW - timedelta(days=20),
        "duration_minutes": 25,
        "summary": "Visited Dr. Kim at Mayo Clinic to discuss COPD management and potential role of CardioMax XR in patients with cardiac comorbidities.",
        "key_topics": ["COPD", "cardiac comorbidities", "comorbidity management"],
        "products_discussed": ["CardioMax XR"],
        "sentiment": "neutral",
        "follow_up_required": True,
        "follow_up_date": NOW + timedelta(days=7),
        "follow_up_notes": "Send COPD-HF comorbidity data. Coordinate with cardiology team.",
        "logged_by": "Rep: John Miller",
        "raw_notes": "Visited Dr. Kim. He sees a lot of COPD patients with heart failure. Interested in how CardioMax XR fits into their management. Wants comorbidity data.",
        "ai_summary": "Dr. Kim sees an overlap population of COPD and HF patients at Mayo Clinic. Interest in CardioMax XR for cardiac comorbidity management. Action: provide relevant comorbidity evidence.",
    },
    {
        "hcp_id": 9,
        "interaction_type": "virtual",
        "date": NOW - timedelta(days=2),
        "duration_minutes": 40,
        "summary": "Virtual meeting with Dr. Müller about OncoShield use in hematologic malignancies and CAR-T sequencing strategies.",
        "key_topics": ["CAR-T", "hematologic malignancies", "treatment sequencing", "immunotherapy"],
        "products_discussed": ["OncoShield"],
        "sentiment": "positive",
        "follow_up_required": True,
        "follow_up_date": NOW + timedelta(days=21),
        "follow_up_notes": "Share pre-clinical data on OncoShield + CAR-T sequencing. Discuss speaker engagement.",
        "logged_by": "Rep: Sarah Lee",
        "raw_notes": "Great virtual meeting with Dr. Müller. She is very interested in how OncoShield might be sequenced with CAR-T. Shared some preliminary ideas. She could be a great speaker for our hem-onc symposium.",
        "ai_summary": "Highly engaged meeting with Dr. Müller on OncoShield sequencing with CAR-T therapy. Strong speaker engagement potential for hem-onc symposium. Action: share pre-clinical sequencing data and explore speaker role.",
    },
]


def seed_database(db: Session) -> dict:
    """
    Populate the database with sample data if the tables are empty.

    This function is idempotent: it only inserts data when no HCPs,
    Products, or Interactions exist yet.

    Args:
        db: An active SQLAlchemy session.

    Returns:
        A dict summarising how many records were created for each table.
    """
    result = {"hcps": 0, "products": 0, "interactions": 0}

    # Seed HCPs
    if db.query(HCP).count() == 0:
        for hcp_data in SAMPLE_HCPS:
            db.add(HCP(**hcp_data))
        db.commit()
        result["hcps"] = len(SAMPLE_HCPS)

    # Seed Products
    if db.query(Product).count() == 0:
        for product_data in SAMPLE_PRODUCTS:
            db.add(Product(**product_data))
        db.commit()
        result["products"] = len(SAMPLE_PRODUCTS)

    # Seed Interactions
    if db.query(Interaction).count() == 0:
        for interaction_data in SAMPLE_INTERACTIONS:
            db.add(Interaction(**interaction_data))
        db.commit()
        result["interactions"] = len(SAMPLE_INTERACTIONS)

    return result


if __name__ == "__main__":
    from database import engine, Base

    Base.metadata.create_all(bind=engine)
    session = get_db_session()
    try:
        counts = seed_database(session)
        print(f"Seeding complete: {counts}")
    finally:
        session.close()
