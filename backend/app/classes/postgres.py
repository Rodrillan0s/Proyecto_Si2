from app.config import Config
import psycopg2
from psycopg2 import pool
import threading

class PostgreSQL():
    _pool = None
    _lock = threading.Lock()

    @classmethod
    def get_pool(cls):
        if cls._pool is None:
            with cls._lock:
                if cls._pool is None:
                    try:
                        cls._pool = pool.ThreadedConnectionPool(
                            minconn=2,
                            maxconn=20,
                            host=Config.DB_HOST,
                            port=Config.DB_PORT,
                            dbname=Config.DB_NAME,
                            user=Config.DB_USER,
                            password=Config.DB_PASSWORD
                        )
                    except Exception as e:
                        print(f"ERROR AL CREAR CONNECTION POOL: {e}")
                        raise
        return cls._pool

    def __init__(self):
        self.db_host = Config.DB_HOST
        self.db_port = Config.DB_PORT
        self.db_name = Config.DB_NAME
        self.db_user = Config.DB_USER
        self.db_password = Config.DB_PASSWORD
        self.conn = None
        self.cur = None
        self._from_pool = False

    def create_connection(self):
        try:
            p = self.get_pool()
            self.conn = p.getconn()
            if self.conn.closed:
                p.putconn(self.conn, close=True)
                self.conn = p.getconn()
            self.cur = self.conn.cursor()
            self._from_pool = True
        except Exception as e:
            try:
                self.conn = psycopg2.connect(
                    host=self.db_host,
                    port=self.db_port,
                    dbname=self.db_name,
                    user=self.db_user,
                    password=self.db_password
                )
                self.cur = self.conn.cursor()
                self._from_pool = False
            except Exception as e2:
                print(f'ERROR DE CONEXION A LA DB: {e2}')

    def close_connection(self, commit=False):
        try:
            if self.conn:
                if commit:
                    self.conn.commit()
                else:
                    try:
                        self.conn.rollback()
                    except Exception:
                        pass
                
                if self.cur:
                    try:
                        self.cur.close()
                    except Exception:
                        pass
                    self.cur = None

                if self._from_pool:
                    p = self.get_pool()
                    p.putconn(self.conn)
                else:
                    self.conn.close()

                self.conn = None
        except Exception as e:
            print(f'ERROR AL CERRAR LA CONEXION CON LA DB: {e}')
            if self.conn:
                try:
                    self.conn.close()
                except Exception:
                    pass
                self.conn = None


    def execute_query(self,query,params=None,fetchall=False,fetchone=False,commit=False):
        if not self.conn or not self.cur:
            print('NO HAY UNA CONEXION ACTIVA A LA BASE DE DATOS')
            return
        
        if fetchall and fetchone:
            print('SOLO PUEDE HACER UNA OPCION "FETCHALL" O "FETCHONE"')
            return

        try:
            self.cur.execute(query,params)

            if commit:
                self.conn.commit()
            
            if fetchone:
                return self.cur.fetchone() if self.cur.description is not None else None
            
            if fetchall:
                return self.cur.fetchall() if self.cur.description is not None else []
            
            return self.cur.rowcount
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print(f'ERROR: {e}, EJECUTANDO ROLLBACK')
            raise

    #def insert_log():