"""
TDC TECH WhatsApp Business Bot
Official auto-reply for +256 751 365093

On first message: introduces the business immediately, then language, then menu.
Services match the TDC Tech dashboard.
"""

import json
import os
import time
import uuid
from pathlib import Path

import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "tdctech-verify")
ADMIN_TO = os.environ.get("ADMIN_WHATSAPP", "")
GRAPH = "https://graph.facebook.com/v21.0"
SITE = "https://tdctech.org"
ROOT = Path(__file__).parent
LEADS = ROOT / "leads.json"
SESS = ROOT / "sessions.json"

SERVICES = [
    ("Social media ads", "From £75", "Managed Meta, TikTok, Google, LinkedIn, and X campaigns.", "platform and daily budget"),
    ("Music and video promotion", "From £120", "Playlist pitching, blogs, and promo campaigns.", "artist name and release title"),
    ("Verification", "£250", "Managed Meta, TikTok, or X application.", "platform and profile link"),
    ("Web and app development", "From £499", "Sites, landing pages, and apps.", "what you want built"),
    ("Account management", "From £299", "Dedicated manager for content and community.", "platforms to manage"),
    ("Press releases", "From £85", "200+ outlets. Tier-1 wire £250. Wikipedia from £150.", "story in one line"),
    ("Likes, views, and followers", "From £1.50", "Instagram, TikTok, YouTube, Spotify, and more.", "platform and quantity"),
    ("Virtual numbers", "From £2", "SMS numbers in 50+ countries.", "country and app, e.g. UK WhatsApp"),
    ("Custom bots", "From £30", "Telegram, DM, and auto-reply bots.", "what the bot should do"),
    ("Proxies", "From £6", "Residential, datacenter, and mobile.", "type and GB"),
    ("Music distribution", "£15", "150+ DSPs per release. ISRC and UPC included.", "artist and track title"),
    ("Video distribution", "From £35", "Music videos and short films to VOD platforms.", "video title"),
    ("Web and app templates", "From £29", "Next.js, React, and HTML templates.", "template you want"),
]

