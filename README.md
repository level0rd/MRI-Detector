# MRI-detector
The program, using the VGG19 convolutional neural network, detects tumors on MRI images. Before using the program, the doctor needs to register. After registration, it is necessary to enter the last name, first name, and password. Upon successful login, the main window of the program becomes available. The program allows you to:
- load the MRI image of the patient (after successful loading, the image is automatically processed by the neural network);
- enter necessary patient information (last name, first name, birthday, and necessary additional information);
- save patient information and recognition results;
- load previously saved additional information.

MySQL database is used for storing information.

## Install
- Install the database MySQL and MySQL Workbench 8.0. 
- Import database from DataBase.sql.
- Clone repo and install requirements.txt in a Python<=3.7.0 environment. 
- Download neural network [weights](https://disk.yandex.ru/d/EGmMmtmHDI0FrQ).
- Use Main.py for launch.

## Architecture
<p align="center">
  <img width="1000" alt="Arch2" src="https://user-images.githubusercontent.com/45522296/175291966-d69670d9-374b-450f-8402-2ee0baf7e67b.png">
</p>

## Enter form
<p align="center">
  <img width="300" alt="Enter" src="https://user-images.githubusercontent.com/45522296/175291446-4efdbb0a-1531-4b41-9bf1-15bb606f930a.png">
</p>

## Main form
<p align="center">
  <img width="800" alt="175292901-e779eb8d-6277-43d7-ba18-ed891f8e8474" src="https://github.com/level0rd/MRI-Detector/assets/45522296/914cad90-8e16-449e-9765-0de2636621ff">
</p>
