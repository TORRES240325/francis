import os
import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from db_models import Usuario, Producto, Key, PaymentMethod, TopUpRequest, inicializar_db, get_session 
from dotenv import load_dotenv
from datetime import datetime

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
LOGIN_KEY, BUY_CATEGORY, BUY_PRODUCT, BUY_DURATION, TOPUP_METHOD, TOPUP_AMOUNT, TOPUP_REFERENCE, SET_LANGUAGE = range(8)

LANGUAGE_BUTTONS = {
    "es": "Español",
    "en": "English",
    "pt": "Português",
    "ar": "العربية",
    "hi": "हिन्दी",
}
LANGUAGE_LABEL_TO_CODE = {label.lower(): code for code, label in LANGUAGE_BUTTONS.items()}

SUPPORTED_LANGS = {"es", "en", "pt", "ar", "hi"}

BUTTONS = {
    "es": {
        "buy": "🛒 Comprar keys",
        "topup": "💳 Recargar saldo",
        "account": "👤 Cuenta",
        "logout": "🚀 Cerrar sesión",
        "language": "🌐 Idioma",
        "login": "🔒 Iniciar sesión",
        "create_account": "➕ Crear cuenta",
        "history": "📜 Historial",
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
        "history": "📜 History",
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
        "history": "📜 Histórico",
        "back": "⬅️ Voltar",
    },
    "ar": {
        "buy": "🛒 شراء المفاتيح",
        "topup": "💳 شحن الرصيد",
        "account": "👤 الحساب",
        "logout": "🚀 تسجيل الخروج",
        "language": "🌐 اللغة",
        "login": "🔒 تسجيل الدخول",
        "create_account": "➕ إنشاء حساب",
        "history": "📜 السجل",
        "back": "⬅️ رجوع",
    },
    "hi": {
        "buy": "🛒 की खरीदें",
        "topup": "💳 बैलेंस रिचार्ज",
        "account": "👤 खाता",
        "logout": "🚀 लॉग आउट",
        "language": "🌐 भाषा",
        "login": "🔒 लॉग इन",
        "create_account": "➕ खाता बनाएं",
        "history": "📜 इतिहास",
        "back": "⬅️ वापस",
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
        "insufficient_balance": "❌ Saldo insuficiente. Tu saldo actual es: ${saldo:.2f}.\nPor favor recarga saldo e intenta de nuevo.",
        "product_out_of_stock": "❌ Producto agotado. No hay claves disponibles para {product_name}.",
        "purchase_success": "🎉 **Compra Exitosa de {product_name}!**\nCosto: **${price:.2f}**\nTu nuevo saldo: **${saldo:.2f}**\n\n🔐 **Tu Key/Licencia:** `{license_key}`",
        "purchase_selection_error": "❌ Error al procesar la selección. Intenta de nuevo.",
        "purchase_error": "❌ Ocurrió un error en la compra. Intenta de nuevo o usa /start.",
        "history_title": "📜 **Tu Historial**",
        "history_purchases": "🛒 **Últimas compras**",
        "history_topups": "💳 **Últimas recargas**",
        "history_empty": "Sin registros todavía.",
        "choose_key_type": "📁 Elige un tipo de key para {product_name}:",
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
        "insufficient_balance": "❌ Insufficient balance. Your current balance is: ${saldo:.2f}.\nPlease top up your balance and try again.",
        "product_out_of_stock": "❌ Out of stock. No keys available for {product_name}.",
        "purchase_success": "🎉 **Successful purchase: {product_name}!**\nCost: **${price:.2f}**\nYour new balance: **${saldo:.2f}**\n\n🔐 **Your key/license:** `{license_key}`",
        "purchase_selection_error": "❌ Error processing selection. Please try again.",
        "purchase_error": "❌ An error occurred during purchase. Try again or use /start.",
        "history_title": "📜 **Your History**",
        "history_purchases": "🛒 **Latest purchases**",
        "history_topups": "💳 **Latest top-ups**",
        "history_empty": "No records yet.",
        "choose_key_type": "📁 Choose a key type for {product_name}:",
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
        "insufficient_balance": "❌ Saldo insuficiente. Seu saldo atual é: ${saldo:.2f}.\nPor favor recarregue o saldo e tente novamente.",
        "product_out_of_stock": "❌ Produto esgotado. Não há chaves disponíveis para {product_name}.",
        "purchase_success": "🎉 **Compra realizada de {product_name}!**\nCusto: **${price:.2f}**\nSeu novo saldo: **${saldo:.2f}**\n\n🔐 **Sua key/licença:** `{license_key}`",
        "purchase_selection_error": "❌ Erro ao processar a seleção. Tente novamente.",
        "purchase_error": "❌ Ocorreu um erro na compra. Tente novamente ou use /start.",
        "history_title": "📜 **Seu Histórico**",
        "history_purchases": "🛒 **Últimas compras**",
        "history_topups": "💳 **Últimas recargas**",
        "history_empty": "Sem registros ainda.",
        "choose_key_type": "📁 Escolha um tipo de key para {product_name}:",
    },
    "ar": {
        "welcome_back": "👋 **مرحبًا بعودتك، {username}.**\nجلستك نشطة.",
        "welcome_guest": "❌ **تم رفض الوصول. الرجاء تسجيل الدخول.**\nليس لديك صلاحية لاستخدام هذه الوظيفة.\nللحصول على الوصول أو الدعم تواصل مع المشرف →",
        "login_prompt": "🔒 أدخل بيانات الاعتماد التي أعطاها لك المشرف بهذا الشكل:\n\n**USERNAME PASSWORD**",
        "login_format_error": "❌ تنسيق غير صحيح. استخدم: `USERNAME PASSWORD`",
        "login_ok": "✅ **تم تسجيل الدخول بنجاح!**",
        "login_fail": "❌ تم رفض الوصول. بيانات الاعتماد غير صحيحة أو المستخدم غير موجود.",
        "id_taken": "❌ معرف Telegram الخاص بك مرتبط بالفعل. تواصل مع المشرف.",
        "account_create_info": "❌ تم رفض الوصول. الرجاء تسجيل الدخول.\nليس لديك صلاحية لاستخدام هذه الوظيفة.\nللوصول أو الدعم تواصل مع المشرف →\n\n🔒 أدخل بيانات الاعتماد بهذا الشكل:\n\nUSERNAME PASSWORD",
        "please_login": "❌ يجب تسجيل الدخول أولاً.",
        "choose_category": "اختر فئة:",
        "choose_product": "اختر منتجًا في الفئة {category}:",
        "no_products": "❌ لا توجد منتجات في الفئة: **{category}**",
        "language_saved": "✅ تم تغيير اللغة إلى العربية.",
        "language_choose": "🌐 اختر لغتك:",
        "language_invalid": "❌ لغة غير صالحة. استخدم الأزرار المتاحة.",
        "language_current": "اللغة الحالية",
        "account_already_linked": "❌ هذا الحساب مرتبط بالفعل بمستخدم Telegram آخر. تواصل مع المشرف.",
        "logout_ok": "🚪 تم تسجيل الخروج. استخدم /start للبدء من جديد.",
        "logout_none": "ليس لديك جلسة نشطة.",
        "account_info": "👤 **حسابك:**\n• المستخدم: **{username}**\n• الرصيد: **${saldo:.2f}**\n\n• اللغة: **{lang_name}**",
        "no_methods": "❌ لا توجد طرق دفع متاحة حاليًا. تواصل مع المشرف.",
        "topup_menu": "💳 **شحن الرصيد**\n\nاختر طريقة الدفع.\n\nالحد الأدنى للشحن: **${min_amount:.2f}**",
        "method_invalid_option": "❌ خيار غير صالح. اختر طريقة من القائمة.",
        "method_not_found": "❌ الطريقة غير موجودة أو غير مفعلة. اختر طريقة أخرى.",
        "topup_method_instructions": "الطريقة: **{method_name}**\n\nالتعليمات:\n{instructions}\n\nأدخل مبلغ الشحن (الحد الأدنى ${min_amount:.2f}):",
        "amount_invalid": "❌ مبلغ غير صالح. أدخل رقمًا (مثال: 10.00).",
        "amount_min_error": "❌ الحد الأدنى للشحن هو ${min_amount:.2f}. أدخل مبلغًا أكبر أو مساويًا.",
        "ask_reference": "الآن أرسل مرجع/إثبات الدفع (مثل ID العملية أو لقطة شاشة أو نص).",
        "reference_empty": "❌ المرجع لا يمكن أن يكون فارغًا. حاول مرة أخرى.",
        "internal_error": "❌ خطأ داخلي. حاول مرة أخرى.",
        "topup_created": "✅ تم إنشاء طلب الشحن.\n\nID: `{request_id}`\nالمبلغ: **${amount:.2f}**\nالحالة: **pending**\n\nسيتم مراجعته من المشرف قريبًا.",
        "topup_create_error": "❌ حدث خطأ أثناء إنشاء الطلب. حاول مرة أخرى.",
        "buy_user_product_not_found": "❌ خطأ داخلي: المستخدم أو المنتج غير موجود.",
        "insufficient_balance": "❌ الرصيد غير كافٍ. رصيدك الحالي: ${saldo:.2f}.\nيرجى شحن الرصيد ثم المحاولة مرة أخرى.",
        "product_out_of_stock": "❌ المنتج غير متوفر. لا توجد مفاتيح متاحة لـ {product_name}.",
        "purchase_success": "🎉 **تم شراء {product_name} بنجاح!**\nالسعر: **${price:.2f}**\nرصيدك الجديد: **${saldo:.2f}**\n\n🔐 **المفتاح/الترخيص:** `{license_key}`",
        "purchase_selection_error": "❌ خطأ في معالجة الاختيار. حاول مرة أخرى.",
        "purchase_error": "❌ حدث خطأ أثناء الشراء. حاول مرة أخرى أو استخدم /start.",
        "history_title": "📜 **سجلك**",
        "history_purchases": "🛒 **آخر المشتريات**",
        "history_topups": "💳 **آخر عمليات الشحن**",
        "history_empty": "لا توجد سجلات بعد.",
        "choose_key_type": "📁 اختر نوع المفتاح لـ {product_name}:",
    },
    "hi": {
        "welcome_back": "👋 **वापसी पर स्वागत है, {username}.**\nआपका सेशन सक्रिय है।",
        "welcome_guest": "❌ **एक्सेस अस्वीकृत। कृपया लॉग इन करें।**\nआपको इस फ़ंक्शन का उपयोग करने की अनुमति नहीं है।\nएक्सेस या सहायता के लिए एडमिन से संपर्क करें →",
        "login_prompt": "🔒 एडमिन द्वारा दिए गए क्रेडेंशियल इस फ़ॉर्मेट में दर्ज करें:\n\n**USERNAME PASSWORD**",
        "login_format_error": "❌ गलत फ़ॉर्मेट। उपयोग करें: `USERNAME PASSWORD`",
        "login_ok": "✅ **सफलतापूर्वक अधिकृत!**",
        "login_fail": "❌ एक्सेस अस्वीकृत। गलत क्रेडेंशियल या उपयोगकर्ता नहीं मिला।",
        "id_taken": "❌ आपका Telegram ID पहले से लिंक है। एडमिन से संपर्क करें।",
        "account_create_info": "❌ एक्सेस अस्वीकृत। कृपया लॉग इन करें।\nआपको इस फ़ंक्शन का उपयोग करने की अनुमति नहीं है।\nएक्सेस या सहायता के लिए एडमिन से संपर्क करें →\n\n🔒 क्रेडेंशियल इस फ़ॉर्मेट में दर्ज करें:\n\nUSERNAME PASSWORD",
        "please_login": "❌ पहले लॉग इन करें।",
        "choose_category": "एक श्रेणी चुनें:",
        "choose_product": "{category} में एक उत्पाद चुनें:",
        "no_products": "❌ इस श्रेणी में कोई उत्पाद नहीं मिला: **{category}**",
        "language_saved": "✅ भाषा हिन्दी में बदल दी गई है।",
        "language_choose": "🌐 अपनी भाषा चुनें:",
        "language_invalid": "❌ अमान्य भाषा। उपलब्ध बटन का उपयोग करें।",
        "language_current": "वर्तमान भाषा",
        "account_already_linked": "❌ यह खाता पहले से किसी अन्य Telegram उपयोगकर्ता से लिंक है। एडमिन से संपर्क करें।",
        "logout_ok": "🚪 सेशन बंद किया गया। फिर से शुरू करने के लिए /start उपयोग करें।",
        "logout_none": "आपका कोई सक्रिय सेशन नहीं है।",
        "account_info": "👤 **आपका खाता:**\n• उपयोगकर्ता: **{username}**\n• बैलेंस: **${saldo:.2f}**\n\n• भाषा: **{lang_name}**",
        "no_methods": "❌ अभी कोई भुगतान विधि उपलब्ध नहीं है। एडमिन से संपर्क करें।",
        "topup_menu": "💳 **बैलेंस रिचार्ज**\n\nभुगतान विधि चुनें।\n\nन्यूनतम रिचार्ज: **${min_amount:.2f}**",
        "method_invalid_option": "❌ अमान्य विकल्प। सूची से एक विधि चुनें।",
        "method_not_found": "❌ विधि नहीं मिली या निष्क्रिय है। दूसरी विधि चुनें।",
        "topup_method_instructions": "विधि: **{method_name}**\n\nनिर्देश:\n{instructions}\n\nरिचार्ज राशि दर्ज करें (न्यूनतम ${min_amount:.2f}):",
        "amount_invalid": "❌ अमान्य राशि। एक संख्या दर्ज करें (जैसे 10.00)।",
        "amount_min_error": "❌ न्यूनतम रिचार्ज राशि ${min_amount:.2f} है। बराबर या अधिक राशि दर्ज करें।",
        "ask_reference": "अब संदर्भ/प्रमाण दर्ज करें (जैसे ट्रांज़ैक्शन ID, स्क्रीनशॉट, टेक्स्ट)।",
        "reference_empty": "❌ संदर्भ खाली नहीं हो सकता। फिर कोशिश करें।",
        "internal_error": "❌ आंतरिक त्रुटि। फिर से कोशिश करें।",
        "topup_created": "✅ रिचार्ज अनुरोध बना दिया गया है।\n\nID: `{request_id}`\nराशि: **${amount:.2f}**\nस्थिति: **pending**\n\nएडमिन जल्द समीक्षा करेगा।",
        "topup_create_error": "❌ अनुरोध बनाते समय त्रुटि हुई। फिर कोशिश करें।",
        "buy_user_product_not_found": "❌ आंतरिक त्रुटि: उपयोगकर्ता या उत्पाद नहीं मिला।",
        "insufficient_balance": "❌ बैलेंस कम है। आपका वर्तमान बैलेंस: ${saldo:.2f}.\nकृपया बैलेंस रिचार्ज करके फिर कोशिश करें।",
        "product_out_of_stock": "❌ स्टॉक समाप्त। {product_name} के लिए कोई key उपलब्ध नहीं है।",
        "purchase_success": "🎉 **{product_name} की खरीद सफल!**\nकीमत: **${price:.2f}**\nआपका नया बैलेंस: **${saldo:.2f}**\n\n🔐 **आपकी key/license:** `{license_key}`",
        "purchase_selection_error": "❌ चयन प्रोसेस करते समय त्रुटि। फिर कोशिश करें।",
        "purchase_error": "❌ खरीद के दौरान त्रुटि हुई। फिर कोशिश करें या /start उपयोग करें।",
        "history_title": "📜 **आपका इतिहास**",
        "history_purchases": "🛒 **हाल की खरीद**",
        "history_topups": "💳 **हाल के रिचार्ज**",
        "history_empty": "अभी कोई रिकॉर्ड नहीं है।",
        "choose_key_type": "📁 {product_name} के लिए key type चुनें:",
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


def md_safe(value: object) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("\\", "\\\\")
        .replace("_", "\\_")
        .replace("*", "\\*")
        .replace("`", "\\`")
        .replace("[", "\\[")
    )


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
    """Genera teclado fijo (ReplyKeyboard) principal."""
    lang = _norm_lang(lang)
    if is_logged_in:
        keyboard = [
            [KeyboardButton(b(lang, "buy")), KeyboardButton(b(lang, "account"))],
            [KeyboardButton(b(lang, "logout")), KeyboardButton(b(lang, "language"))],
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
        [
            InlineKeyboardButton(LANGUAGE_BUTTONS["es"], callback_data="setlang:es"),
            InlineKeyboardButton(LANGUAGE_BUTTONS["en"], callback_data="setlang:en"),
        ],
        [
            InlineKeyboardButton(LANGUAGE_BUTTONS["pt"], callback_data="setlang:pt"),
            InlineKeyboardButton(LANGUAGE_BUTTONS["ar"], callback_data="setlang:ar"),
        ],
        [InlineKeyboardButton(LANGUAGE_BUTTONS["hi"], callback_data="setlang:hi")],
        [InlineKeyboardButton(b(lang, "back"), callback_data="menu_back_start")],
    ]
    return current_label, InlineKeyboardMarkup(keyboard)


def get_account_actions_keyboard(lang: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "history_purchases").replace("**", ""), callback_data="account_purchases")],
        [InlineKeyboardButton(t(lang, "history_topups").replace("**", ""), callback_data="account_topups")],
    ])