COPY = {
    "en": {
        "intro": (
            "TDC TECH®\n"
            "Founded by Topistar Di Congo under TDC CREATIVES.\n\n"
            "We help anyone connect to social media and internet technology.\n"
            "Music distribution, ads, verification, press, virtual numbers, bots, and web work — from one dashboard.\n"
            "Wallet payments: card, USDT, ETH, Bitcoin, MTN, Airtel.\n"
            f"Site: {SITE}\n\n"
            "Choose your language:\n"
            "1 English\n"
            "2 Français\n"
            "3 Kiswahili"
        ),
        "menu": (
            "Main menu — reply with a number:\n"
            "1 Explore services and order\n"
            "2 Make a payment / deposit\n"
            "3 Payment inquiry\n"
            "4 Talk to a human agent\n"
            "5 Request a refund\n"
            "6 Write feedback\n"
            "7 Track an order\n"
            "8 FAQ\n"
            "9 Change language\n\n"
            "Reply 0 anytime for this menu."
        ),
        "svc_head": "TDC TECH services. Price confirmed before checkout.\n",
        "pick": "Reply with the service number to order, or 0 for the menu.",
        "need": "Send {field}, then your name.\nExample: Amina — Spotify single",
        "order_ok": (
            "Order {ref} saved.\n"
            "{name} — {price}\n"
            "Client: {who}\n"
            "Detail: {detail}\n\n"
            f"Pay in the wallet: {SITE}\n"
            "Keep this reference. Reply 3 for payment inquiry, 7 to track."
        ),
        "pay": (
            "Payment goes to the TDC TECH® wallet. Minimum £5.\n"
            "Methods: CARD, USDT, ETH, BTC, MTN, AIRTEL.\n\n"
            "Reply with amount and method.\n"
            "Example: 50 MTN"
        ),
        "pay_ok": (
            "Payment request {ref}\n"
            "£{amount} via {method}\n"
            f"Pay now: {SITE}\n"
            "Use the reference in the note. Reply 3 to inquire."
        ),
        "inq": "Send the reference to check. Example: TDC-A1B2C3\nOr reply LIST to see your requests.",
        "human": (
            "You are in the agent queue. Send your name and what you need.\n"
            "We reply when online. You can still order at the site.\n"
            f"{SITE}"
        ),
        "refund": "Send the order reference and the reason.\nExample: TDC-A1B2C3 service not delivered",
        "refund_ok": "Refund {ref} saved. Failed deliveries return to the wallet after review. Reply 7 to track.",
        "feed": "Write your feedback in one message.",
        "feed_ok": "Feedback {ref} saved. Thank you.",
        "faq": (
            "FAQ\n"
            f"• Prices match {SITE} and are confirmed before you pay.\n"
            "• One wallet pays every service.\n"
            "• Music distribution £15 per release, 5–10 day delivery.\n"
            "• Verification £250 per application.\n"
            "• Virtual numbers from £2.\n"
            "• Refunds when a paid service fails to deliver.\n"
            "• Reply 0 for the menu."
        ),
        "bad": "Reply with a menu number, or 0 for the menu.",
        "none": "No request found for that reference.",
        "hours": "Agents reply in Kampala hours. The bot still takes orders while we are away.",
    },
    "fr": {
        "intro": (
            "TDC TECH®\n"
            "Fondé par Topistar Di Congo sous TDC CREATIVES.\n\n"
            "Nous aidons chacun à se connecter aux réseaux sociaux et à la technologie internet.\n"
            "Distribution musicale, pubs, vérification, presse, numéros virtuels, bots et web.\n"
            f"Site: {SITE}\n\n"
            "Choisissez la langue:\n"
            "1 English\n"
            "2 Français\n"
            "3 Kiswahili"
        ),
        "menu": (
            "Menu — répondez par un numéro:\n"
            "1 Voir les services et commander\n"
            "2 Faire un paiement / dépôt\n"
            "3 Suivi de paiement\n"
            "4 Parler à un agent\n"
            "5 Demander un remboursement\n"
            "6 Écrire un avis\n"
            "7 Suivre une commande\n"
            "8 FAQ\n"
            "9 Changer de langue\n\n"
            "0 pour ce menu."
        ),
        "svc_head": "Services TDC TECH. Prix confirmé avant paiement.\n",
        "pick": "Répondez avec le numéro du service, ou 0 pour le menu.",
        "need": "Envoyez {field}, puis votre nom.\nExemple: Amina — single Spotify",
        "order_ok": (
            "Commande {ref} enregistrée.\n"
            "{name} — {price}\n"
            "Client: {who}\n"
            "Détail: {detail}\n\n"
            f"Payez: {SITE}\n"
            "Gardez la référence. 3 pour le paiement, 7 pour le suivi."
        ),
        "pay": (
            "Paiement sur le portefeuille TDC TECH®. Minimum 5 £.\n"
            "Moyens: CARD, USDT, ETH, BTC, MTN, AIRTEL.\n\n"
            "Répondez avec le montant et le moyen.\n"
            "Exemple: 50 MTN"
        ),
        "pay_ok": (
            "Paiement {ref}\n"
            "{amount} £ via {method}\n"
            f"Payez: {SITE}\n"
            "Indiquez la référence. Répondez 3 pour le suivi."
        ),
        "inq": "Envoyez la référence. Exemple: TDC-A1B2C3\nOu LIST pour vos demandes.",
        "human": "Vous êtes dans la file agent. Envoyez votre nom et le besoin. Réponse dès que nous sommes en ligne.",
        "refund": "Envoyez la référence et la raison.\nExemple: TDC-A1B2C3 service non livré",
        "refund_ok": "Remboursement {ref} enregistré. Un échec de livraison est rendu au portefeuille après revue.",
        "feed": "Écrivez votre avis en un message.",
        "feed_ok": "Avis {ref} enregistré. Merci.",
        "faq": (
            "FAQ\n"
            f"• Les prix sont ceux de {SITE}.\n"
            "• Un portefeuille paie tous les services.\n"
            "• Distribution musicale: 15 £ par sortie.\n"
            "• Vérification: 250 £.\n"
            "• Numéros virtuels: dès 2 £.\n"
            "• Remboursement si le service payé n'est pas livré.\n"
            "• 0 pour le menu."
        ),
        "bad": "Répondez avec un numéro du menu, ou 0.",
        "none": "Aucune demande pour cette référence.",
        "hours": "Les agents répondent aux heures de Kampala. Le bot prend les commandes hors ligne.",
    },
    "sw": {
        "intro": (
            "TDC TECH®\n"
            "Ilianzishwa na Topistar Di Congo chini ya TDC CREATIVES.\n\n"
            "Tunasaidia mtu yeyote kuunganishwa na mitandao ya kijamii na teknolojia ya intaneti.\n"
            "Usambazaji wa muziki, matangazo, uthibitisho, habari, nambari pepe, boti, na tovuti.\n"
            f"Tovuti: {SITE}\n\n"
            "Chagua lugha:\n"
            "1 English\n"
            "2 Français\n"
            "3 Kiswahili"
        ),
        "menu": (
            "Menyu — jibu kwa nambari:\n"
            "1 Angalia huduma na uagize\n"
            "2 Fanya malipo / amana\n"
            "3 Uliza malipo\n"
            "4 Zungumza na wakala\n"
            "5 Omba kurudishiwa pesa\n"
            "6 Andika maoni\n"
            "7 Fuatilia oda\n"
            "8 Maswali\n"
            "9 Badilisha lugha\n\n"
            "0 kurudi hapa."
        ),
        "svc_head": "Huduma za TDC TECH. Bei inathibitishwa kabla ya malipo.\n",
        "pick": "Jibu nambari ya huduma, au 0 kurudi menyu.",
        "need": "Tuma {field}, kisha jina lako.\nMfano: Amina — single ya Spotify",
        "order_ok": (
            "Oda {ref} imehifadhiwa.\n"
            "{name} — {price}\n"
            "Mteja: {who}\n"
            "Maelezo: {detail}\n\n"
            f"Lipa: {SITE}\n"
            "Hifadhi kumbukumbu. 3 malipo, 7 ufuatiliaji."
        ),
        "pay": (
            "Malipo kwenye pochi ya TDC TECH®. Chini ni £5.\n"
            "Njia: CARD, USDT, ETH, BTC, MTN, AIRTEL.\n\n"
            "Jibu kiasi na njia.\n"
            "Mfano: 50 MTN"
        ),
        "pay_ok": (
            "Malipo {ref}\n"
            "£{amount} kwa {method}\n"
            f"Lipa: {SITE}\n"
            "Weka kumbukumbu. Jibu 3 kuuliza."
        ),
        "inq": "Tuma kumbukumbu. Mfano: TDC-A1B2C3\nAu LIST kuona maombi yako.",
        "human": "Uko kwenye foleni ya wakala. Tuma jina na unachohitaji. Tunajibu tukiwa mtandaoni.",
        "refund": "Tuma kumbukumbu na sababu.\nMfano: TDC-A1B2C3 huduma haikutolewa",
        "refund_ok": "Ombi {ref} limehifadhiwa. Utoaji ulioshindwa unarudishwa kwenye pochi baada ya ukaguzi.",
        "feed": "Andika maoni kwa ujumbe mmoja.",
        "feed_ok": "Maoni {ref} yamehifadhiwa. Asante.",
        "faq": (
            "Maswali\n"
            f"• Bei ni zile za {SITE}.\n"
            "• Pochi moja hulipa kila huduma.\n"
            "• Usambazaji wa muziki £15 kwa toleo.\n"
            "• Uthibitisho £250.\n"
            "• Nambari pepe kuanzia £2.\n"
            "• Pesa hurudi ikiwa huduma iliyolipwa haikutolewa.\n"
            "• 0 kurudi menyu."
        ),
        "bad": "Jibu nambari ya menyu, au 0.",
        "none": "Hakuna ombi la kumbukumbu hiyo.",
        "hours": "Mawakala hujibu saa za Kampala. Boti inapokea oda hata tukiwa hatupo.",
    },
}


