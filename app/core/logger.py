### core/logger.py
import logging
import sys
from datetime import datetime
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Log

class DatabaseHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        
    def emit(self, record):
        try:
            db = next(get_db())
            log_entry = Log(
                timestamp=datetime.utcnow(),
                employee_id=getattr(record, 'employee_id', None),
                action=getattr(record, 'action', 'system'),
                details=record.getMessage()
            )
            db.add(log_entry)
            db.commit()
            db.close()
        except Exception:
            # Fallback to console if DB logging fails
            pass

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        DatabaseHandler()
    ]
)

logger = logging.getLogger("email_campaign")

def log_action(employee_id: int, action: str, details: str):
    """Helper function to log user actions"""
    extra = {'employee_id': employee_id, 'action': action}
    logger.info(details, extra=extra)