def _reply_target(update: Update):
    if update.callback_query:
        return update.callback_query.message
    return update.message

# =================================================================
# 3. Handlers de Inicio y Login
# =================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Muestra el mensaje de bienvenida y el teclado de login/menu."""
    user_id_telegram = update.effective_user.id
    target = _reply_target(update)
    if update.callback_query:
        await update.callback_query.answer()
    
    with get_session() as session_db:
        usuario = session_db.query(Usuario).filter_by(telegram_id=user_id_telegram).first() 

    if usuario:
        lang = _norm_lang(getattr(usuario, "idioma", "es"))
        await target.reply_text(
            t(lang, "welcome_back", username=md_safe(usuario.username)),
            reply_markup=get_keyboard_main(True, lang)
        )
    else:
        lang = _norm_lang(context.user_data.get("guest_lang", "es"))
        await target.reply_text(
            f"{t(lang, 'welcome_guest')}\n\n{t(lang, 'login_prompt')}",
            reply_markup=get_keyboard_main(False, lang)
        )
        return LOGIN_KEY
    return ConversationHandler.END

async def show_login_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pide al usuario que ingrese las credenciales."""
    if update.callback_query:
        await update.callback_query.answer()
    lang = _norm_lang(context.user_data.get("guest_lang", get_lang_for_telegram(update.effective_user.id)))
    await _reply_target(update).reply_text(
        t(lang, "login_prompt"),
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
            
            guest_lang = context.user_data.get("guest_lang")
            if guest_lang in SUPPORTED_LANGS and usuario.idioma != guest_lang:
                usuario.idioma = guest_lang
                session_db.commit()

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
    
    if update.callback_query:
        await update.callback_query.answer()
    target = _reply_target(update)

    if is_logged_in:
        await target.reply_text(
            t(lang, "logout_ok"),
            reply_markup=get_keyboard_main(False, lang)
        )
    else:
        await target.reply_text(
            t(lang, "logout_none"),
            reply_markup=get_keyboard_main(False, lang)
        )
        
async def show_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra la información de la cuenta."""
    user_id_telegram = update.effective_user.id
    if update.callback_query:
        await update.callback_query.answer()
    target = _reply_target(update)
    
    with get_session() as session_db:
        usuario = session_db.query(Usuario).filter_by(telegram_id=user_id_telegram).first()
    
    if usuario:
        lang = _norm_lang(getattr(usuario, "idioma", "es"))
        lang_name = LANGUAGE_BUTTONS.get(lang, LANGUAGE_BUTTONS["es"])
        message = t(lang, "account_info", username=md_safe(usuario.username), saldo=usuario.saldo, lang_name=md_safe(lang_name))
        account_actions = get_account_actions_keyboard(lang)

        await target.reply_text(message, parse_mode='Markdown', reply_markup=account_actions)
    else:
        lang = _norm_lang(context.user_data.get("guest_lang", "es"))
        await target.reply_text(t(lang, "please_login"))


