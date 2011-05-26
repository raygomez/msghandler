"""DATABASE UTILITIES
  Generic functions for accessing the database.
"""

# IMPORTS START HERE ---------------------------------------------------------
# standard library imports
from os import chmod

# related third party imports

# local application/library specific imports

# CODE STARTS HERE -----------------------------------------------------------
def log_event(*args, **params):
    """Insert events into event table
    
    Required fields:
    * args[0] - database, if called from a shell script
    * user_id - user who generated the event
    * access - access privilege done. check model for accepted fields
    * table_name - table that generated the event. check model for accepted
    fields
    * item_id - row where the event was made
    * details - free text description
    """
    db = args[0]
    db.event.insert(**params)
    db.commit()