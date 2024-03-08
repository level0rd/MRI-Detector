import sys
import os
import numpy as np
import cv2
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

import pydicom as dicom
from pydicom.pixel_data_handlers.util import apply_voi_lut


from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PyQt5.QtGui import QPixmap, QImage
from enter_form import Ui_EnterWindow
from main_form import Ui_MainWindow

from config import host, port, user, password, db_name
import pymysql

PROJECT_DIR = os.getcwd()
IMAGE_SIZE = 224


class Patient:
    def __init__(self, image_path: str):
        """
        Initialize the Patient class.

        Args:
            image_path (str): Path to the patient's image.
        """
        self.id_patient = 0
        self.tumor = 0
        self.prediction = 0.00
        self.image_path = image_path
        self.exist = False


patient = Patient('../n.jpg')


class EnterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_EnterWindow()
        self.ui.setupUi(self)
        self.ui.buttonEnter.clicked.connect(self.doctor_enter)
        self.ui.buttonRegistration.clicked.connect(self.doctor_registration)

    def open_main_window(self) -> None:
        """
        Open the main window.
        """
        self.mainWindow = MainWindow()
        self.mainWindow.show()
        self.hide()

    def doctor_enter(self) -> None:
        """

        Verification the entered data with the doctors registered in the database.

        """
        surname = self.ui.lineSurename.text()
        name = self.ui.lineName.text()
        doctor_password = self.ui.linePass.text()
        try:
            connection = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor
            )
            print("Successfully connected...")

            try:
                with connection.cursor() as cursor:
                    rows = {}
                    cursor.execute(
                        "SELECT `doctors`.`pass` FROM `doctors` WHERE `doctors`.`surname` = '" + surname + "'"
                        " and `doctors`.`name`= '" + name + "';")

                    rows = cursor.fetchall()
                    if rows != ():
                        for row in rows:
                            if row['pass'] == doctor_password:
                                QMessageBox.about(self, "Сообщение", "Вход успешно выполнен!")
                                self.open_main_window()
                            else:
                                QMessageBox.about(self, "Сообщение", "Неверный пароль!")
                    else:
                        QMessageBox.about(self, "Сообщение", "Такого пользователя не существует!")
            finally:
                connection.close()
        except Exception as ex:
            print("Connection refused...")
            print(ex)

    def doctor_registration(self)-> None:
        """

        Registration of doctor in the database.

        """
        surname = self.ui.lineSurename.text()
        name = self.ui.lineName.text()
        doctor_password = self.ui.linePass.text()
        try:
            connection = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor
            )
            print("Successfully connected...")

            try:
                with connection.cursor() as cursor:
                    cursor.execute("INSERT INTO `doctors` (`surname`, `name`, `pass`) "
                                   "VALUES ('" + surname + "','" + name + "', '" + doctor_password + "');")
                    connection.commit()
                    QMessageBox.about(self, "Сообщение", "Новый пользователь успешно зарегистрирован!")
            finally:
                connection.close()
        except Exception as ex:
            print("Connection refused...")
            print(ex)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.btnSave.clicked.connect(self.save_patient)
        self.ui.actiSave.triggered.connect(self.save_patient)
        self.ui.btnOpen.clicked.connect(self.open_mri_file)
        self.ui.actiOpen.triggered.connect(self.open_mri_file)
        self.ui.btnLoad.clicked.connect(self.load_note)
        self.ui.actiExit.triggered.connect(QApplication.instance().quit)
        self.ui.actiAbout.triggered.connect(self.about)

    def redraw(self, file_name: str) -> None:
        """
        Refreshes the image.

        Args:
            file_name (str): The path of the image file.

        """
        image = cv2.imread(file_name)
        resized_image = cv2.resize(image, (290, 290))
        rgb_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(q_img)
        self.ui.label.setPixmap(pixmap)

    def convert_file(dcm_file_path: str, jpg_file_path: str) -> None:
        """
        Convert a DICOM file to a JPG file.

        Args:
            dcm_file_path (str): The path to the DICOM file.
            jpg_file_path (str): The path to save the JPG file.

        """
        dicom_img = dicom.read_file(dcm_file_path)
        img = apply_voi_lut(dicom_img.pixel_array, dicom_img)
        scaled_img = cv2.convertScaleAbs(img - np.min(img), alpha=(255.0 / min(np.max(img) - np.min(img), 10000)))
        cv2.imwrite(jpg_file_path, scaled_img)

    def tumor_predict(self) -> None:
        """
        Determine the presence of a tumor on the image.

        """
        img_path = os.path.join(PROJECT_DIR, patient.image_path)
        try:
            model = load_model('VGG19_best4_orig.h5')
        except Exception as ex:
            print(ex)
        img = image.load_img(img_path, target_size=(IMAGE_SIZE, IMAGE_SIZE))
        x = image.img_to_array(img)
        x /= 255
        x = np.expand_dims(x, axis=0)

        prediction = model.predict(x)
        if prediction[[0]] < 0.5:
            patient.tumor = 0
            patient.prediction = str(1 - prediction[[0]])
            self.ui.lineRes.setText('Норма, вероятность: ' + patient.prediction[4:6] + '.' + patient.prediction[6:8] +  '%')
        else:
            patient.tumor = 1
            patient.prediction = str(prediction[[0]])
            self.ui.lineRes.setText('Опухоль, вероятность: '  + patient.prediction[4:6] + '.' + patient.prediction[6:8] +  '%')

    def open_file_name_dialog(self) -> None:
        """
        Show FileDialog to select an image.

        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "All Files (*);;MRI Files (*.dcm)", options=options)

        if file_name:
            temp_dcm = file_name.split('.')
            # Intercepting and converting DCM files
            if temp_dcm[1] == 'dcm':
                self.convert_file(file_name, temp_dcm[0] + '.jpg')
            # Path to the image in JPG
            patient.image_path = temp_dcm[0] + '.jpg'
            # Resize
            img_path = os.path.join(PROJECT_DIR, patient.image_path)
            img = image.load_img(img_path, target_size=(IMAGE_SIZE, IMAGE_SIZE))
            img.save(patient.image_path)
            self.redraw(patient.image_path)

    def string_to_date(sself, date: str) -> str:
        """
        Convert string to date.

        Args:
            date (str): The date string in the format 'dd.mm.yyyy'.

        Returns:
            str: The converted date string in the format 'yyyy-mm-dd'.
        """
        temp_str = date.split('.')
        sql_date = temp_str[2] + '-' + temp_str[1] + '-' + temp_str[0]
        return sql_date

    def open_mri_file(self) -> None:
        """
        Load a patient note.

        """
        self.open_file_name_dialog()
        self.tumor_predict()

    def save_patient(self) -> None:
        """
        Saving patient information or/and recognition results.
        """
        surname = self.ui.lineSurename.text()
        name = self.ui.lineName.text()
        date = self.ui.lineDate.text()
        description = self.ui.plainTextEdit.toPlainText()

        try:
            connection = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor)
            print("Successfully connected...")

            try:
                with connection.cursor() as cursor:
                    if patient.exist:
                        cursor.execute(
                            "UPDATE `patients` SET `patients`.`surname` = '" + surname + "', "
                            "`patients`.`name` = '" + name + "', "
                            "`patients`.`birthday` = '" + self.string_to_date(date) + "', "
                            "`patients`.`note` = '" + description + "', "
                            "`patients`.`tumor` = '" + str(patient.tumor) + "', "
                            "`patients`.`percent` = '" + str(patient.prediction[4:6] + '.' + patient.prediction[6:8]) + "' "
                            "WHERE `patients`.`id_patient` = +'" + str(patient.patient_id) + "';"
                        )
                    else:
                        cursor.execute(
                            "INSERT INTO `patients` (`surname`, `name`, `birthday`, `note`, `tumor`, `percent`) "
                            "VALUES ('" + surname + "','" + name + "', '" + self.string_to_date(date) + "'"
                            ", '" + description + "', '" + str(patient.tumor) + "', '" + str(
                            patient.prediction[4:6] + '.' + patient.prediction[6:8]) + "');"
                        )
                    patient.exist = False
                    patient.patient_id = 0
                    connection.commit()
                    QMessageBox.about(self, "Сообщение", "Данные пациента успешно записаны!")
            finally:
                patient.tumor = 0
                patient.prediction = 0.00
                connection.close()
        except Exception as ex:
            print("Connection refused...")
            print(ex)

    def load_note(self) -> None:
        """
        Load a patient note.
        """
        surname = self.ui.lineSurename.text()
        name = self.ui.lineName.text()
        date = self.ui.lineDate.text()
        try:
            connection = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor
            )
            print("Successfully connected...")

            try:
                with connection.cursor() as cursor:
                    rows = {}
                    cursor.execute(
                        "SELECT `patients`.`id_patient`, `patients`.`note` "
                        "FROM `patients` "
                        "WHERE `patients`.`surname` = '" + surname + "' "
                        "and `patients`.`name`= '" + name + "' "
                        "and `patients`.`birthday` = '" + self.string_to_date(date) + "';"
                    )
                    rows = cursor.fetchall()
                    if rows != ():
                        for row in rows:
                            if row['note'] != '':
                                patient.exist = True
                                patient.patient_id = row['id_patient']
                                self.ui.plainTextEdit.setPlainText(row['note'])
                                QMessageBox.about(self, "Сообщение", "Информация успешно загружена!")
                            else:
                                QMessageBox.about(self, "Сообщение", "Для данного пациента нет заметки!")
                    else:
                        QMessageBox.about(self, "Сообщение", "Такого пациента не существует!")

            finally:
                connection.close()
        except Exception as ex:
            print("Connection refused...")
            print(ex)

    def about(self) -> None:
        """
        Show Readme.
        """
        QMessageBox.about(self, "О программе", "Автор: Костоправов Антон Александрович\nГруппа: 4231\n2021 год.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    enterWindow = EnterWindow()
    enterWindow.show()
    sys.exit(app.exec_())