def load(path, fallback):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return fallback
    return fallback


def dump(path, data):
    path.write_text(json.dumps(data, indent=2))


def new_ref():
    return "TDC-" + uuid.uuid4().hex[:6].upper()


def save_lead(row):
    rows = load(LEADS, [])
    row["at"] = int(time.time())
    rows.append(row)
    dump(LEADS, rows)
    if ADMIN_TO:
        send_text(ADMIN_TO, f"New {row.get('kind')} {row.get('ref')} from {row.get('user')}")


def session(user):
    sessions = load(SESS, {})
    if user not in sessions:
        sessions[user] = {"lang": None, "step": "intro", "pending": None}
        dump(SESS, sessions)
    return sessions, sessions[user]


def store(sessions):
    dump(SESS, sessions)


def services_text(lang):
    lines = [COPY[lang]["svc_head"]]
    for i, (name, price, detail, _) in enumerate(SERVICES, 1):
        lines.append(f"{i}. {name} — {price}\n{detail}")
    lines.append("\n" + COPY[lang]["pick"])
    return "\n".join(lines)


def find_ref(user, code):
    code = code.upper().strip()
    for row in reversed(load(LEADS, [])):
        if row.get("ref", "").upper() == code and row.get("user") == user:
            return row
    return None


def list_user(user):
    rows = [r for r in load(LEADS, []) if r.get("user") == user]
    if not rows:
        return "No requests yet."
    lines = ["Your requests:"]
    for row in rows[-8:]:
        lines.append(f"{row.get('ref')} · {row.get('kind')} · {row.get('status', 'received')}")
    return "\n".join(lines)


