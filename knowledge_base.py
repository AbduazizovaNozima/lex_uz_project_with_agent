DATA = {
    "registration": {
        "text": "Lex.uz saytida ro'yxatdan o'tish uchun:\n1. Saytning yuqori o'ng burchagidagi **'Kirish'** tugmasini bosing.\n2. **'Ro'yxatdan o'tish'** havolasini tanlang.\n3. Elektron pochta manzilingizni va parolingizni kiriting.\n4. Tasdiqlash kodini elektron pochtangizga yuborilgan xabarda toping.\n5. Kodni kiritib, ro'yxatdan o'tishni yakunlang.",
        "image": "static/registration.png",
        "tags": ["ro'yxatdan o'tish", "registratsiya", "akkaunt", "hisob", "kirish", "login", "sign up", "qayd qilish"]
    },
    "language_change": {
        "text": "Sayt tilini o'zgartirish uchun:\n1. Saytning yuqori qismidagi til tugmasini toping (O'z/Ўз/Ru).\n2. Kerakli tilni tanlang:\n   - **O'z** - Lotin alifbosi\n   - **Ўз** - Kirill alifbosi\n   - **Ru** - Rus tili\n3. Sahifa avtomatik yangilanadi.",
        "image": "static/language_change.png",
        "tags": ["til", "язык", "language", "lotin", "kirill", "rus", "o'zgartirish", "tilni almashtirish"]
    },
    "search": {
        "text": "Saytdan hujjat qidirish uchun:\n1. Saytning yuqori qismidagi **Qidiruv** maydonini toping.\n2. Hujjat nomi, raqami yoki kalit so'zlarni kiriting.\n3. **Enter** tugmasini bosing yoki **Qidirish** tugmasini bosing.\n4. Natijalar ro'yxatidan kerakli hujjatni tanlang.",
        "image": "static/search.png",
        "tags": ["qidiruv", "поиск", "search", "izlash", "topish", "hujjat qidirish", "qonun qidirish", "qidir", "qidirish", "topsam", "topmoq"]
    },
    "advanced_search": {
        "text": "Kengaytirilgan qidiruv:\n1. Qidiruv maydonining yonidagi **Kengaytirilgan qidiruv** tugmasini bosing.\n2. Quyidagi filtrlarni qo'llang:\n   - Hujjat turi (kodeks, qonun, qaror)\n   - Qabul qilingan sana\n   - Holati (kuchda, bekor qilingan)\n   - Teglar\n3. **Qidirish** tugmasini bosing.",
        "image": "static/search.png",
        "tags": ["kengaytirilgan qidiruv", "расширенный поиск", "advanced search", "filtr", "filter"]
    },
    "contact": {
        "text": "Lex.uz bilan bog'lanish:\n1. Saytning pastki qismidagi **'Aloqa'** bo'limiga o'ting.\n2. Quyidagi ma'lumotlar mavjud:\n   - Telefon: +998 71 202 00 02\n   - Email: info@lex.uz\n   - Manzil: Toshkent sh., Sayilgoh ko'chasi, 5A\n3. Texnik yordam uchun **'Yordam'** bo'limiga murojaat qiling.",
        "image": "static/contact.png",
        "tags": ["aloqa", "контакт", "contact", "telefon", "email", "manzil", "yordam", "support"]
    },
}

def search_guide_by_tags(user_query: str):
    """
    Foydalanuvchi so'rovi asosida taglar ichidan qidiradi.
    Agent uchun to'liq formatda qaytaradi.
    """
    import os
    query = user_query.lower()

    # 1. To'g'ridan-to'g'ri kalit so'z tekshirish (Exact match)
    if query in DATA:
        result = DATA[query]
        # Rasm yo'lini to'liq yo'lga aylantirish
        image_path = os.path.abspath(result['image'])
        return f"""📱 LEX.UZ SAYTI BO'YICHA YORDAM

{result['text']}

📷 Rasm: {image_path}
"""

    # 2. Taglar ichidan qidirish (Fuzzy match)
    for key, info in DATA.items():
        if any(tag in query for tag in info["tags"]):
            # Rasm yo'lini to'liq yo'lga aylantirish
            image_path = os.path.abspath(info['image'])
            return f"""📱 LEX.UZ SAYTI BO'YICHA YORDAM

{info['text']}

📷 Rasm: {image_path}
"""

    # 3. Hech narsa topilmasa
    return None