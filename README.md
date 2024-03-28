# PediGroup
PediGroup es un bot de Telegram con el que las personas van a poder interactuar, con el objetivo de armar sus pedidos de comida junto a sus amigos

## 👤 Integrantes
- Lucas Ziegemann
- Tomás Cowes

## ⚙️ Tecnologías
- [Python 3.12.2](https://www.python.org/) 
- [Django 5.0.3](https://www.djangoproject.com/)
- [TelegramBotApi](https://core.telegram.org/bots/api)
- [PostgreSQL 16.2](https://www.postgresql.org/)

## 🔗 Enlaces
- [Wiki](https://github.com/tcowes/pedigroup/wiki)
- [Backlog](https://lucasziegemann.atlassian.net/jira/core/projects/PED/board)

### ¿Como levantar el proyecto?
- Instalar Python 3.12.2, siguiendo la [documentación](https://www.python.org/downloads/release/python-3122/)
- Verificar que instalamos python correctamente, en una terminal ejecutar:
    ```powershell
    python --version
    ```
- Instalar y configurar la base de datos PostgreSQL, siguiendo la [documentación](https://www.postgresql.org/download/)
- Crear un Virtual Enviroment de Python en el root del proyecto:
    ```powershell
    python -m venv venv
    ```
- Activar el Virtual Enviroment:
    ```powershell
    .\venv\Scripts\activate
    ```
- Instalar los requerimientos:
    ```powershell
    pip install -r .\requirements.txt
    ```
- Copiar el archivo *.env.example* dentro de la carpeta .\pedigroup y pegarlo sin la extensión *.example*, reemplazando con los datos para la conexión a la DB.
- Levantar el servidor de Django:
    ```powershell
    python .\pedigroup\manage.py runserver
    ```
- Generar un token para el bot de Telegram con [@BotFather](https://core.telegram.org/bots/features#botfather)
- Copiar el archivo *.env.example* dentro de la carpeta .\pedigroup\telegram_integration y pegarlo sin la extensión *.example*, reemplazando con el token generado en el paso anterior.
- Levantar el bot en una terminal separada:
    ```powershell
    python .\pedigroup\telegram_integration\bot.py
    ```

### ¿Para qué público está pensado?
PediGroup está pensado en principio para toda persona que utilice Telegram como herramienta de comunicación en grupo, que necesite armar pedidos de comida masivos.

### ¿Qué módulos incluye en una primera etapa y cómo se extendería a futuro?
A definir.