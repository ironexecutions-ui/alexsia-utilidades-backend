import mysql.connector

config = {
    "host": "sql5.freesqldatabase.com",
    "user": "sql5807682",
    "password": "ki8p2GZan2",
    "database": "sql5807682",
    "port": 3306
}


def executar_select(query, params=None):
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        return cursor.fetchall()
    except Exception as e:
        print("Erro no SELECT:", e)
        return None
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except:
            pass


def executar_comando(query, params=None):
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        return True
    except Exception as e:
        print("Erro no comando SQL:", e)
        return False
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except:
            pass


def executar_insert(query, params=None):
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()

        return cursor.lastrowid

    except Exception as e:
        print("Erro no INSERT:", e)
        return None

    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except:
            pass
