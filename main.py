import datetime
import json
import os
import subprocess
import threading
import time
import tkinter
from datetime import datetime
import customtkinter as ctk
import imutils
import mysql.connector
import requests
from imutils.video import VideoStream
from pyzbar import pyzbar
from tkcalendar import *
from pydub import AudioSegment
from pydub.playback import play

if os.environ.get('DISPLAY', '') == '':
    os.environ.__setitem__('DISPLAY', ':0.0')


class Window(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("iFridge")
        self.attributes("-fullscreen", True)
        self.bind("<Escape>", quit)


class ProductItem(ctk.CTkFrame):
    def __init__(self, *args,
                 width: int = 400,
                 height: int = 100,
                 title: str = "Title",
                 product_code: int,
                 **kwargs):
        super().__init__(*args, width=width, height=height, **kwargs)

        self.title = title
        self.product_code = product_code
        self.items = []

        self.configure(fg_color=("gray78", "gray28"))

        self.grid_columnconfigure((1, 2), weight=4, uniform="a")
        self.grid_columnconfigure((0, 3), weight=1, uniform="a")

        self.title = ctk.CTkLabel(self, text=title, font=("default", 26))
        self.title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=10)

        self.row_counter = 1

        try:
            cnx = mysql.connector.connect(user='dbuser', password='Foodguardian', host='127.0.0.1', database='ifridge')
            cursor = cnx.cursor()
            query = "SELECT * FROM Item WHERE Productcode=%s ORDER BY ExpirationDate"
            parameters = (self.product_code,)
            cursor.execute(query, parameters)
            item_result = cursor.fetchall()
            for item in item_result:
                self.items.append(Item(self, itemid=item[0], date=item[2], amount=item[3], row_number=self.row_counter))
                self.row_counter += 1

            cursor.close()
            cnx.close()
        except mysql.connector.Error as err:
            print(err)

    def check_empty_items(self):
        if len(self.items) == 0:
            try:
                cnx = mysql.connector.connect(user='dbuser', password='Foodguardian', host='127.0.0.1',
                                              database='ifridge')
                cursor = cnx.cursor()
                cursor.execute("DELETE FROM Product WHERE Productcode=%s;", (self.product_code,))
                cnx.commit()
                cursor.close()
                cnx.close()
                self.destroy()
            except mysql.connector.Error as err:
                print(err)


class Item():
    def __init__(self, root, itemid, date, amount, row_number):
        self.root = root
        self.id = itemid
        self.date = date
        self.amount = amount
        self.row_number = row_number
        self.button = ctk.CTkButton(root, text="-", command=lambda: threading.Thread(target=self.minus_amount).start())
        self.button.grid(column=0, row=row_number, padx=10)
        self.label = ctk.CTkLabel(root, text=str(amount) + ": " + self.date.strftime("%d/%m/%Y"))
        self.label.grid(column=1, row=row_number, sticky="w", padx=10, pady=10)

    def minus_amount(self):
        if self.amount > 1:
            self.amount -= 1
            try:
                cnx = mysql.connector.connect(user='dbuser', password='Foodguardian', host='127.0.0.1',
                                              database='ifridge')
                cursor = cnx.cursor()
                cursor.execute("UPDATE Item SET amount = %s WHERE ID=%s;", (self.amount, str(self.id),))
                cnx.commit()
                cursor.close()
                cnx.close()
                self.label.configure(text=str(self.amount) + ": " + self.date.strftime("%d/%m/%Y"))
            except mysql.connector.Error as err:
                print(err)
        else:
            try:
                cnx = mysql.connector.connect(user='dbuser', password='Foodguardian', host='127.0.0.1',
                                              database='ifridge')
                cursor = cnx.cursor()
                cursor.execute("DELETE FROM Item WHERE ID=%s;", (str(self.id),))
                cnx.commit()
                cursor.close()
                cnx.close()
                self.root.items.remove(self)
                self.root.check_empty_items()
                self.label.destroy()
                self.button.destroy()
                self.self_del()
            except mysql.connector.Error as err:
                print(err)

    def self_del(self):
        # Destroy label and button and make them invisible
        del self.id
        del self.date
        del self.amount


