# back_end/scripts/update_schema.py
import sqlalchemy
import os
import sys

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.database import engine

print("Attempting to update the database schema...")

with engine.connect() as con:
    try:
        # Use transaction to execute the statement
        trans = con.begin()
        con.execute(sqlalchemy.text('ALTER TABLE espaces_verts ADD COLUMN cree_le DATETIME'))
        trans.commit()
        print("Column 'cree_le' added to 'espaces_verts' table successfully.")
    except sqlalchemy.exc.OperationalError as e:
        # This will happen if the column already exists.
        if "duplicate column name" in str(e).lower():
            print("Column 'cree_le' already exists in 'espaces_verts'. No action taken.")
        else:
            print(f"An unexpected operational error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

