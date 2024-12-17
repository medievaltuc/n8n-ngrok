from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuración de la conexión a PostgreSQL
DATABASE = {
    "dbname": "8nbase",
    "user": "postgres",
    "password": "root",
    "host": "postgres",
    "port": 5432
}

# Inicializar FastAPI
app = FastAPI()

# Modelo para actualizar facturas
class FacturaUpdate(BaseModel):
    estado: str = None
    numero_oc: str = None
    comentarios: str = None

# Conexión a la base de datos
def get_db_connection():
    return psycopg2.connect(
        dbname=DATABASE["dbname"],
        user=DATABASE["user"],
        password=DATABASE["password"],
        host=DATABASE["host"],
        port=DATABASE["port"],
        cursor_factory=RealDictCursor
    )

# Ruta: Obtener facturas pendientes de un usuario
@app.get("/facturas/{id_usuario}")
def obtener_facturas(id_usuario: int):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = """
                SELECT * FROM facturas
                WHERE id_usuario = %s AND estado = 'pendiente'
            """
            cursor.execute(query, (id_usuario,))
            facturas = cursor.fetchall()
        conn.close()
        #return facturas
    #except Exception as e:
        #raise HTTPException(status_code=500, detail=str(e))

# Formatear los resultados como lista de diccionarios
        columnas = [desc[0] for desc in cursor.description]
        resultado = [dict(zip(columnas, fila)) for fila in facturas]

        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Ruta: Actualizar una factura
@app.patch("/facturas/{id_factura}")
def actualizar_factura(id_factura: int, factura: FacturaUpdate):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = """
                UPDATE facturas
                SET estado = COALESCE(%s, estado),
                    numero_oc = COALESCE(%s, numero_oc),
                    comentarios = COALESCE(%s, comentarios)
                WHERE id_factura = %s
            """
            cursor.execute(query, (factura.estado, factura.numero_oc, factura.comentarios, id_factura))
            conn.commit()
        conn.close()
        return {"message": "Factura actualizada correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Ruta opcional: Agregar una factura (para rol "carga")
@app.post("/facturas")
def agregar_factura(factura: FacturaUpdate):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = """
                INSERT INTO facturas (estado, numero_oc, comentarios)
                VALUES (%s, %s, %s)
                RETURNING id_factura
            """
            cursor.execute(query, (factura.estado, factura.numero_oc, factura.comentarios))
            nueva_factura = cursor.fetchone()
            conn.commit()
        conn.close()
        return {"id_factura": nueva_factura["id_factura"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