def main_menu():
    global main
    main = Window()

    main.columnconfigure((0, 1), weight=1, uniform="a")
    main.rowconfigure(0, weight=1, uniform="a")
    main.rowconfigure((1, 2), weight=2, uniform="a")

    title = ctk.CTkLabel(main, text="iFridge", font=("default", 32))
    title.grid(row=0, column=0, sticky="new", padx=20, pady=10, columnspan=2)

    button2 = ctk.CTkButton(main, text="Instellingen", command=lambda: settings())
    button2.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

    button1 = ctk.CTkButton(main, text="Producten scannen", command=lambda: product_scan(), font=("default", 24))
    button1.grid(row=1, column=0, sticky="news", padx=20, pady=10)

    button2 = ctk.CTkButton(main, text="Handmatig toevoegen", command=lambda: add_manually(), font=("default", 24))
    button2.grid(row=1, column=1, sticky="news", padx=20, pady=10)

    button1 = ctk.CTkButton(main, text="Productenlijst", font=("default", 24), command=lambda: product_list())
    button1.grid(row=2, column=0, sticky="news", padx=20, pady=10)

    button2 = ctk.CTkButton(main, text="Recepten maken", font=("default", 24), command=lambda: recipes())
    button2.grid(row=2, column=1, sticky="news", padx=20, pady=10)

    main.mainloop()


def product_scan():
    global result
    global product_scan_window
    global amount
    global amount_label
    global cal
    global scanning
    scanning = False
    amount = 1
    product_scan_window = Window()

    product_scan_window.columnconfigure((0, 4), weight=1, uniform="a")
    product_scan_window.columnconfigure((1, 2, 3), weight=2, uniform="a")
    product_scan_window.rowconfigure(0, weight=1, uniform="a")
    product_scan_window.rowconfigure((1, 2, 3, 4, 5), weight=2, uniform="a")

    back_button = ctk.CTkButton(product_scan_window, text="Terug", command=lambda: exit_product_scan())
    back_button.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

    scan_title = ctk.CTkLabel(product_scan_window, text="Product scannen", font=("default", 32))
    scan_title.grid(row=0, column=1, columnspan=3, sticky="new", padx=20, pady=10)

    button1 = ctk.CTkButton(product_scan_window, text="Scan", font=("default", 24),
                            command=lambda: threading.Thread(target=scan_product).start())
    button1.grid(row=1, column=0, sticky="news", padx=20, pady=10, columnspan=2)

    button2 = ctk.CTkButton(product_scan_window, text="Voeg toe", font=("default", 24),
                            command=lambda: threading.Thread(target=insert_product).start())
    button2.grid(row=5, column=3, sticky="es", padx=20, pady=10, columnspan=2)

    plus_button = ctk.CTkButton(product_scan_window, text="+", font=("default", 24),
                                command=lambda: threading.Thread(target=plus_amount).start())
    plus_button.grid(row=2, column=0, sticky="ews", padx=20, pady=10, columnspan=2)

    minus_button = ctk.CTkButton(product_scan_window, text="-", font=("default", 24),
                                 command=lambda: threading.Thread(target=minus_amount).start())
    minus_button.grid(row=4, column=0, sticky="new", padx=20, pady=10, columnspan=2)

    amount_text = amount
    amount_label = ctk.CTkLabel(product_scan_window, text=amount_text, font=("default", 22))
    amount_label.grid(row=3, column=0, sticky="nwes", padx=20, pady=10, columnspan=2)

    cal = Calendar(product_scan_window, selectmode="day", year=datetime.now().year, month=datetime.now().month,
                   day=datetime.now().day)
    cal.grid(row=2, column=2, sticky="nwes", padx=20, pady=10, columnspan=3, rowspan=3)

    result = ctk.CTkLabel(product_scan_window, text="Result: ", font=("default", 24))
    result.grid(row=1, column=2, sticky="new", padx=20, pady=10, columnspan=3)

    product_scan_window.mainloop()

