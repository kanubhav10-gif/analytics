import streamlit as st
from sqlalchemy import create_engine
from urllib.parse import quote_plus


@st.cache_resource
def get_engine():
    user = st.secrets["mysql"]["user"]
    password = quote_plus(st.secrets["mysql"]["password"])
    host = st.secrets["mysql"]["host"]
    port = st.secrets["mysql"]["port"]
    database = "northwind"

    connection_string = (
        f"mysql+pymysql://{user}:{password}"
        f"@{host}:{port}/{database}"
    )

    engine = create_engine(
        connection_string,
        pool_pre_ping=True
    )

    return engine