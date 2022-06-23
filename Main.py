# -*- coding: utf-8 -*-
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5 import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import gdcm
import cv2 as cv2
import pydicom as dicom
from pydicom import dcmread
from pydicom.pixel_data_handlers.util import apply_voi_lut
import numpy as np
import re
import os
from tensorflow.keras.models import (Model, load_model, Sequential)
from tensorflow.keras.preprocessing import image
import tensorflow as tf
import pymysql

from Enterw import Ui_EnterWindow
from Mainw import Ui_MainWindow
from config import host, user, password, db_name


os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
exec_path = os.getcwd()
fn = 'n.jpg'

app = QtWidgets.QApplication(sys.argv)
EnterWindow = QtWidgets.QMainWindow()
ui = Ui_EnterWindow()
ui.setupUi(EnterWindow)
EnterWindow.show()


def openOtherWindow():
    """

    Show main window.

    """
    global MainWindow
    global fn
    global tumor
    global res
    global patient_flg
    global patient_id
    patient_id = 0
    patient_flg = False
    tumor = 0
    res = 0.00
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    EnterWindow.close()
    loadImage(MainWindow, 'default.jpg')
    MainWindow.show()

    def savePatient():
        """

        Save patient information or/and recognition results.

        """
        global res
        global tumor
        global patient_flg
        global patient_id
        try:
            connection = pymysql.connect(
                host=host,
                port=3306,
                user=user,
                password=password,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor)
            print("Successfully connected...")

            try:
                with connection.cursor() as cursor:
                    if patient_flg:
                        cursor.execute(
                            "UPDATE `patients` SET `patients`.`surname` = '" + ui.lineFam.text() + "',"
                            " `patients`.`name` = '" + ui.lineName.text() + "', "
                            "`patients`.`birthday` = '"+stringToDate(ui.lineDate.text())+"', "
                            " `patients`.`note` = '" + ui.plainTextEdit.toPlainText() + "',  "
                            "`patients`.`tumor` = '" + str(tumor) +"', "
                            "`patients`.`percent` = '" + str(res[4:6] + '.' + res[6:8]) + "'"
                            " WHERE `patients`.`id_patient` = +'" + str(patient_id) + "';")
                    else:
                        cursor.execute(
                            "INSERT INTO `patients` (`surname`, `name`, `birthday`, `note`, `tumor`, `percent`)  "
                            "VALUES ('" + ui.lineFam.text() + "','" + ui.lineName.text() + "', '"+stringToDate(ui.lineDate.text())+"'"
                            ", '" + ui.plainTextEdit.toPlainText() + "', '" + str(tumor) +"', '" + str(res[4:6] + '.' + res[6:8]) + "');")
                    patient_flg = False
                    patient_id = 0
                    connection.commit()
                    QMessageBox.about(MainWindow, "Сообщение", "Данные пациента успешно записаны!")
            finally:
                tumor = 0
                res = 0.00
                connection.close()
        except Exception as ex:
            print("Connection refused...")
            print(ex)


    def tumorPredict():
        """

        Detect of the presence of a tumor on the image.

        """
        global res
        global tumor
        img_path = os.path.join(exec_path, fn)
        try:
            model = load_model('VGG19_best4_orig.h5')
        except Exception as ex:
            print(ex)
        image_size = 224
        img = image.load_img(img_path, target_size=(image_size, image_size))
        x = image.img_to_array(img)
        x /= 255
        x = np.expand_dims(x, axis=0)
        prediction = model.predict(x)
        if prediction[[0]] < 0.5:
            tumor = 0
            res = str(1 - prediction[[0]])
            ui.lineRes.setText('Норма, вероятность: ' + res[4:6] + '.' + res[6:8] +  '%')
        else:
            tumor = 1
            res = str(prediction[[0]])
            ui.lineRes.setText('Опухоль, вероятность: '  + res[4:6] + '.' + res[6:8] +  '%')

    def openClick():
        """

        Load image and detect of the presence of a tumor on the image.

        """
        openFileNameDialog()
        tumorPredict()

    def loadNote():
        """

        Load a patient note.

        """
        global patient_flg
        global patient_id
        try:
            connection = pymysql.connect(
                host=host,
                port=3306,
                user=user,
                password=password,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor
            )
            print("Successfully connected...")

            try:
                with connection.cursor() as cursor:
                    rows = {}
                    cursor.execute("SELECT `patients`.`id_patient`, `patients`.`note` FROM `patients` WHERE `patients`.`surname` = '" + ui.lineFam.text() + "' "
                        "and `patients`.`name`= '" + ui.lineName.text() + "' and "
                        "`patients`.`birthday` = '"+stringToDate(ui.lineDate.text())+"';")
                    rows = cursor.fetchall()
                    if rows != ():
                        for row in rows:
                            if row['note'] != '':
                                patient_flg = True
                                patient_id = row['id_patient']
                                ui.plainTextEdit.setPlainText(row['note'])
                                QMessageBox.about(EnterWindow, "Сообщение", "Информация успешно загружена!")
                            else:
                                QMessageBox.about(EnterWindow, "Сообщение", "Для данного пациента нет заметки!")
                    else:
                        QMessageBox.about(EnterWindow, "Сообщение", "Такого пациента не существует!")

            finally:
                connection.close()
        except Exception as ex:
            print("Connection refused...")
            print(ex)

    ui.btnSave.clicked.connect(savePatient)
    ui.actiSave.triggered.connect(savePatient)
    ui.btnOpen.clicked.connect(openClick)
    ui.actiOpen.triggered.connect(openClick)
    ui.btnLoad.clicked.connect(loadNote)
    ui.actiExit.triggered.connect(app.quit)
    #ui.actiHelp.triggered.connect(test) # Help
    ui.actiAbout.triggered.connect(about)