def exit_product_scan():
    global vs
    global product_scan_window

    vs.stop()
    product_scan_window.destroy()


def plus_amount():
    global amount
    global amount_label
    amount += 1
    amount_label.configure(text=amount)


def minus_amount():
    global amount
    global amount_label
    if amount > 1:
        amount -= 1
        amount_label.configure(text=amount)


def scan_product():
    global product_scan_window
    global barcode_data
    global result
    global response_array
    global response
    global url
    global scanning
    global vs
    result.configure(text="Scanning...")
    if not scanning:
        vs = VideoStream(usePiCamera=True).start()
        time.sleep(2.0)
        scanning = True
        while scanning:
            frame = vs.read()
            frame = imutils.resize(frame, width=400)
            barcodes = pyzbar.decode(frame)
            for barcode in barcodes:
                barcode_data = barcode.data.decode("utf-8")
                print(barcode_data)
                if (barcode_data != None):
                    scanning = False
                    play(AudioSegment.from_mp3("ifridge.mp3"))
                    result.configure(text="Barcode gevonden")
        vs.stop()
        result.configure(text="Product zoeken...")
        url = "https://world.openfoodfacts.org/api/v0/product/" + barcode_data + ".json"
        get_response()
        response_array = json.loads(response)
        print(response_array)
        print(response_array['status'])
        if response_array['status'] == 1:
            try:
                print("Product gevonden")
                print(response_array['product']['brands'])
                print(response_array['product']['product_name'])
                text = response_array['product']['brands'] + " " + response_array['product']['product_name']
                result.configure(text=text)
                scanning = False
            except:
                text = response_array['product']['product_name']
                result.configure(text=text)
                scanning = False
        else:
            print("Product niet gevonden")
            text = barcode_data + " product niet gevonden"
            result.configure(text=text)
            scanning = False


def get_response():
    global response
    global url
    trycountdown = 3
    try:
        response = requests.get(url).text
    except:
        trycountdown -= 1
        if trycountdown > 0:
            get_response()
        else:
            result.configure(text="Geen verbinding")


def insert_manually():
    global product_name
    global amount
    global cal
    global result

    today = datetime.now()
    selected_date = cal.selection_get()
    selected_datetime = datetime.combine(selected_date, datetime.min.time())
    name = product_name.get()

    if name:
        if selected_datetime > today:
            try:
                cnx = mysql.connector.connect(user='dbuser', password='Foodguardian', host='127.0.0.1',
                                              database='ifridge')
                cursor = cnx.cursor()
                add_product = ("INSERT IGNORE INTO Product"
                              "(Productcode, Name)"
                              "VALUES (%s, %s)")
                product_data = (name, name)
                cursor.execute(add_product, product_data)
                add_item = ("INSERT INTO Item"
                           "(Productcode, ExpirationDate, Amount)"
                           "VALUES (%s, %s, %s)")
                expiration_date = cal.selection_get()
                item_data = (name, expiration_date, amount)
                cursor.execute(add_item, item_data)
                cnx.commit()
                cursor.close()
                cnx.close()
                result.configure(text="Product toegevoegd")

            except mysql.connector.Error as err:
                print(err)
        else:
            result.configure(text="Verkeerde datum!")
    else:
        result.configure(text="Naam is leeg!")

def close_osk():
    global open_osk
    if open_osk:
        subprocess.Popen("/home/user/Desktop/killkeyboard.sh")

def handle_click(event):
    global open_osk
    p = subprocess.Popen("/home/user/Desktop/keyboard.sh")
    open_osk = True


