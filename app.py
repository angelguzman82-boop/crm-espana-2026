import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime

st.set_page_config(page_title="CRM España 2026", layout="wide")

# ================= DATABASE =================
conn = sqlite3.connect("crm_espana.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    nombre TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT,
    comercial TEXT,
    email TEXT,
    telefono TEXT,
    estado TEXT,
    ultima_compra TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT,
    comercial TEXT,
    fecha TEXT,
    volumen REAL,
    estado TEXT
)
""")

conn.commit()

# Crear admin automático
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

c.execute("SELECT * FROM usuarios WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO usuarios (username,password,nombre) VALUES (?,?,?)",
              ("admin", hash_password("admin123"), "Administrador"))
    conn.commit()

# ================= LOGIN =================

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:

    st.title("Login CRM España 2026")

    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):
        c.execute("SELECT * FROM usuarios WHERE username=? AND password=?",
                  (u, hash_password(p)))
        user = c.fetchone()
        if user:
            st.session_state.user = user[3]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

else:

    user = st.session_state.user
    st.sidebar.write(f"👤 {user}")

    if st.sidebar.button("Cerrar sesión"):
        st.session_state.user = None
        st.rerun()

    st.title("CRM Comercial España 2026")

    df_clientes = pd.read_sql_query("SELECT * FROM clientes", conn)
    df_ventas = pd.read_sql_query("SELECT * FROM ventas", conn)

    col1,col2,col3 = st.columns(3)

    col1.metric("Total clientes", len(df_clientes))
    col2.metric("Ventas entregadas",
                df_ventas[df_ventas["estado"]=="Entregado"]["volumen"].sum())
    col3.metric("Backlog",
                df_ventas[df_ventas["estado"]=="Backlog"]["volumen"].sum())

    st.divider()

    st.subheader("Importar ventas")

    archivo = st.file_uploader("Subir Excel ventas", type=["xlsx","csv"])

    if archivo:
        if archivo.name.endswith("xlsx"):
            df = pd.read_excel(archivo)
        else:
            df = pd.read_csv(archivo)

        df.columns = df.columns.str.strip()

        for _,row in df.iterrows():

            cliente = row["Cliente"]
            comercial = row["Sales"]
            fecha = pd.to_datetime(row["Fecha"])
            volumen = float(row["Volumen"])
            estado = row["Estado"]

            c.execute("INSERT INTO ventas (cliente,comercial,fecha,volumen,estado) VALUES (?,?,?,?,?)",
                      (cliente,comercial,fecha,volumen,estado))

            c.execute("SELECT * FROM clientes WHERE cliente=?",(cliente,))
            if not c.fetchone():
                c.execute("INSERT INTO clientes (cliente,comercial,email,telefono,estado,ultima_compra) VALUES (?,?,?,?,?,?)",
                          (cliente,comercial,"","","Pendiente",fecha))

        conn.commit()
        st.success("Ventas importadas correctamente")
        st.rerun()

    st.divider()

    st.subheader("Clientes")
    st.dataframe(df_clientes, use_container_width=True)

    st.subheader("Ventas")
    st.dataframe(df_ventas, use_container_width=True)