def stringToDate(dt):
    """

    Convert string to date.

    """
    temp_str = dt.split('.')
    sql_date = temp_str[2] + '-' + temp_str[1] + '-' + temp_str[0]
    return sql_date

def about():
    """

    Show Readme.

    """
    QMessageBox.about(EnterWindow, "О программе", "Автор: Костоправов Антон Александрович\nГруппа: 4231\n2021 год.")

def openFileNameDialog():
    """

    Show FileDialog to select an image.

    """
    global fn
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileName, _ = QFileDialog.getOpenFileName(MainWindow, "QFileDialog.getOpenFileName()", "",
                                              "All Files (*);;MRI Files (*.dcm)", options=options)

    if fileName:
        temp_dcm = fileName.split('.')
        if temp_dcm[1] == 'dcm':
            convertFile(fileName, temp_dcm[0] + '.jpg')
        fn = temp_dcm[0] + '.jpg'
        img_path = os.path.join(exec_path, fn)
        image_size = 300
        img = image.load_img(img_path, target_size=(image_size, image_size))
        img.save(fn)
        redraw(MainWindow, fn)

def convertFile(dcm_file_path, jpg_file_path):
    """

    Convert dcm file to jpg file.

    """
    dicom_img = dicom.read_file(dcm_file_path)
    img = apply_voi_lut(dicom_img.pixel_array, dicom_img)
    scaled_img = cv2.convertScaleAbs(img - np.min(img), alpha=(255.0 / min(np.max(img) - np.min(img), 10000)))
    cv2.imwrite(jpg_file_path, scaled_img)

def redraw(self,file_name):
    """

    Refresh image.

    """
    pixmap = QPixmap(file_name)
    self.label.setPixmap(pixmap)

def loadImage(self,file_name):
    """

    Load image.

    """
    pixmap = QPixmap(file_name)
    self.label = QLabel(self)
    self.label.setGeometry(QtCore.QRect(18, 40, 300, 300))
    self.label.setPixmap(pixmap)

def doctorEnter():
    """

    Verify the entered data with the doctors registered in the database.

    """
    try:
        connection = pymysql.connect(
            host=host,
            port=3306,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("Successfully connected...")

        try:
            with connection.cursor() as cursor:
                rows = {}
                cursor.execute("SELECT `doctors`.`pass` FROM `doctors` WHERE `doctors`.`surname` = '" + ui.lineFam.text() + "'"
                " and `doctors`.`name`= '" + ui.lineName.text() + "';")
                rows = cursor.fetchall()
                if rows != ():
                    for row in rows:
                        if row['pass'] == ui.linePass.text():
                            QMessageBox.about(EnterWindow, "Сообщение", "Вход успешно выполнен!")
                            openOtherWindow()
                        else:
                            QMessageBox.about(EnterWindow, "Сообщение", "Неверный пароль!")
                else:
                    QMessageBox.about(EnterWindow, "Сообщение", "Такого пользователя не существует!")

        finally:
            connection.close()
    except Exception as ex:
        print("Connection refused...")
        print(ex)
    openOtherWindow()

def doctorRegistration():
    """

    Register of doctor in the database.

    """
    try:
        connection = pymysql.connect(
            host=host,
            port=3306,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("Successfully connected...")

        try:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO `doctors` (`surname`, `name`, `pass`) "
                               "VALUES ('" + ui.lineFam.text() + "','" + ui.lineName.text() + "', '" + ui.linePass.text() + "');")
                connection.commit()
                QMessageBox.about(EnterWindow, "Сообщение", "Новый пользователь успешно зарегистрирован!")
        finally:
            connection.close()
    except Exception as ex:
        print("Connection refused...")
        print(ex)

ui.buttonEnter.clicked.connect(doctorEnter)
ui.buttonRegistration.clicked.connect(doctorRegistration)

sys.exit(app.exec_())