def add_manually():
    global product_name
    global amount
    global cal
    global result
    amount = 1
    global amount_label
    global open_osk
    open_osk = False
    global add_manually_window



    add_manually_window = Window()

    add_manually_window.columnconfigure((0, 4), weight=1, uniform="a")
    add_manually_window.columnconfigure((1, 2, 3), weight=2, uniform="a")
    add_manually_window.rowconfigure((0), weight=2, uniform="a")
    add_manually_window.rowconfigure((1, 2, 3, 4, 5, 6), weight=2, uniform="a")

    back_button = ctk.CTkButton(add_manually_window, text="Terug", command=lambda: close_manual())
    back_button.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

    manual_title = ctk.CTkLabel(add_manually_window, text="Handmatig toevoegen", font=("default", 32))
    manual_title.grid(row=0, column=1, columnspan=2, sticky="new", padx=20, pady=10)

    input_title = ctk.CTkLabel(add_manually_window, text="Product naam:", font=("default", 25))
    input_title.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

    product_name = ctk.CTkEntry(add_manually_window, corner_radius=20, width=350)
    product_name.grid(row=2, column=0, columnspan=2, padx=25, pady=25)

    product_name.bind("<1>", handle_click)

    plus_button = ctk.CTkButton(add_manually_window, text="+", font=("default", 24),
                               command=lambda: threading.Thread(target=plus_amount).start())
    plus_button.grid(row=4, column=0, sticky="ews", padx=20, pady=10, columnspan=2)

    minus_button = ctk.CTkButton(add_manually_window, text="-", font=("default", 24),
                                command=lambda: threading.Thread(target=minus_amount).start())
    minus_button.grid(row=6, column=0, sticky="new", padx=20, pady=10, columnspan=2)

    amount_text = amount
    amount_label = ctk.CTkLabel(add_manually_window, text=amount_text, font=("default", 22))
    amount_label.grid(row=5, column=0, sticky="nwes", padx=20, pady=10, columnspan=2)

    cal_title = ctk.CTkLabel(add_manually_window, text="Datum:", font=("default", 25))
    cal_title.grid(row=1, column=2, columnspan=2, padx=10, pady=10)

    cal = Calendar(add_manually_window, selectmode="day", year=datetime.now().year, month=datetime.now().month,
                   day=datetime.now().day)
    cal.grid(row=2, column=2, sticky="nwes", padx=20, pady=10, columnspan=3, rowspan=3)

    button2 = ctk.CTkButton(add_manually_window, text="Voeg toe", font=("default", 24),
                            command=lambda: threading.Thread(target=insert_manually).start())
    button2.grid(row=6, column=3, sticky="es", padx=20, pady=10, columnspan=2)

    result = ctk.CTkLabel(add_manually_window, text="Result: ", font=("default", 24))
    result.grid(row=0, column=3, sticky="new", padx=20, pady=10, columnspan=2)

    add_manually_window.mainloop()


def close_manual():
    global add_manually_window
    subprocess.Popen("/home/user/Desktop/killkeyboard.sh")
    add_manually_window.destroy()


def insert_product():
    global response_array
    global amount
    global cal

    selected_datetime = datetime.combine(cal.selection_get(), datetime.min.time())
    if response_array['status'] == 1:
        if selected_datetime > datetime.now():
            try:
                cnx = mysql.connector.connect(user='dbuser', password='Foodguardian', host='127.0.0.1', database='ifridge')
                cursor = cnx.cursor()
                add_product = ("INSERT IGNORE INTO Product"
                              "(Productcode, Brand, Name)"
                              "VALUES (%s, %s, %s)")
                try:
                    product_data = (barcode_data, response_array['product']['brands'], response_array['product']['product_name'])
                except:
                    product_data = (barcode_data, " ", response_array['product']['product_name'])
                cursor.execute(add_product, product_data)
                add_item = ("INSERT INTO Item"
                           "(Productcode, ExpirationDate, Amount)"
                           "VALUES (%s, %s, %s)")
                expiration_date = cal.selection_get()
                item_data = (barcode_data, expiration_date, amount)
                cursor.execute(add_item, item_data)
                cnx.commit()
                cursor.close()
                cnx.close()
                result.configure(text="Product toegevoegd")

            except mysql.connector.Error as err:
                print(err)
        else:
            result.configure(text="Verkeerde datum ingevuld")


