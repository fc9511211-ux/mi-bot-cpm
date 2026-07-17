import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

# --- CONFIGURACIÓN PARA EVITAR EL ERROR DE PUERTOS EN RENDER ---
server = Flask(__name__)

# El bot lee el Token desde las variables de entorno de Render
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

# 🔒 LISTA BLANCA: Coloca aquí tu ID numérico que te dio @userinfobot
ADMINS = [6810995154]
# <-- REEMPLAZA ESTE NÚMERO CON TU ID REAL

# Base de datos temporal para guardar credenciales por chat_id
usuarios_db = {}

# ----------------- MENÚS DE NAVEGACIÓN -----------------

def menu_opciones_individuales():
    """Genera el panel principal con el nuevo botón de salir incorporado."""
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("👑 Activar Rango King (Individual)", callback_data="opc_king"),
        InlineKeyboardButton("💰 Añadir Monedas de Oro (Individual)", callback_data="opc_monedas"),
        InlineKeyboardButton("💵 Añadir Dinero Infinito (Individual)", callback_data="opc_dinero"),
        InlineKeyboardButton("🛞 Desbloquear Rines de Paga (Individual)", callback_data="opc_rines"),
        InlineKeyboardButton("🚗 Desbloquear Todos los Carros (Individual)", callback_data="opc_carros"),
        InlineKeyboardButton("👥 Clonar Cuenta CPM (Individual)", callback_data="opc_clonar"),
        InlineKeyboardButton("🔐 Ver mi Sesión Actual", callback_data="opc_ver_datos"),
        InlineKeyboardButton("🚪 Cerrar Sesión (Salir)", callback_data="opc_salir")  # <-- NUEVO BOTÓN
    )
    return markup

def menu_confirmar_accion(tipo_funcion):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Confirmar Envío", callback_data=f"exec_{tipo_funcion}"),
        InlineKeyboardButton("❌ Cancelar", callback_data="volver_menu")
    )
    return markup

def boton_regresar():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⬅️ Volver al Panel", callback_data="volver_menu"))
    return markup

# ----------------- MANEJADOR DEL COMANDO /START -----------------

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    chat_id = message.chat.id
    nombre = message.from_user.first_name
    
    # Verificar seguridad de Lista Blanca
    if chat_id not in ADMINS:
        bot.reply_to(message, "⚠️ **Acceso denegado.** No tienes permisos para interactuar con este bot privado.")
        return
    
    # Si el usuario ya está autenticado y usa /start, lo mandamos al menú en vez de borrarle los datos
    if chat_id in usuarios_db and usuarios_db[chat_id]["estado"] == "autenticado":
        bot.send_message(chat_id, "👋 Ya tienes una sesión activa. Selecciona una opción:", reply_markup=menu_opciones_individuales())
        return

    usuarios_db[chat_id] = {
        "estado": "esperando_correo",
        "correo": None,
        "clave": None
    }
    
    texto_inicio = (
        f"👋 ¡Hola, {nombre}! Bienvenido al sistema automatizado de Car Parking Multiplayer.\n\n"
        "🔒 **Verificación de Cuenta Obligatoria**\n"
        "Envía el **CORREO ELECTRÓNICO** vinculado a tu cuenta de CPM:"
    )
    bot.send_message(chat_id, texto_inicio)

# ----------------- MANEJADOR DE ENTRADA DE TEXTO -----------------

@bot.message_handler(func=lambda message: True)
def procesar_entrada_texto(message):
    chat_id = message.chat.id
    texto = message.text.strip()
    
    if chat_id not in ADMINS:
        return

    if chat_id not in usuarios_db:
        bot.reply_to(message, "⚠️ Por favor, inicia el proceso usando el comando /start")
        return
        
    estado_actual = usuarios_db[chat_id]["estado"]
    
    if estado_actual == "esperando_correo":
        usuarios_db[chat_id]["correo"] = texto
        usuarios_db[chat_id]["estado"] = "esperando_clave"
        bot.reply_to(message, "📥 **Correo registrado.** Ahora envía la **CONTRASEÑA** de tu cuenta:")
        
    elif estado_actual == "esperando_clave":
        usuarios_db[chat_id]["clave"] = texto
        usuarios_db[chat_id]["estado"] = "autenticado"
        correo_guardado = usuarios_db[chat_id]["correo"]
        
        texto_exito = (
            f"✅ **¡Sincronización Exitosa!**\n\n"
            f"• **Cuenta:** `{correo_guardado}`\n\n"
            "🔓 Panel desbloqueado. Selecciona una opción individual:"
        )
        bot.send_message(chat_id, texto_exito, parse_mode="Markdown", reply_markup=menu_opciones_individuales())
        
    elif estado_actual == "autenticado":
        bot.send_message(chat_id, "👋 Selecciona una opción del menú interactivo o cierra sesión si deseas cambiar de cuenta:", reply_markup=menu_opciones_individuales())

