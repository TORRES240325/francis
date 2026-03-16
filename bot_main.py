import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from sqlalchemy.orm.exc import NoResultFound
from db_models import Usuario, Producto, Key, PaymentMethod, TopUpRequest, inicializar_db, get_session 
from dotenv import load_dotenv

# =================================================================
# 1. Configuración Inicial (Lectura de Variables de Entorno)
# =================================================================
load_dotenv()
TOKEN = os.getenv('BOT_MAIN_TOKEN') 
if not TOKEN:
    raise ValueError("Error: BOT_MAIN_TOKEN no encontrado. Verifica las variables de entorno.")

MIN_TOPUP_AMOUNT = float(os.getenv('MIN_TOPUP_AMOUNT', '10'))

inicializar_db() 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Estados del ConversationHandler ---
LOGIN_KEY, BUY_CATEGORY, BUY_PRODUCT, TOPUP_METHOD, TOPUP_AMOUNT, TOPUP_REFERENCE, SET_LANGUAGE = range(7)

LANGUAGE_BUTTONS = {
    "es": "Español",
    "en": "English",
    "pt": "Português",
}
LANGUAGE_LABEL_TO_CODE = {label.lower(): code for code, label in LANGUAGE_BUTTONS.items()}

SUPPORTED_LANGS = {"es", "en", "pt"}

BUTTONS = {
    "es": {
        "buy": "🛒 Comprar keys",
        "topup": "💳 Recargar saldo",
        "account": "👤 Cuenta",
        "logout": "🚀 Cerrar sesión",
        "language": "🌐 Idioma",
        "login": "🔒 Iniciar sesión",
        "create_account": "➕ Crear cuenta",
        "back": "⬅️ Volver",
    },
    "en": {
        "buy": "🛒 Buy keys",
        "topup": "💳 Top up balance",
        "account": "👤 Account",
        "logout": "🚀 Log out",
        "language": "🌐 Language",
        "login": "🔒 Log in",
        "create_account": "➕ Create account",
        "back": "⬅️ Back",
    },
    "pt": {
        "buy": "🛒 Comprar keys",
        "topup": "💳 Recarregar saldo",
        "account": "👤 Conta",
        "logout": "🚀 Encerrar sessão",
        "language": "🌐 Idioma",
        "login": "🔒 Entrar",
        "create_account": "➕ Criar conta",
        "back": "⬅️ Voltar",
    },
}