async def handle_account_inline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    user_id_telegram = update.effective_user.id

    with get_session() as session_db:
        usuario = session_db.query(Usuario).filter_by(telegram_id=user_id_telegram).first()
        if not usuario:
            lang = _norm_lang(context.user_data.get("guest_lang", "es"))
            await query.edit_message_text(t(lang, "please_login"))
            return

        lang = _norm_lang(getattr(usuario, "idioma", "es"))
        lang_name = LANGUAGE_BUTTONS.get(lang, LANGUAGE_BUTTONS["es"])
        base_account = t(lang, "account_info", username=md_safe(usuario.username), saldo=usuario.saldo, lang_name=md_safe(lang_name))

        details = ""
        if data == "account_purchases":
            compras = (
                session_db.query(Key)
                .filter(Key.usuario_id == usuario.id, Key.estado == "used")
                .order_by(Key.fecha_compra.desc().nullslast(), Key.id.desc())
                .limit(10)
                .all()
            )
            lines = []
            for c in compras:
                producto_nombre = c.producto.nombre if c.producto else f"ID {c.producto_id}"
                fecha_txt = c.fecha_compra.strftime("%Y-%m-%d %H:%M") if c.fecha_compra else "-"
                lines.append(f"• {md_safe(producto_nombre)} | `{md_safe(c.licencia)}` | {md_safe(fecha_txt)}")
            details = f"\n\n{t(lang, 'history_purchases')}\n{chr(10).join(lines) if lines else t(lang, 'history_empty')}"
        elif data == "account_topups":
            recargas = (
                session_db.query(TopUpRequest)
                .filter(TopUpRequest.usuario_id == usuario.id)
                .order_by(TopUpRequest.fecha_creacion.desc())
                .limit(10)
                .all()
            )
            lines = []
            for r in recargas:
                fecha_txt = r.fecha_creacion.strftime("%Y-%m-%d %H:%M") if r.fecha_creacion else "-"
                metodo = r.metodo_pago.nombre if r.metodo_pago else "-"
                lines.append(f"• ID `{r.id}` | ${r.monto:.2f} | {md_safe(r.status)} | {md_safe(metodo)} | {md_safe(fecha_txt)}")
            details = f"\n\n{t(lang, 'history_topups')}\n{chr(10).join(lines) if lines else t(lang, 'history_empty')}"

    account_actions = get_account_actions_keyboard(lang)
    await query.edit_message_text(f"{base_account}{details}", parse_mode='Markdown', reply_markup=account_actions)


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id_telegram = update.effective_user.id
    lang = get_lang_for_telegram(user_id_telegram)

    if update.callback_query:
        await update.callback_query.answer()
    target = _reply_target(update)

    with get_session() as session_db:
        usuario = session_db.query(Usuario).filter_by(telegram_id=user_id_telegram).first()
        if not usuario:
            await target.reply_text(t(lang, "please_login"), reply_markup=get_keyboard_main(False, lang))
            return

        compras = (
            session_db.query(Key)
            .filter(Key.usuario_id == usuario.id, Key.estado == "used")
            .order_by(Key.fecha_compra.desc().nullslast(), Key.id.desc())
            .limit(10)
            .all()
        )
        recargas = (
            session_db.query(TopUpRequest)
            .filter(TopUpRequest.usuario_id == usuario.id)
            .order_by(TopUpRequest.fecha_creacion.desc())
            .limit(10)
            .all()
        )

        compras_lines = []
        for c in compras:
            producto_nombre = c.producto.nombre if c.producto else f"ID {c.producto_id}"
            fecha_txt = c.fecha_compra.strftime("%Y-%m-%d %H:%M") if c.fecha_compra else "-"
            compras_lines.append(f"• {md_safe(producto_nombre)} | `{md_safe(c.licencia)}` | {md_safe(fecha_txt)}")

        recargas_lines = []
        for r in recargas:
            fecha_txt = r.fecha_creacion.strftime("%Y-%m-%d %H:%M") if r.fecha_creacion else "-"
            metodo = r.metodo_pago.nombre if r.metodo_pago else "-"
            recargas_lines.append(f"• ID `{r.id}` | ${r.monto:.2f} | {md_safe(r.status)} | {md_safe(metodo)} | {md_safe(fecha_txt)}")

    text = (
        f"{t(lang, 'history_title')}\n\n"
        f"{t(lang, 'history_purchases')}\n"
        f"{chr(10).join(compras_lines) if compras_lines else t(lang, 'history_empty')}\n\n"
        f"{t(lang, 'history_topups')}\n"
        f"{chr(10).join(recargas_lines) if recargas_lines else t(lang, 'history_empty')}"
    )

    await target.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=get_keyboard_main(True, lang)
    )


