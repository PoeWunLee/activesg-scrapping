from __future__ import annotations
import psycopg2
from contextlib import contextmanager
from psycopg2.extensions import connection
from pydantic import BaseModel
from typing import Generator, Callable
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class CnxnVariables(BaseModel):
    db_user:str
    db_pwd:str
    db_host:str
    db_port:int
    db_name:str

class DBExecutor:
    def __init__(self, cnxn_var:CnxnVariables):
        self.cnxn_var=cnxn_var

    @contextmanager
    def db_connection(self)->Generator[connection,None,None]:
        """Context manager for pyscopg2 connection with commits and rollbacks"""
        conn = None
        try:
            logger.info("Opening database connection")
            conn = psycopg2.connect(
                f"user={self.cnxn_var.db_user} \
                password={self.cnxn_var.db_pwd} \
                host={self.cnxn_var.db_host} \
                port={self.cnxn_var.db_port} \
                dbname={self.cnxn_var.db_name}"
            )
            yield conn
            conn.commit()
            logger.info("Transaction committed")
        except Exception:
            if conn:
                conn.rollback()
                logger.exception("Transaction rolled back due to error")
            raise
        finally:
            if conn:
                conn.close()
                logger.info("Database connection closed")

    def execute(self):
        """
        Decorator that injects a DB cursor and handles commit/rollback.
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                with self.db_connection() as conn:
                    with conn.cursor() as cur:
                        try:
                            logger.info(f"Executing DB operation: {func.__name__}")
                            result = func(cur, *args, **kwargs)
                            return result
                        except Exception:
                            logger.exception(f"DB operation failed: {func.__name__}")
                            raise
            return wrapper
        return decorator

class QueryExecutor(DBExecutor):
    """Class that holds all possible queries"""

    def select_all(self)->list[tuple]:
        """Selects all raw data scrapped from Postgres"""
        @self.execute()
        def _select(cur):
            cur.execute(
                """SELECT gym_name, capacity from gym_capacity """
            )
        
            return cur.fetchall()

        return _select()
    
    def copy_data(self, csv_filepath:Path|str)->None:
        """Copies current loaded data into Postgres"""
        @self.execute()
        def _copy(cur)->None:
            cols = 'gym_name, capacity, scrape_timestamp'
            with open(csv_filepath, 'r') as f:
                cur.copy_expert("COPY raw_scraped({}) FROM STDIN WITH DELIMITER ',' CSV HEADER".format(cols), f)   
        
        _copy()