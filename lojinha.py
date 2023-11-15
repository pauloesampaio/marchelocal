import streamlit as st
import pandas as pd
from utils.site_utils import publish_list, publish_panier, get_delivery_options, get_client_info, save_document_in_db, send_email_to_farmer
import datetime
from streamlit_extras.switch_page_button import switch_page

steps = {
    "kg": [0, 0.5] + list(range(1, 11, 1)),
    "unité": list(range(0, 11, 1)),
    "gr": list(range(0, 1100, 100)) + [1500, 2000],
    "botte": list(range(0, 11, 1)),
    "pièce": list(range(0, 11, 1)),
    "paquet": list(range(0, 11, 1)),
    "portion": list(range(0, 11, 1)),
}


hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

@st.cache_data
def get_products():
    df = pd.read_csv("./data/products.csv")
    return df

product_list = get_products()

published_products = product_list.loc[product_list["Published"]==1,:].reset_index(drop=True)
published_products["Steps"] = published_products["Mesure"].map(steps)

quantities = publish_list(published_products)   

## Panier
with st.container():
    order_df = publish_panier(published_products, quantities)
    
with st.form("panier"):

    ## Delivery info
    with st.container():
        delivery_dict = get_delivery_options()

    ## Client info
    with st.container():
        st.markdown(f"### Coordonnées du client")
        client_dict = get_client_info()
    
    st.markdown("Il ne vous reste plus qu'à cliquer sur le bouton ci-dessous et votre commande sera transmise à notre vendeur local qui s'occupera de votre livraison. Le paiement sera effectué à la livraison directement en espèces ou en Twint ou après la livraison par Twint.")        
    submitted = st.form_submit_button("Envoyez ma commande!", type="primary")

    if submitted:
        timestamp = datetime.datetime.now()
        #save_document_in_db(timestamp, order_df, client_dict, delivery_dict)
        send_email_to_farmer(timestamp, order_df, client_dict, delivery_dict)
        st.balloons()
        switch_page("success")
