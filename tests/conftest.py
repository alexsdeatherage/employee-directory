import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base, get_db
import app.main as main_module
from app.main import app


@pytest.fixture()
def db_session():
	engine = create_engine(
		"sqlite://",
		connect_args={"check_same_thread": False},
		poolclass=StaticPool,
	)
	TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
	Base.metadata.create_all(bind=engine)

	session = TestingSessionLocal()
	try:
		yield session
	finally:
		session.close()
		Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
	def override_get_db():
		yield db_session

	app.dependency_overrides[get_db] = override_get_db
	original_init_db = main_module.init_db
	main_module.init_db = lambda: None
	with TestClient(app) as test_client:
		yield test_client
	main_module.init_db = original_init_db
	app.dependency_overrides.clear()
