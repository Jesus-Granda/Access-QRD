from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
import uuid

from bson.objectid import ObjectId

from extensions import mongo, socketio

from utils.auth import login_required, role_required
from utils.qr_generator import generate_qr
from utils.uploads import guardar_imagen
from utils.visita_validacion import vigencia_recurrente_meses

resident_bp = Blueprint("resident", __name__, url_prefix="/resident")


@resident_bp.route("/dashboard")
@login_required
@role_required("residente")
def dashboard():

    visitas = list(mongo.db.visits.find({"residente_id": session["user_id"]}))

    return render_template("residente_dashboard.html", visitas=visitas)


@resident_bp.route("/create-visit", methods=["GET", "POST"])
@login_required
@role_required("residente")
def create_visit():

    residente = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})

    if request.method == "POST":

        modalidad = request.form.get("modalidad_visita", "temporal")

        token = str(uuid.uuid4())
        qr_path = generate_qr(token)

        foto_visitante = guardar_imagen(
            request.files.get("foto_visitante"), "visitantes"
        )
        foto_placa = guardar_imagen(request.files.get("foto_placa"), "placas")

        vigencia_desde = None
        vigencia_hasta = None
        dia_semana = None
        hora_programada = None
        fecha_visita = request.form.get("fecha_visita")
        hora_inicio = request.form.get("hora_inicio")

        if modalidad == "recurrente":
            dia_semana = request.form.get("dia_semana", "").strip().lower()
            hora_programada = request.form.get("hora_programada")
            hora_inicio = hora_programada
            vigencia_desde, vigencia_hasta = vigencia_recurrente_meses(1)
            fecha_visita = vigencia_desde.strftime("%Y-%m-%d")

        visita = {
            "residente_id": session["user_id"],
            "residente_nombre": session["nombre"],
            "nombre_visitante": request.form["nombre_visitante"].strip(),
            "foto_visitante": foto_visitante,
            "foto_placa": foto_placa,
            "telefono": request.form["telefono"].strip(),
            "modalidad_visita": modalidad,
            "motivo": request.form["motivo"].strip(),
            "fraccionamiento": residente["fraccionamiento"],
            "condominio": residente["privada"],
            "residencia_destino": residente["numero_casa"],
            "fecha_visita": fecha_visita,
            "hora_inicio": hora_inicio,
            "dia_semana": dia_semana,
            "hora_programada": hora_programada,
            "vigencia_desde": vigencia_desde,
            "vigencia_hasta": vigencia_hasta,
            "hora_salida": None,
            "fecha_salida": None,
            "entrada_consumida": False,
            "vehiculo": {
                "tiene_vehiculo": True,
                "placa": request.form.get("placa", "").strip(),
                "marca": request.form.get("marca", "").strip(),
                "modelo": request.form.get("modelo", "").strip(),
                "color": request.form.get("color", "").strip(),
            },
            "qr_token": token,
            "qr_path": qr_path,
            "qr_estado": "activo",
            "estado": "activo",
            "created_at": datetime.now(),
        }

        mongo.db.visits.insert_one(visita)

        socketio.emit(
            "nueva_visita",
            {
                "mensaje": "Nueva visita registrada",
                "visitante": visita["nombre_visitante"],
                "residente": visita["residente_nombre"],
            },
        )

        return redirect(url_for("resident.dashboard"))

    return render_template("crear_visita.html", residente=residente)
