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
    published_products = product_list.loc[product_list["Published"]==1,:].reset_index(drop=True)
    with st.container():
        c = st.columns([1,4,1,1,1])
        c[0].markdown("**Picture**")
        c[1].markdown("**Product**")
        c[2].markdown("**Price**")
        c[3].markdown("**Quantity**")
        c[4].markdown("**Total**")
    for i, each in product_list.iterrows():
        with st.container():
            c = st.columns([1,4,1,1,1])
            c[0].image("https://placehold.co/64x64")
            c[1].markdown(f'''
                            {each["Name"]}\n
                            {each["Description"]}\n
                            Weight (g): {each["Weight (g)"]}\n                             
                           ''')
            c[2].markdown(f'CHF {float(each["Regular price"]):.2f}')
            quantities[each["ID"]] = c[3].number_input(label="Quantity", min_value=0, max_value=10, step=1, key=i, label_visibility="collapsed")
            c[4].markdown(f'CHF {quantities[each["ID"]] * float(each["Regular price"]):.2f}')

    total =  sum([x*y for x,y in zip(quantities.values(), product_list["Regular price"].tolist())])
    c = st.columns([1,4,1,1,1])
    c[3].markdown("**Total:**")
    c[4].markdown(f"**CHF {total:.2f}**")
    if c[1].button(label="Add to cart", type="primary"):
        st.write("Test")

except URLError as e:
    st.error(
        """
        **This demo requires internet access.**
        Connection error: %s
    """
        % e.reason)