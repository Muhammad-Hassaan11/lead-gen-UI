"""
Google Maps Website Extractor
==============================
Setup (run once in terminal):
    pip install playwright
    playwright install chromium

Run:
    python maps_scraper.py
"""

from playwright.sync_api import sync_playwright
import time

# ============================================================
#   YAHAN APNE GOOGLE MAPS URLS PASTE KARO
#   (har line ke end pe comma lagao)
# ============================================================
urls = [
    "https://www.google.com/maps/place/Khay/data=!4m7!3m6!1s0x80e852ab8ece39a5:0xea006706378aeb11!8m2!3d34.2600173!4d-119.2380575!16s%2Fg%2F1tvw5787!19sChIJpTnOjqtS6IAREeuKNwZnAOo?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kbby/data=!4m7!3m6!1s0x80e852ab8ece39a5:0x40013493945865f4!8m2!3d34.2600457!4d-119.2380408!16s%2Fg%2F1hbpwrxk8!19sChIJpTnOjqtS6IAR9GVYlJM0AUA?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KDAR-FM+Oxnard/data=!4m7!3m6!1s0x80e9adaa234833d9:0x9573a8d9bd278f00!8m2!3d34.2964642!4d-119.2735514!16s%2Fg%2F1tj5lggv!19sChIJ2TNII6qt6YARAI8nvdmoc5U?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KCAQ-FM+Oxnard/data=!4m7!3m6!1s0x80e9a930739099cb:0x2b60e4815796c450!8m2!3d34.3481833!4d-119.3362304!16s%2Fg%2F1td7j0z1!19sChIJy5mQczCp6YARUMSWV4HkYCs?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KCAQ+FM/data=!4m7!3m6!1s0x80e84d4095a69bd1:0x74b4cd79de12190a!8m2!3d34.2530275!4d-119.2094211!16s%2Fg%2F1ttdn91b!19sChIJ0ZumlUBN6IARChkS3nnNtHQ?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Cumulus+Broadcasting+Inc/data=!4m7!3m6!1s0x80e9acff90b2c167:0x33fc6f20fd9c2c86!8m2!3d34.2921232!4d-119.2807338!16s%2Fg%2F113dpgptk!19sChIJZ8GykP-s6YARhiyc_SBv_DM?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/LIVE+105.5/data=!4m7!3m6!1s0x80e84d407ced0311:0x7aef794d2c90ad73!8m2!3d34.2530275!4d-119.2094211!16s%2Fg%2F1tggtv9j!19sChIJEQPtfEBN6IARc62QLE1573o?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Cumulus+Broadcasting+Inc/data=!4m7!3m6!1s0x80e852ab8ece39a5:0x50321268bff23874!8m2!3d34.2600263!4d-119.2381127!16s%2Fg%2F1tg3bdt7!19sChIJpTnOjqtS6IARdDjyv2gSMlA?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Radio+Lazer+102+9+FM/data=!4m7!3m6!1s0x80e84c291572422b:0xa5a5cf85c3776b5a!8m2!3d34.2014122!4d-119.1781616!16s%2Fg%2F1wk6_22g!19sChIJK0JyFSlM6IARWmt3w4XPpaU?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/CAPS+Media+Center/data=!4m7!3m6!1s0x80e9b2a60e913e9b:0x8745d3eb36a28a7f!8m2!3d34.2782507!4d-119.2272842!16s%2Fg%2F1v75s6nj!19sChIJmz6RDqay6YARf4qiNuvTRYc?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/LaM+103.7FM/data=!4m7!3m6!1s0x80e84c29912741c1:0x9d34df20d9682279!8m2!3d34.199286!4d-119.1788237!16s%2Fg%2F1tfrh1_y!19sChIJwUEnkSlM6IAReSJo2SDfNJ0?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KBBY-FM+Ventura/data=!4m7!3m6!1s0x80e84d0bf6413a4f:0x5d9a6ede64ccb21f!8m2!3d34.2366711!4d-119.2039974!16s%2Fg%2F1v5fs6fp!19sChIJTzpB9gtN6IARH7LMZN5uml0?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KZTR-FM+Camarillo/data=!4m7!3m6!1s0x80e9adaa1aa5772d:0x68c7ef2ede7e46b4!8m2!3d34.2956753!4d-119.2736787!16s%2Fg%2F1tdxfllh!19sChIJLXelGqqt6YARtEZ-3i7vx2g?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kvyb/data=!4m7!3m6!1s0x80e852ab8ece39a5:0x9a36e581ea4dd39a!8m2!3d34.2600402!4d-119.2380473!16s%2Fg%2F1tdcb3c_!19sChIJpTnOjqtS6IARmtNN6oHlNpo?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Gold+Coast+Radio+LLC/data=!4m7!3m6!1s0x80e84c2990495555:0x34ec3d8a1fe5934!8m2!3d34.199286!4d-119.1788237!16s%2Fg%2F11gydkg4w0!19sChIJVVVJkClM6IARNFn-odjDTgM?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Radio+Oasis+107.9+FM/data=!4m7!3m6!1s0x80e84e851ebca1e5:0xc6f3e3599a764507!8m2!3d34.1840512!4d-119.1671938!16s%2Fg%2F11bwl3plhl!19sChIJ5aG8HoVO6IARB0V2mlnj88Y?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KMRO-FM+Camarillo/data=!4m7!3m6!1s0x80e9b058c781f6a5:0x2ffad2d3bc9d59e0!8m2!3d34.4125696!4d-119.1879328!16s%2Fg%2F1tdqhsp7!19sChIJpfaBx1iw6YAR4FmdvNPS-i8?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Straight+Talk+Radio/data=!4m7!3m6!1s0x80e84d4bdf910001:0xbef7d7f6eba4c02e!8m2!3d34.2649476!4d-119.2130647!16s%2Fg%2F11lcj9t93b!19sChIJAQCR30tN6IARLsCk6_bX974?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kocp/data=!4m7!3m6!1s0x80e84d407ced0311:0x4345921c27d39042!8m2!3d34.2530206!4d-119.2094115!16s%2Fg%2F1v9gvsf9!19sChIJEQPtfEBN6IARQpDTJxySRUM?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/98.3+KDAR+FM/data=!4m7!3m6!1s0x80e84d4e4ecb0fbb:0x1823531c35e89342!8m2!3d34.2289407!4d-119.1720775!16s%2Fg%2F11j0h9snhp!19sChIJuw_LTk5N6IARQpPoNRxTIxg?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kczn+96+7+Req+Line/data=!4m7!3m6!1s0x80e84c291572422b:0xb0d44221de2e3ad3!8m2!3d34.2014628!4d-119.1782662!16s%2Fg%2F1tnhyn3n!19sChIJK0JyFSlM6IAR0zou3iFC1LA?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/La+M+107.3/data=!4m7!3m6!1s0x80e84c2991025e93:0x49df1308b5487798!8m2!3d34.1992854!4d-119.1789248!16s%2Fg%2F11vhf_90fk!19sChIJk14CkSlM6IARmHdItQgT30k?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/LaM+107.3FM/data=!4m7!3m6!1s0x470278f4d4f472a5:0xc82cb6efba1e2ccb!8m2!3d35.0589575!4d-120.550039!16s%2Fg%2F11rmx9rzbr!19sChIJpXL01PR4AkcRyyweuu-2LMg?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KTMS-AM+990/data=!4m7!3m6!1s0x80e84d3f87d51ca5:0xed25959548b2757!8m2!3d34.2527022!4d-119.2086753!16s%2Fg%2F11cs3_hk5s!19sChIJpRzVhz9N6IARVyeLVFlZ0g4?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Sin+Limites+Radio+93.3+FM+KOXZ/data=!4m7!3m6!1s0x80e84c92b7a19e3f:0xd92eccb8aad027e7!8m2!3d34.2539636!4d-119.161688!16s%2Fg%2F11c462lkvb!19sChIJP56ht5JM6IAR5yfQqrjMLtk?authuser=0&hl=en&rclk=1",

    "https://www.google.com/maps/place/Voicehorsey/data=!4m7!3m6!1s0x41cf1b054435ddc7:0x23fa5befdf196980!8m2!3d46.423669!4d-129.9427086!16s%2Fg%2F11sfdcrbfr!19sChIJx901RAUbz0ERgGkZ3-9b-iM?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/LaKonsentida/data=!4m7!3m6!1s0x4f3b5b4a94b513d9:0xef44fe58c009a133!8m2!3d37.2695056!4d-119.306607!16s%2Fg%2F11n48k122m!19sChIJ2RO1lEpbO08RM6EJwFj-RO8?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KZTR-AM+Santa+Paula/data=!4m7!3m6!1s0x80e9b4e29c74ecfd:0xd0b2d2b49bec17a!8m2!3d34.3300003!4d-119.0928827!16s%2Fg%2F1wt3nqwj!19sChIJ_ex0nOK06YAResG-SSstCw0?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/New+Inspiration+Broadcasting/data=!4m7!3m6!1s0x80e84c45397c838d:0x81218c8fe6d0bf8d!8m2!3d34.2289481!4d-119.1721521!16s%2Fg%2F1tfbj0nz!19sChIJjYN8OUVM6IARjb_Q5o-MIYE?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Radio+Content+Pro/data=!4m7!3m6!1s0xac042574996c50dd:0x1a20919b76d6fdbd!8m2!3d46.423669!4d-129.9427086!16s%2Fg%2F11l32rcbcb!19sChIJ3VBsmXQlBKwRvf3WdpuRIBo?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KXLM/data=!4m7!3m6!1s0x80e84c291572422b:0xce2ca2dbe4d5554e!8m2!3d34.2014696!4d-119.1782274!16s%2Fg%2F1vs1s5py!19sChIJK0JyFSlM6IARTlXV5NuiLM4?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/God+Stories/data=!4m7!3m6!1s0x80e9afc5460efd7f:0x19f3b6cf09afeef9!8m2!3d34.3941178!4d-119.3010327!16s%2Fg%2F11h0js9hhg!19sChIJf_0ORsWv6YAR-e6vCc-28xk?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Luminary+Sounds/data=!4m7!3m6!1s0x80e84f6795445e89:0x3e1ddc5ce55412b0!8m2!3d34.1661554!4d-119.156804!16s%2Fg%2F11s7mmp1qy!19sChIJiV5ElWdP6IARsBJU5VzcHT4?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Purpose,+Poder,+Pleasure/data=!4m7!3m6!1s0x685a76b9496ee2c9:0x3e5876a4a3c761b5!8m2!3d46.423669!4d-129.9427086!16s%2Fg%2F11rq97dtsb!19sChIJyeJuSbl2WmgRtWHHo6R2WD4?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/87.7+FM+LA+PRIMERA+EN+TU+CORAZ%C3%93N/data=!4m7!3m6!1s0x80e84c2998cd6bf1:0xb3a12327febb5a6a!8m2!3d34.199884!4d-119.1782948!16s%2Fg%2F1pp2w_ky1!19sChIJ8WvNmClM6IARalq7_icjobM?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KJEE/data=!4m7!3m6!1s0x80e9147b722bb2d9:0xe86d5a699279b87e!8m2!3d34.4182588!4d-119.7057005!16s%2Fg%2F1td0nb9v!19sChIJ2bIrcnsU6YARfrh5kmlabeg?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KTYD-FM+99.9/data=!4m7!3m6!1s0x80e91386b8323d3d:0x6288f8756887f156!8m2!3d34.4223164!4d-119.6917303!16s%2Fg%2F11c1qsglf1!19sChIJPT0yuIYT6YARVvGHaHX4iGI?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Santa+Barbara+Amateur+Radio+Club+Station+K6TZ/data=!4m7!3m6!1s0x80e914ea30f50733:0x158e557e34ee73b1!8m2!3d34.4374933!4d-119.7243263!16s%2Fg%2F11c6ql24_z!19sChIJMwf1MOoU6YARsXPuNH5VjhU?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Rincon+Broadcasting+LLC/data=!4m7!3m6!1s0x80e91386b82fa997:0x1070ff32515364f3!8m2!3d34.4221804!4d-119.6917932!16s%2Fg%2F1hg4s52xl!19sChIJl6kvuIYT6YAR82RTUTL_cBA?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KCSB-FM/data=!4m7!3m6!1s0x80e93f681a0b11c7:0xfa7088bc576eda4e!8m2!3d34.4127157!4d-119.848318!16zL20vMDVrMDJk!19sChIJxxELGmg_6YARTtpuV7yIcPo?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kist/data=!4m7!3m6!1s0x80e91386b7a8f513:0xda4aaab21d6a5786!8m2!3d34.4222674!4d-119.6916811!16s%2Fg%2F1tgh7wjt!19sChIJE_Wot4YT6YARhldqHbKqSto?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KEYT-TV/data=!4m7!3m6!1s0x80e9146e274580c7:0xcb8fa8c7642218b7!8m2!3d34.4101556!4d-119.7080917!16s%2Fg%2F1tm8kx90!19sChIJx4BFJ24U6YARtxgiZMeoj8s?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KTYD-FM+Santa+Barbara/data=!4m7!3m6!1s0x80e9134b17406673:0x206f536692788c1d!8m2!3d34.470876!4d-119.676913!16s%2Fg%2F1tdzrg3j!19sChIJc2ZAF0sT6YARHYx4kmZTbyA?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KRRF/data=!4m7!3m6!1s0x80e9147c00000001:0xa860c5d188dbb193!8m2!3d34.4203053!4d-119.7108591!16s%2Fg%2F1tgn9y3l!19sChIJAQAAAHwU6YARk7HbiNHFYKg?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KFYZ-FM+94.5/data=!4m7!3m6!1s0x80e91386b82fffff:0x2d686b771b797947!8m2!3d34.4221804!4d-119.6917932!16s%2Fg%2F11g0vzlg05!19sChIJ__8vuIYT6YARR3l5G3draC0?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Teen+Sports+Radio/data=!4m7!3m6!1s0x80e914871b1cee7f:0x914d1e1944abca97!8m2!3d34.4266979!4d-119.7041049!16s%2Fg%2F11byykl6q0!19sChIJf-4cG4cU6YARl8qrRBkeTZE?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Community+Radio+Inc/data=!4m7!3m6!1s0x80e9147ff29f46d5:0xe324f423d9a582d5!8m2!3d34.4251959!4d-119.6969301!16s%2Fg%2F1tptqxyx!19sChIJ1Uaf8n8U6YAR1YKl2SP0JOM?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KZAA-LP+FM/data=!4m7!3m6!1s0x80e913851f56f0f1:0x45be9e68a4d75652!8m2!3d34.4215319!4d-119.6861429!16s%2Fg%2F11f2x51kl5!19sChIJ8fBWH4UT6YARUlbXpGievkU?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KCSB-FM+Santa+Barbara/data=!4m7!3m6!1s0x80e945710678c755:0x51decea760defbe2!8m2!3d34.5252553!4d-119.9589894!16s%2Fg%2F1tfcj1qp!19sChIJVcd4BnFF6YAR4vveYKfO3lE?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/kdb/data=!4m7!3m6!1s0x80e91386b7a8f513:0xf49181df098dc9b4!8m2!3d34.4222674!4d-119.6916811!16s%2Fg%2F1tj808sj!19sChIJE_Wot4YT6YARtMmNCd-BkfQ?authuser=0&hl=en&rclk=1",

    "https://www.google.com/maps/place/San+Marcus+VORTAC+RZS+114.9+96X/data=!4m7!3m6!1s0x80e96b49fda08803:0x1f7638250dbc6980!8m2!3d34.5095403!4d-119.77101!16s%2Fg%2F11q8rx1n1y!19sChIJA4ig_Ulr6YARgGm8DSU4dh8?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/AM+1290+Radio/data=!4m7!3m6!1s0x80e914870567e1a3:0xc9f61e6275933044!8m2!3d34.4267025!4d-119.7041136!16s%2Fg%2F1tdp5by6!19sChIJo-FnBYcU6YARRDCTdWIe9sk?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kbko/data=!4m7!3m6!1s0x80e91386b7a8f513:0xd21383d388382a1!8m2!3d34.4222674!4d-119.6916811!16s%2Fg%2F1td42t79!19sChIJE_Wot4YT6YARoYKDOD04IQ0?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/The+Jeremiah+Show/data=!4m7!3m6!1s0x80e914871b1cee7f:0x61034bd8d54ba4ce!8m2!3d34.4196899!4d-119.6939369!16s%2Fg%2F11f122gdp2!19sChIJf-4cG4cU6YARzqRL1dhLA2E?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KMGQ-FM+Goleta/data=!4m7!3m6!1s0x80e9134930a3f663:0x70effed26455a101!8m2!3d34.4664949!4d-119.6777221!16s%2Fg%2F1tnss71h!19sChIJY_ajMEkT6YARAaFVZNL-73A?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/NOAA+Weather+Radio+WWF62/data=!4m7!3m6!1s0x80e945df0a7ce61f:0xd3c710cd4307ded6!8m2!3d34.5034023!4d-119.819418!16s%2Fg%2F11s_x6wg1_!19sChIJH-Z8Ct9F6YAR1t4HQ80Qx9M?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Cumulus+Broadcasting+Inc/data=!4m7!3m6!1s0x80e9138596e75055:0x7cf01f84d96d5978!8m2!3d34.4196864!4d-119.6885979!16s%2Fg%2F1tfklg_p!19sChIJVVDnloUT6YAReFlt2YQf8Hw?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Lazer+Broadcasting+Corporation/data=!4m7!3m6!1s0x80e940794539e75d:0xc5ee687a91b052e9!8m2!3d34.4362359!4d-119.8285262!16s%2Fg%2F1w0h7tw2!19sChIJXec5RXlA6YAR6VKwkXpo7sU?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/BNS+Electronics+Inc/data=!4m7!3m6!1s0x80e9147f92a91edd:0xda610939f5200c07!8m2!3d34.4251959!4d-119.6969301!16s%2Fg%2F1wz53077!19sChIJ3R6pkn8U6YARBwwg9TkJYdo?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/L-Tronics/data=!4m7!3m6!1s0x80e9406a2ec11e77:0x6c43d35a3c3e844!8m2!3d34.4529358!4d-119.8174168!16s%2Fg%2F1tk8cf65!19sChIJdx7BLmpA6YARROjDozU9xAY?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KFAC-FM+Santa+Barbara/data=!4m7!3m6!1s0x80e913493ba3f2ef:0xb3675d462ea32b88!8m2!3d34.4659879!4d-119.6780248!16s%2Fg%2F1tdp0sbm!19sChIJ7_KjO0kT6YARiCujLkZdZ7M?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KCHJ+radio+transmitter/data=!4m7!3m6!1s0x80eae70009bf5df3:0x5e01a2fec55ef3ce!8m2!3d35.8103328!4d-119.3227235!16s%2Fg%2F11xmcdx468!19sChIJ812_CQDn6oARzvNexf6iAV4?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Lotus+Bakersfield+Corporation/data=!4m7!3m6!1s0x80eae6d585b03915:0xb5919772221279df!8m2!3d35.8121213!4d-119.3215483!16s%2Fg%2F1261lq315!19sChIJFTmwhdXm6oAR33kSInKXkbU?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KCHJ/data=!4m7!3m6!1s0x80eae593b667bf35:0x2623f17fab715195!8m2!3d35.7688321!4d-119.2471204!16s%2Fg%2F1tkf18t7!19sChIJNb9ntpPl6oARlVFxq3_xIyY?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KDUV-FM+Visalia/data=!4m7!3m6!1s0x80eaad47b211c45f:0xcdc23bff8922ce9a!8m2!3d36.2871697!4d-118.8389855!16s%2Fg%2F1wc488l0!19sChIJX8QRsket6oARms4iif87ws0?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KIOO-FM+Porterville/data=!4m7!3m6!1s0x80eab7e9a25c9cd1:0xc9a1f83822226c32!8m2!3d36.1071661!4d-119.0301031!16s%2Fg%2F1tgdtg3j!19sChIJ0Zxcoum36oARMmwiIjj4ock?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KUZZ/data=!4m7!3m6!1s0x80ea69e0afabd58d:0xa46bfb1c012fdb5c!8m2!3d35.3856501!4d-119.0409981!16s%2Fg%2F1tl4dbm1!19sChIJjdWrr-Bp6oARXNsvARz7a6Q?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Precious+95.7+FM/data=!4m7!3m6!1s0x80ea6bb760b4cb6d:0x702d2d4f6afe3fdc!8m2!3d35.3725728!4d-119.0050317!16s%2Fg%2F11tgh8qs1p!19sChIJbcu0YLdr6oAR3D_-ak8tLXA?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KAXL/data=!4m7!3m6!1s0x80ea41fadeeef4df:0x936997e8ae68a224!8m2!3d35.3837869!4d-119.0750556!16s%2Fg%2F1tcx79xl!19sChIJ3_Tu3vpB6oARJKJoruiXaZM?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KTIE-FM+Bakersfield/data=!4m7!3m6!1s0x80ea6a2c240a0113:0x7bea13fef1a2165f!8m2!3d35.3688476!4d-119.0048232!16s%2Fg%2F1v2f0v2c!19sChIJEwEKJCxq6oARXxai8f4T6ns?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Spanish+Radio+Group/data=!4m7!3m6!1s0x80ea421b231e346f:0x7a53e7e0081f0a36!8m2!3d35.3682448!4d-119.0590095!16s%2Fg%2F1tdmf5pt!19sChIJbzQeIxtC6oARNgofCODnU3o?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KRJK/data=!4m7!3m6!1s0x80ea69e0afabd58d:0x1ea475ac74caf94f!8m2!3d35.3856804!4d-119.0410207!16s%2Fg%2F12641rq97!19sChIJjdWrr-Bp6oART_nKdKx1pB4?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Radio+Lobo/data=!4m7!3m6!1s0x80ea421b231ccfb9:0x4643c729bf67df0!8m2!3d35.3683043!4d-119.0588879!16s%2Fg%2F11g8_2cdw_!19sChIJuc8cIxtC6oAR8H32m3I8ZAQ?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Outlaw+Country+Radio+103.7/data=!4m7!3m6!1s0x80ea69194bc0474b:0x484983f65acf7c03!8m2!3d35.3722392!4d-119.024027!16s%2Fg%2F11vkm9txh_!19sChIJS0fASxlp6oARA3zPWvaDSUg?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kern/data=!4m7!3m6!1s0x80ea6996aaaaaaab:0x5b7734182287193a!8m2!3d35.3876891!4d-119.0190927!16s%2Fg%2F126228gbf!19sChIJq6qqqpZp6oAROhmHIhg0d1s?authuser=0&hl=en&rclk=1",

    "https://www.google.com/maps/place/Lotus+Bakersfield+Corporation/data=!4m7!3m6!1s0x80ea6a4f684a0cd7:0x6d47f2867b1c180f!8m2!3d35.3478822!4d-119.0101946!16s%2Fg%2F1261k0_tn!19sChIJ1wxKaE9q6oARDxgce4byR20?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/101.5+BIG+FM+-+KGFM/data=!4m7!3m6!1s0x80ea69fe64f70bbb:0x637fb372fbdd34fd!8m2!3d35.3698423!4d-119.0442183!16s%2Fg%2F1262bv61p!19sChIJuwv3ZP5p6oAR_TTd-3Kzf2M?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Q92.1+%7C+Classic+Hits/data=!4m7!3m6!1s0x80ea421b23155555:0x572c383375a21401!8m2!3d35.3682871!4d-119.0588116!16s%2Fg%2F11srgk7w69!19sChIJVVUVIxtC6oARARSidTM4LFc?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/iHeartMedia/data=!4m7!3m6!1s0x80ea4319faa52735:0x2743e40ad1e95ea1!8m2!3d35.3645588!4d-119.0648118!16s%2Fg%2F11fk81wtc1!19sChIJNSel-hlD6oARoV7p0QrkQyc?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KISV/data=!4m7!3m6!1s0x80ea69fddd9de3e3:0xb5c457a578a5dd01!8m2!3d35.3700388!4d-119.0442958!16s%2Fg%2F1tp_6q6d!19sChIJ4-Od3f1p6oARAd2leKVXxLU?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/23ABC+Bakersfield/data=!4m7!3m6!1s0x80ea6986d9cecba3:0x9eae9519cf2e31a7!8m2!3d35.3778316!4d-119.0056184!16s%2Fg%2F1wrgkgl4!19sChIJo8vO2YZp6oARpzEuzxmVrp4?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Big+96-5+Request+Line/data=!4m7!3m6!1s0x80ea6996aaaaaaab:0xed8e01afc78bef8c!8m2!3d35.3873269!4d-119.0170043!16s%2Fg%2F1263r6t0p!19sChIJq6qqqpZp6oARjO-Lx68Bju0?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kebt+La+Caliente/data=!4m7!3m6!1s0x80ea69fe64f70bbb:0x90d05d4f6cd2da7e!8m2!3d35.3696128!4d-119.0445826!16s%2Fg%2F1262pphbv!19sChIJuwv3ZP5p6oARftrSbE9d0JA?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KKXX/data=!4m7!3m6!1s0x80ea69fddd9de3e3:0x93b3ee31614ff1e3!8m2!3d35.3700388!4d-119.0442958!16s%2Fg%2F1tdwf7bg!19sChIJ4-Od3f1p6oAR4_FPYTHus5M?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KCWR/data=!4m7!3m6!1s0x80ea69e0afabd58d:0x1e3e591a20df8f9a!8m2!3d35.3856771!4d-119.0409482!16s%2Fg%2F1thf8wdw!19sChIJjdWrr-Bp6oARmo_fIBpZPh4?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/K-His+800+Am/data=!4m7!3m6!1s0x80ea6996aaaaaaab:0x67981fdcebf596ee!8m2!3d35.3873269!4d-119.0170043!16s%2Fg%2F12630bpbq!19sChIJq6qqqpZp6oAR7pb169wfmGc?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kwac/data=!4m7!3m6!1s0x80ea421b231e346f:0xb272ea942fb63ddb!8m2!3d35.368275!4d-119.058898!16s%2Fg%2F1tfj3gss!19sChIJbzQeIxtC6oAR2z22L5TqcrI?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/98.5+the+Fox/data=!4m7!3m6!1s0x80ea421e84d49841:0xe4e0a2d668a02693!8m2!3d35.3645588!4d-119.0648118!16s%2Fg%2F1tgln69d!19sChIJQZjUhB5C6oARkyagaNai4OQ?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/La+Preciosa+105.3FM%2F800AM/data=!4m7!3m6!1s0x80ea421e84d49841:0x9817fe510587d81f!8m2!3d35.3646734!4d-119.0648183!16s%2Fg%2F1xpwk2mx!19sChIJQZjUhB5C6oARH9iHBVH-F5g?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Forge+103.9/data=!4m7!3m6!1s0x80ea402e5c01479b:0x7326539cc151e031!8m2!3d35.3152314!4d-119.0558513!16s%2Fg%2F11fx8_dkmg!19sChIJm0cBXC5A6oARMeBRwZxTJnM?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kmap/data=!4m7!3m6!1s0x80ea6995dec1b2ff:0xb8e91cb53e68b9c6!8m2!3d35.390656!4d-119.0171596!16s%2Fg%2F1tfkwmgy!19sChIJ_7LB3pVp6oARxrloPrUc6bg?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Lotus+Bakersfield+Corporation/data=!4m7!3m6!1s0x80ea421b177b7251:0xae0477a9e62eb12e!8m2!3d35.368275!4d-119.058898!16s%2Fg%2F12645qns5!19sChIJUXJ7FxtC6oARLrEu5ql3BK4?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/La+Picosita+OnLine/data=!4m7!3m6!1s0x80ea6bf16182c6d7:0x8a563b69caa00c77!8m2!3d35.3621862!4d-119.0186707!16s%2Fg%2F11kq_3l_4p!19sChIJ18aCYfFr6oARdwygymk7Voo?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KIWI-FM+Bakersfield/data=!4m7!3m6!1s0x80ea6a2c240a0113:0x4de27254e4812073!8m2!3d35.3688476!4d-119.0048232!16s%2Fg%2F1xfsp1bk!19sChIJEwEKJCxq6oARcyCB5FRy4k0?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/La+Campesina+92.5+FM/data=!4m7!3m6!1s0x80ea404b171a940b:0xc80ec501650f941e!8m2!3d35.3152173!4d-119.056154!16s%2Fg%2F1tp8_byj!19sChIJC5QaF0tA6oARHpQPZQHFDsg?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kiwi/data=!4m7!3m6!1s0x80ea421b177b7251:0xb0d23c967defe5d5!8m2!3d35.3681193!4d-119.0590249!16s%2Fg%2F1263vf0kj!19sChIJUXJ7FxtC6oAR1eXvfZY80rA?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kgeo/data=!4m7!3m6!1s0x80ea69fddd9de3e3:0xd23a479c10a22da8!8m2!3d35.3700388!4d-119.0442958!16s%2Fg%2F1thqh1qw!19sChIJ4-Od3f1p6oARqC2iEJxHOtI?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Radio+Manantial+De+Vida+Eterna/data=!4m7!3m6!1s0x80ea69a1a1622cf9:0xd602e99cf9285f01!8m2!3d35.3980941!4d-119.0035586!16s%2Fg%2F11bv3r2tgm!19sChIJ-SxioaFp6oARAV8o-ZzpAtY?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Radio+Fe/data=!4m7!3m6!1s0x80ea6a923093595d:0x38262859fceea67!8m2!3d35.3172679!4d-119.0275593!16s%2Fg%2F11hy9n_8qh!19sChIJXVmTMJJq6oARZ-rOn4ViggM?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Your+Radio+Store/data=!4m7!3m6!1s0x80ea69fe759133f1:0xbd1578fe60e98ff3!8m2!3d35.3698423!4d-119.0442183!16s%2Fg%2F11c5b7h8v8!19sChIJ8TORdf5p6oAR84_pYP54Fb0?authuser=0&hl=en&rclk=1",

    "https://www.google.com/maps/place/103.5+FM+KRHM+REDEMPTION/data=!4m7!3m6!1s0x80ea697d148544f1:0x10a53fbc50a17030!8m2!3d35.3808109!4d-118.9895646!16s%2Fg%2F11bzwpbsdd!19sChIJ8USFFH1p6oARMHChULw_pRA?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KWCD-FM+Grover+City/data=!4m7!3m6!1s0x80ec6767dded800f:0x87dfdd23c33919f9!8m2!3d35.1069206!4d-120.5168332!16s%2Fg%2F1twyzw2g!19sChIJD4Dt3Wdn7IAR-Rk5wyPd34c?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/American+General+Media/data=!4m7!3m6!1s0x80ecf14a8c848921:0x4eff4980ca410e64!8m2!3d35.2553941!4d-120.6414263!16s%2Fg%2F1tkvb23f!19sChIJIYmEjErx7IARZA5ByoBJ_04?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kzoz/data=!4m7!3m6!1s0x80ecf14a8c848921:0x9f5fd1733b52635e!8m2!3d35.2553941!4d-120.6414263!16s%2Fg%2F1v7tlpsb!19sChIJIYmEjErx7IARXmNSO3PRX58?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KCBX-FM+San+Luis+Obispo/data=!4m7!3m6!1s0x80ecee5068f07cd7:0xe06d974b6af9c84e!8m2!3d35.3603431!4d-120.6557379!16s%2Fg%2F1tfrmnfv!19sChIJ13zwaFDu7IARTsj5akuXbeA?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Cal+Poly+Amateur+Radio+Club/data=!4m7!3m6!1s0x80ecf1b3bfb366ef:0x5229b4662c359e56!8m2!3d35.3005929!4d-120.6617206!16s%2Fg%2F1tgh38zf!19sChIJ72azv7Px7IARVp41LGa0KVI?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KCBX/data=!4m7!3m6!1s0x80ecf72d3ea4e89b:0x144a4307e1087334!8m2!3d35.242816!4d-120.675396!16s%2Fg%2F1tfqlpx8!19sChIJm-ikPi337IARNHMI4QdDShQ?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KCPR+Cal+Poly+Radio/data=!4m7!3m6!1s0x80ecf1b236ededad:0x977d99b5e23d035d!8m2!3d35.299078!4d-120.6609036!16s%2Fg%2F1pv0_s1dj!19sChIJre3tNrLx7IARXQM94rWZfZc?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Nueva+Radio+Vision/data=!4m7!3m6!1s0x80ec6b84e40eaaab:0xaa870c1f39ab735d!8m2!3d34.9552166!4d-120.4453965!16s%2Fg%2F11g_1kx5jd!19sChIJq6oO5IRr7IARXXOrOR8Mh6o?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/ESPN+Radio/data=!4m7!3m6!1s0x80ecf13625795ab9:0xe1be4a3d481cef75!8m2!3d35.259249!4d-120.6432237!16s%2Fg%2F1vn_z86m!19sChIJuVp5JTbx7IARde8cSD1KvuE?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Ksly/data=!4m7!3m6!1s0x80ecf0d11bb79a2b:0x23c6a3576874ddac!8m2!3d35.2511314!4d-120.6736864!16s%2Fg%2F1wh4g4_c!19sChIJK5q3G9Hw7IARrN10aFejxiM?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Radio+Mixteca/data=!4m7!3m6!1s0x80ec6b80f98e9979:0x8338be97830fb77!8m2!3d34.952878!4d-120.4380381!16s%2Fg%2F11csp7pvk5!19sChIJeZmO-YBr7IARd_sweOmLMwg?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/K-Life/data=!4m7!3m6!1s0x80ecf0fd75b7079f:0x86747dd21b546301!8m2!3d35.2776435!4d-120.6671541!16s%2Fg%2F1trpr30x!19sChIJnwe3df3w7IARAWNUG9J9dIY?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Radio+Ranchito/data=!4m7!3m6!1s0x80ec6c7d428a46ef:0x4ddd3dd53b86abc2!8m2!3d34.954042!4d-120.4258026!16s%2Fg%2F1tf3684n!19sChIJ70aKQn1s7IARwquGO9U93U0?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KWSP-FM+Santa+Margarita/data=!4m7!3m6!1s0x80ecee5057aad169:0x5c810a065a15e5f2!8m2!3d35.360532!4d-120.6568216!16s%2Fg%2F1tfzh24y!19sChIJadGqV1Du7IAR8uUVWgYKgVw?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Lazer+Broadcasting/data=!4m7!3m6!1s0x80ec6c7eef105855:0xab43051b5d8a4b03!8m2!3d34.9551735!4d-120.4321347!16s%2Fg%2F1tdqhsrm!19sChIJVVgQ735s7IARA0uKXRsFQ6s?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kkal/data=!4m7!3m6!1s0x80ecf14a8c848921:0x2030c4663efaad08!8m2!3d35.2553941!4d-120.6414263!16s%2Fg%2F1td4kfc_!19sChIJIYmEjErx7IARCK36PmbEMCA?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Knight+Broadcasting/data=!4m7!3m6!1s0x80ec6b62addda1a3:0x8d55943c81603b27!8m2!3d34.940248!4d-120.4363687!16s%2Fg%2F1trxkldt!19sChIJo6HdrWJr7IARJztggTyUVY0?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/San+Luis+Obispo+Broadcasting/data=!4m7!3m6!1s0x80ecf0d11bb79a2b:0xce860eef5124adbd!8m2!3d35.2511314!4d-120.6736864!16s%2Fg%2F1tdgq41s!19sChIJK5q3G9Hw7IARva0kUe8Ohs4?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Pacific+Coast+Media+LLC/data=!4m7!3m6!1s0x80ecf136289eda6b:0xc1e2398728ea7d1a!8m2!3d35.2593211!4d-120.6432089!16s%2Fg%2F1tdcxdkl!19sChIJa9qeKDbx7IARGn3qKIc54sE?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kxtz/data=!4m7!3m6!1s0x80ecf6dbb2db55e5:0x439edc1929d93431!8m2!3d35.2353775!4d-120.6405166!16s%2Fg%2F1w97vq0n!19sChIJ5VXbstv27IARMTTZKRncnkM?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KJDJ/data=!4m7!3m6!1s0x80ec6b880af3c1bf:0x76038476a78a02ff!8m2!3d34.9606585!4d-120.4370594!16s%2Fg%2F1td1q5rb!19sChIJv8HzCohr7IAR_wKKp3aEA3Y?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KRQK/data=!4m7!3m6!1s0x80ec6b46f2f53973:0x45abe7e96fb3d88a!8m2!3d34.9185438!4d-120.4549622!16s%2Fg%2F1vq9mlt1!19sChIJczn18kZr7IARitizb-nnq0U?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/La+Raza+102.1FM+%26+1380AM/data=!4m7!3m6!1s0x80ec6b9b73fe4469:0x17e718a73f595023!8m2!3d34.9402694!4d-120.4363299!16s%2Fg%2F11fr2cxpzr!19sChIJaUT-c5tr7IARI1BZP6cY5xc?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kyns/data=!4m7!3m6!1s0x80ecf6bfaf64427f:0xc5af78f233f8e1b!8m2!3d35.2353956!4d-120.6405109!16s%2Fg%2F1w8wbbbn!19sChIJf0Jkr7_27IARG44_I4_3Wgw?authuser=0&hl=en&rclk=1",

    "https://www.google.com/maps/place/Kxtk/data=!4m7!3m6!1s0x80ecf13625795ab9:0x264c9c8599d50881!8m2!3d35.2593211!4d-120.6432089!16s%2Fg%2F1td4dw9r!19sChIJuVp5JTbx7IARgQjVmYWcTCY?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Ksni/data=!4m7!3m6!1s0x80ec6b46b7f7b573:0xe44af13b8c6a0588!8m2!3d34.9185051!4d-120.4547688!16s%2Fg%2F1tdwv_sm!19sChIJc7X3t0Zr7IARiAVqjDvxSuQ?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kraz/data=!4m7!3m6!1s0x80ec6b62addda1a3:0xad34fb97670b6abf!8m2!3d34.940248!4d-120.4363687!16s%2Fg%2F1tf1p4br!19sChIJo6HdrWJr7IARv2oLZ5f7NK0?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Fuego+97.1+FM+KRTO/data=!4m7!3m6!1s0x80ec6c7d428a413b:0x6e6d748e051e02b2!8m2!3d34.9540502!4d-120.4257717!16s%2Fg%2F1tj1sdh8!19sChIJO0GKQn1s7IARsgIeBY50bW4?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KSBQ/data=!4m7!3m6!1s0x80ec6c7eef105855:0x98a8bdbc865c2c25!8m2!3d34.9551735!4d-120.4321347!16s%2Fg%2F1tgm3564!19sChIJVVgQ735s7IARJSxchry9qJg?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/La+Buena+105.1+FM+KIDI/data=!4m7!3m6!1s0x80ec6c7d428a46ef:0xca03367d5a21dcc0!8m2!3d34.9540502!4d-120.4257717!16s%2Fg%2F1tdx9049!19sChIJ70aKQn1s7IARwNwhWn02A8o?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KPIG/data=!4m7!3m6!1s0x80ecf6dbb2db55e5:0x22d2148e1fab2e45!8m2!3d35.2354782!4d-120.6405584!16s%2Fg%2F1tdywp7k!19sChIJ5VXbstv27IARRS6rH44U0iI?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/SLO+Echo+Link/data=!4m7!3m6!1s0x80ece8ab30fecf8b:0xc1fefc58a570b9dc!8m2!3d35.3940848!4d-120.7082806!16s%2Fg%2F11b6_fm59z!19sChIJi8_-MKvo7IAR3LlwpVj8_sE?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Lazer+Broadcasting/data=!4m7!3m6!1s0x80ec6a4ecd8edd0f:0x442ca85428750e86!8m2!3d34.9504188!4d-120.4904626!16s%2Fg%2F1vbl7x8f!19sChIJD92OzU5q7IARhg51KFSoLEQ?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KXFM+99.1+The+Fox/data=!4m7!3m6!1s0x80ec6b46b7f7b573:0x9b8f5fb8f747a028!8m2!3d34.9199871!4d-120.4543579!16s%2Fg%2F119wfpfx2!19sChIJc7X3t0Zr7IARKKBH97hfj5s?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Syndicom/data=!4m7!3m6!1s0x80ecf103cfbd712b:0x6b9ea2a31e7cb64b!8m2!3d35.2812896!4d-120.6624995!16s%2Fg%2F1tj89r8w!19sChIJK3G9zwPx7IARS7Z8HqOinms?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Tele+Vida+Abundante/data=!4m7!3m6!1s0x80ec6b8870ac47b9:0x593f976ff545a713!8m2!3d34.9606373!4d-120.4378354!16s%2Fg%2F1tfhgqrt!19sChIJuUescIhr7IARE6dF9W-XP1k?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Eat+Drink+Explore+Media/data=!4m7!3m6!1s0x80ecf10394e926a5:0x9e3e74e62eed7b7!8m2!3d35.2809455!4d-120.6615537!16s%2Fg%2F11cfcrlb2!19sChIJpSbplAPx7IARt9fuYk7n4wk?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Guadalupe+VOR/data=!4m7!3m6!1s0x80ec6b3b8dc54017:0x780bc66581816f9d!8m2!3d34.9523854!4d-120.5215309!16s%2Fg%2F11rmbznb5g!19sChIJF0DFjTtr7IARnW-BgWXGC3g?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Five+Cities+Fire+Authority/data=!4m7!3m6!1s0x80ec5e88ae560063:0x47df729c97948db2!8m2!3d35.1212721!4d-120.5792806!16s%2Fg%2F1td0gtv1!19sChIJYwBWrohe7IARso2Ul5xy30c?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Kbox/data=!4m7!3m6!1s0x80ec6b46f2400001:0x15759e583fb04b46!8m2!3d34.9185051!4d-120.4547688!16s%2Fg%2F11fnyp9hjh!19sChIJAQBA8kZr7IARRkuwP1iedRU?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Met+105/data=!4m7!3m6!1s0x80c221085ad7c1e1:0x66325ce749b7149e!8m2!3d35.0892833!4d-118.2544579!16s%2Fg%2F11h2g4lf49!19sChIJ4cHXWgghwoARnhS3SedcMmY?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KGBB-FM+Mojave/data=!4m7!3m6!1s0x80c23ba8d4b5799b:0xc16cc29f1cb3dd56!8m2!3d34.9791396!4d-118.1681308!16s%2Fg%2F1tfk986_!19sChIJm3m11Kg7woARVt2zHJ_CbME?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KTLW-FM+Rosamond/data=!4m7!3m6!1s0x80c2479dc5da9727:0x6ea5b81dd759f2d8!8m2!3d34.8508692!4d-118.1570658!16s%2Fg%2F1tgtfrrd!19sChIJJ5faxZ1HwoAR2PJZ1x24pW4?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Saddleback+Broadcasting+Inc/data=!4m7!3m6!1s0x80c23fb50850ff25:0x575198a3b9227450!8m2!3d34.873973!4d-118.274019!16s%2Fg%2F1tdpgg3k!19sChIJJf9QCLU_woARUHQiuaOYUVc?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/K219AO+fm+91.7/data=!4m7!3m6!1s0x80c21cacc3cc18a1:0x355320f13691b3e0!8m2!3d35.0322369!4d-118.48514!16s%2Fg%2F11fx8z8y4y!19sChIJoRjMw6wcwoAR4LORNvEgUzU?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KTPI-FM+Tehachapi/data=!4m7!3m6!1s0x80c21ebffef714c1:0xb04e6e826a04cc04!8m2!3d35.0749682!4d-118.3698042!16s%2Fg%2F1tk1n7kg!19sChIJwRT3_r8ewoARBMwEaoJuTrA?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Bluvth+Muzick+Radio/data=!4m7!3m6!1s0x80c23903c615bb5f:0x45fa45ee6c65d896!8m2!3d34.313294!4d-118.3034226!16s%2Fg%2F11j6rfd4d9!19sChIJX7sVxgM5woARlthlbO5F-kU?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/High+Desert+Broadcasting/data=!4m7!3m6!1s0x80c25825e16c27ef:0x40467d71973bcb75!8m2!3d34.5785145!4d-118.1184785!16s%2Fg%2F1thq0zhc!19sChIJ7yds4SVYwoARdcs7l3F9RkA?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Little+Mount+Gleason/data=!4m7!3m6!1s0x80c2f01d8de8ed05:0xccb24c5d66f455da!8m2!3d34.3838034!4d-118.1280411!16s%2Fg%2F11c6dktj8w!19sChIJBe3ojR3wwoAR2lX0Zl1Mssw?authuser=0&hl=en&rclk=1",

    "https://www.google.com/maps/place/KKZQ-FM+100.1+The+Quake/data=!4m7!3m6!1s0x80c25825e11541f5:0xd7a2c0e91851c96a!8m2!3d34.5785549!4d-118.1183873!16s%2Fg%2F11cnc56842!19sChIJ9UEV4SVYwoARaslRGOnAotc?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/BOB+FM+103.9/data=!4m7!3m6!1s0x80c25c62bab6fbcf:0x2b219d2c9af50e86!8m2!3d34.6458984!4d-118.2181573!16s%2Fg%2F1ptwgnyll!19sChIJz_u2umJcwoARhg71miydISs?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Ktpi/data=!4m7!3m6!1s0x80c25a87e24c09d7:0xe6d8372d0b478796!8m2!3d34.6708015!4d-118.1238346!16s%2Fg%2F1tjz3mn9!19sChIJ1wlM4odawoARlodHCy032OY?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KFXM/data=!4m7!3m6!1s0x80c25ad1e7e70267:0x542a0011962e482e!8m2!3d34.6985124!4d-118.1483387!16s%2Fg%2F1tnbld5f!19sChIJZwLn59FawoARLkgulhEAKlQ?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KLKX/data=!4m7!3m6!1s0x80c25825e16c27ef:0x3cdf9bbe76decd9a!8m2!3d34.5785178!4d-118.118415!16s%2Fg%2F1tt1hgn6!19sChIJ7yds4SVYwoARms3edr6b3zw?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Radio+La+Poderosa+con+Cristo+99.1FM/data=!4m7!3m6!1s0x80c2593304379705:0x74ab79ab9dc7f458!8m2!3d34.5858773!4d-118.1149102!16s%2Fg%2F11jw9r8jlh!19sChIJBZc3BDNZwoARWPTHnat5q3Q?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Clear+Channel+Radio/data=!4m7!3m6!1s0x80c25a87e24c09d7:0x3b54d4d2f03d29b2!8m2!3d34.6709958!4d-118.1236918!16s%2Fg%2F1td5xdws!19sChIJ1wlM4odawoARsik98NLUVDs?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KMVE-FM+106.9/data=!4m7!3m6!1s0x80c25825e11541f5:0xf36df5cff30b3859!8m2!3d34.5785549!4d-118.1183873!16s%2Fg%2F11ddwj33vx!19sChIJ9UEV4SVYwoARWTgL88_1bfM?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KePadre+104.9/data=!4m7!3m6!1s0x80c25d4b453363b3:0x1452a5a312be96c9!8m2!3d34.6458984!4d-118.2181573!16s%2Fg%2F11kl7rn8ht!19sChIJs2MzRUtdwoARyZa-EqOlUhQ?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Finding+Music+Podcast/data=!4m7!3m6!1s0x699eb6c692bf33e7:0x78d6c32f83112815!8m2!3d46.423669!4d-129.9427086!16s%2Fg%2F11rhs5hqvd!19sChIJ5zO_ksa2nmkRFSgRgy_D1ng?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Fox+Sports+610+AM/data=!4m7!3m6!1s0x80c25a87e24c09d7:0xda7b3e5922721eb5!8m2!3d34.6709974!4d-118.123904!16s%2Fg%2F1td4pz9_!19sChIJ1wlM4odawoARtR5yIlk-e9o?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Mister+Ben+Bipolar/data=!4m7!3m6!1s0x80c259499d5592b1:0x55e21e6135775f7d!8m2!3d34.585417!4d-118.1019555!16s%2Fg%2F11nccw75p5!19sChIJsZJVnUlZwoARfV93NWEe4lU?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/DRFM+Radio+Station/data=!4m7!3m6!1s0x80944abbc5fe6cc7:0x1a8ee3daeed7cb0f!8m2!3d37.0749486!4d-119.4331866!16s%2Fg%2F1tg35gdf!19sChIJx2z-xbtKlIARD8vX7trjjho?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/KTNS/data=!4m7!3m6!1s0x8094276375a6e389:0xc9f86d205167d503!8m2!3d37.3358678!4d-119.6643224!16s%2Fg%2F1tp8_8s1!19sChIJieOmdWMnlIARA9VnUSBt-Mk?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/The+Yosemite+Breeze+Radio+Network/data=!4m7!3m6!1s0x2a9d3d647cb1f771:0x5d871e47c2fb8639!8m2!3d46.423669!4d-129.9427086!16s%2Fg%2F11qfnm1xyw!19sChIJcfexfGQ9nSoROYb7wkceh10?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Immaculate+Heart+Radio+KHOT/data=!4m7!3m6!1s0x80940c595e016c8d:0xb0cc1d0cd25ff03e!8m2!3d36.9666056!4d-120.0358139!16s%2Fg%2F1tdks0yy!19sChIJjWwBXlkMlIARPvBf0gwdzLA?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/B95+KBOS-FM/data=!4m7!3m6!1s0x80945d62429d79b1:0x319ae8e73cf2be54!8m2!3d36.8078216!4d-119.7885129!16s%2Fg%2F1tf0qw5h!19sChIJsXmdQmJdlIARVL7yPOfomjE?authuser=0&hl=en&rclk=1"
]

