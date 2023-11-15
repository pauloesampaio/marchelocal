from st_card_component import card_component
import pandas as pd
import streamlit as st
import smtplib
import markdown
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.cloud import firestore

def get_email_body(timestamp, order, client, delivery):
    email_body = f"Bonjour\n\n" 
    email_body += f"Vous avez reçu une nouvelle commande !\n\n"
    email_body += f"Vous trouverez ci-dessous les détails relatifs à cette commande:\n\n"
    email_body += f"**Date et heure de la commande :** {timestamp.strftime('%m/%d/%Y, %H:%M')}\n\n"
    email_body += f"**Montant total de l'achat :** {order['Total'].sum():.2f} CHF\n\n"
    email_body += f"**Coordonnées du client et livraison :**\n\n"
    email_body += f"**Client :** {client['first_name']} {client['last_name']}\n\n"
    email_body += f"**Téléphone :** {client['telephone']}\n\n"
    email_body += f"**Adresse email :** {client['email']}\n\n"
    email_body += f"**Adresse :** {client['adress']}, {client['city']}, {client['zip']}, {client['state']}\n\n"
    email_body += f"**Jour de livraison :** {delivery['schedule']}\n\n"
    email_body += f"**Instruction de livraison :** {delivery['instruction']}\n\n"
    if delivery["free_text"]:
        email_body += f"**Autre comentaire :** {delivery['free_text']}\n\n"
    
    email_body += "**Donnéesde commande:**\n\n"
    email_body += order.to_html(index=False)
    email_body += "\n\n"

    if delivery["special_demand"]:
        email_body += f"**Instructions ou des demandes spéciales :** {delivery['special_demand']}\n\n"
    else:
        email_body += f"**Instructions ou des demandes spéciales : Aucun commentaire ou demande supplémentaire**\n\n"
    

    email_body += "Il s'agit des produits et des données pour la nouvelle commande reçue. Si vous avez des questions ou des commentaires sur les produits, veuillez contacter directement le client par téléphone ou par courrier électronique.\n\n"
    email_body += "Si la méthode de livraison consiste à déposer le colis sans rencontre en personne, il serait gentil d'envoyer également un SMS informant que vous avez déjà effectué la livraison et l'envoyant au client pour qu'il paie par Twint.\n\n"
    email_body += "N'oubliez pas de laisser le nom et le prénom du client visibles à l'extérieur de la boîte ou du sac afin d'éviter que le colis ne soit égaré.\n\n"

    email_body += "Cordialement,\n\n"
    email_body += "Votre site Marché Local"
    
    return markdown.markdown(email_body)


def publish_list(published_products):
    quantities = {}
    for i, each in published_products.iterrows():
        id = each["ID"]
        name = each["Name"]
        description = "" if pd.isnull(each["Description"]) else each["Description"]
        category = each["Categories"]
        price = each["Regular price"]
        image_url = each["Images"]
        decorator = each["Mesure"]
        steps = each["Steps"]

        quantities[id] = card_component(
            name=name,
            description=description,
            category=category,
            price=price,
            image_url=image_url,
            decorator=decorator,
            steps=steps,
            key=i,
        )       
    return quantities  

def publish_panier(published_products, quantities):
    st.markdown(f"### Total panier")
    quantities_df = pd.DataFrame(quantities.values(), index=quantities.keys(), columns=["Quantité"])
    quantities_df = quantities_df.loc[quantities_df["Quantité"]>0, :]
    quantities_df = quantities_df.merge(published_products.set_index("ID")[["Name", "Regular price", "Mesure"]], left_index=True, right_index=True)
    quantities_df = quantities_df.rename(columns={"Name": "Produit", "Regular price": "Prix", "Mesure": "Mesure"})
    quantities_df.loc[quantities_df["Mesure"]=="gr", "Quantité"] = quantities_df.loc[quantities_df["Mesure"]=="gr", "Quantité"]/100
    quantities_df["Total"] = quantities_df["Prix"] * quantities_df["Quantité"]
    quantities_df = quantities_df[["Produit", "Prix", "Quantité", "Mesure", "Total"]]
    st.dataframe(quantities_df.reset_index(drop=True).style.format(subset=["Prix","Quantité","Total"]), use_container_width=True)

    total_panier = quantities_df["Total"].sum()
    st.markdown(f"### Résumé de la commande")
    st.markdown(f'''
                |Total| CHF {total_panier:.2f}|
                | :-------- | :------- |
                | Articles  | CHF {total_panier:.2f}    |
                | Livraison | CHF 0.00     |
                | Taxes    | CHF 0.00    |
                ''')
    st.write("\n")
    return quantities_df

def get_delivery_options():
    delivery_dict = {}
    st.markdown(f"### Ajouter une note pour des intructions et demandes spéciales.")
    st.markdown(f"Il y a possibilité de faire des demandes pour des produits ne figurants pas sur la liste et nous ferons de notre mieux pour y satisfaire.")
    delivery_dict["special_demand"] = st.text_area(placeholder="Ajoutez des instructions ou des demandes spécialles ici",label="Instructions", label_visibility="collapsed")
    st.markdown(f"### Jour et période de livraison gratuite")
    delivery_dict["schedule"] = st.radio(label="delivery_schedule", options=["Mardi matin suivant (vers 4h30, avant l'heure de début du marché)", "Mardi prochain à la mi-journée", "Jeudi matin suivant (entre 7h00 et 8h30)"], label_visibility="collapsed")
    st.markdown(f"### Instruction de livraison")
    st.markdown("Veuilliz indiquer ci-dessous comment vous préférez recevoir votre commande")
    delivery_dict["instruction"] = st.radio(label="livraison", label_visibility="collapsed",
                                                options=["En haut de la boîte aux lettres", 
                                                        "A côté de la porte d'entrée (à l'extérieur)",
                                                        "A côté de la porte d'entrée (à l'intérieur)",
                                                        "Sonnez à l'interphone",
                                                        "Autre (indiquer ci-dessous)"])
    delivery_dict["free_text"] = st.text_input(label="autre_option", label_visibility="collapsed")
    return delivery_dict

def get_client_info():
    client_dict = {}
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
    return client_dict

def save_document_in_db(timestamp, order, client, delivery):
    db = firestore.Client.from_service_account_info(st.secrets["firebase"])
    print(timestamp)
    print(order["Total"].sum())
    print(order["Quantité"].sum())
    print(client)
    print(delivery)
    print(order.to_dict(orient="records"))
    order_document = {"timestamp": timestamp, 
                      "order_price": order["Total"].sum(), 
                      "order_n_products": order["Quantité"].sum(), 
                      "client": client, 
                      "order": order.to_dict(orient="records"), 
                      "delivery": delivery}
    db.collection("orders").add(order_document)


def send_email_to_farmer(timestamp, order, client, delivery):
    email_sender = st.secrets["email"]["from"]
    email_receiver = client["email"]
    email_body = get_email_body(timestamp, order, client, delivery)
    subject = "Marche local: vous avez une nouvelle commande"
    password = st.secrets["email"]["password"]
    part1 = MIMEText(email_body, 'plain')
    part2 = MIMEText(email_body, 'html')
    try:
        msg = MIMEMultipart('alternative')
        msg.attach(part1)
        msg.attach(part2)
        msg['From'] = email_sender
        msg['To'] = email_receiver
        msg['Subject'] = subject
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_sender, password)
        server.sendmail(email_sender, email_receiver, msg.as_string())
        server.quit()

        st.success('Order sent successfully! 🚀')
        st.balloons()

    except Exception as e:
        st.error(f"Error: {e}")