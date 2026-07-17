from flask import Flask, render_template, request, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz

app = Flask(__name__)

# ══════════════════════════════════════════════════════════
# CONFIGURACIÓN  ← edita solo esta sección
# ══════════════════════════════════════════════════════════
GMAIL_REMITENTE     = "potinesdomiclios@gmail.com"
GMAIL_PASSWORD      = "srzn fcmf xnsr bdip"
CORREO_DESPACHADORA = "potinesdomiclios@gmail.com"

# TARIFAS INTERNAS DE ENVÍO (Protegidas en Backend)
TARIFAS_BARRIOS = {
    # Veredas y zonas rurales
    "la_aguacatala_vereda": 7500,
    "el_cano": 7000,
    "la_miel": 8000,
    "la_chuscala_vereda": 10000,
    "el_raizal": 10000,
    "la_raya": 7000,
    "la_corrala": 8000,
    "la_valeria": 8000,
    "salinas": 13000,
    "la_salada_alta": 12000,
    "la_salada_baja": 12000,
    "la_clara": 13000,
    "primavera": 12000,

    # Barrios
    "barrios_unidos": 5000,
    "la_pradera": 4000,
    "barrio_nuevo": 5000,
    "los_cerezos": 6000,
    "cristo_rey": 6000,
    "olaya_herrera": 5000,
    "la_docena": 5000,
    "la_inmaculada": 5000,
    "felipe_1": 6000,
    "felipe_2": 6000,
    "la_chuscala_barrio": 8500,
    "el_minuto": 8500,
    "la_planta": 5000,
    "las_margaritas": 5000,
    "la_acuarela": 6000,
    "zona_centro": 6000,
    "andalucia": 7000,
    "la_goretti": 5000,
    "el_socorro": 5000,
    "villa_capri": 6000,
    "la_esperanza": 2000,
    "fundadores": 5000,
    "centenario": 6000,
    "mandalay": 6000,
    "la_playita": 6000,
    "la_aguacatala_kaiser": 6000,
    "bellavista": 2000,
    "el_porvenir": 2000,
    "la_loceria": 5000
}

COSTO_DOMICILIO_DEFECTO = 5000
# ══════════════════════════════════════════════════════════

_orden_counter = 0

def generar_numero_orden():
    global _orden_counter
    _orden_counter += 1
    return f"#{str(_orden_counter).zfill(6)}"


# NUEVOS COMBOS Y PRECIOS
COMBO_NAMES  = {
    "potibombon": "Potibombon (Papas, bombón de pollo, salchicha, huevo, gaseosa)",
    "potipapa":   "Potipapa (Papas, huevo, salchicha, gaseosa)",
    "potifull":   "Potifull (Papas, snack de pollo, bombón de pollo, salchicha, huevo, gaseosa)",
    "potisanck":  "Potisanck (Papas, 3 snacks de pollo, salchicha, 2 huevos, gaseosa)"
}

COMBO_PRICES = {
    "potibombon": 16900,
    "potipapa":   13900,
    "potifull":   18900,
    "potisanck":  21900
}

SAUCE_NAMES  = {
    "rosada":"Salsa Rosada",
    "enacorradora":"Salsa Encacorradora",
    "bbq":"Salsa BBQ",
    "pina":"Salsa de Piña",
    "sin_salsa":"Sin salsa"
}

# NUEVAS BEBIDAS Y PRECIOS
SODA_NAMES   = {
    "cocacola":"Coca-Cola",
    "quatro":"Cuatro",
    "aguamanzana":"Agua de Manzana",
    "aguamaracuya":"Agua de Maracuyá",
    "delvalle":"Del Valle",
    "gaseosa_generica": "Gaseosa",
    "agua": "Agua"
}

SODA_PRICES  = {
    "cocacola":3500,
    "quatro":3500,
    "aguamanzana":3500,
    "aguamaracuya":3500,
    "delvalle":3500,
    "gaseosa_generica": 3500,
    "agua": 3000
}

# NUEVAS ADICIONES ("AGREGLAE MAS")
ADICION_PRICES = {
    "papa": 8500,
    "snack": 5900,
    "bombon": 5900,
    "salchicha": 1500,
    "gaseosa": 3500,
    "agua": 3000
}

ADICION_NAMES = {
    "papa": "Papa Porción",
    "snack": "Snack de Pollo",
    "bombon": "Bombón de Pollo",
    "salchicha": "Salchicha (10g)",
    "gaseosa": "Gaseosa",
    "agua": "Agua"
}

def verificar_horario_abierto():
    # Configurar la zona horaria de Colombia
    zona_co = pytz.timezone('America/Bogota')
    hora_actual = datetime.now(zona_co).time()
    
    # Definir hora de cierre (22:00 = 10:00 PM) y apertura (16:00 = 4:00 PM)
    hora_cierre = hora_actual.replace(hour=22, minute=0, second=0, microsecond=0)
    hora_apertura = hora_actual.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Si la hora actual es mayor o igual a las 10 PM O menor que las 6 AM, está CERRADO
    if hora_actual >= hora_cierre or hora_actual < hora_apertura:
        return False
    return True

