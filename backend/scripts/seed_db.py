import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from seed import seed_database

if __name__ == "__main__":
    print("Seeding QuizForge database...")
    seed_database()
    print("Database seeding completed.")
