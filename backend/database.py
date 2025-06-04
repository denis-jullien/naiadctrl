from sqlmodel import create_engine

# Database setup
DATABASE_URL = "sqlite:///./hydro_system.db"
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})