# ============================================================


def get_website(page, url):
    try:
        page.goto(url, timeout=20000)
        time.sleep(5)  # 5 sec wait jab tak page load ho

        # Try multiple selectors
        selectors = [
            'a[data-item-id="authority"]',
            'a[aria-label*="website" i]',
            'a[data-tooltip="Open website"]',
            'a[href*="http"]:has-text("Website")',
        ]

        for selector in selectors:
            try:
                el = page.query_selector(selector)
                if el:
                    href = el.get_attribute("href")
                    if href and "google" not in href:
                        return href
            except:
                continue

        return "Website nahi mila (Maps pe listed nahi)"

    except Exception as e:
        return f"ERROR: {e}"


def main():
    print("\n" + "="*60)
    print("   Google Maps Website Extractor")
    print("="*60 + "\n")

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = context.new_page()

        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] Processing...")
            website = get_website(page, url)
            results.append((url, website))
            print(f"         Website : {website}\n")

        browser.close()

    # Save to file bhi karo
    output_file = "results.txt"
    with open(output_file, "w") as f:
        f.write("Google Maps Website Results\n")
        f.write("="*60 + "\n\n")
        for url, website in results:
            f.write(f"Maps URL : {url}\n")
            f.write(f"Website  : {website}\n")
            f.write("-"*60 + "\n")

    print("\n" + "="*60)
    print("FINAL RESULTS:")
    print("="*60)
    for _, website in results:
        print(website)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