TEXTS = {
    "es": {
        "welcome_back": "👋 **Bienvenido de nuevo, {username}.**\nTu sesión está activa.",
        "welcome_guest": "❌ **Acceso denegado. Por favor, inicie sesión.**\nNo tiene permiso para usar esta función.\nPara obtener acceso o asistencia, póngase en contacto con el administrador →",
        "login_prompt": "🔒 Introduce las credenciales proporcionadas por el administrador en el siguiente formato:\n\n**NOMBRE_USUARIO CONTRASEÑA**",
        "login_format_error": "❌ Formato incorrecto. Usa: `NOMBRE_USUARIO CONTRASEÑA`",
        "login_ok": "✅ **¡Autorizado correctamente!**",
        "login_fail": "❌ Acceso denegado. Credenciales incorrectas o usuario no encontrado.",
        "id_taken": "❌ Tu ID de Telegram ya está en uso. Contacta al administrador.",
        "account_create_info": "❌ Acceso denegado. Por favor, inicie sesión.\nNo tiene permiso para usar esta función.\nPara obtener acceso o asistencia, póngase en contacto con el administrador →\n\n🔒 Introduce las credenciales proporcionadas por el administrador en el siguiente formato:\n\nNOMBRE_USUARIO CONTRASEÑA",
        "please_login": "❌ Debes iniciar sesión primero.",
        "choose_category": "Elige una categoría:",
        "choose_product": "Elige un producto en la categoría {category}:",
        "no_products": "❌ No hay productos en la categoría: **{category}**",
        "language_saved": "✅ Idioma actualizado a Español.",
        "language_choose": "🌐 Elige tu idioma:",
        "language_invalid": "❌ Idioma no válido. Usa los botones disponibles.",
        "language_current": "Idioma actual",
        "account_already_linked": "❌ Esta cuenta ya está vinculada a otro Telegram. Contacta al administrador.",
        "logout_ok": "🚪 Sesión cerrada. Usa /start para iniciar de nuevo.",
        "logout_none": "No tienes una sesión activa.",
        "account_info": "👤 **Tu cuenta:**\n• Usuario: **{username}**\n• Saldo: **${saldo:.2f}**\n\n• Idioma: **{lang_name}**",
        "no_methods": "❌ No hay métodos de pago disponibles en este momento. Contacta al administrador.",
        "topup_menu": "💳 **Recargar saldo**\n\nSelecciona un método de pago.\n\nMínimo de recarga: **${min_amount:.2f}**",
        "method_invalid_option": "❌ Opción no válida. Selecciona un método de la lista.",
        "method_not_found": "❌ Método no encontrado o inactivo. Elige otro.",
        "topup_method_instructions": "Método: **{method_name}**\n\nInstrucciones:\n{instructions}\n\nIngresa el monto a recargar (mínimo ${min_amount:.2f}):",
        "amount_invalid": "❌ Monto no válido. Ingresa un número (ej: 10.00).",
        "amount_min_error": "❌ El mínimo de recarga es ${min_amount:.2f}. Ingresa un monto mayor o igual.",
        "ask_reference": "Ahora ingresa una referencia/comprobante (ej: ID de transacción, captura, texto).",
        "reference_empty": "❌ La referencia no puede estar vacía. Intenta de nuevo.",
        "internal_error": "❌ Error interno. Vuelve a intentar.",
        "topup_created": "✅ Solicitud de recarga creada.\n\nID: `{request_id}`\nMonto: **${amount:.2f}**\nStatus: **pending**\n\nUn administrador la revisará pronto.",
        "topup_create_error": "❌ Error al crear la solicitud. Intenta de nuevo.",
        "buy_user_product_not_found": "❌ Error interno: Usuario o producto no encontrado.",
        "insufficient_balance": "❌ Saldo insuficiente. Tu saldo es: ${saldo:.2f}",
        "product_out_of_stock": "❌ Producto agotado. No hay claves disponibles para {product_name}.",
        "purchase_success": "🎉 **Compra Exitosa de {product_name}!**\nCosto: **${price:.2f}**\nTu nuevo saldo: **${saldo:.2f}**\n\n🔐 **Tu Key/Licencia:** `{license_key}`",
        "purchase_selection_error": "❌ Error al procesar la selección. Intenta de nuevo.",
        "purchase_error": "❌ Ocurrió un error en la compra. Intenta de nuevo o usa /start.",
    },
    "en": {
        "welcome_back": "👋 **Welcome back, {username}.**\nYour session is active.",
        "welcome_guest": "❌ **Access denied. Please log in.**\nYou don't have permission to use this function.\nFor access or support, contact the administrator →",
        "login_prompt": "🔒 Enter admin-provided credentials in this format:\n\n**USERNAME PASSWORD**",
        "login_format_error": "❌ Invalid format. Use: `USERNAME PASSWORD`",
        "login_ok": "✅ **Successfully authorized!**",
        "login_fail": "❌ Access denied. Invalid credentials or user not found.",
        "id_taken": "❌ Your Telegram ID is already linked. Contact admin.",
        "account_create_info": "❌ Access denied. Please log in.\nYou don't have permission to use this function.\nFor access or support, contact the administrator →\n\n🔒 Enter credentials in this format:\n\nUSERNAME PASSWORD",
        "please_login": "❌ Please log in first.",
        "choose_category": "Choose a category:",
        "choose_product": "Choose a product in {category}:",
        "no_products": "❌ No products found in: **{category}**",
        "language_saved": "✅ Language updated to English.",
        "language_choose": "🌐 Choose your language:",
        "language_invalid": "❌ Invalid language. Use the available buttons.",
        "language_current": "Current language",
        "account_already_linked": "❌ This account is already linked to another Telegram user. Contact admin.",
        "logout_ok": "🚪 Session closed. Use /start to begin again.",
        "logout_none": "You don't have an active session.",
        "account_info": "👤 **Your account:**\n• User: **{username}**\n• Balance: **${saldo:.2f}**\n\n• Language: **{lang_name}**",
        "no_methods": "❌ No payment methods are available right now. Contact the administrator.",
        "topup_menu": "💳 **Top up balance**\n\nSelect a payment method.\n\nMinimum top up: **${min_amount:.2f}**",
        "method_invalid_option": "❌ Invalid option. Select a method from the list.",
        "method_not_found": "❌ Method not found or inactive. Choose another.",
        "topup_method_instructions": "Method: **{method_name}**\n\nInstructions:\n{instructions}\n\nEnter top-up amount (minimum ${min_amount:.2f}):",
        "amount_invalid": "❌ Invalid amount. Enter a number (e.g. 10.00).",
        "amount_min_error": "❌ Minimum top-up amount is ${min_amount:.2f}. Enter a higher or equal amount.",
        "ask_reference": "Now enter a reference/proof (e.g. transaction ID, screenshot, text).",
        "reference_empty": "❌ Reference cannot be empty. Try again.",
        "internal_error": "❌ Internal error. Please try again.",
        "topup_created": "✅ Top-up request created.\n\nID: `{request_id}`\nAmount: **${amount:.2f}**\nStatus: **pending**\n\nAn administrator will review it soon.",
        "topup_create_error": "❌ Error creating request. Please try again.",
        "buy_user_product_not_found": "❌ Internal error: user or product not found.",
        "insufficient_balance": "❌ Insufficient balance. Your balance is: ${saldo:.2f}",
        "product_out_of_stock": "❌ Out of stock. No keys available for {product_name}.",
        "purchase_success": "🎉 **Successful purchase: {product_name}!**\nCost: **${price:.2f}**\nYour new balance: **${saldo:.2f}**\n\n🔐 **Your key/license:** `{license_key}`",
        "purchase_selection_error": "❌ Error processing selection. Please try again.",
        "purchase_error": "❌ An error occurred during purchase. Try again or use /start.",
    },
    "pt": {
        "welcome_back": "👋 **Bem-vindo de volta, {username}.**\nSua sessão está ativa.",
        "welcome_guest": "❌ **Acesso negado. Faça login.**\nVocê não tem permissão para usar esta função.\nPara acesso ou suporte, fale com o administrador →",
        "login_prompt": "🔒 Digite as credenciais no formato:\n\n**USUARIO SENHA**",
        "login_format_error": "❌ Formato inválido. Use: `USUARIO SENHA`",
        "login_ok": "✅ **Autorizado com sucesso!**",
        "login_fail": "❌ Acesso negado. Credenciais inválidas ou usuário não encontrado.",
        "id_taken": "❌ Seu ID do Telegram já está em uso. Fale com o admin.",
        "account_create_info": "❌ Acesso negado. Faça login.\nVocê não tem permissão para usar esta função.\nPara acesso ou suporte, fale com o administrador →\n\n🔒 Digite as credenciais no formato:\n\nUSUARIO SENHA",
        "please_login": "❌ Faça login primeiro.",
        "choose_category": "Escolha uma categoria:",
        "choose_product": "Escolha um produto em {category}:",
        "no_products": "❌ Nenhum produto na categoria: **{category}**",
        "language_saved": "✅ Idioma alterado para Português.",
        "language_choose": "🌐 Escolha seu idioma:",
        "language_invalid": "❌ Idioma inválido. Use os botões disponíveis.",
        "language_current": "Idioma atual",
        "account_already_linked": "❌ Esta conta já está vinculada a outro Telegram. Fale com o admin.",
        "logout_ok": "🚪 Sessão encerrada. Use /start para começar de novo.",
        "logout_none": "Você não tem uma sessão ativa.",
        "account_info": "👤 **Sua conta:**\n• Usuário: **{username}**\n• Saldo: **${saldo:.2f}**\n\n• Idioma: **{lang_name}**",
        "no_methods": "❌ Não há métodos de pagamento disponíveis no momento. Fale com o administrador.",
        "topup_menu": "💳 **Recarregar saldo**\n\nSelecione um método de pagamento.\n\nValor mínimo: **${min_amount:.2f}**",
        "method_invalid_option": "❌ Opção inválida. Selecione um método da lista.",
        "method_not_found": "❌ Método não encontrado ou inativo. Escolha outro.",
        "topup_method_instructions": "Método: **{method_name}**\n\nInstruções:\n{instructions}\n\nDigite o valor da recarga (mínimo ${min_amount:.2f}):",
        "amount_invalid": "❌ Valor inválido. Digite um número (ex: 10.00).",
        "amount_min_error": "❌ O valor mínimo de recarga é ${min_amount:.2f}. Digite um valor maior ou igual.",
        "ask_reference": "Agora digite uma referência/comprovante (ex: ID da transação, captura, texto).",
        "reference_empty": "❌ A referência não pode estar vazia. Tente novamente.",
        "internal_error": "❌ Erro interno. Tente novamente.",
        "topup_created": "✅ Solicitação de recarga criada.\n\nID: `{request_id}`\nValor: **${amount:.2f}**\nStatus: **pending**\n\nUm administrador irá revisar em breve.",
        "topup_create_error": "❌ Erro ao criar a solicitação. Tente novamente.",
        "buy_user_product_not_found": "❌ Erro interno: usuário ou produto não encontrado.",
        "insufficient_balance": "❌ Saldo insuficiente. Seu saldo é: ${saldo:.2f}",
        "product_out_of_stock": "❌ Produto esgotado. Não há chaves disponíveis para {product_name}.",
        "purchase_success": "🎉 **Compra realizada de {product_name}!**\nCusto: **${price:.2f}**\nSeu novo saldo: **${saldo:.2f}**\n\n🔐 **Sua key/licença:** `{license_key}`",
        "purchase_selection_error": "❌ Erro ao processar a seleção. Tente novamente.",
        "purchase_error": "❌ Ocorreu um erro na compra. Tente novamente ou use /start.",
    },
}

