"""inicio de la aplicacion"""
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
    """actualiza el caso"""
    estado: str | None = None
    numero_oc: str | None = None
    comentarios: str | None = None

# Conexión a la base de datos


def get_db_connection():
    """toma los datos de la base da datos en funcion del numero de caso"""
    try:
        return psycopg2.connect(**DATABASE, cursor_factory=RealDictCursor)
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Error al conectar a la base de datos: {e}") from e

# Obtener las facturas pendientes en funcion del usuario


@app.get("/facturas/{id_usuario}")
def obtener_facturas(id_usuario: int, estado: str = "pendiente"):
    """obtine los datos de la base de datos en funcion del numero de caso"""
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
        raise HTTPException(
            status_code=500, detail=f"Error en la base de datos: {e}") from e


# Buscar y modificar lo que recibe el trigger formulario
# y lo transforma para poder ser enviados a facturas nuevas
@app.get("/buscar/")
def buscar_registros(
    nombre_usuario: str = Query(...),
    nombre_proveedor: str = Query(...),
    nombre_sector: str = Query(...),
):
    """busca los datos en la base de datos en funcion del numero de caso"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id_usuario FROM usuarios WHERE nombre = %s", (nombre_usuario,))
            resultado_usuario = cursor.fetchone()

            cursor.execute(
                "SELECT id_proveedor FROM proveedores WHERE nombre = %s", (nombre_proveedor,))
            resultado_proveedor = cursor.fetchone()

            cursor.execute(
                "SELECT id_sector FROM sectores WHERE nombre = %s", (nombre_sector,))
            resultado_sector = cursor.fetchone()

        conn.close()

        return {
            "id_usuario": resultado_usuario["id_usuario"] if resultado_usuario else None,
            "id_proveedor": resultado_proveedor["id_proveedor"] if resultado_proveedor else None,
            "id_sector": resultado_sector["id_sector"] if resultado_sector else None,
        }
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Error en la base de datos: {e}") from e


# Agregar datos obtenidos del formulario en tabla facturas
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
                    id_factura, id_usuario, id_proveedor, id_sector, estado, tipo_factura,
                    importe_neto, importe_total, moneda, numero_oc, dias_vencida, comentarios, fecha
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_factura
            """
            cursor.execute(query, (
                factura.get("id_factura"),
                factura.get("id_usuario"),
                factura.get("id_proveedor"),
                factura.get("id_sector"),
                factura.get("estado"),  # Cambiado a minúscula
                factura.get("tipo_factura"),
                factura.get("importe_neto"),
                factura.get("importe_total"),
                factura.get("moneda"),
                factura.get("numero_oc"),
                factura.get("dias_vencida"),
                factura.get("comentarios"),
                factura.get("fecha")
            ))
            nueva_factura = cursor.fetchone()
            conn.commit()

        if nueva_factura:
            # Devolver el ID de la factura para confirmar
            return {"message":
                    "Factura agregada con éxito", "id_factura": nueva_factura["id_factura"]}
        else:
            raise HTTPException(
                status_code=500, detail="No se pudo agregar la factura.")
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Error en la base de datos: {e}") from e
    finally:
        if conn:
            conn.close()


# Obtener una factura específica por número de factura
@app.get("/facturas/numero/{id_factura}")
def obtener_factura_por_numero(id_factura: int):
    """
    Obtiene los datos de una factura específica para mostrarlos al usuario.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = "SELECT * FROM facturas WHERE id_factura = %s"
            cursor.execute(query, (id_factura,))
            factura = cursor.fetchone()
        conn.close()

        if factura is None:
            raise HTTPException(
                status_code=404, detail="Factura no encontrada.")

        return factura
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Error en la base de datos: {e}") from e

# Actualizar datos de una factura existente


@app.patch("/facturas/numero/{id_factura}")
def actualizar_factura(id_factura: int, factura: FacturaUpdate):
    """
    Actualiza los datos de una factura existente en la base de datos.
    """
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
            cursor.execute(query, (
                factura.estado or "completado",  # Si no se envía, marcar como "completado"
                factura.numero_oc,
                factura.comentarios,
                id_factura
            ))
            resultado = cursor.fetchone()
            conn.commit()

        if resultado is None:
            raise HTTPException(
                status_code=404, detail="Factura no encontrada.")

        # Mensaje de éxito
        return {"message":
            "Factura actualizada correctamente", "id_factura": resultado["id_factura"]}
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Error en la base de datos: {e}") from e
    finally:
        if conn:
            conn.close()
