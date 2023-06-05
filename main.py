import datetime
import json
import os
import subprocess
import threading
import time
from datetime import datetime
import customtkinter as ctk
import imutils
import mysql.connector
import requests
from imutils.video import VideoStream
from pyzbar import pyzbar
from tkcalendar import *

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

    button1 = ctk.CTkButton(main, text="Producten scannen", command=lambda: product_scan(), font=("default", 24))
    button1.grid(row=1, column=0, sticky="news", padx=20, pady=10)

    button2 = ctk.CTkButton(main, text="Handmatig toevoegen", command=lambda: add_manually(), font=("default", 24))
    button2.grid(row=1, column=1, sticky="news", padx=20, pady=10)

    button1 = ctk.CTkButton(main, text="Productenlijst", font=("default", 24), command=lambda: product_list())
    button1.grid(row=2, column=0, sticky="news", padx=20, pady=10)

    button2 = ctk.CTkButton(main, text="Instellingen", font=("default", 24), command=lambda: settings())
    button2.grid(row=2, column=1, sticky="news", padx=20, pady=10)

    main.mainloop()


def product_scan():
    global result
    global product_scan_window
    global amount
    global amount_label
    global cal
    amount = 1
    product_scan_window = Window()

    product_scan_window.columnconfigure((0, 4), weight=1, uniform="a")
    product_scan_window.columnconfigure((1, 2, 3), weight=2, uniform="a")
    product_scan_window.rowconfigure(0, weight=1, uniform="a")
    product_scan_window.rowconfigure((1, 2, 3, 4, 5), weight=2, uniform="a")

    back_button = ctk.CTkButton(product_scan_window, text="Terug", command=lambda: product_scan_window.destroy())
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
    vs = VideoStream(usePiCamera=True).start()
    time.sleep(2.0)
    scanning = True
    result.configure(text="Scanning...")
    while scanning:
        frame = vs.read()
        frame = imutils.resize(frame, width=400)
        barcodes = pyzbar.decode(frame)
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            print(barcode_data)
            if (barcode_data != None):
                scanning = False
    vs.stop()
    result.configure(text="Product zoeken...")
    url = "https://world.openfoodfacts.org/api/v0/product/" + barcode_data + ".json"
    get_response()
    response_array = json.loads(response)
    print(response_array)
    print(response_array['status'])
    if response_array['status'] == 1:
        print("Product gevonden")
        print(response_array['product']['brands'])
        print(response_array['product']['product_name'])
        text = response_array['product']['brands'] + " " + response_array['product']['product_name']
        result.configure(text=text)
    else:
        print("Product niet gevonden")
        text = barcode_data + " product niet gevonden"
        result.configure(text=text)


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


def add_manually():
    global product_name
    global amount
    global cal
    global result
    amount = 1
    global amount_label
    open_osk = False
    global add_manually_window

    def close_osk():
        if open_osk:
            subprocess.Popen("/home/user/Desktop/killkeyboard.sh")

    def handle_click(event):
        p = subprocess.Popen("/home/user/Desktop/keyboard.sh")
        open_osk = True

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

    if response_array['status'] == 1:
        try:
            cnx = mysql.connector.connect(user='dbuser', password='Foodguardian', host='127.0.0.1', database='ifridge')
            cursor = cnx.cursor()
            add_product = ("INSERT IGNORE INTO Product"
                          "(Productcode, Brand, Name)"
                          "VALUES (%s, %s, %s)")
            product_data = (barcode_data, response_array['product']['brands'], response_array['product']['product_name'])
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

    recipes_button = ctk.CTkButton(settings_window, text="Recepten Maker", command=lambda: recipes(), font=("defaut", 24))
    recipes_button.grid(row=2, column=1, columnspan=2, sticky="news", padx=20, pady=10)

    settings_window.mainloop()

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
    back_button.grid(row=0, column=0, sticky="nwse", padx=5, pady=5)

    list_title = ctk.CTkLabel(recipes_window, text="Recepten Maker", font=("default", 32))
    list_title.grid(row=0, rowspan=2, column=1, columnspan=2, sticky="new", padx=20, pady=10)

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

    dropdown = ctk.CTkOptionMenu(master=recipes_window, values=products)
    dropdown.grid(row=2, column=1, columnspan=2, sticky="nsew", padx=10, pady=10)

    generate_button = ctk.CTkButton(recipes_window, width=300, text="maak recept", command=lambda: threading.Thread(target=generate_recipie).start())
    generate_button.grid(row=3, column=1, columnspan=2, sticky="nsew", padx=10, pady=10)

    recipes_window.mainloop()


def generaterecipie():
    main_ingredient = str(dropdown.get())

    try:
        response = requests.post("http://ifridge.local/recipe", data={"mainIngredient": main_ingredient, "ingredients": products})
        recipe_Title = response.json()["prefix"]
        ingredient_List = response.json()["ingredients"]
        recipe_instructions = response.json()["instructions"]
        suffix = response.json()["suffix"]
    except requests.exceptions.ConnectionError:
        response

    recipe_Title_Text = ctk.CTkLabel(recipes_window, text=recipe_Title, font=("default", 16), justify="center", bg_color="grey")
    recipe_Title_Text.grid(row=4, column=1, columnspan=2, padx=10, pady=10)

    ingridient_list_Text = ctk.CTkLabel(recipes_window, text=ingredient_List, font=("default", 16), justify="center", bg_color="grey")
    ingridient_list_Text.grid(row=5, rowspan=3, column=1, columnspan=2, padx=10, pady=10)

    recipe_instructions_Text = ctk.CTkLabel(recipes_window, text=recipe_instructions, font=("default", 16), justify="center", bg_color="grey")
    recipe_instructions_Text.grid(row=5, rowspan=3, column=2, columnspan=2, padx=10, pady=10)

    suffix_Text = ctk.CTkLabel(recipes_window, text=suffix, font=("default", 16), justify="center",bg_color="grey")
    suffix_Text.grid(row=8, rowspan=1, column=1, columnspan=2, padx=10, pady=10)


def quitall():
    settings_window.destroy()
    main.destroy()


main_menu()
