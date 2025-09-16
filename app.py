import os
import datetime
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from telegram import Bot

# ================================
# CONFIGURACIÓN INICIAL
# ================================
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tareas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 🔑 TU TOKEN DEL BOT DE TELEGRAM
TELEGRAM_TOKEN = "8429392509:AAFGL1aNT8zbZ5AoVptivry2VdOjSpkfIZs"
CHAT_IDS = [8380086072]  # aquí puedes poner los ID de Telegram de tu grupo (ej: [123456789, 987654321])
bot = Bot(token=TELEGRAM_TOKEN)

# ================================
# BASE DE DATOS
# ================================
class Grupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    miembros = db.relationship('Miembro', backref='grupo', lazy=True)
    tareas = db.relationship('Tarea', backref='grupo', lazy=True)

class Miembro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telegram_id = db.Column(db.String(50), nullable=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)

class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    curso = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.String(20), nullable=False)
    hecha = db.Column(db.Boolean, default=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)

with app.app_context():
    db.create_all()

# ================================
# FUNCIONES DE NOTIFICACIÓN
# ================================
def enviar_notificacion(texto, chat_ids=CHAT_IDS):
    """Envía mensaje a todos los miembros registrados."""
    for cid in chat_ids:
        try:
            bot.send_message(chat_id=cid, text=texto)
        except Exception as e:
            print(f"❌ Error enviando mensaje a {cid}: {e}")

def notificar_tareas():
    """Revisa tareas pendientes y notifica por Telegram."""
    hoy = datetime.date.today().strftime("%Y-%m-%d")
    tareas = Tarea.query.filter_by(hecha=False, fecha=hoy).all()
    if tareas:
        mensaje = "📌 *Recordatorio de Tareas Pendientes Hoy*:\n\n"
        for t in tareas:
            mensaje += f"📚 {t.curso}: {t.descripcion} (Grupo: {t.grupo.nombre})\n"
        enviar_notificacion(mensaje)

# ================================
# ROUTES (WEB)
# ================================
@app.route("/")
def index():
    grupos = Grupo.query.all()
    return render_template("index.html", grupos=grupos)

@app.route("/grupo/nuevo", methods=["POST"])
def nuevo_grupo():
    nombre = request.form["nombre"]
    grupo = Grupo(nombre=nombre)
    db.session.add(grupo)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/miembro/nuevo/<int:grupo_id>", methods=["POST"])
def nuevo_miembro(grupo_id):
    nombre = request.form["nombre"]
    telegram_id = request.form["telegram_id"]
    miembro = Miembro(nombre=nombre, telegram_id=telegram_id, grupo_id=grupo_id)
    db.session.add(miembro)
    db.session.commit()
    # lo agregamos a la lista global de notificaciones
    if telegram_id not in CHAT_IDS:
        CHAT_IDS.append(telegram_id)
    return redirect(url_for("index"))

@app.route("/tarea/nueva/<int:grupo_id>", methods=["POST"])
def nueva_tarea(grupo_id):
    curso = request.form["curso"]
    descripcion = request.form["descripcion"]
    fecha = request.form["fecha"]
    tarea = Tarea(curso=curso, descripcion=descripcion, fecha=fecha, grupo_id=grupo_id)
    db.session.add(tarea)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/tarea/hecha/<int:id>")
def tarea_hecha(id):
    tarea = Tarea.query.get(id)
    tarea.hecha = True
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/tarea/eliminar/<int:id>")
def eliminar_tarea(id):
    tarea = Tarea.query.get(id)
    db.session.delete(tarea)
    db.session.commit()
    return redirect(url_for("index"))

# ================================
# SCHEDULER (para notificaciones diarias)
# ================================
scheduler = BackgroundScheduler(timezone=pytz.timezone("America/Lima"))
scheduler.add_job(func=notificar_tareas, trigger="interval", hours=24)  # cada 24h
scheduler.start()

# ================================
# MAIN
# ================================
if __name__ == "__main__":
    bot.send_message(chat_id="8380086072", text="✅ Bot conectado con Flask")
    app.run(debug=True, host="0.0.0.0")

