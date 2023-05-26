import customtkinter as ctk
import tkinter as tk
from imutils.video import VideoStream
from pyzbar import pyzbar
import datetime
import imutils
import time
import threading
import json
import requests
from datetime import date, datetime, timedelta
import mysql.connector
from tkcalendar import *
import os

if os.environ.get('DISPLAY','') == '':
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
                 **kwargs):
        super().__init__(*args, width=width, height=height, **kwargs)

        self.title = title

        self.configure(fg_color=("gray78", "gray28"))

        self.grid_columnconfigure((1,2), weight=4, uniform="a")
        self.grid_columnconfigure((0,3), weight=1, uniform="a")
        #self.grid_rowconfigure((0,1,2), weight=1, uniform="a")

        self.title = ctk.CTkLabel(self, text=title, font=("default", 26))
        self.title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=10)

        self.rowcounter = 1

        #Loop die alle items als tuples uit de database haalt
        test1 = item(self, 1, "30-5-2023", 2, self.rowcounter)
        self.rowcounter += 1
        test2 = item(self, 1, "30-5-2023", 2, self.rowcounter)


class item():
    def __init__(self, root, itemid, date, amount, rownumber):
        self.root = root
        self.id = itemid
        self.date = date
        self.amount = amount
        self.rownumber = rownumber
        self.button = ctk.CTkButton(root, text="-", command=lambda: self.minusamount())
        self.button.grid(column=0, row=rownumber, padx=10)
        self.label = ctk.CTkLabel(root, text=str(amount) + ": " + date)
        self.label.grid(column=1, row=rownumber, sticky="w", padx=10, pady=10)

    def minusamount(self):
        if self.amount > 1:
            #SQL update - 1
            self.amount -= 1
            self.label.configure(text=str(self.amount) + ": " + self.date)

        else:
            #SQL remove
            self.selfdel()

    def selfdel(self):
        # Destroy label and button and make them invisible
        del self.id
        del self.date
        del self.amount


def mainmenu():
    global main
    main = Window()

    main.columnconfigure((0, 1), weight=1, uniform="a")
    main.rowconfigure(0, weight=1, uniform="a")
    main.rowconfigure((1, 2), weight=2, uniform="a")

    title = ctk.CTkLabel(main, text="iFridge", font=("default", 32))
    title.grid(row=0, column=0, sticky="new", padx=20, pady=10, columnspan=2)

    button1 = ctk.CTkButton(main, text="Producten scannen", command=lambda: productscan(), font=("default", 24))
    button1.grid(row=1, column=0, sticky="news", padx=20, pady=10)

    button2 = ctk.CTkButton(main, text="Productenlijst", font=("default", 24), command=lambda: productlist())
    button2.grid(row=1, column=1, sticky="news", padx=20, pady=10)

    button1 = ctk.CTkButton(main, text="Instellingen", font=("default", 24), command=lambda: settings())
    button1.grid(row=2, column=0, sticky="news", padx=20, pady=10)

    main.mainloop()


def productscan():
    global result
    global prodductscanwindow
    global amount
    global amountLabel
    global cal
    amount = 1
    productscanwindow = Window()

    productscanwindow.columnconfigure((0, 4), weight=1, uniform="a")
    productscanwindow.columnconfigure((1, 2, 3), weight=2, uniform="a")
    productscanwindow.rowconfigure(0, weight=1, uniform="a")
    productscanwindow.rowconfigure((1, 2, 3, 4, 5), weight=2, uniform="a")

    backbutton = ctk.CTkButton(productscanwindow, text="Terug", command=lambda: productscanwindow.destroy())
    backbutton.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

    scantitle = ctk.CTkLabel(productscanwindow, text="Product scannen", font=("default", 32))
    scantitle.grid(row=0, column=1, columnspan=3, sticky="new", padx=20, pady=10)

    button1 = ctk.CTkButton(productscanwindow, text="Scan", font=("default", 24), command=lambda: threading.Thread(target=scanproduct).start())
    button1.grid(row=1, column=0, sticky="news", padx=20, pady=10, columnspan=2)

    button2 = ctk.CTkButton(productscanwindow, text="Voeg toe", font=("default", 24), command=lambda: threading.Thread(target=insertproduct).start())
    button2.grid(row=5, column=3, sticky="es", padx=20, pady=10, columnspan=2)

    plusbutton = ctk.CTkButton(productscanwindow, text="+", font=("default", 24),command=lambda: threading.Thread(target=plusamount).start())
    plusbutton.grid(row=2, column=0, sticky="ews", padx=20, pady=10, columnspan=2)

    minusbutton = ctk.CTkButton(productscanwindow, text="-", font=("default", 24),
                               command=lambda: threading.Thread(target=minusamount).start())
    minusbutton.grid(row=4, column=0, sticky="new", padx=20, pady=10, columnspan=2)

    amountText = amount
    # Amount goed krijgen
    amountLabel = ctk.CTkLabel(productscanwindow, text=amountText, font=("default", 22))
    amountLabel.grid(row=3, column=0, sticky="nwes", padx=20, pady=10, columnspan=2)

    cal = Calendar(productscanwindow, selectmode="day", year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)
    cal.grid(row=2, column=2, sticky="nwes", padx=20, pady=10, columnspan=3, rowspan=3)

    result = ctk.CTkLabel(productscanwindow, text="Result: ", font=("default", 24))
    result.grid(row=1, column=2, sticky="new", padx=20, pady=10, columnspan=3)

    productscanwindow.mainloop()