async def prompt_set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
    lang = _norm_lang(context.user_data.get("guest_lang", get_lang_for_telegram(update.effective_user.id)))
    current_label, lang_keyboard = get_language_keyboard(lang)
    await _reply_target(update).reply_text(
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
        current_lang = _norm_lang(context.user_data.get("guest_lang", get_lang_for_telegram(update.effective_user.id)))
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
            reply_markup=ReplyKeyboardRemove()
        )
        return LOGIN_KEY

    return ConversationHandler.END


async def save_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "menu_back_start":
        return await start(update, context)

    lang_input = data.split(":", 1)[1] if ":" in data else ""
    if lang_input not in SUPPORTED_LANGS:
        current_lang = _norm_lang(context.user_data.get("guest_lang", get_lang_for_telegram(update.effective_user.id)))
        await query.message.reply_text(t(current_lang, "language_invalid"))
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

    await query.message.reply_text(
        t(lang_input, "language_saved"),
        reply_markup=get_keyboard_main(is_logged_in, lang_input)
    )

    if not is_logged_in:
        await query.message.reply_text(
            t(lang_input, "login_prompt"),
            reply_markup=ReplyKeyboardRemove()
        )
        return LOGIN_KEY

    return ConversationHandler.END


async def show_create_account_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
    lang = _norm_lang(context.user_data.get("guest_lang", get_lang_for_telegram(update.effective_user.id)))
    await _reply_target(update).reply_text(t(lang, "account_create_info"), reply_markup=get_keyboard_main(False, lang))
    return LOGIN_KEY


