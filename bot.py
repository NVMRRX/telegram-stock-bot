import logging
import requests
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler

# Configuration du bot
TOKEN = "7869876698:AAFQmdneS0nSyDI36M0wPyAjnxQx3Mw91Mo"
CHAT_ID = 7924516784  # Ton ID utilisateur Telegram (remplace avec le tien)
bot = Bot(token=TOKEN)

# URLs des produits
PRODUCTS = {
    "Vinyle Mayhem Dédicacé": "https://shopfr.ladygaga.com/products/lp-exc-carte",
    "CD Mayhem Dédicacé": "https://shopfr.ladygaga.com/products/mayhem-cd-exclusif-store-dedicace",
}

PRODUCT_OPAQUE = "Vinyle Mayhem Opaque"
URL_OPAQUE = "https://shopfr.ladygaga.com/products/mayhem-exclusivite-store-vinyle-argente-opaque"

# Dictionnaire pour suivre l'état précédent des stocks
previous_stock = {product: True for product in PRODUCTS}
previous_stock[PRODUCT_OPAQUE] = True

async def check_stock():
    """Vérifie la disponibilité des produits (sauf vinyle opaque) et envoie une alerte."""
    global previous_stock
    while True:
        for product, url in PRODUCTS.items():
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                in_stock = "Prévenez-moi" not in response.text
                
                if in_stock and previous_stock[product]:
                    message = f"🔥 {product} est disponible ! FONCE !"
                    await bot.send_message(chat_id=CHAT_ID, text=message)
                previous_stock[product] = in_stock
            
            except requests.RequestException as e:
                logging.error(f"Erreur lors de la vérification de {product}: {e}")
                await bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Erreur de vérification pour {product}. Retente dans 10s.")
        
        await asyncio.sleep(10)  # Vérifie toutes les 10 secondes

async def check_stock_opaque():
    """Vérifie la disponibilité du Vinyle Opaque toutes les 30 minutes."""
    global previous_stock
    while True:
        try:
            response = requests.get(URL_OPAQUE, timeout=10)
            response.raise_for_status()
            in_stock = "Prévenez-moi" not in response.text
            
            if in_stock and previous_stock[PRODUCT_OPAQUE]:
                message = f"🔥 {PRODUCT_OPAQUE} est disponible ! FONCE !"
                await bot.send_message(chat_id=CHAT_ID, text=message)
            previous_stock[PRODUCT_OPAQUE] = in_stock
        
        except requests.RequestException as e:
            logging.error(f"Erreur lors de la vérification de {PRODUCT_OPAQUE}: {e}")
            await bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Erreur de vérification pour {PRODUCT_OPAQUE}. Retente dans 30 min.")
        
        await asyncio.sleep(1800)  # 30 minutes

async def manual_stock(update: Update, context):
    """Commande !stock pour vérifier manuellement le stock."""
    messages = []
    for product, url in {**PRODUCTS, PRODUCT_OPAQUE: URL_OPAQUE}.items():
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            in_stock = "Prévenez-moi" not in response.text
            status = "✅ En stock" if in_stock else "❌ Indisponible"
        except requests.RequestException:
            status = "⚠️ Erreur de vérification"
        messages.append(f"{product} : {status}")
    await update.message.reply_text("\n".join(messages))

async def periodic_check():
    """Effectue une vérification toutes les 4 minutes sans envoyer de message."""
    while True:
        await check_stock()
        await asyncio.sleep(240)  # 4 minutes

async def main():
    """Démarre le bot Telegram."""
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("stock", manual_stock))

    # Démarrer les tâches en arrière-plan
    asyncio.create_task(check_stock())
    asyncio.create_task(check_stock_opaque())
    asyncio.create_task(periodic_check())

    # Lancer le bot en mode polling (évite le problème de destruction des tâches)
    await application.run_polling()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot arrêté proprement.")