def product_list():
    product_list_window = Window()

    product_list_window.columnconfigure((0, 3), weight=1, uniform="a")
    product_list_window.columnconfigure((1, 2), weight=2, uniform="a")
    product_list_window.rowconfigure((0), weight=1, uniform="a")
    product_list_window.rowconfigure((1, 2,), weight=2, uniform="a")

    back_button = ctk.CTkButton(product_list_window, text="Terug", command=lambda: product_list_window.destroy())
    back_button.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

    list_title = ctk.CTkLabel(product_list_window, text="Productenlijst", font=("default", 32))
    list_title.grid(row=0, column=1, columnspan=2, sticky="new", padx=20, pady=10)

    main_frame = ctk.CTkFrame(master=product_list_window)
    main_frame.grid(column=0, columnspan=4, row=1, rowspan=2, sticky="nsew")

    product_canvas = ctk.CTkCanvas(master=main_frame)
    product_canvas.pack(side="left", fill="both", expand=1)

    scrollbar = ctk.CTkScrollbar(main_frame, orientation="vertical", command=product_canvas.yview, width=45)
    scrollbar.pack(side="right", fill="y")

    product_canvas.configure(yscrollcommand=scrollbar.set)
    product_canvas.bind('<Configure>', lambda e: product_canvas.configure(scrollregion=product_canvas.bbox("all")))

    product_frame = ctk.CTkFrame(master=product_canvas)

    product_canvas.create_window((0, 0), window=product_frame, anchor="nw")

    product_row_count = 1
    try:
        cnx = mysql.connector.connect(user='dbuser', password='Foodguardian', host='127.0.0.1', database='ifridge')
        cursor = cnx.cursor()
        cursor.execute("SELECT * FROM Product")
        result_product_list = cursor.fetchall()
        cursor.close()
        cnx.close()
        for product in result_product_list:
            ProductItem(product_frame, title=product[1] + " " + product[2], product_code=product[0]).grid(
                row=product_row_count, pady=10, padx=30, sticky="nsew")
            product_row_count += 1
    except mysql.connector.Error as err:
        print(err)

    expand_label = ctk.CTkLabel(product_frame, text=" ", height=250)
    expand_label.grid(row=product_row_count, pady=10, padx=30, sticky="nsew")

    product_list_window.mainloop()


def settings():
    global settings_window
    settings_window = ctk.CTk()
    settings_window.title("iFridge")
    settings_window.attributes("-fullscreen", True)
    settings_window.bind("<Escape>", quit)

    settings_window.columnconfigure((0, 3), weight=1, uniform="a")
    settings_window.columnconfigure((1, 2), weight=2, uniform="a")
    settings_window.rowconfigure((0), weight=1, uniform="a")
    settings_window.rowconfigure((1, 2, 3, 4), weight=2, uniform="a")

    back_button = ctk.CTkButton(settings_window, text="Terug", command=lambda: settings_window.destroy())
    back_button.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

    settings_title = ctk.CTkLabel(settings_window, text="Instellingen", font=("default", 32))
    settings_title.grid(row=0, column=1, columnspan=2, sticky="new", padx=20, pady=10)

    quit_button = ctk.CTkButton(settings_window, text="Quit", command=lambda: quitall(), font=("defaut", 24))
    quit_button.grid(row=1, column=1, columnspan=2, sticky="news", padx=20, pady=10)

    wifi_button = ctk.CTkButton(settings_window, text="WIFI", command=lambda: wifi_settings(), font=("defaut", 24))
    wifi_button.grid(row=2, column=1, columnspan=2, sticky="news", padx=20, pady=10)

    shutdown_button = ctk.CTkButton(settings_window, text="Uitschakelen", command=lambda: shutdown(), font=("defaut", 24))
    shutdown_button.grid(row=3, column=1, columnspan=2, sticky="news", padx=20, pady=10)

    settings_window.mainloop()


def shutdown():
    os.popen("sudo shutdown now")