# =================================================================
# 2. Funciones de Utilidad y Teclados
# =================================================================

def _norm_lang(lang: str) -> str:
    return lang if lang in SUPPORTED_LANGS else "es"


def t(lang: str, key: str, **kwargs) -> str:
    lang = _norm_lang(lang)
    template = TEXTS.get(lang, TEXTS["es"]).get(key, TEXTS["es"].get(key, key))
    return template.format(**kwargs)


def b(lang: str, key: str) -> str:
    return BUTTONS.get(_norm_lang(lang), BUTTONS["es"]).get(key, BUTTONS["es"][key])


def is_button(text: str, key: str) -> bool:
    return any(text == BUTTONS[lang][key] for lang in SUPPORTED_LANGS)


def get_lang_for_telegram(telegram_id: int) -> str:
    with get_session() as session_db:
        usuario = session_db.query(Usuario).filter_by(telegram_id=telegram_id).first()
        if usuario and usuario.idioma:
            return _norm_lang(usuario.idioma)
    return "es"


def get_keyboard_main(is_logged_in, lang="es"):
    """Genera el teclado principal basado en el estado de login."""
    lang = _norm_lang(lang)
    if is_logged_in:
        keyboard = [
            [KeyboardButton(b(lang, "buy"))],
            [KeyboardButton(b(lang, "topup"))],
            [KeyboardButton(b(lang, "account")), KeyboardButton(b(lang, "logout"))],
            [KeyboardButton(b(lang, "language"))],
        ]
    else:
        keyboard = [
            [KeyboardButton(b(lang, "login")), KeyboardButton(b(lang, "create_account"))],
            [KeyboardButton(b(lang, "language"))],
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_language_keyboard(lang: str = "es"):
    current_label = LANGUAGE_BUTTONS.get(_norm_lang(lang), LANGUAGE_BUTTONS["es"])
    keyboard = [
        [KeyboardButton(LANGUAGE_BUTTONS["es"]), KeyboardButton(LANGUAGE_BUTTONS["en"])],
        [KeyboardButton(LANGUAGE_BUTTONS["pt"])],
        [KeyboardButton(b(lang, "back"))],
    ]
    return current_label, ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# =================================================================
# 3. Handlers de Inicio y Login
# =================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Muestra el mensaje de bienvenida y el teclado de login/menu."""
    user_id_telegram = update.effective_user.id
    
    with get_session() as session_db:
        usuario = session_db.query(Usuario).filter_by(telegram_id=user_id_telegram).first() 

    if usuario:
        lang = _norm_lang(getattr(usuario, "idioma", "es"))
        await update.message.reply_text(
            t(lang, "welcome_back", username=usuario.username),
            parse_mode='Markdown',
            reply_markup=get_keyboard_main(True, lang)
        )
    else:
        lang = _norm_lang(context.user_data.get("guest_lang", "es"))
        await update.message.reply_text(
            f"{t(lang, 'welcome_guest')}\n\n{t(lang, 'login_prompt')}",
            parse_mode='Markdown',
            reply_markup=get_keyboard_main(False, lang)
        )
        return LOGIN_KEY
    return ConversationHandler.END

async def show_login_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pide al usuario que ingrese las credenciales."""
    lang = _norm_lang(context.user_data.get("guest_lang", get_lang_for_telegram(update.effective_user.id)))
    await update.message.reply_text(
        t(lang, "login_prompt"),
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return LOGIN_KEY

async def handle_login_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Procesa el login_key y la contraseña ingresada."""
    text = update.message.text

    if is_button(text, "login"):
        return await show_login_prompt(update, context) 

    if is_button(text, "language"):
        return await prompt_set_language(update, context)

    if is_button(text, "create_account"):
        return await show_create_account_info(update, context)

    if is_button(text, "back"):
        current_lang = _norm_lang(context.user_data.get("guest_lang", get_lang_for_telegram(update.effective_user.id)))
        await update.message.reply_text(
            t(current_lang, "login_prompt"),
            parse_mode='Markdown',
            reply_markup=get_keyboard_main(False, current_lang)
        )
        return LOGIN_KEY

    parts = text.split()
    lang = _norm_lang(context.user_data.get("guest_lang", get_lang_for_telegram(update.effective_user.id)))

    session_db = get_session()
    try:
        if len(parts) != 2:
            await update.message.reply_text(
                t(lang, "login_format_error"),
                parse_mode='Markdown'
            )
            return LOGIN_KEY

        username, login_key_input = parts
        user_id_telegram = update.effective_user.id

        usuario = session_db.query(Usuario).filter_by(username=username, login_key=login_key_input).first()

        if usuario:
            if usuario.telegram_id is None:
                if session_db.query(Usuario).filter_by(telegram_id=user_id_telegram).first() is None:
                    usuario.telegram_id = user_id_telegram
                    session_db.commit()
                else:
                    await update.message.reply_text(
                        t(lang, "id_taken")
                    )
                    return LOGIN_KEY
            elif usuario.telegram_id != user_id_telegram:
                await update.message.reply_text(t(lang, "account_already_linked"))
                return LOGIN_KEY

            await update.message.reply_text(
                t(_norm_lang(getattr(usuario, "idioma", "es")), "login_ok"),
                parse_mode='Markdown',
                reply_markup=get_keyboard_main(True, _norm_lang(getattr(usuario, "idioma", "es")))
            )
            context.user_data.pop("guest_lang", None)
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                t(lang, "login_fail")
            )
            return LOGIN_KEY
    except Exception as e:
        logger.error(f"Error en handle_login_key: {e}")
        session_db.rollback()
        await update.message.reply_text("Ha ocurrido un error inesperado. Intenta de nuevo o usa /start.")
        return ConversationHandler.END
    finally:
        session_db.close()

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cierra la sesión del usuario desasociando el telegram_id."""
    user_id_telegram = update.effective_user.id
    is_logged_in = False
    lang = get_lang_for_telegram(user_id_telegram)
    
    with get_session() as session_db:
        usuario = session_db.query(Usuario).filter_by(telegram_id=user_id_telegram).first()
        if usuario:
            usuario.telegram_id = None
            session_db.commit()
            is_logged_in = True
    
    if is_logged_in:
        await update.message.reply_text(
            t(lang, "logout_ok"),
            reply_markup=get_keyboard_main(False, lang)
        )
    else:
        await update.message.reply_text(
            t(lang, "logout_none"),
            reply_markup=get_keyboard_main(False, lang)
        )
        
async def show_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra la información de la cuenta."""
    user_id_telegram = update.effective_user.id
    
    with get_session() as session_db:
        usuario = session_db.query(Usuario).filter_by(telegram_id=user_id_telegram).first()
    
    if usuario:
        lang = _norm_lang(getattr(usuario, "idioma", "es"))
        lang_name = LANGUAGE_BUTTONS.get(lang, LANGUAGE_BUTTONS["es"])
        message = t(lang, "account_info", username=usuario.username, saldo=usuario.saldo, lang_name=lang_name)
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=get_keyboard_main(True, lang)
        )
    else:
        await update.message.reply_text("❌ Debes iniciar sesión primero.")