# ----------------- MANEJADOR DE EVENTOS DE BOTONES -----------------

@bot.callback_query_handler(func=lambda call: True)
def interactuar_botones(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if chat_id not in ADMINS:
        bot.answer_callback_query(call.id, text="⚠️ No tienes acceso a este bot.", show_alert=True)
        return

    # Lógica exclusiva para salir (no requiere estar autenticado para evitar bloqueos)
    if call.data == "opc_salir":
        bot.answer_callback_query(call.id, text="🚪 Cerrando sesión...", show_alert=False)
        
        # Eliminar por completo los datos guardados del usuario en el bot
        if chat_id in usuarios_db:
            usuarios_db.pop(chat_id)
            
        texto_salida = (
            "🚪 **Sesión Cerrada Correctamente**\n\n"
            "Tus datos locales han sido borrados de la memoria del bot.\n"
            "Si deseas conectar una nueva cuenta, presiona el comando inferior:"
            "\n\n👉 /start"
        )
        bot.edit_message_text(texto_salida, chat_id, message_id, parse_mode="Markdown")
        return

    datos_usuario = usuarios_db.get(chat_id, None)
    if not datos_usuario or datos_usuario["estado"] != "autenticado":
        bot.answer_callback_query(call.id, text="⚠️ Inicia sesión con /start", show_alert=True)
        return

    if call.data == "volver_menu":
        bot.answer_callback_query(call.id)
        texto = "👉 Selecciona una sola opción para gestionar de forma individual:"
        bot.edit_message_text(texto, chat_id, message_id, reply_markup=menu_opciones_individuales())
        return

    if call.data == "opc_ver_datos":
        bot.answer_callback_query(call.id)
        texto_datos = (
            f"🔐 **Datos de la Sesión Actual:**\n\n"
            f"• **Correo:** `{datos_usuario['correo']}`\n"
            f"• **Contraseña:** `{datos_usuario['clave']}`"
        )
        bot.edit_message_text(texto_datos, chat_id, message_id, parse_mode="Markdown", reply_markup=boton_regresar())
        return

    diccionario_servicios = {
        "opc_king": "Activación de Rango King",
        "opc_monedas": "Inyección de Monedas de Oro",
        "opc_dinero": "Inyección de Dinero Máximo",
        "opc_rines": "Desbloqueo de Rines de Paga",
        "opc_carros": "Desbloqueo de Todos los Vehículos",
        "opc_clonar": "Clonación Completa de Perfil"
    }

    if call.data in diccionario_servicios:
        bot.answer_callback_query(call.id)
        nombre_servicio = diccionario_servicios[call.data]
        bot.edit_message_text(
            text=f"❓ **Confirmación**\n\n¿Deseas ejecutar *{nombre_servicio}* en la cuenta `{datos_usuario['correo']}`?",
            chat_id=chat_id,
            message_id=message_id,
            parse_mode="Markdown",
            reply_markup=menu_confirmar_accion(call.data.replace("opc_", ""))
        )

    elif call.data.startswith("exec_"):
        bot.answer_callback_query(call.id)
        funcion_ejecutada = call.data.replace("exec_", "").upper()
        texto_final = (
            f"🚀 **Orden enviada de forma aislada**\n\n"
            f"• **Cuenta Destino:** `{datos_usuario['correo']}`\n"
            f"• **Función:** {funcion_ejecutada}\n"
            f"• **Estado:** En cola de sincronización..."
        )
        bot.edit_message_text(texto_final, chat_id, message_id, parse_mode="Markdown", reply_markup=boton_regresar())

# --- RUTA FALSA PARA QUE RENDER NO DE ERROR DE PUERTOS ---
@server.route("/")
def webhook():
    return "Bot activo", 200

# ----------------- INICIO SIMULTÁNEO -----------------
if __name__ == "__main__":
    import threading
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=lambda: server.run(host="0.0.0.0", port=port)).start()
    
    print(">>> Servidor del Bot de Telegram listo...")
    bot.polling(none_stop=True)
  