def wifi_settings():
    global open_osk
    open_osk = False
    global wifi_window
    global ssid_entry
    global pswd_entry
    global wifi_result

    wifi_window = Window()

    wifi_window.columnconfigure((0, 4), weight=1, uniform="a")
    wifi_window.columnconfigure((1, 2, 3), weight=2, uniform="a")
    wifi_window.rowconfigure((0), weight=2, uniform="a")
    wifi_window.rowconfigure((1, 2, 3, 4, 5, 6), weight=2, uniform="a")

    back_button = ctk.CTkButton(wifi_window, text="Terug", command=lambda: close_wifi())
    back_button.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

    wifi_title = ctk.CTkLabel(wifi_window, text="WIFI", font=("default", 32))
    wifi_title.grid(row=0, column=1, columnspan=2, sticky="new", padx=20, pady=10)

    ssid_title = ctk.CTkLabel(wifi_window, text="SSID:", font=("default", 25))
    ssid_title.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ws")

    ssid_entry = ctk.CTkEntry(wifi_window, corner_radius=20, width=350)
    ssid_entry.grid(row=2, column=0, columnspan=2, rowspan=2, padx=25, pady=25, sticky="nw")

    pswd_title = ctk.CTkLabel(wifi_window, text="Wachtwoord:", font=("default", 25))
    pswd_title.grid(row=1, column=3, columnspan=2, padx=10, pady=10, sticky="ws")

    pswd_entry = ctk.CTkEntry(wifi_window, corner_radius=20, width=350)
    pswd_entry.grid(row=2, column=3, columnspan=2, padx=25, pady=25, sticky="nw", rowspan=2)

    ssid_entry.bind("<1>", handle_click)
    pswd_entry.bind("<1>", handle_click)

    button2 = ctk.CTkButton(wifi_window, text="Opslaan en restart", font=("default", 24),
                            command=lambda: threading.Thread(target=save_wifi).start())
    button2.grid(row=6, column=3, sticky="es", padx=20, pady=10, columnspan=3)

    wifi_window.mainloop()

def close_wifi():
    global wifi_window
    subprocess.Popen("/home/user/Desktop/killkeyboard.sh")
    wifi_window.destroy()

def save_wifi():
    global ssid_entry
    global pswd_entry
    config_lines = [
        'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev',
        'update_config=1',
        'country=NL',
        '\n',
        'network={',
        '\tssid="{}"'.format(ssid_entry.get()),
        '\tpsk="{}"'.format(pswd_entry.get()),
        '}'
    ]
    config = '\n'.join(config_lines)

    os.popen("sudo chmod a+w /etc/wpa_supplicant/wpa_supplicant.conf")

    with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as wifi:
        wifi.write(config)

    os.popen("sudo reboot")


def recipes():
    global recipes_window
    recipes_window = Window()
    global dropdown
    global products

    products = []

    recipes_window.columnconfigure((0, 3), weight=1, uniform="a")
    recipes_window.columnconfigure((1, 2), weight=2, uniform="a")
    recipes_window.rowconfigure((0), weight=1, uniform="a")
    recipes_window.rowconfigure((1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11), weight=2, uniform="a")

    back_button = ctk.CTkButton(recipes_window, text="Terug", command=lambda: recipes_window.destroy())
    back_button.grid(row=0, column=0, sticky="nw", padx=5, pady=2)

    list_title = ctk.CTkLabel(recipes_window, text="Recepten Maker", font=("default", 32))
    list_title.grid(row=0, column=1, columnspan=2, sticky="new", padx=20)

    #A connection to the database, all products are pulled from the database and put in the list 'products'.
    try:
        cnx = mysql.connector.connect(user='dbuser', password='Foodguardian', host='127.0.0.1', database='ifridge')
        cursor = cnx.cursor()
        cursor.execute("SELECT * FROM Product")
        result_product_list = cursor.fetchall()
        cursor.close()
        cnx.close()
        for product in result_product_list:
            products.append(product[1] + " " + product[2])
    except mysql.connector.Error as err:
        print(err)

    instruction = ctk.CTkLabel(recipes_window, text="Kies een product om een recept op te baseren", font=("default", 18), height=50)
    instruction.grid(row=1, column=1, columnspan=2, sticky="nsew", padx=10, pady=10)

    #The dropdown menu in witch the list 'products' is put.
    dropdown = ctk.CTkOptionMenu(master=recipes_window, values=products)
    dropdown.grid(row=2, column=1, columnspan=2, sticky="nsew", padx=10, pady=10)

    #The button witch when pressed threads to 'generate_recipe' and thus generates a recipe based on the selected product.
    generate_button = ctk.CTkButton(recipes_window, width=300, text="maak recept", command=lambda: threading.Thread(target=generate_recipe).start())
    generate_button.grid(row=3, column=1, columnspan=2, sticky="nsew", padx=10, pady=10)

    recipes_window.mainloop()