async def prompt_set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_lang_for_telegram(update.effective_user.id)
    current_label, lang_keyboard = get_language_keyboard(lang)
    await update.message.reply_text(
        f"{t(lang, 'language_choose')}\n\n{t(lang, 'language_current')}: **{current_label}**",
        parse_mode='Markdown',
        reply_markup=lang_keyboard
    )
    return SET_LANGUAGE


async def save_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    text_norm = text.lower()

    if is_button(text, "back"):
        return await start(update, context)

    lang_input = LANGUAGE_LABEL_TO_CODE.get(text_norm)
    if not lang_input:
        current_lang = get_lang_for_telegram(update.effective_user.id)
        await update.message.reply_text(t(current_lang, "language_invalid"), parse_mode='Markdown')
        return SET_LANGUAGE

    with get_session() as session_db:
        usuario = session_db.query(Usuario).filter_by(telegram_id=update.effective_user.id).first()
        is_logged_in = bool(usuario)
        if usuario:
            usuario.idioma = lang_input
            session_db.commit()
            context.user_data.pop("guest_lang", None)
        else:
            context.user_data["guest_lang"] = lang_input

    await update.message.reply_text(
        t(lang_input, "language_saved"),
        reply_markup=get_keyboard_main(is_logged_in, lang_input)
    )

    if not is_logged_in:
        await update.message.reply_text(
            t(lang_input, "login_prompt"),
            parse_mode='Markdown',
            reply_markup=get_keyboard_main(False, lang_input)
        )
        return LOGIN_KEY

    return ConversationHandler.END