def plusamount():
    global amount
    global amountLabel
    amount += 1
    amountLabel.configure(text=amount)

def minusamount():
    global amount
    global amountLabel
    if amount > 1:
        amount -= 1
        amountLabel.configure(text=amount)

def scanproduct():
    global productscanwindow
    global barcodeData
    global result
    global responseArray
    vs = VideoStream(usePiCamera=True).start()
    time.sleep(2.0)
    scanning = True
    while scanning:
        frame = vs.read()
        frame = imutils.resize(frame, width=400)
        barcodes = pyzbar.decode(frame)
        for barcode in barcodes:
            barcodeData = barcode.data.decode("utf-8")
            print(barcodeData)
            if(barcodeData != None):
                scanning = False
    vs.stop()
    result.configure(text="Scanning...")
    url = "https://world.openfoodfacts.org/api/v0/product/" + barcodeData + ".json"
    response = requests.get(url).text
    responseArray = json.loads(response)
    print(responseArray)
    print(responseArray['status'])
    if responseArray['status'] == 1:
        print("Product gevonden")
        print(responseArray['product']['brands'])
        print(responseArray['product']['product_name'])
        text = responseArray['product']['brands'] + " " + responseArray['product']['product_name']
        result.configure(text=text)
    else:
        print("Product niet gevonden")
        text = barcodeData + " product niet gevonden"
        result.configure(text=text)

def insertproduct():
    global responseArray
    global amount
    global cal

    if responseArray['status'] == 1:
        try:
            cnx = mysql.connector.connect(user='dbuser', password='Foodguardian', host='127.0.0.1', database='ifridge')
            cursor = cnx.cursor()
            addProduct = ("INSERT IGNORE INTO Product"
                           "(Productcode, Brand, Name)"
                           "VALUES (%s, %s, %s)")
            productData = (barcodeData, responseArray['product']['brands'], responseArray['product']['product_name'])
            cursor.execute(addProduct, productData)
            addItem = ("INSERT INTO Item"
                       "(Productcode, ExpirationDate, Amount)"
                       "VALUES (%s, %s, %s)")
            expirationDate = cal.selection_get()
            itemData = (barcodeData, expirationDate, amount)
            cursor.execute(addItem, itemData)
            cnx.commit()
            cursor.close()
            cnx.close()
            result.configure(text="Product toegevoegd")

        except mysql.connector.Error as err:
            print(err)


def productlist():
    productlistwindow = Window()

    productlistwindow.columnconfigure((0, 3), weight=1, uniform="a")
    productlistwindow.columnconfigure((1, 2), weight=2, uniform="a")
    productlistwindow.rowconfigure((0), weight=1, uniform="a")
    productlistwindow.rowconfigure((1, 2,), weight=2, uniform="a")

    backbutton = ctk.CTkButton(productlistwindow, text="Terug", command=lambda: productlistwindow.destroy())
    backbutton.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

    listtitle = ctk.CTkLabel(productlistwindow, text="Productenlijst", font=("default", 32))
    listtitle.grid(row=0, column=1, columnspan=2, sticky="new", padx=20, pady=10)

    product_frame = ctk.CTkScrollableFrame(master=productlistwindow)
    product_frame.grid(column=0, columnspan=4, row=1, rowspan=2, sticky="nsew")

    test = ProductItem(product_frame, title="test")
    test.grid(row=1, pady=10, padx=30, sticky="nsew")

    test2 = ProductItem(product_frame, title="test2")
    test2.grid(row=2, pady=10, padx=30, sticky="nsew")

    test3 = ProductItem(product_frame, title="test3")
    test3.grid(row=3, pady=10, padx=30, sticky="nsew")

    test4 = ProductItem(product_frame, title="test4")
    test4.grid(row=4, pady=10, padx=30, sticky="nsew")
    

    productlistwindow.mainloop()


def settings():
    global settingswindow
    settingswindow = ctk.CTk()
    settingswindow.title("iFridge")
    settingswindow.attributes("-fullscreen", True)
    settingswindow.bind("<Escape>", quit)

    settingswindow.columnconfigure((0, 3), weight=1, uniform="a")
    settingswindow.columnconfigure((1, 2), weight=2, uniform="a")
    settingswindow.rowconfigure((0), weight=1, uniform="a")
    settingswindow.rowconfigure((1, 2, 3, 4), weight=2, uniform="a")

    backbutton = ctk.CTkButton(settingswindow, text="Terug", command=lambda: settingswindow.destroy())
    backbutton.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

    settingstitle = ctk.CTkLabel(settingswindow, text="Instellingen", font=("default", 32))
    settingstitle.grid(row=0, column=1, columnspan=2, sticky="new", padx=20, pady=10)

    quitbutton = ctk.CTkButton(settingswindow, text="Quit", command=lambda: quitall(), font=("defaut", 24))
    quitbutton.grid(row=1, column=1, columnspan=2, sticky="news", padx=20, pady=10)

    settingswindow.mainloop()


def quitall():
    settingswindow.destroy()
    main.destroy()


mainmenu()