@app.route('/estado-tienda')
def estado_tienda():
    return jsonify({"abierto": verificar_horario_abierto()})


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/enviar-pedido', methods=['POST'])
def enviar_pedido():

    datos     = request.json
    combos    = datos.get('combos', {})
    salsas    = datos.get('salsas', {})
    bebidas   = datos.get('bebidas', {})
    adiciones = datos.get('adiciones', {})
    domicilio = datos.get('domicilio', {})

    numero_orden = generar_numero_orden()

    total_combos  = sum(COMBO_PRICES.get(k,0)*v for k,v in combos.items() if v>0)
    total_bebidas = sum(SODA_PRICES.get(k,0)*v for k,v in bebidas.items() if v>0)
    total_adiciones = sum(ADICION_PRICES.get(k,0)*v for k,v in adiciones.items() if v>0)

    # Cálculo seguro del domicilio basado en el identificador recibido
    barrio_recibido = str(domicilio.get('barrio', '')).lower().strip()
    costo_domicilio = TARIFAS_BARRIOS.get(barrio_recibido, COSTO_DOMICILIO_DEFECTO)

    total_general = total_combos + total_bebidas + total_adiciones + costo_domicilio

    # Extraer y formatear datos críticos para alertas de la despachadora
    alerta_barrio = barrio_recibido.upper()
    alerta_direccion = str(domicilio.get('direccion', 'N/A')).upper()

    # ══════════════════════════════════════════════════════
    # RESUMEN DEL PEDIDO
    # ══════════════════════════════════════════════════════

    lineas = [
        "🍟 NUEVO PEDIDO POTINES 🍟",
        "="*40,
        f"📋 ORDEN: {numero_orden}",
        "="*40,
        "",
        "📦 COMBOS:"
    ]

    for k,v in combos.items():
        if v>0:
            lineas.append(
                f"  x{v} {COMBO_NAMES.get(k,k)}  →  ${COMBO_PRICES.get(k,0)*v:,}"
            )

    lineas += ["","🥫 SALSAS:"]

    for ck,qty in combos.items():
        for i in range(1,qty+1):
            sk  = f"sauce_{ck}_{i}"
            sel = salsas.get(sk,[])
            lbl = (COMBO_NAMES.get(ck,ck)+f" #{i}") if qty>1 else COMBO_NAMES.get(ck,ck)
            lineas.append(
                f"  {lbl}: {', '.join(SAUCE_NAMES.get(s,s) for s in sel) if sel else 'Sin especificar'}"
            )


    # BEBIDAS
    bped = {k:v for k,v in bebidas.items() if v>0}
    lineas += ["","🥤 BEBIDAS:" if bped else "🥤 BEBIDAS: Sin bebidas"]

    for k,v in bped.items():
        lineas.append(
            f"  x{v} {SODA_NAMES.get(k,k)}  →  ${SODA_PRICES.get(k,0)*v:,}"
        )


    # ADICIONES ("AGREGLAE MAS")
    aped = {k:v for k,v in adiciones.items() if v>0}
    lineas += ["","➕ AGREGLAE MAS:" if aped else "➕ AGREGLAE MAS: Sin adiciones"]

    for k,v in aped.items():
        nombre = ADICION_NAMES.get(k, k.replace('_', ' ').capitalize())
        lineas.append(
            f"  x{v} {nombre}  →  ${ADICION_PRICES.get(k,0)*v:,}"
        )


    # DOMICILIO (Reestructurado con Bloque de Validación Crítica al Inicio)
    lineas += [
        "",
        "🚨 VERIFICACIÓN DE DIRECCIÓN 🚨",
        "━━━ BARRIO Y DIRECCIÓN SELECCIONADOS ━━━",
        f"📍 BARRIO:    {alerta_barrio}",
        f"🏠 DIRECCIÓN: {alerta_direccion}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        "📍 DETALLES DE ENTREGA:",
        f"  Nombre:     {domicilio.get('nombre','N/A')}",
        f"  Celular:    {domicilio.get('celular','N/A')}",
        f"  Referencia: {domicilio.get('referencia','—') or '—'}",
        "",
        "="*40,
        f"  Subtotal productos: ${total_combos+total_bebidas+total_adiciones:,}",
        f"  Domicilio:          ${costo_domicilio:,}",
        f"💰 TOTAL A COBRAR:    ${total_general:,}",
        "="*40
    ]

    resumen_texto = "\n".join(lineas)

    print(resumen_texto)


    try:
        _enviar_correo(numero_orden, resumen_texto, domicilio, total_general)
        correo_ok = True
    except Exception as e:
        import traceback
        print("🚨 DETALLE DEL ERROR DE CORREO:")
        traceback.print_exc()  # <--- Esto te dirá la línea exacta y la respuesta de Google
        correo_ok = False


    return jsonify({
        "status":"success",
        "numero_orden":numero_orden,
        "total":total_general,
        "correo_ok":correo_ok
    }), 200



# ══════════════════════════════════════════════════════
# ENVÍO DE CORREO
# ══════════════════════════════════════════════════════

def _enviar_correo(numero_orden, resumen_texto, domicilio, total):

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🍟 POTINES — Nuevo pedido {numero_orden}"
    msg["From"]    = GMAIL_REMITENTE
    msg["To"]      = CORREO_DESPACHADORA

    html = f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial;background:#f9f9f9;padding:20px;">

<h2>🍟 POTINES</h2>

<pre style="background:white;padding:20px;border-radius:10px;font-family:monospace;font-size:14px;line-height:1.5;">
{resumen_texto}
</pre>

<h3>Total a cobrar: ${total:,}</h3>

</body>
</html>
"""

    msg.attach(MIMEText(resumen_texto,"plain","utf-8"))
    msg.attach(MIMEText(html,"html","utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com",465) as server:
        server.login(GMAIL_REMITENTE, GMAIL_PASSWORD)
        server.sendmail(
            GMAIL_REMITENTE,
            CORREO_DESPACHADORA,
            msg.as_string()
        )


if __name__ == '__main__':
    app.run(debug=True, port=5000)