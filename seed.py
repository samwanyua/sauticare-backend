from api.db.database import SessionLocal, engine, Base
from api.db import models
from api.utils.security import hash_password

# Ensure tables exist in Supabase
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# --- Seed Users ---
users = [
    {"name": "Sam Wanyua", "email": "sam@example.com", "password": "password123"},
    {"name": "Jane Doe", "email": "jane@example.com", "password": "password456"},
]

for u in users:
    existing_user = db.query(models.User).filter_by(email=u["email"]).first()
    if not existing_user:
        new_user = models.User(
            name=u["name"],
            email=u["email"],
            hashed_password=hash_password(u["password"][:72])  
        )
        db.add(new_user)


# --- Seed Lessons ---
easy_lessons = [
    "I wash my hands",
    "I drink water",
    "I eat fruits",
    "I brush my teeth",
    "I eat vegetables",
    "I cover my mouth when coughing",
    "I wear clean clothes",
    "I comb my hair",
    "I use soap",
    "I sleep early",
    "I eat breakfast",
    "I wash fruits before eating",
    "I drink milk",
    "I wash utensils",
    "I clean my room",
    "I wash my face",
    "I cover food",
    "I drink clean water",
    "I wash hands before meals",
    "I eat healthy snacks"
]

medium_lessons = [
    "I avoid eating junk food",
    "I eat three meals a day",
    "I practice hand hygiene regularly",
    "I wash fruits and vegetables before eating",
    "I brush teeth twice a day",
    "I exercise daily",
    "I eat balanced meals",
    "I follow safe food handling",
    "I avoid touching my face with dirty hands",
    "I use clean utensils",
    "I store food safely",
    "I eat seasonal fruits",
    "I wash cooking utensils after use",
    "I avoid sharing towels",
    "I cover my nose when sneezing",
    "I maintain clean nails",
    "I drink water frequently",
    "I eat fiber-rich foods",
    "I avoid sugary drinks",
    "I avoid cross-contamination when cooking"
]

hard_lessons = [
    "I ensure proper sanitation in the kitchen",
    "I practice food hygiene to prevent illness",
    "I follow handwashing protocols before cooking",
    "I maintain personal hygiene daily",
    "I teach younger siblings about hygiene",
    "I monitor my diet for balanced nutrition",
    "I reduce consumption of processed foods",
    "I separate raw and cooked food to avoid contamination",
    "I follow safe water practices at home",
    "I dispose of waste properly",
    "I read food labels for nutritional content",
    "I practice good oral hygiene consistently",
    "I maintain hygiene during outdoor activities",
    "I encourage friends to follow hygiene habits",
    "I identify clean and safe drinking water",
    "I implement hygiene routines at school",
    "I prepare meals safely",
    "I avoid foodborne illnesses through hygiene",
    "I practice healthy eating habits",
    "I maintain overall cleanliness and health awareness"
]


def add_lessons(level, lesson_list):
    for i, phrase in enumerate(lesson_list, start=1):
        lesson_id = f"{level.lower()}{i}"
        exists = db.query(models.Lesson).filter_by(id=lesson_id).first()
        if not exists:
            new_lesson = models.Lesson(
                id=lesson_id,
                level=level,
                phrase=phrase
            )
            db.add(new_lesson)


add_lessons("Easy", easy_lessons)
add_lessons("Medium", medium_lessons)
add_lessons("Hard", hard_lessons)

db.commit()
db.close()

print(" Seeding completed successfully — data stored in Supabase Postgres!")
