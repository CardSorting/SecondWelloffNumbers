import sqlite3
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_NAME = 'database.db'

def get_db_connection():
    """
    Create and return a database connection.
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def execute_query(conn, query, params=None):
    """
    Execute a SQL query with error handling.
    """
    try:
        c = conn.cursor()
        if params:
            c.execute(query, params)
        else:
            c.execute(query)
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Error executing query: {e}")
        conn.rollback()
        raise

def create_users_table(conn):
    """
    Create the users table.
    """
    query = '''
    CREATE TABLE IF NOT EXISTS users (
        shopify_shop TEXT PRIMARY KEY,
        access_token TEXT,
        charge_id TEXT,
        plan_name TEXT
    )
    '''
    execute_query(conn, query)
    logger.info("Users table created or already exists.")

def create_orders_table(conn):
    """
    Create the orders table.
    """
    query = '''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shopify_order_id TEXT UNIQUE,
        shopify_shop TEXT,
        status TEXT,
        details TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shopify_shop) REFERENCES users(shopify_shop)
    )
    '''
    execute_query(conn, query)
    logger.info("Orders table created or already exists.")

def create_notifications_table(conn):
    """
    Create the notifications table.
    """
    query = '''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shopify_shop TEXT,
        message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shopify_shop) REFERENCES users(shopify_shop)
    )
    '''
    execute_query(conn, query)
    logger.info("Notifications table created or already exists.")

def create_projects_table(conn):
    """
    Create the projects table.
    """
    query = '''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shopify_shop TEXT,
        image TEXT,
        attributes TEXT,
        applied_attribute TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shopify_shop) REFERENCES users(shopify_shop)
    )
    '''
    execute_query(conn, query)
    logger.info("Projects table created or already exists.")

def create_tables():
    """
    Create all necessary tables in the database.
    """
    conn = get_db_connection()
    try:
        create_users_table(conn)
        create_orders_table(conn)
        create_notifications_table(conn)
        create_projects_table(conn)
        logger.info("All tables created successfully.")
    except sqlite3.Error as e:
        logger.error(f"Error creating tables: {e}")
    finally:
        conn.close()

def initialize_database():
    """
    Initialize the database by creating all necessary tables.
    """
    logger.info("Initializing database...")
    create_tables()
    logger.info("Database initialization completed.")

def update_project(project_id, data):
    """
    Update a project in the database.
    """
    conn = get_db_connection()
    try:
        query = '''
        UPDATE projects
        SET image = ?, attributes = ?, applied_attribute = ?, updated_at = ?
        WHERE id = ?
        '''
        execute_query(conn, query, (
            data.get('image'),
            json.dumps(data.get('attributes')),
            data.get('appliedAttribute'),
            datetime.now().isoformat(),
            project_id
        ))
        logger.info(f"Project {project_id} updated successfully.")
    except sqlite3.Error as e:
        logger.error(f"Error updating project: {e}")
    finally:
        conn.close()

def get_project(project_id):
    """
    Retrieve a project from the database.
    """
    conn = get_db_connection()
    try:
        query = "SELECT * FROM projects WHERE id = ?"
        c = conn.cursor()
        c.execute(query, (project_id,))
        project = c.fetchone()
        if project:
            return {
                'id': project['id'],
                'shopify_shop': project['shopify_shop'],
                'image': project['image'],
                'attributes': json.loads(project['attributes']),
                'appliedAttribute': project['applied_attribute'],
                'created_at': project['created_at'],
                'updated_at': project['updated_at']
            }
        else:
            logger.warning(f"Project {project_id} not found.")
            return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving project: {e}")
    finally:
        conn.close()

def save_project(project_id, shopify_shop, image, attributes, applied_attribute):
    """
    Save or update a project in the database.
    """
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        existing_project = c.fetchone()

        if existing_project:
            query = '''
                UPDATE projects
                SET image = ?, attributes = ?, applied_attribute = ?, updated_at = ?
                WHERE id = ?
            '''
            params = (image, json.dumps(attributes), applied_attribute, datetime.now().isoformat(), project_id)
        else:
            query = '''
                INSERT INTO projects (shopify_shop, image, attributes, applied_attribute)
                VALUES (?, ?, ?, ?, ?)
            '''
            params = (shopify_shop, image, json.dumps(attributes), applied_attribute)

        execute_query(conn, query, params)
        logger.info(f"Project {project_id} saved successfully.")
    except sqlite3.Error as e:
        logger.error(f"Error saving project: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    initialize_database()