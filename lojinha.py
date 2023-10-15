import streamlit as st
from urllib.error import URLError
import pandas as pd
from streamlit.logger import get_logger
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

st.set_page_config(layout="wide")
columns_proportion = [5,40,20,10,5,20]

@st.cache_data
def get_products():
    df = pd.read_csv("./data/products.csv")
    return df
quantities = {}

@st.cache_resource
def init_connection():
    uri = f'mongodb+srv://{st.secrets["mongo"]["username"]}:{st.secrets["mongo"]["password"]}@{st.secrets["mongo"]["host"]}/?retryWrites=true&w=majority'
    return MongoClient(uri)

try:
    product_list = get_products()
    published_products = product_list.loc[product_list["Published"]==1,:].reset_index(drop=True)
    with st.container():
        c = st.columns(columns_proportion)
        c[0].markdown("**Picture**")
        c[1].markdown("**Product**")
        c[2].markdown("**Category**")
        c[3].markdown("**Price**")
        c[4].markdown("**Quantity**")
        c[5].markdown("**Total**")
    for i, each in published_products.iterrows():
        with st.container():
            c = st.columns(columns_proportion)
            c[0].image(each["Images"], use_column_width=True)
            product_name_and_description=f'#### {each["Name"]}\n\n'
            if not pd.isnull(each["Description"]):
                product_name_and_description+=f'{each["Description"]}\n\n'
            c[1].markdown(product_name_and_description)
            c[2].markdown(f'{each["Categories"]}')
            c[3].markdown(f'CHF {float(each["Regular price"]):.2f}')
            quantities[each["ID"]] = c[4].number_input(label="Quantity", min_value=0, max_value=99, step=1, key=i, label_visibility="collapsed")
            c[5].markdown(f'CHF {quantities[each["ID"]] * float(each["Regular price"]):.2f}')

    total =  sum([x*y for x,y in zip(quantities.values(), product_list["Regular price"].tolist())])
    c = st.columns(columns_proportion)
    c[4].markdown("**Total:**")
    c[5].markdown(f"**CHF {total:.2f}**")
    with st.form("panier"):
        if c[1].button(label="Add to cart", type="primary"):
            client = init_connection()
            with st.container():
                st.markdown(f"### Total panier")
                quantities_df = pd.DataFrame(quantities.values(), index=quantities.keys(), columns=["Quantity"])
                quantities_df = quantities_df.loc[quantities_df["Quantity"]>0, :]
                quantities_df = quantities_df.merge(published_products.set_index("ID")[["Name", "Regular price"]], left_index=True, right_index=True)
                quantities_df["Total"] = quantities_df["Regular price"] * quantities_df["Quantity"]
                st.table(quantities_df.reset_index(drop=True))

            with st.container():
                total_panier = quantities_df["Total"].sum()
                st.markdown(f"### Ajouter une note pour des intructions et demandes spéciales")
                st.text_area(label="Instructions", label_visibility="collapsed")
                st.markdown(f"### Résumé de la commande")
                st.markdown(f'''
                            |Total| CHF {total_panier:.2f}|
                            | :-------- | :------- |
                            | - Articles  | CHF {total_panier:.2f}    |
                            | - Livraison | CHF 0.00     |
                            | - Taxes    | CHF 0.00    |
                            ''')

            with st.container():
                st.markdown(f"### Coordonnées du client et livraison")
                
                row_1 = st.columns(2)
                row_1[0].text("Prénom")
                prenom = row_1[1].text_input(label="Prénom", label_visibility="collapsed")
                
                row_2 = st.columns(2)
                row_2[0].text("Nom")
                nom = row_2[1].text_input(label="Nom de famille", label_visibility="collapsed")

                row_3 = st.columns(2)
                row_3[0].text("Téléphone")
                telephone = row_3[1].text_input(label="Téléphone", label_visibility="collapsed")

                row_4 = st.columns(2)
                row_4[0].text("E-mail pour confirmer la commande")
                email = row_4[1].text_input(label="E-mail pour confirmer la commande", label_visibility="collapsed")

                row_5 = st.columns(2)
                row_5[0].text("Adresse")
                adresse = row_5[1].text_input(label="Adresse", label_visibility="collapsed")

                row_6 = st.columns(2)
                row_6[0].text("Ville")
                ville = row_6[1].text_input(label="Ville", label_visibility="collapsed")

                row_7 = st.columns(2)
                row_7[0].text("Code postal")
                code_postal = row_7[1].text_input(label="Code postal", label_visibility="collapsed")

                row_8 = st.columns(2)
                row_8[0].text("Région")
                region = row_8[1].text("Fribourg")

                row_9 = st.columns(2)
                row_9[0].text("Pays")
                pays = row_9[1].text("Suisse")

                st.markdown(f"### Instruction de livraison")
                livraison = st.radio(label="livraison",
                                    options=["En haut de la boîte aux lettres", 
                                            "A côté de la porte d'entrée (à l'extérieur)",
                                            "A côté de la porte d'entrée (à l'intérieur)",
                                            "Sonnez à l'interphone",
                                            "Autre"])
            submitted = st.form_submit_button("Submit")
            if submitted:
                st.write("OIOI")

except URLError as e:
    st.error(
        """
        **This demo requires internet access.**
        Connection error: %s
    """
        % e.reason)
    
    MongoClient()