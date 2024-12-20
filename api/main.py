from fastapi import FastAPI, HTTPException, Query
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

class FacturaUpdate(BaseModel):
    estado: str | None = None
    numero_oc: str | None = None
    comentarios: str | None = None

# Conexión a la base de datos
def get_db_connection():
    try:
        return psycopg2.connect(**DATABASE, cursor_factory=RealDictCursor)
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Error al conectar a la base de datos: {e}")

# Obtener las facturas pendientes en funcion del usuario
@app.get("/facturas/{id_usuario}")
def obtener_facturas(id_usuario: int, estado: str = "pendiente"):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = """
                SELECT * FROM facturas
                WHERE id_usuario = %s AND estado = %s
            """
            cursor.execute(query, (id_usuario, estado))
            facturas = cursor.fetchall()
        conn.close()

        if not facturas:
            return {"message": f"No hay facturas con estado '{estado}'."}
        return facturas
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {e}")

#Registrar datos en la tabla facturas
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
                RETURNING id_factura
            """
            cursor.execute(query, (factura.estado, factura.numero_oc, factura.comentarios, id_factura))
            resultado = cursor.fetchone()
            conn.commit()

        conn.close()

        if resultado is None:
            raise HTTPException(status_code=404, detail="Factura no encontrada.")
        return {"message": "Factura actualizada correctamente", "id_factura": resultado["id_factura"]}
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {e}")

#Buscar y modificar lo que recibe el trigger formulario y lo transforma para poder ser enviados a facturas nuevas
@app.get("/buscar/")
def buscar_registros(
    nombre_usuario: str = Query(...),
    nombre_proveedor: str = Query(...),
    nombre_sector: str = Query(...),
):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id_usuario FROM usuarios WHERE nombre = %s", (nombre_usuario,))
            resultado_usuario = cursor.fetchone()

            cursor.execute("SELECT id_proveedor FROM proveedores WHERE nombre = %s", (nombre_proveedor,))
            resultado_proveedor = cursor.fetchone()

            cursor.execute("SELECT id_sector FROM sectores WHERE nombre = %s", (nombre_sector,))
            resultado_sector = cursor.fetchone()

        conn.close()

        return {
            "id_usuario": resultado_usuario["id_usuario"] if resultado_usuario else None,
            "id_proveedor": resultado_proveedor["id_proveedor"] if resultado_proveedor else None,
            "id_sector": resultado_sector["id_sector"] if resultado_sector else None,
        }
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {e}")

@app.post("/facturas")
def agregar_factura(factura: dict):
    """
    Agrega una nueva factura en la base de datos.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = """
                INSERT INTO facturas (
                    numero_factura, id_usuario, id_proveedor, id_sector, estado, tipo_factura,
                    importe_neto, importe_total, moneda, numero_oc, dias_vencida, comentarios, fecha
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_factura
            """
            cursor.execute(query, (
                factura.get("Numero de Factura"),
                factura.get("id_usuario"),
                factura.get("id_proveedor"),
                factura.get("id_sector"),
                factura.get("Estado"),
                factura.get("Tipo de Factura"),
                factura.get("Importe Neto"),
                factura.get("Importe Total"),
                factura.get("Moneda"),
                factura.get("Numero de OC"),
                factura.get("Dias Vencida"),
                factura.get("Comentarios"),
                factura.get("Fecha")
            ))
            nueva_factura = cursor.fetchone()
            conn.commit()
        
        if nueva_factura:
            # Devolver el ID de la factura para confirmar
            return {"message": "Factura agregada con éxito", "id_factura": nueva_factura["id_factura"]}
        else:
            raise HTTPException(status_code=500, detail="No se pudo agregar la factura.")
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {e}")
    finally:
        if conn:
            conn.close()