def generate_recipe():

    #A text that indicates when a recipe is being generated.
    generating_text = ctk.CTkLabel(recipes_window, text="Recept aan het genereren ", font=("default", 24), justify="center")
    generating_text.grid(row=6, column=1, columnspan=2, padx=10, pady=10)

    #The ingredient/product that is selected in the dropdown menu.
    main_ingredient = str(dropdown.get())

    #A connection is made to the /recipe part of the api. Both the mainingredient and all the other products in the fridge are given as parameters.
    #Then the api generates a recipe based on these parameters.
    try:
        response = requests.post("http://ifridge.local/recipe", data={"mainIngredient": main_ingredient, "ingredients": products})
        recipe_title = response.json()["prefix"].replace("Recept: ", "")
        suffix = response.json()["suffix"].replace("Opmerking: ", "")
        ingredients = "\n".join(response.json()["ingredients"])
        instructions = response.json()["instructions"]
        # A check that makes sure there aren't really long sentences.
        count1 = 0
        count2 = instructions.count(".")
        if count1 <= count2:
            for x in instructions:
                if len(x) > 125:
                    index = x.find(" ", x.find(" ") + 10)
                    instructions[count1] = x[:index] + "\n" + x[index:]
                count1 += 1
        recipe_check = True
        instructions = "\n".join(instructions)
    except requests.exceptions.ConnectionError:
        recipe_check = False

    #A check to make sure that there was a connection made to the api and everything went right in the api.
    if recipe_check:
        generating_text.destroy()

        #The title of the generated recipe.
        recipe_title_text = ctk.CTkLabel(recipes_window, text=recipe_title, font=("default", 12), justify="center")
        recipe_title_text.grid(row=4, column=0, columnspan=4, padx=10, pady=10)

        #The ingredients and instructions are combined into one string.
        ingredients_and_instructions = ingredients + "\n" + "\n" + instructions

        #A check that makes it so when the ingredients and instruction are small they take less space.
        if len(ingredients_and_instructions) > 850:
            ingredients_and_instructions_text = ctk.CTkLabel(recipes_window, text=ingredients_and_instructions, font=("default", 12), justify="center")
            ingredients_and_instructions_text.grid(rowspan=6, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        else:
            ingredients_and_instructions_text = ctk.CTkLabel(recipes_window, text=ingredients_and_instructions, font=("default", 12), justify="center")
            ingredients_and_instructions_text.grid(rowspan=4, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        #A check that cuts up the string if its on the long side.
        if len(suffix) < 75:
            suffix_text = ctk.CTkLabel(recipes_window, text=suffix, font=("default", 12), justify="center")
            suffix_text.grid(rowspan=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        else:
            suffix.find(".")
            index = suffix.find(" ", suffix.find(" ") + 100)
            suffix = suffix[:index] + "\n" + suffix[index:]
            suffix_text = ctk.CTkLabel(recipes_window, text=suffix, font=("default", 12), justify="center")
            suffix_text.grid(rowspan=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

    else:
        #The error meesage for if the connection wasn't good.
        generating_text.destroy()
        error_message = ctk.CTkLabel(recipes_window, text="Er is iets mis gegaan.", font=("default", 24))
        error_message.grid(row=6, column=1, columnspan=2, padx=10, pady=10)


def quitall():
    settings_window.destroy()
    main.destroy()


main_menu()