async def show_topup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id_telegram = update.effective_user.id
    lang = get_lang_for_telegram(user_id_telegram)

    if update.callback_query:
        await update.callback_query.answer()
    target = _reply_target(update)

    with get_session() as session_db:
        usuario = session_db.query(Usuario).filter_by(telegram_id=user_id_telegram).first()
        if not usuario:
            await target.reply_text(t(lang, "please_login"))
            return ConversationHandler.END

        metodos = session_db.query(PaymentMethod).filter_by(activo=True).order_by(PaymentMethod.id.asc()).all()

    if not metodos:
        await target.reply_text(
            t(lang, "no_methods"),
            reply_markup=get_keyboard_main(True, lang)
        )
        return ConversationHandler.END

    keyboard_rows = [[InlineKeyboardButton(m.nombre, callback_data=f"topup_method:{m.id}")] for m in metodos]
    keyboard_rows.append([InlineKeyboardButton(b(lang, "back"), callback_data="menu_back_start")])
    reply_markup = InlineKeyboardMarkup(keyboard_rows)

    await target.reply_text(
        t(lang, "topup_menu", min_amount=MIN_TOPUP_AMOUNT),
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return TOPUP_METHOD


async def handle_topup_method_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = get_lang_for_telegram(update.effective_user.id)
    data = query.data or ""

    if data == "menu_back_start":
        await start(update, context)
        return ConversationHandler.END

    try:
        method_id = int(data.split(":", 1)[1])
    except Exception:
        await query.message.reply_text(t(lang, "method_invalid_option"))
        return TOPUP_METHOD

    with get_session() as session_db:
        metodo = session_db.query(PaymentMethod).filter_by(id=method_id, activo=True).first()

    if not metodo:
        await query.message.reply_text(t(lang, "method_not_found"))
        return TOPUP_METHOD

    context.user_data['topup_method_id'] = metodo.id
    context.user_data['topup_method_name'] = metodo.nombre

    await query.message.reply_text(
        t(lang, "topup_method_instructions", method_name=metodo.nombre, instructions=metodo.instrucciones, min_amount=MIN_TOPUP_AMOUNT),
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return TOPUP_AMOUNT


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
    reference = ""
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        caption = (update.message.caption or "").strip()
        reference = f"PHOTO:{file_id}"
        if caption:
            reference = f"{reference} | {caption}"
    else:
        reference = (update.message.text or "").strip()

    reference = reference[:240]
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
    
    category_map = {}
    keyboard_rows = []
    for cat_tuple in categorias:
        categoria = cat_tuple[0]
        if categoria:
            idx = str(len(category_map))
            category_map[idx] = categoria
            keyboard_rows.append([InlineKeyboardButton(categoria, callback_data=f"buy_cat:{idx}")])

    context.user_data["buy_category_map"] = category_map
    keyboard_rows.append([InlineKeyboardButton(b(lang, "back"), callback_data="menu_back_start")])
    reply_markup = InlineKeyboardMarkup(keyboard_rows)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(t(lang, "choose_category"), reply_markup=reply_markup)
    else:
        await update.message.reply_text(t(lang, "choose_category"), reply_markup=reply_markup)
    return BUY_CATEGORY


async def handle_category_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    lang = get_lang_for_telegram(update.effective_user.id)

    if data == "menu_back_start":
        await start(update, context)
        return ConversationHandler.END

    key = data.split(":", 1)[1] if ":" in data else ""
    category = context.user_data.get("buy_category_map", {}).get(key)
    if not category:
        await query.message.reply_text(t(lang, "purchase_selection_error"))
        return BUY_CATEGORY

    with get_session() as session_db:
        productos = session_db.query(Producto).filter_by(categoria=category).all()

    if not productos:
        await query.edit_message_text(t(lang, "no_products", category=category), parse_mode='Markdown')
        return BUY_CATEGORY

    context.user_data["selected_category"] = category
    keyboard_rows = []
    for producto in productos:
        with get_session() as s:
            stock = s.query(Key).filter(Key.producto_id == producto.id, Key.estado == 'available').count()
        button_text = f"{producto.nombre} - ${producto.precio:.2f} (Stock: {stock})"
        keyboard_rows.append([InlineKeyboardButton(button_text, callback_data=f"buy_prod:{producto.id}")])

    keyboard_rows.append([InlineKeyboardButton(b(lang, "back"), callback_data="menu_buy")])
    await query.edit_message_text(
        t(lang, "choose_product", category=category),
        reply_markup=InlineKeyboardMarkup(keyboard_rows)
    )
    return BUY_PRODUCT


async def handle_product_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    user_id_telegram = update.effective_user.id
    lang = get_lang_for_telegram(user_id_telegram)

    if data == "menu_buy":
        return await show_buy_menu(update, context)

    try:
        product_id = int(data.split(":", 1)[1])
    except Exception:
        await query.edit_message_text(t(lang, "purchase_selection_error"))
        return BUY_PRODUCT

    with get_session() as session_db:
        producto = session_db.query(Producto).filter_by(id=product_id).first()
        if not producto:
            await query.edit_message_text(t(lang, "buy_user_product_not_found"))
            return ConversationHandler.END

        duration_rows = (
            session_db.query(
                Key.duracion,
                func.coalesce(Key.precio, Producto.precio).label("price_value"),
                func.count(Key.id).label("stock_value"),
            )
            .join(Producto, Producto.id == Key.producto_id)
            .filter(Key.producto_id == producto.id, Key.estado == "available")
            .group_by(Key.duracion, func.coalesce(Key.precio, Producto.precio))
            .order_by(Key.duracion.asc())
            .all()
        )

    if not duration_rows:
        await query.edit_message_text(t(lang, "product_out_of_stock", product_name=producto.nombre))
        return BUY_PRODUCT

    duration_map = {}
    keyboard_rows = []
    for idx, row in enumerate(duration_rows):
        duration_value = row[0] or "General"
        price_value = float(row[1] if row[1] is not None else producto.precio)
        stock_value = int(row[2] or 0)
        key = str(idx)
        duration_map[key] = {"duration": duration_value, "price": price_value}
        button_text = f"{duration_value} - ${price_value:.2f} (Stock: {stock_value})"
        keyboard_rows.append([InlineKeyboardButton(button_text, callback_data=f"buy_dur:{producto.id}:{key}")])

    context.user_data["buy_selected_product_id"] = producto.id
    context.user_data["buy_duration_map"] = duration_map
    keyboard_rows.append([InlineKeyboardButton(b(lang, "back"), callback_data="buy_back_prod")])
    await query.edit_message_text(
        t(lang, "choose_key_type", product_name=producto.nombre),
        reply_markup=InlineKeyboardMarkup(keyboard_rows)
    )
    return BUY_DURATION


async def handle_final_purchase_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    user_id_telegram = update.effective_user.id
    lang = get_lang_for_telegram(user_id_telegram)

    if data == "menu_buy":
        return await show_buy_menu(update, context)
    if data == "buy_back_prod":
        category = context.user_data.get("selected_category")
        if not category:
            return await show_buy_menu(update, context)

        with get_session() as session_db:
            productos = session_db.query(Producto).filter_by(categoria=category).all()

        keyboard_rows = []
        for producto in productos:
            with get_session() as s:
                stock = s.query(Key).filter(Key.producto_id == producto.id, Key.estado == 'available').count()
            button_text = f"{producto.nombre} - ${producto.precio:.2f} (Stock: {stock})"
            keyboard_rows.append([InlineKeyboardButton(button_text, callback_data=f"buy_prod:{producto.id}")])
        keyboard_rows.append([InlineKeyboardButton(b(lang, "back"), callback_data="menu_buy")])

        await query.edit_message_text(
            t(lang, "choose_product", category=category),
            reply_markup=InlineKeyboardMarkup(keyboard_rows)
        )
        return BUY_PRODUCT

    parts = data.split(":")
    if len(parts) != 3 or parts[0] != "buy_dur":
        await query.edit_message_text(t(lang, "purchase_selection_error"))
        return BUY_DURATION

    try:
        product_id = int(parts[1])
    except Exception:
        await query.edit_message_text(t(lang, "purchase_selection_error"))
        return BUY_DURATION

    duration_key = parts[2]
    selected_duration_data = context.user_data.get("buy_duration_map", {}).get(duration_key)
    if not selected_duration_data:
        await query.edit_message_text(t(lang, "purchase_selection_error"))
        return BUY_DURATION
    selected_duration = selected_duration_data.get("duration", "General")
    selected_price = float(selected_duration_data.get("price", 0.0))

    session_db = get_session()
    try:
        usuario = session_db.query(Usuario).filter_by(telegram_id=user_id_telegram).first()
        producto = session_db.query(Producto).filter_by(id=product_id).first()

        if not usuario or not producto:
            await query.message.reply_text(t(lang, "buy_user_product_not_found"), reply_markup=get_keyboard_main(True, lang))
            return ConversationHandler.END

        price_to_charge = selected_price if selected_price > 0 else float(producto.precio)

        if usuario.saldo < price_to_charge:
            await query.edit_message_text(t(lang, "insufficient_balance", saldo=usuario.saldo))
            return BUY_DURATION

        available_key = session_db.query(Key).filter_by(
            producto_id=producto.id,
            duracion=selected_duration,
            estado='available'
        ).with_for_update().first()

        if not available_key:
            await query.edit_message_text(t(lang, "product_out_of_stock", product_name=producto.nombre))
            return BUY_DURATION

        usuario.saldo -= price_to_charge
        available_key.estado = 'used'
        available_key.usuario_id = usuario.id
        available_key.fecha_compra = datetime.now()
        session_db.commit()

        await query.message.reply_text(
            t(
                lang,
                "purchase_success",
                product_name=md_safe(producto.nombre),
                price=price_to_charge,
                saldo=usuario.saldo,
                license_key=md_safe(available_key.licencia),
            ),
            parse_mode='Markdown',
            reply_markup=get_keyboard_main(True, lang)
        )
        context.user_data.pop("buy_duration_map", None)
        context.user_data.pop("buy_selected_product_id", None)
        context.user_data.pop("selected_category", None)
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error en compra inline: {e}")
        session_db.rollback()
        await query.edit_message_text(t(lang, "purchase_error"))
        return ConversationHandler.END
    finally:
        session_db.close()

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
    product_button_map = {}
    
    for producto in productos:
        with get_session() as s:
            stock = s.query(Key).filter(Key.producto_id == producto.id, Key.estado == 'available').count()
        
        button_text = f"{producto.nombre} - ${producto.precio:.2f} (Stock: {stock})"
        product_keys.append([KeyboardButton(button_text)])
        product_button_map[button_text] = producto.id
            
    product_keys.append([KeyboardButton(b(lang, "back"))])
    context.user_data["product_button_map"] = product_button_map
    
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
        product_map = context.user_data.get("product_button_map", {})
        product_id = product_map.get(text)
        if not product_id:
            raise ValueError("Invalid product format.")
        
        usuario = session_db.query(Usuario).filter_by(telegram_id=user_id_telegram).first()
        producto = session_db.query(Producto).filter_by(id=product_id).first()

        if not usuario or not producto:
            await update.message.reply_text(t(lang, "buy_user_product_not_found"), reply_markup=get_keyboard_main(True, lang))
            return ConversationHandler.END

        # 1. Verificar Saldo
        if usuario.saldo < producto.precio:
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
        usuario.saldo -= producto.precio
        available_key.estado = 'used'
        available_key.usuario_id = usuario.id
        available_key.fecha_compra = datetime.now()
        
        session_db.commit()

        # 4. Éxito y Entrega de Clave
        await update.message.reply_text(
            t(
                lang,
                "purchase_success",
                product_name=md_safe(producto.nombre),
                price=producto.precio,
                saldo=usuario.saldo,
                license_key=md_safe(available_key.licencia),
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


async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = (update.callback_query.data or "") if update.callback_query else ""

    if data == "menu_login":
        return await show_login_prompt(update, context)
    if data == "menu_create":
        return await show_create_account_info(update, context)
    if data == "menu_lang":
        return await prompt_set_language(update, context)
    if data == "menu_account":
        await show_account(update, context)
        return ConversationHandler.END
    if data == "menu_history":
        await show_history(update, context)
        return ConversationHandler.END
    if data == "menu_logout":
        await logout(update, context)
        return ConversationHandler.END
    if data == "menu_back_start":
        return await start(update, context)

    if update.callback_query:
        await update.callback_query.answer()
    return ConversationHandler.END


# =================================================================
# 5. Función Principal de Ejecución
# =================================================================

def main() -> None:
    """Ejecuta el bot."""
    application = Application.builder().token(TOKEN).build()

    # Handlers de comandos y botones de texto
    application.add_handler(CommandHandler("logout", logout))
    application.add_handler(MessageHandler(filters.Regex("^👤"), show_account))
    application.add_handler(MessageHandler(filters.Regex("^🚀"), logout))
    application.add_handler(CallbackQueryHandler(handle_account_inline, pattern=r"^account_(purchases|topups)$"))

    # Flujo de Login
    login_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^🔒"), show_login_prompt),
            CallbackQueryHandler(show_login_prompt, pattern=r"^menu_login$"),
            CallbackQueryHandler(prompt_set_language, pattern=r"^menu_lang$"),
            CallbackQueryHandler(show_create_account_info, pattern=r"^menu_create$"),
        ],
        states={
            LOGIN_KEY: [
                CallbackQueryHandler(show_login_prompt, pattern=r"^menu_login$"),
                CallbackQueryHandler(prompt_set_language, pattern=r"^menu_lang$"),
                CallbackQueryHandler(show_create_account_info, pattern=r"^menu_create$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_login_key),
            ],
            SET_LANGUAGE: [
                CallbackQueryHandler(save_language_callback, pattern=r"^(setlang:|menu_back_start$)"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )
    application.add_handler(login_conv_handler)

    language_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🌐"), prompt_set_language)],
        states={
            SET_LANGUAGE: [
                CallbackQueryHandler(save_language_callback, pattern=r"^(setlang:|menu_back_start$)"),
            ]
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(language_conv_handler)

    # Flujo de Compra
    buy_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🛒"), show_buy_menu)],
        states={
            BUY_CATEGORY: [CallbackQueryHandler(handle_category_selection_callback, pattern=r"^(buy_cat:|menu_back_start$)")],
            BUY_PRODUCT: [CallbackQueryHandler(handle_product_selection_callback, pattern=r"^(buy_prod:|menu_buy$)")],
            BUY_DURATION: [CallbackQueryHandler(handle_final_purchase_callback, pattern=r"^(buy_dur:|buy_back_prod$|menu_buy$)")],
        },
        fallbacks=[CommandHandler("start", start)], 
        per_user=True,
    )
    application.add_handler(buy_conv_handler)

    topup_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(show_topup_menu, pattern=r"^menu_topup$")],
        states={
            TOPUP_METHOD: [CallbackQueryHandler(handle_topup_method_callback, pattern=r"^(topup_method:|menu_back_start$)")],
            TOPUP_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_topup_amount)],
            TOPUP_REFERENCE: [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_topup_reference)],
        },
        fallbacks=[CommandHandler("start", start)],
        per_user=True,
    )
    application.add_handler(topup_conv_handler)
    logger.info("El Bot de Telegram se está iniciando...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
