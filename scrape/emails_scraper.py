"""
Email Extractor from Websites
=============================
Setup:
    pip install playwright
    playwright install chromium

Run:
    python email_scraper.py
"""

from playwright.sync_api import sync_playwright
import time
import re
import csv

# ============================================================
#   YAHAN APNE WEBSITE URLS PASTE KARO
# ============================================================
urls = [
    "http://kson.com/",
    "http://www.imef.marines.mil/Units/I-MIG/1ST-RADIO-BN/",
    "https://anchor.fm/christopher-boyd83",
    "http://magic925.com/",
    "http://www.arrl.org/Groups/view/escondido-ars/type:club",
    "http://www.rezradio.fm/",
    "https://www.radiousabrasil.com/",
    "http://voicemarketing.com/",
    "http://resonatewithgod.com/",
    "http://www.slacker.com/",
    "https://www.repeaterbook.com/repeaters/details.php?state_id=06&ID=11079",
    "http://www.z90.com/",
    "http://www.91x.com/",
    "http://www.iheartmedia.com/",
    "http://kool959fm.com/",
    "http://www.thebig106.com/",
    "https://www.larradio.com/",
    "http://www.kolafm.com/",
    "https://ksgn.com/",
    "https://www.kcaaradio.com/",
    "http://www.radiodigital07.com/",
    "https://www.studiowbuzz.com/",
    "http://www.kdawgradio.com/",
    "http://www.kcalfm.com/",
    "http://kvcr.org/",
    "https://am590theanswer.com/",
    "http://www.radiolazer.com/",
    "http://celticrockradio.net/",
    "https://katyfm.com/",
    "http://spinlogicradio.com/",
    "http://movementonair.com/",
    "http://www.palatribe.com/businesses/pala-rez-radio/",
    "https://www.blackpoliticalopinion.com/",
    "https://www.guadaluperadio.com/",
    
    "https://www.straighttalkwealth.com/contact-us/",
    "http://983fmtheword.com/",
    "https://lam1073.com/contacto/",
    "http://www.lam1073.com/",
    "http://ktms.com/",
    "https://radiocontentpro.com/",
    "http://godstoriesministries.com/",
    "http://www.luminary-sounds.com/",
    "https://kjee.com/",
    "http://www.sbarc.org/",
    "http://www.kcsb.org/",
    "http://www.radiobronco.com/",
    
    "https://www.outlawcountry1037.com/",
    "https://www.1015bigfm.com/",
    "https://q921radio.com/contact/",
    "http://www.turnto23.com/",
    "https://www.969lacaliente.com/",
    "http://www.hits931fm.com/",
    "http://www.985thefox.com/",
    "http://www.forge1039.com/",
    "https://www.lotuscorp.com/",
    "https://www.lapicositaonline.com/",
    "https://campesina.com/",
    "http://radiolobo.com/",
    "https://www.espnbakersfield.com/",
    "http://yourradiostore.com/",
    "http://laredencion.net/",
   
    "http://www.radiovidaabundante.com/",
    "http://eatdrinkexplore.com/",
    "https://www.airnav.com/cgi-bin/navaid-info?id=GLJ",
    "http://www.arroyogrande.org/",
    "http://1041pirateradio.com/",
    "http://bobfm1039.com/",
    "http://www.air1.com/",
    "http://familyradio.org/",
    "http://www.ktpifm.com/",
    "https://bluvth-muzick-radio.ueniweb.com/?utm_campaign=gmb",
    "https://pointbroadcasting.com/",
    "http://1001thequake.com/",
    "https://mister-ben-bipolar.ueniweb.com/?utm_campaign=gmb"
]
# ============================================================

# Email regex - standard, case-insensitive
EMAIL_REGEX = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'

# Junk extensions jo email jaisa lagta hai par hai nahi (image files etc.)
BAD_TLD = {
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'css', 'js',
    'ico', 'bmp', 'tiff', 'woff', 'woff2', 'ttf', 'eot', 'mp4', 'webm'
}

# Junk domains - substring match (wixpress, sentry sab catch)
JUNK_DOMAINS = [
    'wixpress.com', 'sentry', 'example.com', 'domain.com',
    'email.com', 'yourdomain.com', 'godaddy.com', 'wix.com'
]


def clean_email(raw):
    email = raw.strip().lower().strip('.')

    # mailto query strip (?subject=...)
    email = email.split('?')[0]

    if email.count('@') != 1:
        return None

    local, domain = email.split('@')
    if not local or not domain:
        return None

    # TLD check - file extension nahi hona chahiye
    tld = domain.rsplit('.', 1)[-1]
    if tld in BAD_TLD:
        return None

    # junk domain block (substring)
    if any(j in domain for j in JUNK_DOMAINS):
        return None

    # 32-char hex local = sentry tracking ID, real email nahi
    if re.fullmatch(r'[0-9a-f]{32}', local):
        return None

    # koi bhi lamba hex blob (24+ chars) bhi reject
    if re.fullmatch(r'[0-9a-f]{24,}', local):
        return None

    # version-number type junk (e.g. logo@2x) reject
    if re.search(r'@\d+x$', email):
        return None

    # basic sanity
    if len(email) > 100 or len(email) < 6:
        return None

    return email