def send_text(to, body):
    if not TOKEN or not PHONE_ID or not to:
        app.logger.warning("reply not sent (missing credentials): %s", (body or "")[:80])
        return
    try:
        requests.post(
            f"{GRAPH}/{PHONE_ID}/messages",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": (body or "")[:4096]},
            },
            timeout=20,
        )
    except Exception as e:
        app.logger.error("send failed: %s", e)


def handle(user, text):
    sessions, state = session(user)
    raw = (text or "").strip()
    low = raw.lower()

    # Always introduce first for brand-new sessions
    if state.get("step") == "intro" or state.get("lang") is None:
        pick = {
            "1": "en",
            "2": "fr",
            "3": "sw",
            "english": "en",
            "français": "fr",
            "francais": "fr",
            "kiswahili": "sw",
            "swahili": "sw",
        }
        chosen = pick.get(low)
        if not chosen:
            # First contact or invalid: send intro immediately
            store(sessions)
            return COPY["en"]["intro"]
        state["lang"] = chosen
        state["step"] = "menu"
        store(sessions)
        return COPY[chosen]["menu"]

    lang = state["lang"]
    c = COPY[lang]

    if low in {"0", "menu", "start", "hi", "hello", "bonjour", "habari", "salama"}:
        state["step"] = "menu"
        store(sessions)
        # Fast re-intro + menu on greeting words
        if low in {"hi", "hello", "bonjour", "habari", "salama"}:
            return c["intro"] + "\n\n" + c["menu"]
        return c["menu"]

    if state["step"] == "menu":
        if raw == "1":
            state["step"] = "services"
            store(sessions)
            return services_text(lang)
        if raw == "2":
            state["step"] = "pay"
            store(sessions)
            return c["pay"]
        if raw == "3":
            state["step"] = "inquiry"
            store(sessions)
            return c["inq"]
        if raw == "4":
            code = new_ref()
            save_lead({"kind": "human", "ref": code, "user": user, "lang": lang, "status": "queued"})
            state["step"] = "menu"
            store(sessions)
            return c["human"] + "\n" + c["hours"] + f"\nRef {code}"
        if raw == "5":
            state["step"] = "refund"
            store(sessions)
            return c["refund"]
        if raw == "6":
            state["step"] = "feedback"
            store(sessions)
            return c["feed"]
        if raw == "7":
            state["step"] = "track"
            store(sessions)
            return c["inq"]
        if raw == "8":
            return c["faq"]
        if raw == "9":
            state["lang"] = None
            state["step"] = "intro"
            store(sessions)
            return COPY["en"]["intro"]
        return c["bad"]

    if state["step"] == "services":
        if raw.isdigit() and 1 <= int(raw) <= len(SERVICES):
            name, price, detail, field = SERVICES[int(raw) - 1]
            state["pending"] = {"name": name, "price": price, "detail": detail, "field": field}
            state["step"] = "order"
            store(sessions)
            return f"{name}\n{price}\n{detail}\n\n" + c["need"].format(field=field)
        return c["bad"]

    if state["step"] == "order":
        pending = state.get("pending") or {}
        who = raw.split("—")[0].split("-")[0].strip()[:40] or "Client"
        code = new_ref()
        save_lead(
            {
                "kind": "order",
                "ref": code,
                "user": user,
                "lang": lang,
                "status": "awaiting-payment",
                "service": pending,
                "note": raw,
                "client": who,
            }
        )
        state["step"] = "menu"
        store(sessions)
        return c["order_ok"].format(
            ref=code,
            name=pending.get("name"),
            price=pending.get("price"),
            who=who,
            detail=raw,
        )

    if state["step"] == "pay":
        parts = raw.replace("£", "").split()
        if len(parts) < 2:
            return c["pay"]
        try:
            amount = float(parts[0])
        except ValueError:
            return c["pay"]
        if amount < 5:
            return c["pay"]
        method = " ".join(parts[1:]).upper()
        code = new_ref()
        save_lead(
            {
                "kind": "payment",
                "ref": code,
                "user": user,
                "lang": lang,
                "status": "awaiting-payment",
                "amount": amount,
                "method": method,
            }
        )
        state["step"] = "menu"
        store(sessions)
        return c["pay_ok"].format(ref=code, amount=f"{amount:.2f}", method=method)

    if state["step"] in {"inquiry", "track"}:
        if low == "list":
            state["step"] = "menu"
            store(sessions)
            return list_user(user)
        row = find_ref(user, raw)
        state["step"] = "menu"
        store(sessions)
        if not row:
            return c["none"]
        extra = (row.get("service") or {}).get("name") or row.get("method") or ""
        return f"{row.get('ref')} · {row.get('kind')} · {row.get('status', 'received')}\n{extra}\n{SITE}"

    if state["step"] == "refund":
        code = new_ref()
        save_lead({"kind": "refund", "ref": code, "user": user, "lang": lang, "status": "in-review", "note": raw})
        state["step"] = "menu"
        store(sessions)
        return c["refund_ok"].format(ref=code)

    if state["step"] == "feedback":
        code = new_ref()
        save_lead({"kind": "feedback", "ref": code, "user": user, "lang": lang, "status": "saved", "note": raw})
        state["step"] = "menu"
        store(sessions)
        return c["feed_ok"].format(ref=code)

    state["step"] = "menu"
    store(sessions)
    return c["menu"]


@app.get("/webhook")
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "forbidden", 403


@app.post("/webhook")
def incoming():
    data = request.get_json(silent=True) or {}
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                sender = message.get("from", "")
                body = ""
                if message.get("type") == "text":
                    body = message.get("text", {}).get("body", "")
                # Any message (including non-text) gets a fast intro reply
                reply = handle(sender, body)
                send_text(sender, reply)
    return "ok", 200


@app.get("/")
def health():
    return {
        "bot": "TDC TECH WhatsApp",
        "site": SITE,
        "languages": ["en", "fr", "sw"],
        "status": "ready",
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
