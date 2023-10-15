import streamlit as st
from urllib.error import URLError
import pandas as pd
from streamlit.logger import get_logger

@st.cache_data
def get_products():
    df = pd.read_csv("./data/products.csv")
    return df
quantities = {}

try:
    product_list = get_products()
    with st.container():
        c = st.columns(4)
        c[0].text("Picture")
        c[1].text("Product")
        c[2].text("Price")
        c[3].text("Quantity")
    for i, each in product_list.iterrows():
        with st.container():
            c = st.columns(5)
            c[0].image("https://placehold.co/64x64")
            c[1].text(each["name"])
            c[2].text(float(each["price"]))
            quantities[each["name"]] = c[3].number_input(label="Quantity", min_value=0, max_value=10, step=1, key=i, label_visibility="collapsed")
            c[4].text(quantities[each["name"]] * float(each["price"]))

    total =  sum([x*y for x,y in zip(quantities.values(), product_list["price"].tolist())])
    st.write(f"Total: {total}")
except URLError as e:
    st.error(
        """
        **This demo requires internet access.**
        Connection error: %s
    """
        % e.reason)