def collect_emails_from_page(page):
    found = set()

    # 1) mailto: links - most reliable
    hrefs = page.eval_on_selector_all(
        "a[href^='mailto:']",
        "els => els.map(e => e.getAttribute('href'))"
    )
    for href in hrefs:
        if not href:
            continue
        raw = href.replace('mailto:', '').split(',')[0]
        email = clean_email(raw)
        if email:
            found.add(email)

    # 2) full page text scan
    try:
        text = page.inner_text("body")
    except Exception:
        text = ""
    for match in re.findall(EMAIL_REGEX, text):
        email = clean_email(match)
        if email:
            found.add(email)

    # 3) raw HTML scan (kabhi email text mein nahi hota par HTML mein hota)
    try:
        html = page.content()
    except Exception:
        html = ""
    for match in re.findall(EMAIL_REGEX, html):
        email = clean_email(match)
        if email:
            found.add(email)

    return found


def find_links(page, base_url, keyword_regex, limit=3):
    """Page se aise links dhoondo jo keyword_regex match karein."""
    links = page.eval_on_selector_all(
        "a[href]",
        "els => els.map(e => e.getAttribute('href'))"
    )
    base = re.match(r'https?://[^/]+', base_url)
    base = base.group() if base else base_url.rstrip('/')

    out = []
    seen = set()
    for href in links:
        if not href:
            continue
        if re.search(keyword_regex, href, re.IGNORECASE):
            if href.startswith("http"):
                full = href
            elif href.startswith("/"):
                full = base + href
            else:
                full = base + "/" + href
            if full not in seen:
                seen.add(full)
                out.append(full)

    return out[:limit]


def load_full(page, url, timeout=60000):
    """Pura page load - network idle tak wait, phir extra delay."""
    page.goto(url, timeout=timeout, wait_until="domcontentloaded")
    # network settle hone do (lazy-load content)
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    # extra delay - full reload + JS render
    time.sleep(8)
    # neeche scroll karo taa-ke lazy footer load ho (email aksar footer mein)
    try:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)
    except Exception:
        pass


def get_emails(page, url):
    try:
        # STEP 1: home page
        load_full(page, url)
        found = collect_emails_from_page(page)
        if found:
            return sorted(found)

        # STEP 2: contact / about pages
        contact_urls = find_links(
            page, url,
            r'contact|about|reach|support|connect|info'
        )
        for c_url in contact_urls:
            try:
                load_full(page, c_url, timeout=30000)
                found.update(collect_emails_from_page(page))
                if found:
                    return sorted(found)
            except Exception:
                continue

        # STEP 3: terms / privacy / legal pages (email aksar yahan hota)
        # home page se hi links lene ke liye wapas home par jao
        try:
            load_full(page, url, timeout=30000)
        except Exception:
            pass
        legal_urls = find_links(
            page, url,
            r'terms|privacy|legal|policy|disclaimer|conditions|tos'
        )
        for l_url in legal_urls:
            try:
                load_full(page, l_url, timeout=30000)
                found.update(collect_emails_from_page(page))
                if found:
                    return sorted(found)
            except Exception:
                continue

        return ["Email nahi mila"]

    except Exception as e:
        return [f"ERROR: {e}"]


def main():
    print("\n" + "=" * 60)
    print("   Email Extractor from Websites")
    print("=" * 60 + "\n")

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = context.new_page()

        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] {url}")
            emails = get_emails(page, url)
            results.append((url, emails))
            for email in emails:
                print(f"         Email : {email}")
            print()

        browser.close()

    # TXT output
    with open("email_results.txt", "w", encoding="utf-8") as f:
        f.write("Email Extraction Results\n")
        f.write("=" * 60 + "\n\n")
        for url, emails in results:
            f.write(f"Website : {url}\n")
            for email in emails:
                f.write(f"Email   : {email}\n")
            f.write("-" * 60 + "\n")

    # CSV output (1 row per email - excel ke liye behtar)
    with open("email_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Website", "Email"])
        for url, emails in results:
            for email in emails:
                writer.writerow([url, email])

    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print("=" * 60)
    for website, emails in results:
        print(f"\n{website}")
        for email in emails:
            print(f"  -> {email}")

    print("\nSaved: email_results.txt , email_results.csv")


if __name__ == "__main__":
    main()