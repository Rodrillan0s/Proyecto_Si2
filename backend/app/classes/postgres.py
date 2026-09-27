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
                            minconn=1,
                            maxconn=20,
                            host=Config.DB_HOST,
                            port=Config.DB_PORT,
                            dbname=Config.DB_NAME,
                            user=Config.DB_USER,
                            password=Config.DB_PASSWORD,
                            connect_timeout=10,
                            keepalives=1,
                            keepalives_idle=30,
                            keepalives_interval=10,
                            keepalives_count=5
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
        p = None
        try:
            p = self.get_pool()
        except Exception as e:
            print(f"No se pudo inicializar el connection pool: {e}")

        # Intentar obtener una conexión activa del pool (hasta 3 intentos)
        if p:
            for _ in range(3):
                conn = None
                try:
                    conn = p.getconn()
                    if conn.closed:
                        p.putconn(conn, close=True)
                        continue
                    # Probar si la conexión remota no fue cerrada por inactividad
                    with conn.cursor() as test_cur:
                        test_cur.execute("SELECT 1;")
                    self.conn = conn
                    self.cur = self.conn.cursor()
                    self._from_pool = True
                    return
                except Exception:
                    if conn:
                        try:
                            p.putconn(conn, close=True)
                        except Exception:
                            pass

        # Fallback a conexión directa si el pool falla o no tiene conexiones vivas
        try:
            self.conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                connect_timeout=10,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5
            )
            self.cur = self.conn.cursor()
            self._from_pool = False
        except Exception as e2:
            print(f'ERROR DE CONEXION A LA DB: {e2}')
            raise

    def close_connection(self, commit=False):
        try:
            if self.conn:
                is_dead = (self.conn.closed != 0)
                if not is_dead:
                    try:
                        if commit:
                            self.conn.commit()
                        else:
                            self.conn.rollback()
                    except Exception:
                        is_dead = True
                
                if self.cur:
                    try:
                        self.cur.close()
                    except Exception:
                        pass
                    self.cur = None

                if self._from_pool:
                    p = self.get_pool()
                    p.putconn(self.conn, close=is_dead)
                else:
                    try:
                        self.conn.close()
                    except Exception:
                        pass

                self.conn = None
        except Exception as e:
            print(f'ERROR AL CERRAR LA CONEXION CON LA DB: {e}')
            if self.conn:
                try:
                    if self._from_pool:
                        self.get_pool().putconn(self.conn, close=True)
                    else:
                        self.conn.close()
                except Exception:
                    pass
                self.conn = None


    def execute_query(self, query, params=None, fetchall=False, fetchone=False, commit=False):
        if not self.conn or not self.cur:
            print('NO HAY UNA CONEXION ACTIVA A LA BASE DE DATOS')
            return None
        
        if fetchall and fetchone:
            print('SOLO PUEDE HACER UNA OPCION "FETCHALL" O "FETCHONE"')
            return None

        try:
            self.cur.execute(query, params)

            if commit:
                self.conn.commit()
            
            if fetchone:
                return self.cur.fetchone() if self.cur.description is not None else None
            
            if fetchall:
                return self.cur.fetchall() if self.cur.description is not None else []
            
            return self.cur.rowcount
        except Exception as e:
            if self.conn:
                try:
                    if not self.conn.closed:
                        self.conn.rollback()
                except Exception:
                    pass
            print(f'ERROR: {e}')
            raise

    #def insert_log():