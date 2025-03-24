# 🚀 Express Dry Clean – Plateforme Web

Bienvenue sur le dépôt officiel de **Express Dry Clean**, une application web professionnelle dédiée à la gestion de nos services de blanchisserie, couture et pressing en ligne.

---

## ✨ Fonctionnalités principales

- 🧾 **Formulaire de contact, de collaboration et de candidature**
- 🌍 **Site multilingue (FR, EN, NL, IT) avec Flask-Babel**
- 🔐 **Authentification sécurisée via Auth0 (RS256)**
- 📦 **API REST pour la gestion des services, catégories, traductions**
- 📬 **Envoi d'e-mails avec pièces jointes (CV)**
- 📁 **Upload sécurisé de fichiers**
- 🌐 **Déploiement sur serveur Linux avec Gunicorn + Apache (reverse proxy)**

---

## 🛠 Technologies utilisées

- **Backend** : Python + Flask
- **Auth** : Auth0 (`access_token`, JWT, RS256)
- **Mailing** : `smtplib` + `MIME` (multi-part HTML + pièce jointe)
- **I18n** : Flask-Babel (`.po`, `.mo`, `gettext`)
- **DB** : MySQL (via `mysql-connector-python`)
- **UI côté client** : HTML / Jinja2 / CSS / JS
- **Sécurité** : ReCAPTCHA v3, upload filtré, nettoyage historique Git

---

## ⚙️ Configuration

1. **Créer un fichier `.env` à la racine du projet :**

```env
AUTH0_CLIENT_ID=...
AUTH0_CLIENT_SECRET=...
AUTH0_DOMAIN=...
AUTH0_AUDIENCE=...
APP_SECRET_KEY=...

MYSQL_USER=...
MYSQL_PASSWORD=...
MYSQL_HOST=...
MYSQL_DB=...

MAIL_SERVER=...
MAIL_PORT=...
SMTP_USER=...
SMTP_PASSWORD=...
NOREPLY_EMAIL=...
ADMIN_EMAIL=...

RECAPTCHA_SERVER_KEY=...

UPLOAD_FOLDER=...
ROOT_FOLDER=/var/www/website
SERVICE_NAME=website.service
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```
4. ** Lancer le serveur Flask **
```bash
flask run
```


