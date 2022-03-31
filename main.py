import os
from imbox import Imbox
import json
from config import host, username, password, download_folder, user_emails, admin_emails
import re
from time import sleep
import shutil

if not os.path.isdir(download_folder):
    os.makedirs(download_folder, exist_ok=True)


def check_mail():

    mail = Imbox(host, username=username, password=password, ssl=True, ssl_context=None, starttls=False)  # abrimos el correo
    messages = mail.messages(unread=True)  # vemos todos los no leidos
    new_paths = []

    for uid, message in messages:  # para cada id del mensaje, mensaje
        mail.mark_seen(uid) # marcamos el mensaje como leido
        uid = int(uid)

        metadata = get_metadata(message, uid)  # si el correo no está en la lista, no lo pescamos, por gil
        print(metadata)
        if not(metadata["sent_from"] in user_emails):
            continue
        
        if "print" in metadata["subject"].lower():  # si viene para imprimir, bajamos los datos
            # handle printing
            new_paths.append(f"{download_folder}/{uid}")

            os.makedirs(f"{download_folder}/{uid}")  # hacemos una carpeta para el correo
            download_path = f"{download_folder}/{uid}"  # acá vamos a guardar todo lo de este correo
            metadata_path = f"{download_folder}/{uid}/data.json"  # acá vamos a guardar la metadata

            save_data_for_printing(metadata_path, metadata, message, download_folder, uid)
        
        elif "admin" in metadata["subject"].lower():
            handle_admin(metadata)

    return new_paths


def get_metadata(msg, uid):
    uid = int(uid)
    path = f"{download_folder}/{uid}/data.json"
    body = msg.body["plain"][0] 
    subject = msg.subject
    sent_from = msg.sent_from[0]["email"]

    return {"body":body, "subject":subject, "sent_from":sent_from}


def save_data_for_printing(metadata_path, metadata, message, download_folder, uid):
    
    with open(metadata_path, "w") as fp:
        json.dump(metadata,fp) 

    for idx, attachment in enumerate(message.attachments): 
        try:
            att_fn = attachment.get('filename')
            download_path = f"{download_folder}/{uid}/{att_fn}"
            print(download_path)
            
            with open(download_path, "wb") as fp:
                fp.write(attachment.get('content').read())
            
        except:
            print(traceback.print_exc())


def handle_admin(metadata):
    if "addemail" in metadata["body"]:
        admin_addemail(metadata)
        




def admin_addemail(metadata):
    match = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', metadata["body"])
    global user_emails
    user_emails += match
    new_email_list = {"users": user_emails, "admins": admin_emails}
    with open("email_list.json", "w") as fp:
        json.dump(new_email_list,fp) 



def handle_printing(printing_folder):
    with open() as fp:
        metadata = json.load(fp)
    
    files2print = os.listdir(printing_folder)
    files2print = [f for f in files if not(".json" in f)]

    command_string = handle_printing_commands(metadata["body"])
    for file_ in files2print:

        os.system(f"lp {command_string} {file_}")


def handle_printing_commands(email_body):
    options = []

    email_body_ = email_body.lowe()

    if ("doble-corto" in email_body_) and not("doble-largo" in email_body_):
        options.append("-o sides=two-sided-long-edge")

    if ("doble-largo" in email_body_) and not("doble-corto" in email_body_):
        options.append("-o sides=two-sided-long-edge")
    
    if "pgs" in email_body_:
        a, b = email_body_.find("[") + 1, email_body_.find("]")
        options.append(f"-o page-ranges={email_body_[a:b]}")
    
    options_ = " ".join(str(item) for item in options)

    return options_

        

if __name__=="__main__":
    sleep(30)
    folders_for_printing = check_mail()
    for folder in folders_for_printing:
        handle_printing(folder)
        sleep(5)
        shutil.rmtree(folder)

