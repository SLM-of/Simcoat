import sys
import json
import os
import requests
import base64
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QPainter, QColor, QPixmap, QIcon, QAction
from PyQt6.QtCore import Qt, QSize, QRect, QByteArray

DATA_FILE = "users.json"

def save_user(username, email, password, photo_data=None):
    users = load_users()
    users[username] = {
        "email": email,
        "password": password,
        "photo": photo_data or users.get(username, {}).get("photo", None)
    }
    with open(DATA_FILE, "w") as f:
        json.dump(users, f)

def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def validate_login(username, password):
    users = load_users()
    return username in users and users[username]["password"] == password

class VerticalLine(QWidget):
    def __init__(self, height=60):
        super().__init__()
        self.height = height
        self.setFixedSize(4, self.height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#1edb5c"))
        painter.drawRect(QRect(0, 0, 4, self.height))

class ProfileDialog(QWidget):
    def __init__(self, parent, username):
        super().__init__()
        self.parent = parent
        self.username = username
        self.users = load_users()
        self.setWindowTitle(f"Profil de @{username}")
        self.setFixedSize(350, 200)
        self.setStyleSheet("background:white;")

        layout = QVBoxLayout(self)

        # Pseudo row
        pseudo_layout = QHBoxLayout()
        pseudo_label = QLabel("Pseudo:")
        pseudo_label.setFixedWidth(60)
        self.pseudo_edit = QLineEdit(username)
        self.pseudo_edit.setReadOnly(True)
        self.pseudo_edit.setStyleSheet("border:1px solid gray; padding:5px;")
        self.pseudo_edit.setFixedWidth(180)

        btn_change_pseudo = QPushButton("Chg")
        btn_change_pseudo.setStyleSheet("background:red; color:white; font-weight:bold;")
        btn_change_pseudo.setFixedWidth(40)
        btn_change_pseudo.clicked.connect(self.enable_pseudo_edit)

        # Photo profile mini
        self.photo_label = QLabel()
        self.photo_label.setFixedSize(40,40)
        self.photo_label.setStyleSheet("border: 2px solid green; border-radius: 20px;")
        self.load_photo()

        # bouton pour changer photo
        btn_change_photo = QPushButton("Changer photo")
        btn_change_photo.setStyleSheet("background:#1edb5c; color:white; padding:5px;")
        btn_change_photo.clicked.connect(self.change_photo)

        pseudo_layout.addWidget(pseudo_label)
        pseudo_layout.addWidget(self.pseudo_edit)
        pseudo_layout.addWidget(btn_change_pseudo)
        pseudo_layout.addWidget(self.photo_label)
        pseudo_layout.addWidget(btn_change_photo)

        # Password row
        pass_layout = QHBoxLayout()
        pass_label = QLabel("Mot de passe:")
        pass_label.setFixedWidth(80)
        self.pass_edit = QLineEdit(self.users[username]["password"])
        self.pass_edit.setReadOnly(True)
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_edit.setFixedWidth(180)
        self.pass_edit.setStyleSheet("border:1px solid gray; padding:5px;")

        btn_eye = QPushButton("👁")
        btn_eye.setCheckable(True)
        btn_eye.setFixedWidth(40)
        btn_eye.clicked.connect(self.toggle_password)

        btn_change_pass = QPushButton("Chg")
        btn_change_pass.setStyleSheet("background:red; color:white; font-weight:bold;")
        btn_change_pass.setFixedWidth(40)
        btn_change_pass.clicked.connect(self.enable_pass_edit)

        pass_layout.addWidget(pass_label)
        pass_layout.addWidget(self.pass_edit)
        pass_layout.addWidget(btn_eye)
        pass_layout.addWidget(btn_change_pass)

        # Save changes button
        btn_save = QPushButton("Enregistrer")
        btn_save.setStyleSheet("background:#3897f0; color:white; padding:10px; border-radius:5px;")
        btn_save.clicked.connect(self.save_changes)

        # Disconnect button bottom left
        btn_logout = QPushButton("Se déconnecter")
        btn_logout.setStyleSheet("background:red; color:white; font-weight:bold; padding:10px; border-radius:5px;")
        btn_logout.clicked.connect(self.logout)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(btn_logout)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_save)

        layout.addLayout(pseudo_layout)
        layout.addLayout(pass_layout)
        layout.addStretch()
        layout.addLayout(bottom_layout)

    def load_photo(self):
        photo_data = self.users[self.username].get("photo", None)
        if photo_data:
            pixmap = QPixmap()
            pixmap.loadFromData(base64.b64decode(photo_data))
            pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.photo_label.setPixmap(pixmap)
        else:
            # Placeholder icon
            self.photo_label.setText("No Photo")
            self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def change_photo(self):
        file_dialog = QFileDialog(self, "Choisir une photo", "", "Images (*.png *.jpg *.jpeg)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                QMessageBox.warning(self, "Erreur", "Image non valide.")
                return
            # Redimensionner image pour stockage léger
            pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            ba = QByteArray()
            buffer = QBuffer(ba)
            buffer.open(QBuffer.OpenModeFlag.WriteOnly)
            pixmap.save(buffer, "PNG")
            photo_b64 = base64.b64encode(ba.data()).decode('utf-8')
            # Sauvegarder en mémoire temporaire, pas encore dans fichier
            self.new_photo_data = photo_b64
            self.photo_label.setPixmap(pixmap.scaled(40,40,Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def enable_pseudo_edit(self):
        self.pseudo_edit.setReadOnly(False)
        self.pseudo_edit.setFocus()

    def enable_pass_edit(self):
        self.pass_edit.setReadOnly(False)
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        self.pass_edit.setFocus()

    def toggle_password(self, checked):
        if checked:
            self.pass_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def save_changes(self):
        new_pseudo = self.pseudo_edit.text().strip()
        new_pass = self.pass_edit.text().strip()
        if not new_pseudo:
            QMessageBox.warning(self, "Erreur", "Le pseudo ne peut pas être vide.")
            return
        if len(new_pass) < 6:
            QMessageBox.warning(self, "Erreur", "Le mot de passe doit contenir au moins 6 caractères.")
            return
        # Vérifier si pseudo changé et pas déjà pris
        if new_pseudo != self.username:
            users = load_users()
            if new_pseudo in users:
                QMessageBox.warning(self, "Erreur", "Ce pseudo est déjà utilisé.")
                return
            # Modifier pseudo dans le fichier: supprimer l'ancien, ajouter le nouveau
            user_data = users.pop(self.username)
            user_data["password"] = new_pass
            if hasattr(self, 'new_photo_data'):
                user_data["photo"] = self.new_photo_data
            users[new_pseudo] = user_data
            with open(DATA_FILE, "w") as f:
                json.dump(users, f)
            self.username = new_pseudo
            self.parent.current_user = new_pseudo
            QMessageBox.information(self, "Succès", "Pseudo et/ou mot de passe modifiés.")
            self.close()
            self.parent.main_ui(new_pseudo)
        else:
            # Sinon on modifie juste password et photo
            users = load_users()
            user_data = users[self.username]
            user_data["password"] = new_pass
            if hasattr(self, 'new_photo_data'):
                user_data["photo"] = self.new_photo_data
            users[self.username] = user_data
            with open(DATA_FILE, "w") as f:
                json.dump(users, f)
            QMessageBox.information(self, "Succès", "Mot de passe modifié.")
            self.close()
            self.parent.main_ui(self.username)

    def logout(self):
        self.close()
        self.parent.current_user = None
        self.parent.login_ui()

class Instaclone(QWidget):
    ICON_URLS = [
        "https://images.icon-icons.com/1997/PNG/512/architecture_building_home_house_property_icon_123288.png",  # maison
        "https://cdn-icons-png.flaticon.com/512/622/622669.png",    # rechercher
        "https://cdn-icons-png.flaticon.com/512/992/992651.png",    # plus
        "https://images.icon-icons.com/3385/PNG/512/conversation_speak_discussion_speech_bubble_talk_message_communication_chat_icon_212632.png",  # chat
        "https://cdn-icons-png.flaticon.com/512/1077/1077063.png",  # profil
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SimCoat")
        self.setFixedSize(400, 600)
        self.setStyleSheet(
            "background-color: white;"
            "background-repeat: no-repeat;"
            "background-position: center;"
            "background-size: cover;"
        )
        self.layout = QVBoxLayout(self)
        self.current_user = None
        self.login_ui()

    def clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if widget := item.widget():
                widget.setParent(None)

    def login_ui(self):
        self.current_user = None
        self.clear_layout()

        title = QLabel()
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setText(
            "<span style='font-family:Mistral; font-size:43pt; font-weight:bold;'>"
            "<span style='color:#f58529;'>S</span>"
            "<span style='color:#dd2a7b;'>i</span>"
            "<span style='color:#8134af;'>m</span>"
            "<span style='color:#515bd4;'>c</span>"
            "<span style='color:#f58529;'>o</span>"
            "<span style='color:#dd2a7b;'>a</span>"
            "<span style='color:#8134af;'>t</span>"
            "</span>"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Pseudo")
        self.username_input.setStyleSheet("border:2px solid #1edb5c; padding:10px; border-radius:6px;")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("border:2px solid #1edb5c; padding:10px; border-radius:6px;")

        login_btn = QPushButton("Connexion")
        login_btn.setStyleSheet("background:#3897f0; color:white; padding:10px; border-radius:5px;")
        login_btn.clicked.connect(self.check_login)

        switch_btn = QPushButton("Créer un compte")
        switch_btn.setStyleSheet("background:#1edb5c; color:white; padding:10px; border-radius:5px;")
        switch_btn.clicked.connect(self.signup_ui)

        self.layout.addStretch()
        for w in (title, self.username_input, self.password_input, login_btn, switch_btn):
            self.layout.addWidget(w)
        self.layout.addStretch()

    def signup_ui(self):
        self.clear_layout()

        title = QLabel()
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setText(
            "<span style='font-family:Mistral; font-size:43pt; font-weight:bold;'>"
            "<span style='color:#f58529;'>C</span>"
            "<span style='color:#dd2a7b;'>r</span>"
            "<span style='color:#8134af;'>é</span>"
            "<span style='color:#515bd4;'>e</span>"
            "<span style='color:#f58529;'>r</span>"
            "<span style='color:#dd2a7b;'> </span>"
            "<span style='color:#8134af;'>u</span>"
            "<span style='color:#515bd4;'>n</span>"
            "<span style='color:#f58529;'> </span>"
            "<span style='color:#dd2a7b;'>c</span>"
            "<span style='color:#8134af;'>o</span>"
            "<span style='color:#515bd4;'>m</span>"
            "<span style='color:#f58529;'>p</span>"
            "<span style='color:#dd2a7b;'>t</span>"
            "<span style='color:#8134af;'>e</span>"
            "</span>"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.new_user = QLineEdit()
        self.new_user.setPlaceholderText("Pseudo")
        self.new_email = QLineEdit()
        self.new_email.setPlaceholderText("Adresse e‑mail")
        self.new_pass = QLineEdit()
        self.new_pass.setPlaceholderText("Mot de passe (min 6 char.)")
        self.new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_pass = QLineEdit()
        self.confirm_pass.setPlaceholderText("Confirmer mot de passe")
        self.confirm_pass.setEchoMode(QLineEdit.EchoMode.Password)

        for field in (self.new_user, self.new_email, self.new_pass, self.confirm_pass):
            field.setStyleSheet("border:2px solid #1edb5c; padding:10px; border-radius:6px;")

        submit_btn = QPushButton("S'inscrire")
        submit_btn.setStyleSheet("background:#3897f0; color:white; padding:10px; border-radius:5px;")
        submit_btn.clicked.connect(self.create_account)

        retour_btn = QPushButton("← Retour")
        retour_btn.setStyleSheet("background:#1edb5c; color:white; padding:10px; border-radius:5px;")
        retour_btn.clicked.connect(self.login_ui)

        self.layout.addStretch()
        for w in (title, self.new_user, self.new_email, self.new_pass, self.confirm_pass, submit_btn, retour_btn):
            self.layout.addWidget(w)
        self.layout.addStretch()

    def create_account(self):
        u, e, p, cp = self.new_user.text(), self.new_email.text(), self.new_pass.text(), self.confirm_pass.text()
        if not all((u, e, p, cp)):
            QMessageBox.warning(self, "Erreur", "Tous les champs sont obligatoires.")
        elif len(p) < 6:
            QMessageBox.warning(self, "Erreur", "Le mot de passe doit contenir au moins 6 caractères.")
        elif p != cp:
            QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas.")
        else:
            users = load_users()
            if u in users:
                QMessageBox.warning(self, "Erreur", "Ce nom d'utilisateur existe déjà.")
                return
            save_user(u, e, p)
            QMessageBox.information(self, "Succès", "Compte créé avec succès.")
            self.login_ui()

    def check_login(self):
        u, p = self.username_input.text(), self.password_input.text()
        if validate_login(u, p):
            self.current_user = u
            self.main_ui(u)
        else:
            QMessageBox.warning(self, "Erreur", "Identifiants incorrects.")

    def main_ui(self, username):
        self.clear_layout()
        users = load_users()
        user_data = users.get(username, {})
        photo_data = user_data.get("photo", None)

        sim_label = QLabel()
        sim_label.setTextFormat(Qt.TextFormat.RichText)
        sim_label.setText(
            "<span style='font-family:Mistral; font-size:36pt; font-weight:bold;'>"
            "<span style='color:#f58529;'>S</span>"
            "<span style='color:#dd2a7b;'>i</span>"
            "<span style='color:#8134af;'>m</span>"
            "<span style='color:#515bd4;'>c</span>"
            "<span style='color:#f58529;'>o</span>"
            "<span style='color:#dd2a7b;'>a</span>"
            "<span style='color:#8134af;'>t</span>"
            "</span>"
        )
        user_label = QLabel(f"@{username}")
        user_label.setFont(QFont("Modern No. 20", 14))

        # Photo profil mini à côté de @username
        photo_label = QLabel()
        photo_label.setFixedSize(40,40)
        photo_label.setStyleSheet("border: 2px solid green; border-radius: 20px;")
        if photo_data:
            pixmap = QPixmap()
            pixmap.loadFromData(base64.b64decode(photo_data))
            pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            photo_label.setPixmap(pixmap)
        else:
            photo_label.setText("No Photo")
            photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_layout = QHBoxLayout()
        vlayout = QVBoxLayout()
        vlayout.addWidget(sim_label)
        user_hlayout = QHBoxLayout()
        user_hlayout.addWidget(user_label)
        user_hlayout.addWidget(photo_label)
        vlayout.addLayout(user_hlayout)

        text_layout.addLayout(vlayout)
        text_layout.addSpacing(10)
        text_layout.addWidget(VerticalLine(60))
        self.layout.addLayout(text_layout)
        self.layout.addStretch()

        # Navigation
        nav = QHBoxLayout()
        for i, url in enumerate(Instaclone.ICON_URLS):
            btn = QPushButton()
            try:
                response = requests.get(url)
                response.raise_for_status()
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                btn.setIcon(QIcon(pixmap))
            except Exception as e:
                print(f"Erreur chargement icône {url}: {e}")
            btn.setIconSize(QSize(28, 28))
            btn.setStyleSheet("border:none; background:white;")
            nav.addWidget(btn)
            if i == len(Instaclone.ICON_URLS) - 1:
                # Profil (dernier bouton) : ouvrir profil
                btn.clicked.connect(self.open_profile)

        self.layout.addLayout(nav)

    def open_profile(self):
        if not self.current_user:
            return
        self.profile_dialog = ProfileDialog(self, self.current_user)
        self.profile_dialog.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Instaclone()
    window.show()
    sys.exit(app.exec())
