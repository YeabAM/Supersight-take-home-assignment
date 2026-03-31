from database.config import get_engine
from database.models import Device
from sqlalchemy.orm import Session


def get_all_devices():
    engine = get_engine()
    with Session(engine) as session:
        devices = session.query(Device).all()
        return devices