async def show_create_account_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _norm_lang(context.user_data.get("guest_lang", get_lang_for_telegram(update.effective_user.id)))
    await update.message.reply_text(t(lang, "account_create_info"), reply_markup=get_keyboard_main(False, lang))
    return LOGIN_KEY


async def show_topup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id_telegram = update.effective_user.id
    lang = get_lang_for_telegram(user_id_telegram)

    with get_session() as session_db:
        usuario = session_db.query(Usuario).filter_by(telegram_id=user_id_telegram).first()
        if not usuario:
            await update.message.reply_text(t(lang, "please_login"))
            return ConversationHandler.END

        metodos = session_db.query(PaymentMethod).filter_by(activo=True).order_by(PaymentMethod.id.asc()).all()

    if not metodos:
        await update.message.reply_text(
            t(lang, "no_methods"),
            reply_markup=get_keyboard_main(True, lang)
        )
        return ConversationHandler.END

    keyboard_rows = [[KeyboardButton(f"ID {m.id}: {m.nombre}")] for m in metodos]
    keyboard_rows.append([KeyboardButton(b(lang, "back"))])
    reply_markup = ReplyKeyboardMarkup(keyboard_rows, resize_keyboard=True, one_time_keyboard=False)

    await update.message.reply_text(
        t(lang, "topup_menu", min_amount=MIN_TOPUP_AMOUNT),
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return TOPUP_METHOD


async def handle_topup_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    lang = get_lang_for_telegram(update.effective_user.id)
    if is_button(text, "back"):
        return await start(update, context)

    try:
        method_id = int(text.split(':')[0].replace('ID', '').strip().split()[0])
    except Exception:
        await update.message.reply_text(t(lang, "method_invalid_option"))
        return TOPUP_METHOD

    with get_session() as session_db:
        metodo = session_db.query(PaymentMethod).filter_by(id=method_id, activo=True).first()

    if not metodo:
        await update.message.reply_text(t(lang, "method_not_found"))
        return TOPUP_METHOD

    context.user_data['topup_method_id'] = metodo.id
    context.user_data['topup_method_name'] = metodo.nombre

    await update.message.reply_text(
        t(lang, "topup_method_instructions", method_name=metodo.nombre, instructions=metodo.instrucciones, min_amount=MIN_TOPUP_AMOUNT),
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return TOPUP_AMOUNT


async def handle_topup_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_lang_for_telegram(update.effective_user.id)
    try:
        amount = float(update.message.text.replace(',', '.'))
    except ValueError:
        await update.message.reply_text(t(lang, "amount_invalid"))
        return TOPUP_AMOUNT

    if amount < MIN_TOPUP_AMOUNT:
        await update.message.reply_text(t(lang, "amount_min_error", min_amount=MIN_TOPUP_AMOUNT))
        return TOPUP_AMOUNT

    context.user_data['topup_amount'] = amount
    await update.message.reply_text(
        t(lang, "ask_reference"),
    )
    return TOPUP_REFERENCE


async def handle_topup_reference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_lang_for_telegram(update.effective_user.id)
    reference = (update.message.text or "").strip()
    if not reference:
        await update.message.reply_text(t(lang, "reference_empty"))
        return TOPUP_REFERENCE

    method_id = context.user_data.get('topup_method_id')
    amount = context.user_data.get('topup_amount')
    if not method_id or amount is None:
        context.user_data.clear()
        await update.message.reply_text(t(lang, "internal_error"))
        return ConversationHandler.END

    user_id_telegram = update.effective_user.id
    session_db = get_session()
    try:
        usuario = session_db.query(Usuario).filter_by(telegram_id=user_id_telegram).first()
        if not usuario:
            await update.message.reply_text(t(get_lang_for_telegram(user_id_telegram), "please_login"))
            return ConversationHandler.END

        solicitud = TopUpRequest(
            usuario_id=usuario.id,
            metodo_pago_id=method_id,
            monto=float(amount),
            referencia=reference,
            status='pending'
        )
        session_db.add(solicitud)
        session_db.commit()

        await update.message.reply_text(
            t(lang, "topup_created", request_id=solicitud.id, amount=amount),
            parse_mode='Markdown',
            reply_markup=get_keyboard_main(True, _norm_lang(getattr(usuario, 'idioma', 'es')))
        )

        admins = session_db.query(Usuario).filter(Usuario.es_admin == True, Usuario.telegram_id.isnot(None)).all()
        for a in admins:
            try:
                await context.bot.send_message(
                    chat_id=a.telegram_id,
                    text=(
                        "📥 **Nueva solicitud de recarga**\n"
                        f"ID: `{solicitud.id}`\n"
                        f"Usuario: **{usuario.username}** (ID {usuario.id})\n"
                        f"Monto: **${amount:.2f}**\n"
                        f"Método: **{context.user_data.get('topup_method_name', '')}**\n"
                        f"Referencia: `{reference}`\n\n"
                        "Revisa en el Panel Admin para aprobar/rechazar."
                    ),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"No se pudo notificar al admin {a.id}: {e}")

    except Exception as e:
        logger.error(f"Error creando solicitud de recarga: {e}")
        session_db.rollback()
        await update.message.reply_text(t(lang, "topup_create_error"), reply_markup=get_keyboard_main(True, get_lang_for_telegram(user_id_telegram)))
    finally:
        session_db.close()
        context.user_data.clear()

    return ConversationHandler.END
        
# =================================================================
# 4. Handlers de Compra (Buy keys) - Lógica de Inventario
# =================================================================

async def show_buy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Muestra las categorías de productos."""
    user_id_telegram = update.effective_user.id
    lang = get_lang_for_telegram(user_id_telegram)
    
    with get_session() as session_db:
        usuario = session_db.query(Usuario).filter_by(telegram_id=user_id_telegram).first()
        
        if not usuario:
            await update.message.reply_text(t(lang, "please_login"))
            return ConversationHandler.END

        categorias = session_db.query(Producto.categoria).distinct().all()
    
    keyboard_rows = []
    for cat_tuple in categorias:
        categoria = cat_tuple[0]
        if categoria: 
            keyboard_rows.append([KeyboardButton(categoria)])
            
    keyboard_rows.append([KeyboardButton("Volver")]) 

    reply_markup = ReplyKeyboardMarkup(keyboard_rows, resize_keyboard=True, one_time_keyboard=False)

    await update.message.reply_text(
        t(lang, "choose_category"),
        reply_markup=reply_markup
    )
    return BUY_CATEGORY

async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja la selección de la categoría y muestra los productos y acciones."""
    category = update.message.text
    lang = get_lang_for_telegram(update.effective_user.id)
    
    if is_button(category, "back"):
        return await start(update, context) 

    with get_session() as session_db:
        productos = session_db.query(Producto).filter_by(categoria=category).all()

    if not productos:
        await update.message.reply_text(t(lang, "no_products", category=category), parse_mode='Markdown')
        return BUY_CATEGORY

    context.user_data['selected_category'] = category

    product_keys = []
    
    for producto in productos:
        with get_session() as s:
            stock = s.query(Key).filter(Key.producto_id == producto.id, Key.estado == 'available').count()
        
        button_text = f"{producto.nombre} - ${producto.precio:.2f} (Stock: {stock})"
        product_keys.append([KeyboardButton(button_text)])
            
    product_keys.append([KeyboardButton(b(lang, "back"))])
    
    reply_markup = ReplyKeyboardMarkup(product_keys, resize_keyboard=True, one_time_keyboard=False)
    
    await update.message.reply_text(
        t(lang, "choose_product", category=category),
        reply_markup=reply_markup
    )
    return BUY_PRODUCT


async def handle_final_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Procesa las selecciones de compra (Buy)."""
    text = update.message.text
    user_id_telegram = update.effective_user.id
    
    lang = get_lang_for_telegram(user_id_telegram)

    if is_button(text, "back"):
        return await show_buy_menu(update, context)
    
    session_db = get_session()
    try:
        parts = text.rsplit(' - $', 1) 
        if len(parts) != 2:
            raise ValueError("Invalid product format.")
            
        product_name = parts[0].strip()
        price_str = parts[1].split('(')[0].strip() 
        price = float(price_str.replace('$', '').replace(',', '.'))
        
        usuario = session_db.query(Usuario).filter_by(telegram_id=user_id_telegram).first()
        producto = session_db.query(Producto).filter_by(nombre=product_name).first()

        if not usuario or not producto:
            await update.message.reply_text(t(lang, "buy_user_product_not_found"), reply_markup=get_keyboard_main(True, lang))
            return ConversationHandler.END

        # 1. Verificar Saldo
        if usuario.saldo < price:
            await update.message.reply_text(t(lang, "insufficient_balance", saldo=usuario.saldo), reply_markup=update.message.reply_markup)
            return BUY_PRODUCT
            
        # 2. Buscar Key Disponible (Inventario)
        available_key = session_db.query(Key).filter_by(
            producto_id=producto.id, 
            estado='available'
        ).with_for_update().first() 

        if not available_key:
            await update.message.reply_text(t(lang, "product_out_of_stock", product_name=producto.nombre), reply_markup=update.message.reply_markup)
            return BUY_PRODUCT
            
        # 3. Realizar la Transacción
        usuario.saldo -= price
        available_key.estado = 'used'
        
        session_db.commit()

        # 4. Éxito y Entrega de Clave
        await update.message.reply_text(
            t(
                lang,
                "purchase_success",
                product_name=producto.nombre,
                price=price,
                saldo=usuario.saldo,
                license_key=available_key.licencia,
            ),
            parse_mode='Markdown'
        )
        return await start(update, context)

    except ValueError:
        await update.message.reply_text(t(lang, "purchase_selection_error"), reply_markup=update.message.reply_markup)
        return BUY_PRODUCT
    except Exception as e:
        logger.error(f"Error en la transacción: {e}")
        session_db.rollback()
        await update.message.reply_text(t(lang, "purchase_error"))
        return ConversationHandler.END
    finally:
        session_db.close()
            
    await update.message.reply_text("Opción no válida. Elige una de las opciones del menú.", reply_markup=update.message.reply_markup)
    return BUY_PRODUCT


# =================================================================
# 5. Función Principal de Ejecución
# =================================================================

def main() -> None:
    """Ejecuta el bot."""
    application = Application.builder().token(TOKEN).build()

    # Handlers de comandos y botones de texto simples
    application.add_handler(CommandHandler("logout", logout))
    application.add_handler(MessageHandler(filters.Regex("^👤"), show_account))
    application.add_handler(MessageHandler(filters.Regex("^🚀"), logout))

    # Flujo de Login
    login_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^🔒"), show_login_prompt),
        ],
        states={
            LOGIN_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_login_key)],
            SET_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_language)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )
    application.add_handler(login_conv_handler)

    language_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🌐"), prompt_set_language)],
        states={
            SET_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_language)]
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(language_conv_handler)
    
    # Flujo de Compra
    buy_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🛒"), show_buy_menu)],
        states={
            BUY_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_selection)],
            BUY_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_final_purchase)],
        },
        fallbacks=[CommandHandler("start", start)], 
        per_user=True,
    )
    application.add_handler(buy_conv_handler)

    topup_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💳"), show_topup_menu)],
        states={
            TOPUP_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_topup_method)],
            TOPUP_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_topup_amount)],
            TOPUP_REFERENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_topup_reference)],
        },
        fallbacks=[CommandHandler("start", start)],
        per_user=True,
    )
    application.add_handler(topup_conv_handler)
    
    # Manejar el botón "➕ Crear cuenta"
    application.add_handler(MessageHandler(filters.Regex("^➕"), show_create_account_info))

    logger.info("El Bot de Telegram se está iniciando...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
