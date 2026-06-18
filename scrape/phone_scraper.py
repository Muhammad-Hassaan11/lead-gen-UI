"""
Phone Number Extractor from Websites
====================================
Setup:
    pip install playwright
    playwright install chromium

Run:
    python dy_email.py
"""

from playwright.sync_api import sync_playwright
import time
import re

# ============================================================
#   YAHAN APNE WEBSITE URLS PASTE KARO
# ============================================================
urls = [
    "https://genie.pk/",
    "https://www.wasaaz.com/",
    "https://shopdoem.com/",
    "https://lostgenpk.com/",
    "https://theblatic.com/",
    "https://drappy.pk/",
    "https://lezaar.pk/",
    "https://dudslondon.com/",
    "https://manahillakhani.com/",
    "https://bluetagonline.com/",
    "https://theblwck.com/",
    "https://modwestandco.com/",
    "https://alurescarves.com/",
    "https://us.cayecollection.com/",
    "https://loomnlane.com/",
    "https://virsaaxe.com/",
    "https://zunairateli.com/",
    "https://purplepk.com/",
    "https://aemaystudio.com/",
    "https://banobyhya.pk/",
    "https://nem-ow.com/",
    "https://nazenur.com/",
    "https://www.baraekhanom.com/",
    "https://emergeofficial.pk/",
    "https://sunehridastaan.com/",
    "https://viebarna.com/",
    "https://vybezofficial.com/",
    "https://dandych.com/",
    "https://athenapparels.com/",
    "https://www.amarasaraofficial.com/",
    "https://amorretail.com/",
    "https://wear-kaari.com/",
    "https://inahaofficial.com/",
    "https://naseemenoor.com/",
    "https://cultstore.co/",
    "https://wearhype.co/",
    "https://timelessbywaliyanoor.com/",
    "https://solidsofficial.com/",
    "https://laaleh.com/",
    "https://chikankaribyansharah.com/",
    "https://saazstore.com/",
    "https://www.lemesh.shop/",
    "https://betterbasics.co.in/",
    "https://elahiofficial.com/",
    "https://dariaclothing.com/",
    "https://gulezan.pk/",
    "https://www.nurafashion.com/",
    "https://shopmusejewels.com/",
    "https://wearzal.com/",
    "https://www.ameenaz.com/",
    "https://siyahaks.com/",
    "https://orhwear.com/",
    "https://fetchy.pk/",
    "https://boands.com/",
    "https://www.citrinepk.com/",
    "https://amalshoponline.com/",
    "https://beige.pk/",
    "https://www.bluesandjazz.pk/",
    "https://zouj.store/",
    "https://humraahofficial.com/",
    "https://gentixify.com/",
    "https://eckoapparel.com/",
    "https://fear.com.pk/",
    "https://mayapret.com/",
    "https://www.lapretofficial.com/",
    "https://themugho.com/",
    "https://pashmire.com/",
    "https://humabajwa.com/",
    "https://shopminash.com/",
    "https://orujofficial.com/",
    "https://saajforher.com/",
    "https://vashah.pk/",
    "https://aurawi.store/",
    "https://vulpescorsac.pk/",
    "https://www.naqshiofficial.com/",
    "https://wearwasli.com/",
    "https://rangoonclothing.com/"
]
# ============================================================

PHONE_REGEX = r'(?:\+92|0092|92|0)?[\s\-().]*3\d{2}[\s\-().]*\d{7}|(?:\+92|0092|92|0)?[\s\-().]*\d{2,4}[\s\-().]*\d{6,8}'


def clean_phone(raw_phone):
    phone = re.sub(r'[^\d+]', '', raw_phone)

    if phone.startswith("0092"):
        phone = "+92" + phone[4:]
    elif phone.startswith("92"):
        phone = "+92" + phone[2:]
    elif phone.startswith("03"):
        phone = "+92" + phone[1:]

    digits = re.sub(r'\D', '', phone)
    if len(digits) < 7 or len(digits) > 15:
        return None
    if len(set(digits)) <= 2:
        return None

    return phone


def collect_numbers_from_page(page):
    found = set()

    hrefs = page.eval_on_selector_all(
        "a[href^='tel:'], a[href*='wa.me'], a[href*='whatsapp'], a[href*='api.whatsapp.com']",
        "els => els.map(e => e.getAttribute('href'))"
    )
    for href in hrefs:
        if not href:
            continue
        for match in re.findall(PHONE_REGEX, href):
            phone = clean_phone(match)
            if phone:
                found.add(phone)

    text = page.inner_text("body")
    for match in re.findall(PHONE_REGEX, text):
        phone = clean_phone(match)
        if phone:
            found.add(phone)

    return found


def get_numbers(page, url):
    try:
        page.goto(url, timeout=60000)
        time.sleep(5)

        found = collect_numbers_from_page(page)

        # Contact page bhi check karo agar number nahi mila.
        if not found:
            contact_links = page.eval_on_selector_all(
                "a[href]",
                "els => els.map(e => e.getAttribute('href'))"
            )
            contact_url = None
            for href in contact_links:
                if href and re.search(r'contact|about|reach|support|whatsapp', href, re.IGNORECASE):
                    if href.startswith("http"):
                        contact_url = href
                    elif href.startswith("/"):
                        base = re.match(r'https?://[^/]+', url)
                        if base:
                            contact_url = base.group() + href
                    break

            if contact_url:
                try:
                    page.goto(contact_url, timeout=15000)
                    time.sleep(2)
                    found.update(collect_numbers_from_page(page))
                except:
                    pass

        if found:
            return sorted(found)

        return ["Number nahi mila"]

    except Exception as e:
        return [f"ERROR: {e}"]


def main():
    print("\n" + "=" * 60)
    print("   Phone Number Extractor from Websites")
    print("=" * 60 + "\n")

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = context.new_page()

        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] {url}")
            numbers = get_numbers(page, url)
            results.append((url, numbers))
            for number in numbers:
                print(f"         Number : {number}")
            print()

        browser.close()

    output_file = "phone_results.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("Phone Number Extraction Results\n")
        f.write("=" * 60 + "\n\n")
        for url, numbers in results:
            f.write(f"Website : {url}\n")
            for number in numbers:
                f.write(f"Number  : {number}\n")
            f.write("-" * 60 + "\n")

    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print("=" * 60)
    for website, numbers in results:
        print(f"\n{website}")
        for number in numbers:
            print(f"  -> {number}")

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
