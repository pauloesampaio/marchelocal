import streamlit as st
from urllib.error import URLError
import pandas as pd
from datetime import datetime
from streamlit.logger import get_logger
from google.cloud import firestore
import smtplib
from email.mime.text import MIMEText

st.set_page_config(layout="wide")
columns_proportion = [5,40,20,10,5,20]

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
quantities = {}

@st.cache_resource
def init_connection():
    client = firestore.Client.from_service_account_info(st.secrets["firebase"])
    return client

try:
    product_list = get_products()
    published_products = product_list.loc[product_list["Published"]==1,:].reset_index(drop=True)
    with st.container():
        c = st.columns(columns_proportion)
        #c[0].markdown("**Picture**")
        c[1].markdown("**Produit**")
        c[2].markdown("**Catégorie**")
        c[3].markdown("**Prix**")
        c[4].markdown("**Quantité**")
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
    #if c[1].button(label="Add to cart", type="primary"):
    with st.form("panier"):
            db = init_connection()
            with st.container():
                st.markdown(f"### Total panier")
                quantities_df = pd.DataFrame(quantities.values(), index=quantities.keys(), columns=["Quantité"])
                quantities_df = quantities_df.loc[quantities_df["Quantité"]>0, :]
                quantities_df = quantities_df.merge(published_products.set_index("ID")[["Name", "Regular price"]], left_index=True, right_index=True)
                quantities_df = quantities_df.rename(columns={"Name": "Produit", "Regular price": "Prix"})
                quantities_df["Total"] = quantities_df["Prix"] * quantities_df["Quantité"]
                quantities_df = quantities_df[["Produit", "Prix", "Quantité", "Total"]]
                st.dataframe(quantities_df.reset_index(drop=True).style.format(subset=["Prix","Total"], formatter="{:.2f}"))
                order_dict = quantities_df.to_dict(orient="records")

            with st.container():
                total_panier = quantities_df["Total"].sum()
                st.markdown(f"### Ajouter une note pour des intructions et demandes spéciales")
                special_demand = st.text_area(placeholder="Ajoutez des instructions ou des demandes spécialles ici",label="Instructions", label_visibility="collapsed")
                st.markdown(f"### Résumé de la commande")
                st.markdown(f'''
                            |Total| CHF {total_panier:.2f}|
                            | :-------- | :------- |
                            | - Articles  | CHF {total_panier:.2f}    |
                            | - Livraison | CHF 0.00     |
                            | - Taxes    | CHF 0.00    |
                            ''')
            with st.container():
                st.markdown(f"### Jour et période de livraison gratuite")
                delivery_schedule = st.radio(label="delivery_schedule", options=["Mardi matin suivant", "Mardi prochain à la mi-journée", "Jeudi matin suivant"], label_visibility="collapsed")
            with st.container():
                client_dict = {}
                st.markdown(f"### Coordonnées du client et livraison")
                
                row_1 = st.columns(2)
                row_1[0].text("Prénom")
                client_dict["first_name"] = row_1[1].text_input(label="Prénom", label_visibility="collapsed")
                
                row_2 = st.columns(2)
                row_2[0].text("Nom")
                client_dict["last_name"] = row_2[1].text_input(label="Nom de famille", label_visibility="collapsed")

                row_3 = st.columns(2)
                row_3[0].text("Téléphone")
                client_dict["telephone"] = row_3[1].text_input(label="Téléphone", label_visibility="collapsed")

                row_4 = st.columns(2)
                row_4[0].text("E-mail pour confirmer la commande")
                client_dict["email"] = row_4[1].text_input(label="E-mail pour confirmer la commande", label_visibility="collapsed")

                row_5 = st.columns(2)
                row_5[0].text("Adresse")
                client_dict["adress"] = row_5[1].text_input(label="Adresse", label_visibility="collapsed")

                row_6 = st.columns(2)
                row_6[0].text("Ville")
                client_dict["city"] = row_6[1].text_input(label="Ville", label_visibility="collapsed")

                row_7 = st.columns(2)
                row_7[0].text("Code postal")
                client_dict["zip"] = row_7[1].text_input(label="Code postal", label_visibility="collapsed")

                row_8 = st.columns(2)
                row_8[0].text("Région")
                row_8[1].text("Fribourg")
                client_dict["state"] = "Fribourg"

                row_9 = st.columns(2)
                row_9[0].text("Pays")
                row_9[1].text("Suisse")
                client_dict["country"] = "Suisse"

                st.markdown(f"### Instruction de livraison")
                st.markdown("Veuilliz indiquer ci-dessous comment vous préférez recevoir votre commande")
                client_dict["delivery_option"] = st.radio(label="livraison", label_visibility="collapsed",
                                                            options=["En haut de la boîte aux lettres", 
                                                                    "A côté de la porte d'entrée (à l'extérieur)",
                                                                    "A côté de la porte d'entrée (à l'intérieur)",
                                                                    "Sonnez à l'interphone",
                                                                    "Autre (indiquer ci-dessous)"])
                client_dict["delivery_free_text"] = st.text_input(label="autre_option", label_visibility="collapsed")
                st.markdown("Il ne vous reste plus qu'à cliquer sur le bouton ci-dessous et votre commande sera transmise à notre vendeur local qui s'occupera de votre livraison. Le paiement sera effectué à la livraison directement en espèces ou en Twint ou après la livraison par Twint.")
            submitted = st.form_submit_button("Envoyez ma commande!", type="primary")

            if submitted:
                timestamp = datetime.now()
                order_document = {"timestamp": timestamp, "order_price": total_panier, "client": client_dict, "order": order_dict, "delivery_schedule": delivery_schedule, "special_demand": special_demand}
                print(order_document)
                db.collection("orders").add(order_document)

                email_sender = st.secrets["email"]["from"]
                email_receiver = client_dict["email"]
                subject = "Your Marche Local order"
                body = str(order_document)
                password = st.secrets["email"]["password"]

                try:
                    msg = MIMEText(body)
                    msg['From'] = email_sender
                    msg['To'] = email_receiver
                    msg['Subject'] = subject

                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(email_sender, password)
                    server.sendmail(email_sender, email_receiver, msg.as_string())
                    server.quit()

                    st.success('Order sent successfully! 🚀')
                except Exception as e:
                    st.error(f"Error: {e}")


except URLError as e:
    st.error(
        """
        **This demo requires internet access.**
        Connection error: %s
    """
        % e.reason)
    