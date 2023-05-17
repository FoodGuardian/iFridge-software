import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from imutils.video import VideoStream
from pyzbar import pyzbar
import datetime
import imutils
import time
import cv2
import threading

class Window(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("iFridge")
        self.attributes("-fullscreen", True)
        self.bind("<Escape>", quit)


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
    productscanwindow = Window()

    productscanwindow.columnconfigure((0, 3), weight=1, uniform="a")
    productscanwindow.columnconfigure((1, 2), weight=2, uniform="a")
    productscanwindow.rowconfigure((0), weight=1, uniform="a")
    productscanwindow.rowconfigure((1, 2), weight=2, uniform="a")

    backbutton = ctk.CTkButton(productscanwindow, text="Terug", command=lambda: productscanwindow.destroy())
    backbutton.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

    scantitle = ctk.CTkLabel(productscanwindow, text="Product scannen", font=("default", 32))
    scantitle.grid(row=0, column=1, columnspan=2, sticky="new", padx=20, pady=10)

    button1 = ctk.CTkButton(productscanwindow, text="Scan", font=("default", 24), command=lambda: threading.Thread(target=scanproduct).start())
    button1.grid(row=1, column=0, sticky="news", padx=20, pady=10, columnspan=2)

    result = ctk.CTkLabel(productscanwindow, text="Result: ", font=("default", 24))
    result.grid(row=1, column=2, sticky="new", padx=20, pady=10, columnspan=2)

    productscanwindow.mainloop()
    #Lijkt er op dat de code na de mainloop niet uitgevoerd wordt


def scanproduct():
    global barcodeData
    global result
    vs = VideoStream(usePiCamera=True).start()
    time.sleep(2.0)
    scanning = True
    while scanning:
        frame = vs.read()
        frame = imutils.resize(frame, width=400)
        barcodes = pyzbar.decode(frame)
        for barcode in barcodes:
            barcodeData = barcode.data.decode("utf-8")
            #barcodeType = barcode.type
            print(barcodeData)
            if(barcodeData != None):
                scanning = False
    #messagebox.showinfo("Productcode", barcodeData)
    vs.stop()
    result.configure(text=barcodeData)

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
