"""DATABASE UTILITIES
  Generic functions for accessing the database.
"""

# IMPORTS START HERE ---------------------------------------------------------
# standard library imports
from os import chmod

# related third party imports

# local application/library specific imports

# CODE STARTS HERE -----------------------------------------------------------
def log_event(db, user_id, item_id, table_name, access, details=None):
    """Insert events into event table
    
    Required fields:
    * db - database to save events
    * user_id - user who generated the event
    * access - access privilege done. check model for accepted fields
    * table_name - table that generated the event. check model for accepted
    fields
    * item_id - row where the event was made
    * details - free text description
    """
    db.event.insert(user_id=user_id, item_id=item_id, table_name=table_name,
                    access=access, details=details)
    db.commit()

my_logging = log_event
