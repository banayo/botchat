"""
Brand master for the LangChain SQL agents (export / mkt).

Source: ERP table IN_BRAND, exported as IN_BRAND.xls. BRAND_CODE values are kept
byte-for-byte because the views store them that way - e.g. Dr.NIKS is 'Dr.N'
followed by a TAB, so WHERE BRAND_CODE = 'Dr.N' matches nothing.

Regenerate BRAND_CATALOG from a fresh export instead of hand-editing it.
"""

from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy import text
from sqlalchemy.engine import Engine

# Umbrella brands whose sales are split across several BRAND_CODE values.
# A question about the umbrella ("ยอด Cathy Doll") must sum every code in it.
BRAND_FAMILIES: dict[str, dict[str, Any]] = {
    "cathy_doll": {
        "name_en": "Cathy Doll",
        "name_th": "เคที่ดอลล์",
        "aliases": ["cathy doll", "cathy dolls", "cathydoll", "เคที่ดอลล์"],
        "brand_codes": ["CD", "CD (A)", "CD (B)", "CD (F)", "CD (M)"],
        "description": "ถามถึง Cathy Doll โดยไม่ระบุไลน์ย่อย ให้รวมทุก BRAND_CODE ในกลุ่มนี้",
    },
    "dr_niks": {
        "name_en": "Dr.NIKS",
        "name_th": "ดร.นิกส์",
        "aliases": ["dr.niks", "dr niks", "drniks", "ดร.นิกส์"],
        "brand_codes": ["Dr.N\t"],
        "description": "BRAND_CODE ในระบบมีอักขระ TAB ต่อท้าย ต้องใช้ค่าตามที่ให้ไว้เท่านั้น",
    },
}

# Active brands only. ATP BEAUTY (ACTIVE=N, "เลิกใช้งาน ซ้ำ ATP") is left out.
BRAND_CATALOG: dict[str, dict[str, str]] = {
    "3M": {"name_en": "3M", "name_th": "สามเอ็ม", "group": "BBB"},
    "3W Clinic": {"name_en": "3W Clinic", "name_th": "3ดับเบิ้ลยูคลีนิค", "group": "BBB"},
    "3W Clinic.": {"name_en": "3W Clinic.", "name_th": "3ดับเบิ้ลยูคลีนิค", "group": "BBB"},
    "4U2": {"name_en": "4U2", "name_th": "โฟร์ยูทู", "group": ""},
    "7C": {"name_en": "7Clean", "name_th": "เซเว่นคลีน", "group": "BBB"},
    "AB": {"name_en": "Anbio Biotech", "name_th": "แอนไบโอไบโอเทค", "group": "CTD"},
    "Absorb Bla": {"name_en": "Absorb Black Head", "name_th": "แอบซอร์ฟแบล็คเฮด", "group": "BBB"},
    "AC": {"name_en": "ACCA by Dr.DSP", "name_th": "แอคก้าบายดร.ดีเอสพี", "group": "BBB"},
    "Addict": {"name_en": "Addict", "name_th": "แอดดิคท์", "group": "BBB"},
    "Affection": {"name_en": "Affectionate Love", "name_th": "เอฟเฟ็คชั่นเนทเลิฟ", "group": "BBB"},
    "Aide": {"name_en": "Aide", "name_th": "", "group": "BBB"},
    "Aloe": {"name_en": "Aloe", "name_th": "อโล", "group": "BBB"},
    "AM": {"name_en": "AmieAmi", "name_th": "อามีอามี", "group": ""},
    "Amame": {"name_en": "Amame", "name_th": "อามาเมะ", "group": "CTD"},
    "Angeala": {"name_en": "Angeala", "name_th": "แอนจีล่า", "group": "BBB"},
    "Angel Col": {"name_en": "Angel Color", "name_th": "แองเจิลคัลเลอร์", "group": "BBB"},
    "Anionblue": {"name_en": "Anionblue", "name_th": "เอเนียนบลู", "group": "BBB"},
    "Anjo": {"name_en": "Anjo", "name_th": "แอนโจ", "group": "BBB"},
    "AO": {"name_en": "And Only", "name_th": "แอนด์โอนลี่", "group": ""},
    "Aspasia": {"name_en": "Aspasia", "name_th": "แอสปาเซีย", "group": "BBB"},
    "ATP": {"name_en": "ATP BEAUTY", "name_th": "เอทีพีบิวตี้", "group": ""},
    "Aulles": {"name_en": "Aulles", "name_th": "ออร่า", "group": "BBB"},
    "Avant Gar": {"name_en": "Avant Gardero", "name_th": "อาวังท์กาเดโร่", "group": "BBB"},
    "B-Happy": {"name_en": "B-Happy", "name_th": "บีแฮปปี้", "group": "BBB"},
    "Baby Blink": {"name_en": "Baby Blink", "name_th": "เบบี้บริ๊งค์", "group": "BBB"},
    "BB": {"name_en": "Baby Bright", "name_th": "เบบี้ไบร์ท", "group": "BBB"},
    "BB (A)": {"name_en": "Baby Bright (A)", "name_th": "เบบี้ไบร์ท (A)", "group": "BBB"},
    "BB (B)": {"name_en": "Baby Bright (B)", "name_th": "เบบี้ไบร์ท (B)", "group": "BBB"},
    "BB (F)": {"name_en": "Baby Bright (F)", "name_th": "เบบี้ไบร์ท (F)", "group": "BBB"},
    "BB (M)": {"name_en": "Baby Bright (M)", "name_th": "เบบี้ไบร์ท (M)", "group": "BBB"},
    "Bear": {"name_en": "Bear", "name_th": "แบร์", "group": "BBB"},
    "Beauskin": {"name_en": "Beauskin", "name_th": "", "group": "BBB"},
    "Beautrium": {"name_en": "Beautrium", "name_th": "บิวเทรี่ยม", "group": ""},
    "Beauty Ang": {"name_en": "Beauty Angel", "name_th": "บิวตี้แองเจิล", "group": "BBB"},
    "Beauty Bat": {"name_en": "Beauty Bath", "name_th": "บิวตี้บาธ", "group": "BBB"},
    "Beauty Dia": {"name_en": "Beauty Diary", "name_th": "บิวตี้ไดอารี่", "group": "BBB"},
    "Beauty Fas": {"name_en": "Beauty Fashion", "name_th": "บิวตี้แฟชั่น", "group": "BBB"},
    "BeauuGreen": {"name_en": "BeauuGreen", "name_th": "บูกรีน", "group": "BBB"},
    "Bemei": {"name_en": "Bemei", "name_th": "บีเมอิ", "group": "BBB"},
    "Bergamo": {"name_en": "Bergamo", "name_th": "เบอร์กาโม่", "group": "BBB"},
    "Bergamo Ca": {"name_en": "Bergamo Caviar", "name_th": "เบอร์กาโม่คาเวียร์", "group": "BBB"},
    "Bergamo*": {"name_en": "Bergamo*", "name_th": "เบอร์กาโม่", "group": "BBB"},
    "Betty Bon": {"name_en": "Betty Bonnie", "name_th": "เบตตี้บอนนี่", "group": "BBB"},
    "BI": {"name_en": "Browit", "name_th": "บราวอิท", "group": "BBB"},
    "BI Men": {"name_en": "Browit Men", "name_th": "บราวอิทเมน", "group": ""},
    "Bizanne": {"name_en": "Bizanne", "name_th": "", "group": "BBB"},
    "BL": {"name_en": "BEAUTILOX", "name_th": "บิวตี้ล็อกซ์", "group": "BBB"},
    "BO.KIN": {"name_en": "BO.KIN", "name_th": "โบกิ้น", "group": "BBB"},
    "Body Lux": {"name_en": "Body Luxuries", "name_th": "บอดี้ลักซ์ชัวรี่", "group": "BBB"},
    "Body Sec": {"name_en": "Body Secrets", "name_th": "บอดี้ซีเคร็ท", "group": "BBB"},
    "Bomic": {"name_en": "Bomic", "name_th": "โบมิค", "group": "BBB"},
    "BONAIFEI": {"name_en": "BONAIFEI", "name_th": "โบไนเฟ", "group": "CTD"},
    "Bourjois": {"name_en": "Bourjois", "name_th": "เบอจัว", "group": "BBB"},
    "Boya": {"name_en": "Boya", "name_th": "โบย่า", "group": "BBB"},
    "BRTC": {"name_en": "BRTC", "name_th": "บีอาร์ทีซี", "group": "BBB"},
    "BT": {"name_en": "BOTANIST", "name_th": "โบทานิสต์", "group": ""},
    "Buzzle": {"name_en": "Buzzle", "name_th": "บัซเซิล", "group": "CTD"},
    "BYB": {"name_en": "BYB", "name_th": "บีวายบี", "group": "BBB"},
    "C Git": {"name_en": "C Git", "name_th": "ซีกิต", "group": "BBB"},
    "Cailin": {"name_en": "Cailin", "name_th": "", "group": "BBB"},
    "Calorie Of": {"name_en": "Calorie Off", "name_th": "แคลอรี่ออฟ", "group": "BBB"},
    "Candy Doll": {"name_en": "Candy Doll", "name_th": "แคนดี้ดอลล์", "group": "BBB"},
    "Carden Inc": {"name_en": "Carden Incense", "name_th": "คาร์เด้นอินเซนส์", "group": "BBB"},
    "CARDIN": {"name_en": "CARDIN", "name_th": "คาร์ดิน", "group": "BBB"},
    "Care Salon": {"name_en": "Care Salon", "name_th": "แคร์ซาลอน", "group": "BBB"},
    "Caremate": {"name_en": "Caremate", "name_th": "แคร์เมท", "group": ""},
    "Catena": {"name_en": "Catena", "name_th": "แค๊ททีน่า", "group": "BBB"},
    "Cathy": {"name_en": "Cathy", "name_th": "เคที่", "group": "BBB"},
    "Cawaii Min": {"name_en": "Cawaii Mini", "name_th": "คาวาอิมินิ", "group": "BBB"},
    "CB": {"name_en": "Candy Blink", "name_th": "แคนดี้บลิ๊งค์", "group": ""},
    "CC": {"name_en": "Cathy Choo", "name_th": "เคที่ชู", "group": "BBB"},
    "CD": {"name_en": "Cathy Doll", "name_th": "เคที่ดอลล์", "group": "CTD"},
    "CD (A)": {"name_en": "Cathy Doll (A)", "name_th": "เคที่ดอลล์ (A)", "group": "CTD"},
    "CD (B)": {"name_en": "Cathy Doll (B)", "name_th": "เคที่ดอลล์ (B)", "group": "CTD"},
    "CD (F)": {"name_en": "Cathy Doll (F)", "name_th": "เคที่ดอลล์ (F)", "group": "CTD"},
    "CD (M)": {"name_en": "Cathy Doll (M)", "name_th": "เคที่ดอลล์ (M)", "group": "CTD"},
    "Ceboa": {"name_en": "Ceboa", "name_th": "", "group": "BBB"},
    "Chalong": {"name_en": "Chalongbeach", "name_th": "", "group": "BBB"},
    "CHAT": {"name_en": "CHAT", "name_th": "ฉัตร", "group": ""},
    "ChceDo": {"name_en": "ChceDo", "name_th": "", "group": "BBB"},
    "Chen Chun": {"name_en": "Chen Chun", "name_th": "เฉินชุน", "group": "CTD"},
    "Choute": {"name_en": "Choute", "name_th": "ชูตู", "group": "BBB"},
    "CK Kabeis": {"name_en": "CK Kabeis", "name_th": "ซีเคคาเบอิ", "group": "BBB"},
    "clean": {"name_en": "clean", "name_th": "คลีน", "group": "BBB"},
    "Clean Sma": {"name_en": "Clean Smart", "name_th": "คลีนสมาร์ท", "group": "BBB"},
    "Clinic": {"name_en": "Clinic", "name_th": "คลีนิค", "group": "BBB"},
    "CN": {"name_en": "Catchy Nesty", "name_th": "แคชชี่เนสตี้", "group": "CTD"},
    "Co.E": {"name_en": "Co.E", "name_th": "โคอี", "group": "BBB"},
    "CocoBa": {"name_en": "Coco Babara", "name_th": "โคโค่บาบาร่า", "group": "BBB"},
    "Collogen": {"name_en": "Collogen", "name_th": "คอลโลเจน", "group": "BBB"},
    "Color": {"name_en": "Color", "name_th": "Color", "group": "BBB"},
    "Colordium": {"name_en": "Colordium", "name_th": "คัลเลอร์ดิอุ้ม", "group": "BBB"},
    "Colorful D": {"name_en": "Colorful Days", "name_th": "คัลเลอร์ฟูลเดย์", "group": "BBB"},
    "Cool Bea": {"name_en": "Cool Beauty", "name_th": "คูลบิวตี้", "group": "BBB"},
    "Cool Bet": {"name_en": "Cool Betty", "name_th": "คูลเบทตี้", "group": "BBB"},
    "Cool Flo": {"name_en": "Cool Flower", "name_th": "คูลฟลาวเวอร์", "group": "BBB"},
    "Coolber": {"name_en": "Coolber", "name_th": "คูลเบอร์", "group": "BBB"},
    "Coso": {"name_en": "Coso", "name_th": "โคโซ่", "group": "BBB"},
    "Crayon": {"name_en": "Crayon", "name_th": "เครยอน", "group": "BBB"},
    "Cresson": {"name_en": "Cresson", "name_th": "", "group": "BBB"},
    "Crong": {"name_en": "Crong", "name_th": "ครอง", "group": "BBB"},
    "Cute Miss": {"name_en": "Cute Miss", "name_th": "คิ้วมิส", "group": "BBB"},
    "D & D": {"name_en": "D & D", "name_th": "ดีแอนด์ดี", "group": "BBB"},
    "D ORO": {"name_en": "D'ORO", "name_th": "ดิโอโร่", "group": ""},
    "DaHoc": {"name_en": "DaHoc", "name_th": "ดาฮ็อก", "group": "BBB"},
    "Daiso": {"name_en": "Daiso", "name_th": "ไดโซ", "group": "BBB"},
    "DayLight": {"name_en": "DayLight & hue", "name_th": "เดย์ไลท์แอนด์ฮิว", "group": "BBB"},
    "Dear Body": {"name_en": "Dear Body", "name_th": "เดียร์บอดี้", "group": "BBB"},
    "Deco Nail": {"name_en": "Deco Nail", "name_th": "", "group": "BBB"},
    "Dejavu": {"name_en": "Dejavu", "name_th": "เดจาวู", "group": "BBB"},
    "Deold": {"name_en": "Deold", "name_th": "ดีโอลด์", "group": "BBB"},
    "Derfill": {"name_en": "Derfill", "name_th": "เดอร์ฟิล", "group": "BBB"},
    "DERMAID": {"name_en": "DERMAID", "name_th": "เดิร์มเอด", "group": ""},
    "Dew & Dew": {"name_en": "Dew & Dew", "name_th": "ดิวแอนด์ดิว", "group": "BBB"},
    "Dew & Dew.": {"name_en": "Dew & Dew.", "name_th": "ดิวแอนด์ดิว", "group": "BBB"},
    "Difan": {"name_en": "Difan", "name_th": "ดีฟาน", "group": "BBB"},
    "Diff": {"name_en": "Diff", "name_th": "ดิฟ", "group": "BBB"},
    "Distar": {"name_en": "Distar", "name_th": "ไดสตาร์", "group": "BBB"},
    "DIY": {"name_en": "DIY", "name_th": "ดีไอวาย", "group": "BBB"},
    "DN": {"name_en": "DN", "name_th": "ดีเอ็น", "group": "BBB"},
    "Dodora": {"name_en": "Dodora", "name_th": "โดโดร่า", "group": "BBB"},
    "Dongbaek": {"name_en": "Dongbaekmiin", "name_th": "", "group": "BBB"},
    "Dora": {"name_en": "Dora", "name_th": "โดร่า", "group": "BBB"},
    "Double Ric": {"name_en": "Double rich", "name_th": "ดับเบิ้ลริช", "group": "BBB"},
    "Dr.Bath": {"name_en": "Dr.Bath", "name_th": "ด๊อกเตอร์บาธ", "group": "BBB"},
    "Dr.DSP": {"name_en": "Dr.DSP", "name_th": "ดร.ดีเอสพี", "group": "BBB"},
    "Dr.N\t": {"name_en": "Dr.NIKS", "name_th": "ดร.นิกส์", "group": "CTD"},
    "Dr.Polir": {"name_en": "Dr.Polir", "name_th": "ด๊อกเตอร์ โพลิ", "group": "BBB"},
    "Dr.Pro": {"name_en": "Beauty Secret Dr.Pro", "name_th": "บิวติ้ซีเคร็ทด็อกเตอร์โปร", "group": ""},
    "Dr.Reborn": {"name_en": "Dr.Reborn", "name_th": "ด็อกเตอร์ รีบอร์น", "group": "BBB"},
    "E.saline V": {"name_en": "E.saline Vogue", "name_th": "อี.สลินโวค", "group": "BBB"},
    "East-Skin": {"name_en": "East-Skin", "name_th": "อีส-สกิน", "group": "BBB"},
    "Ebou": {"name_en": "Ebou", "name_th": "อีโบว์", "group": "BBB"},
    "Ecotime": {"name_en": "Ecotime", "name_th": "อีโคไทม์", "group": "BBB"},
    "Efolar": {"name_en": "Efolar", "name_th": "อีโฟล่า", "group": "BBB"},
    "Eizhang": {"name_en": "Eizhang", "name_th": "อีจาง", "group": "BBB"},
    "Elizabeth": {"name_en": "Elizabeth", "name_th": "อลิซาเบธ", "group": "BBB"},
    "Enery": {"name_en": "Enery", "name_th": "", "group": "BBB"},
    "Enesti": {"name_en": "Enesti", "name_th": "อีเนสตี้", "group": "BBB"},
    "Enesti.": {"name_en": "Enesti.", "name_th": "อีเนสตี้.", "group": "BBB"},
    "Eno Greet": {"name_en": "Eno Greeting", "name_th": "อีโน่กรีทติ้ง", "group": "BBB"},
    "Esedo": {"name_en": "Esedo", "name_th": "อิเซโด้", "group": "BBB"},
    "Essence": {"name_en": "Essence", "name_th": "เอสเซนต์", "group": "BBB"},
    "Eucerin": {"name_en": "Eucerin", "name_th": "ยูเซรีน", "group": "BBB"},
    "FaceQ": {"name_en": "FaceQ", "name_th": "เฟรซคิว", "group": "BBB"},
    "Fairy": {"name_en": "Fairy", "name_th": "แฟรี่", "group": "BBB"},
    "Fairy Drop": {"name_en": "Fairy Drops", "name_th": "แฟรี่ดรอปส์", "group": "BBB"},
    "Fascina": {"name_en": "Fascination", "name_th": "ฟาสสิเนชั่น", "group": "BBB"},
    "Fayever": {"name_en": "Fayever", "name_th": "ฝ้ายเอเวอร์", "group": ""},
    "FC": {"name_en": "Fasclean", "name_th": "ฟาสคลีน", "group": "BBB"},
    "Feng Hua": {"name_en": "Feng Hua", "name_th": "", "group": "BBB"},
    "FI": {"name_en": "FACE IT", "name_th": "เฟสอิท", "group": "BBB"},
    "Flamingo": {"name_en": "Flamingo", "name_th": "ฟาร์มิงโก้", "group": "BBB"},
    "FN": {"name_en": "Fantasy Noodle", "name_th": "แฟนตาซีนู้ดเดิ้ล", "group": "CTD"},
    "Foli": {"name_en": "Foli", "name_th": "ฟูลิ", "group": "BBB"},
    "Fozhimei": {"name_en": "Fozhimei", "name_th": "โฟจื้อเม่ย", "group": "BBB"},
    "Freen x CD": {"name_en": "Freen x Cathy Doll (B)", "name_th": "ฟรีนเอ็กซ์เคที่ดอลล์ (B)", "group": ""},
    "Fruit": {"name_en": "Fruit", "name_th": "ฟรุ๊ต", "group": "BBB"},
    "Fruity": {"name_en": "Fruity", "name_th": "ฟรุ๊ตตี้", "group": "BBB"},
    "Fuli Fen": {"name_en": "Fuli Fenling", "name_th": "", "group": "BBB"},
    "Gainly": {"name_en": "Gainly", "name_th": "เกนลี่", "group": "BBB"},
    "Germanium": {"name_en": "Germanium", "name_th": "เจอร์มาเนี่ยม", "group": "BBB"},
    "Gift Set": {"name_en": "Gift Set", "name_th": "กิฟท์เซ็ท", "group": "BBB"},
    "Ginger Foo": {"name_en": "Ginger Foot", "name_th": "จิงเจอร์ฟู๊ท", "group": "BBB"},
    "Gold": {"name_en": "Gold", "name_th": "โกลด์", "group": "BBB"},
    "Grache": {"name_en": "Grache", "name_th": "กราเซ่", "group": "BBB"},
    "Grasse-Fra": {"name_en": "Grasse-Fragrance", "name_th": "แกรซซ์เฟรแกรนซ์", "group": "BBB"},
    "GS": {"name_en": "Get Skin by EYETA", "name_th": "เก็ทสกินบายอายตา", "group": "BBB"},
    "Hair Load": {"name_en": "Hair Load", "name_th": "แฮร์โหลด", "group": ""},
    "Hair Salon": {"name_en": "Hair Salon", "name_th": "แฮร์ซาลอน", "group": "BBB"},
    "Hakuhodo": {"name_en": "Hakuhodo", "name_th": "ฮะคุโฮโตะ", "group": "BBB"},
    "Han Hui": {"name_en": "Han Hui", "name_th": "ฮั่นฮุ่ย", "group": "BBB"},
    "Hanlu": {"name_en": "Hanlu", "name_th": "ฮันลุ", "group": "BBB"},
    "Happer": {"name_en": "Happer", "name_th": "แฮปเปอร์", "group": "BBB"},
    "Hashy": {"name_en": "Hashy", "name_th": "ฮาชาย", "group": "BBB"},
    "Hatomugi": {"name_en": "Hatomugi", "name_th": "ฮาโตะมูกิ", "group": "BBB"},
    "Heal Pharm": {"name_en": "Heal Pharm", "name_th": "ฮีลฟาร์ม", "group": "BBB"},
    "Hearts Lov": {"name_en": "Hearts Love", "name_th": "", "group": "BBB"},
    "Heavy Leg": {"name_en": "Heavy Leg Refresher", "name_th": "เฮฟวี่เลกรีเฟรชเชอร์", "group": "BBB"},
    "Hengesy": {"name_en": "Hengesy", "name_th": "Hengesy", "group": "BBB"},
    "Hengfang": {"name_en": "Hengfang", "name_th": "เฮิงฟาง", "group": "BBB"},
    "HI": {"name_en": "HAIR IT", "name_th": "แฮร์อิท", "group": "BBB"},
    "Hive": {"name_en": "Hive Professional", "name_th": "ไฮฟ์ โปรเฟสชั่นแนล", "group": "BBB"},
    "Homing You": {"name_en": "Homing Youth", "name_th": "", "group": "BBB"},
    "HP": {"name_en": "HP", "name_th": "เอชพี", "group": "BBB"},
    "Hualian": {"name_en": "Hualian", "name_th": "ฮัวเลียน", "group": "BBB"},
    "Huo Li Yin": {"name_en": "Huo Li Yin Zi", "name_th": "", "group": "BBB"},
    "Hygienix": {"name_en": "Hygienix", "name_th": "ไฮจีนิกซ์", "group": "BBB"},
    "Hyssop": {"name_en": "Hyssop", "name_th": "ฮิสซอพ", "group": "BBB"},
    "I Soo": {"name_en": "I Soo", "name_th": "ไอซู", "group": "BBB"},
    "Icharming": {"name_en": "Icharmingkorea", "name_th": "ไอชาร์มมิ่งโคเรีย", "group": "BBB"},
    "IFME": {"name_en": "IFME", "name_th": "อีฟมี", "group": "BBB"},
    "INTA": {"name_en": "INTA", "name_th": "อินทา", "group": "BBB"},
    "Intercolor": {"name_en": "Intercolor", "name_th": "อินเตอร์คัลเลอร์", "group": "BBB"},
    "Intimi": {"name_en": "Intimi", "name_th": "อินทิมี่", "group": "CTD"},
    "Is'SIE": {"name_en": "Is'SIE", "name_th": "อีส'ซี่", "group": "BBB"},
    "Is'Slim": {"name_en": "Is'Slim", "name_th": "อีสสลิม", "group": "BBB"},
    "J24": {"name_en": "J24", "name_th": "เจ ทเว็นตี้โฟร์", "group": "BBB"},
    "Jasaengsu": {"name_en": "Jasaengsu", "name_th": "จาซังซู", "group": "BBB"},
    "Jinsamy": {"name_en": "Jinsamy", "name_th": "จิ้นซั่งเหม่ย", "group": "BBB"},
    "JLXIAN": {"name_en": "JLXIAN", "name_th": "เจแอลเชี่ยน", "group": "BBB"},
    "Joa": {"name_en": "Joa", "name_th": "โจว่า", "group": "BBB"},
    "Juicy Jam": {"name_en": "Juicy Jam", "name_th": "จุ๊ยส์ซี่แจม", "group": "BBB"},
    "JV": {"name_en": "Jejuvita", "name_th": "เจจูวิต้า", "group": "BBB"},
    "K-Select": {"name_en": "K-Select", "name_th": "เคซีเล็คท์", "group": "BBB"},
    "Kaloo": {"name_en": "Kaloo", "name_th": "กาลูร์", "group": "BBB"},
    "Kanier": {"name_en": "Kanier", "name_th": "คาเนียร์", "group": "BBB"},
    "Kawaii Vin": {"name_en": "Kawaii Vink", "name_th": "คาวาอิวิ้งค์", "group": "BBB"},
    "KBROW": {"name_en": "K.BROW", "name_th": "เค.บราว", "group": ""},
    "Kenny & Co": {"name_en": "Kenny & Co", "name_th": "เคนนี่&โค", "group": "BBB"},
    "Kinepin": {"name_en": "Kinepin", "name_th": "คิเนพิน", "group": "BBB"},
    "Kiss Me": {"name_en": "Kiss Me", "name_th": "คิสมี", "group": "BBB"},
    "Kitchen K": {"name_en": "Kitchen K", "name_th": "คิทเช่นเค", "group": "CTD"},
    "KK": {"name_en": "Kitty Kawaii", "name_th": "คิตตี้ คาวาอิ", "group": ""},
    "KKP": {"name_en": "Kitty Kawaii Plus", "name_th": "คิตตี้คาวาอิพัส", "group": ""},
    "KM": {"name_en": "Karmarts", "name_th": "คาร์มาร์ท", "group": "BBB"},
    "KMGI": {"name_en": "KMGI", "name_th": "เคเอ็มจีไอ", "group": ""},
    "KMS": {"name_en": "Karmarts Shop", "name_th": "คาร์มาร์ท ช้อป", "group": "BBB"},
    "Korea": {"name_en": "Korea", "name_th": "โคเรีย", "group": "BBB"},
    "Korean": {"name_en": "Korean", "name_th": "โคเรียน", "group": "BBB"},
    "KY": {"name_en": "Keumyon", "name_th": "กึมยอน", "group": "BBB"},
    "L&D": {"name_en": "L&D", "name_th": "แอลแอนด์ดี", "group": "BBB"},
    "La Mei La": {"name_en": "La Mei La", "name_th": "ลาเหม่ยลา", "group": "BBB"},
    "Lacvert Es": {"name_en": "Lacvert Essance", "name_th": "แลคเวิทแอสซองส์", "group": "BBB"},
    "Lalisa": {"name_en": "Lalisa", "name_th": "ลลิษา", "group": "CTD"},
    "Lan Bi Zi": {"name_en": "Lan Bi Zi", "name_th": "หลันปีจือ", "group": "BBB"},
    "LandBis": {"name_en": "LandBis", "name_th": "แลนด์บิส", "group": "BBB"},
    "LanKou": {"name_en": "LanKouYiRen", "name_th": "", "group": "BBB"},
    "LAQREE": {"name_en": "LAQREE", "name_th": "แลครี", "group": ""},
    "Lassie'el": {"name_en": "Lassie'el", "name_th": "ลาซี่เอล", "group": "BBB"},
    "Leezi": {"name_en": "Leezi", "name_th": "ลีซี่", "group": "BBB"},
    "Liceko": {"name_en": "Liceko", "name_th": "ลิเซโก", "group": "BBB"},
    "Ling Mei": {"name_en": "Ling Mei", "name_th": "หลิงเหม่ย", "group": "BBB"},
    "Lip It": {"name_en": "Lip It", "name_th": "ลิปอิท", "group": "CTD"},
    "Liyan": {"name_en": "Liyanshijia", "name_th": "ลิยาชิเจีย", "group": "BBB"},
    "Luabo": {"name_en": "Luabo", "name_th": "", "group": "BBB"},
    "Lulanjina": {"name_en": "Lulanjina", "name_th": "ลูแลนจิน่า", "group": "BBB"},
    "Macely": {"name_en": "Macely", "name_th": "มาเคลย์", "group": "BBB"},
    "Mali": {"name_en": "Mali", "name_th": "มะลิ", "group": ""},
    "Manshili": {"name_en": "Manshili", "name_th": "มันซือลี่", "group": "BBB"},
    "Marshmal": {"name_en": "Marshmallow", "name_th": "มาร์ชเมลโล่", "group": "BBB"},
    "Maycheer": {"name_en": "Maycheer", "name_th": "เมย์เชียร์", "group": "BBB"},
    "Mei Li": {"name_en": "Mei Li Cheng Nuo", "name_th": "เม่ยลี่เฉิงนัว", "group": "BBB"},
    "Meidun": {"name_en": "Meidun", "name_th": "เมยดัน", "group": "BBB"},
    "Mengkou": {"name_en": "Mengkou", "name_th": "เมงโกะ", "group": "BBB"},
    "Menow": {"name_en": "Menow", "name_th": "มีนาว", "group": "BBB"},
    "Mingkou": {"name_en": "Mingkou", "name_th": "มิงโกะ", "group": "BBB"},
    "Mini": {"name_en": "Mini", "name_th": "มินิ", "group": "BBB"},
    "Miss & Mrs": {"name_en": "Miss & Mrs", "name_th": "มิส&มิสซิส", "group": "BBB"},
    "Missha": {"name_en": "Missha", "name_th": "มิสชา", "group": "BBB"},
    "MM": {"name_en": "Mochi Michi", "name_th": "โมจิมิจิ", "group": ""},
    "MMHC": {"name_en": "Mhee Mahachon", "name_th": "หมี่มหาชน", "group": ""},
    "Moche": {"name_en": "Moche", "name_th": "โมเช่", "group": ""},
    "MUA": {"name_en": "MUA", "name_th": "เอ็มยูเอ", "group": ""},
    "Multi B": {"name_en": "Multi Brand", "name_th": "มัลติแบนด์", "group": "BBB"},
    "My Schem": {"name_en": "My Scheming", "name_th": "มายสกีมมิ่ง", "group": "BBB"},
    "NANGNGAM": {"name_en": "NANGNGAM", "name_th": "นางงาม", "group": ""},
    "Natural Ri": {"name_en": "Natural Rich", "name_th": "เนเชอรัลริช", "group": "BBB"},
    "Necko": {"name_en": "Necko", "name_th": "เนคโกะ", "group": "BBB"},
    "Neo Medi": {"name_en": "Neo-Medical", "name_th": "นิโอ-เมดิคอล", "group": "BBB"},
    "New": {"name_en": "New", "name_th": "นิว", "group": "BBB"},
    "NN": {"name_en": "Nuna", "name_th": "นูน่า", "group": "BBB"},
    "Nut Gall": {"name_en": "Nut Gall", "name_th": "", "group": "BBB"},
    "Oasemeen": {"name_en": "Oasemeen", "name_th": "", "group": "BBB"},
    "Obestom": {"name_en": "Obestom", "name_th": "โอเบสต้อม", "group": "BBB"},
    "Off-White": {"name_en": "Off-White", "name_th": "ออฟไวท์", "group": "BBB"},
    "Onuge": {"name_en": "Onuge", "name_th": "โอนู๊ด", "group": "BBB"},
    "Opera": {"name_en": "Opera", "name_th": "โอเปร่า", "group": "BBB"},
    "Oppa": {"name_en": "Oppa Style", "name_th": "โอปป้าสไตล์", "group": "BBB"},
    "Oracle": {"name_en": "Oracle", "name_th": "ออราเคิล", "group": "BBB"},
    "Oximeter": {"name_en": "Oximeter", "name_th": "ออกซิมิเตอร์", "group": "CTD"},
    "Palma Chr": {"name_en": "Palma Christie", "name_th": "พาล์ม่าคริสตี้", "group": "BBB"},
    "Pascucci": {"name_en": "Pascucci", "name_th": "พาสคุซซี่", "group": "BBB"},
    "PD": {"name_en": "Pa Donphutsa", "name_th": "ป่าดอนพุทรา", "group": ""},
    "Peau-Reve": {"name_en": "Peau-Reve", "name_th": "", "group": "BBB"},
    "Peripera": {"name_en": "Peripera", "name_th": "เพอร์ริเพอร์ร่า", "group": "BBB"},
    "Petty": {"name_en": "Petty", "name_th": "แพทตี้", "group": "BBB"},
    "PKM CD (A)": {"name_en": "Pokemon Cathy Doll (A)", "name_th": "โปเกม่อน เคที่ดอลล์ (A)", "group": "BBB"},
    "PKM CD (B)": {"name_en": "Pokemon Cathy Doll (B)", "name_th": "โปเกม่อน เคที่ดอลล์ (B)", "group": "BBB"},
    "PKM CD (F)": {"name_en": "Pokemon Cathy Doll (F)", "name_th": "โปเกม่อน เคที่ดอลล์ (F)", "group": "BBB"},
    "PKM CD (M)": {"name_en": "Pokemon Cathy Doll (M)", "name_th": "โปเกม่อน เคที่ดอลล์ (M)", "group": "BBB"},
    "Pofeili": {"name_en": "Pofeili", "name_th": "", "group": "BBB"},
    "Pok Pok": {"name_en": "Pok Pok", "name_th": "ป๊อกป๊อก", "group": ""},
    "Polina": {"name_en": "Polina", "name_th": "โพลีน่า", "group": "BBB"},
    "Poppin": {"name_en": "Poppin", "name_th": "", "group": "BBB"},
    "Pororo": {"name_en": "Pororo", "name_th": "โปโรโร่", "group": "BBB"},
    "Posong": {"name_en": "Posong", "name_th": "โปซอง", "group": "BBB"},
    "Prism Dol": {"name_en": "Prism Dolce", "name_th": "", "group": "BBB"},
    "Puroz": {"name_en": "Puroz", "name_th": "พูโรส", "group": "BBB"},
    "Purr": {"name_en": "Purretty", "name_th": "เพอร์เรตตี้", "group": "CTD"},
    "Q": {"name_en": "Q", "name_th": "คิว", "group": "BBB"},
    "Q.Mio": {"name_en": "Q.Mio", "name_th": "คิว.มิโอ้", "group": "BBB"},
    "Qiansoto": {"name_en": "Qiansoto", "name_th": "เชียนโซโต้", "group": "BBB"},
    "QLMJ": {"name_en": "QLMJ", "name_th": "", "group": "BBB"},
    "Qtica": {"name_en": "Qtica", "name_th": "คิวติก้า", "group": "BBB"},
    "RAN": {"name_en": "RAN", "name_th": "รัน", "group": "BBB"},
    "Rectskin": {"name_en": "Rectskin", "name_th": "", "group": "BBB"},
    "Richenna": {"name_en": "Richenna", "name_th": "รีชันน่า", "group": "BBB"},
    "Rolanjona": {"name_en": "Rolanjona", "name_th": "โรแลนโจน่า", "group": "BBB"},
    "Royalty": {"name_en": "Royalty", "name_th": "รอเยลตี้", "group": "BBB"},
    "RR": {"name_en": "Reunrom", "name_th": "รื่นรมย์", "group": "BBB"},
    "Rubaijin": {"name_en": "Rubaijin", "name_th": "รูไป่จิน", "group": "BBB"},
    "Sabina": {"name_en": "Sabina", "name_th": "ซาบีน่า", "group": ""},
    "Sariayu": {"name_en": "Sariayu", "name_th": "ซาเรียยู", "group": "BBB"},
    "Scandal": {"name_en": "Scandal", "name_th": "สแกนเดิล", "group": "BBB"},
    "Sea Zar": {"name_en": "Sea'Zar", "name_th": "ซีซาร์", "group": "CTD"},
    "Season Col": {"name_en": "Season Colour4", "name_th": "ซีซันคัลเลอร์โฟร์", "group": "BBB"},
    "Sembem": {"name_en": "Sembem", "name_th": "ซันเปิ่น", "group": "BBB"},
    "Seven Cat": {"name_en": "Seven Cat", "name_th": "เซเว่นแคท", "group": "BBB"},
    "Shijing": {"name_en": "Shijing", "name_th": "ชิจิง", "group": "BBB"},
    "Shills": {"name_en": "Shills", "name_th": "ชิลล์", "group": "BBB"},
    "Shining Gi": {"name_en": "Shining Girl", "name_th": "ไชนิ่งเกิร์ล", "group": "BBB"},
    "Shunda": {"name_en": "Shunda", "name_th": "ชุนดา", "group": "BBB"},
    "Singles": {"name_en": "Singles", "name_th": "ซิงเกิ้ล", "group": "BBB"},
    "SIRI ISSUE": {"name_en": "SIRI ISSUE", "name_th": "สิริอิชชู่", "group": ""},
    "SKINLOAD": {"name_en": "SKINLOAD", "name_th": "สกินโหลด", "group": ""},
    "SL": {"name_en": "Skynlab", "name_th": "สกินแล็บ", "group": "CTD"},
    "Small D": {"name_en": "Small D", "name_th": "สมอลล์ด๊อกเตอร์", "group": "BBB"},
    "Splat": {"name_en": "Splat", "name_th": "สแปลต", "group": ""},
    "ss": {"name_en": "ss", "name_th": "เอส เอส", "group": "BBB"},
    "ST": {"name_en": "Scente", "name_th": "เซนเต้", "group": ""},
    "StarReborn": {"name_en": "Star Reborn", "name_th": "สตาร์รีบอร์น", "group": "BBB"},
    "Sunnuts": {"name_en": "Sunnuts", "name_th": "ซันนัท", "group": "BBB"},
    "Supalai": {"name_en": "Supalai", "name_th": "ศุภาลัย", "group": ""},
    "Syndrome": {"name_en": "Syndrome", "name_th": "ซินดรอม", "group": "BBB"},
    "Szybio": {"name_en": "Szybio", "name_th": "เอสซีวายไบโอ", "group": "CTD"},
    "Tamago ha": {"name_en": "Tamago hada", "name_th": "ทามาโกะฮาดะ", "group": "BBB"},
    "THA": {"name_en": "THA BY NONGCHAT", "name_th": "ฑาบายน้องฉัตร", "group": "BBB"},
    "The Mask": {"name_en": "The Mask", "name_th": "เดอะมาส์ก", "group": "BBB"},
    "The Med": {"name_en": "The Med", "name_th": "เดอะเมด", "group": "BBB"},
    "The Rice": {"name_en": "The Rice", "name_th": "เดอะไรซ์", "group": "BBB"},
    "Tiannuo": {"name_en": "Tiannuo", "name_th": "เทียนนัว", "group": "BBB"},
    "Tiffanys": {"name_en": "Tiffany's Beaute", "name_th": "ทิฟฟานี โบเต้", "group": ""},
    "Tom Kui": {"name_en": "Tomkui x Haifusheng Brand", "name_th": "ต้มกุ๊ย x ไห่ฟู่เฉิง", "group": "CTD"},
    "Toshiba": {"name_en": "Toshiba", "name_th": "โตชิบา", "group": "BBB"},
    "Tous": {"name_en": "Tous", "name_th": "ทูส", "group": "BBB"},
    "TSR": {"name_en": "Thammachart Seafood x Baby Bright", "name_th": "ธรรมชาติซีฟู้ด x เบบี้ไบร์ท", "group": ""},
    "UMASK": {"name_en": "UMASK", "name_th": "ยูมาส์ก", "group": "BBB"},
    "UMix": {"name_en": "UMix", "name_th": "ยูมิกซ์", "group": "BBB"},
    "Vi Huong": {"name_en": "Vi Huong", "name_th": "วีฮอง", "group": "BBB"},
    "VitC & AHA": {"name_en": "VitC & AHA", "name_th": "วิทซีแอนด์เอเอชเอ", "group": "BBB"},
    "VM": {"name_en": "VM", "name_th": "วีเอ็ม", "group": "BBB"},
    "VOV": {"name_en": "VOV", "name_th": "วีโอวี", "group": "BBB"},
    "Vsoya": {"name_en": "Vsoya", "name_th": "วีโซย่า", "group": "BBB"},
    "White Beau": {"name_en": "White BEAUTY", "name_th": "ไวท์บิวตี้", "group": "BBB"},
    "Winks Doll": {"name_en": "Winks Doll", "name_th": "วินค์ดอลล์", "group": "BBB"},
    "Wuttisak": {"name_en": "Wuttisak", "name_th": "วุฒิศักดิ์", "group": "BBB"},
    "X & D": {"name_en": "X & D", "name_th": "เอ๊กซ์แอนด์ดี", "group": "BBB"},
    "XF": {"name_en": "XF", "name_th": "เอ็กซ์เอฟ", "group": "BBB"},
    "Xistan": {"name_en": "Xistan", "name_th": "ซิสแตท", "group": "BBB"},
    "Xueyinzi": {"name_en": "Xueyinzi", "name_th": "เสวียอิงจือ", "group": "BBB"},
    "XuoLiYinZi": {"name_en": "XuoLiYinZi", "name_th": "หัวลี่อินจื่อ", "group": "BBB"},
    "Y-CID": {"name_en": "Y-CID", "name_th": "วาย-ซีไอดี", "group": "BBB"},
    "YADAH": {"name_en": "YADAH", "name_th": "ยาดะ", "group": "BBB"},
    "Yalanbees": {"name_en": "Yalanbees", "name_th": "ยาลาบีส", "group": "BBB"},
    "Yalina": {"name_en": "Yalina", "name_th": "ยาลิน่า", "group": "BBB"},
    "Yan Lai": {"name_en": "Yan Lai Mei", "name_th": "ยานหลายเหม่ย", "group": "BBB"},
    "Yan Qi Na": {"name_en": "Yan Qi Na", "name_th": "หยานชิน่า", "group": "BBB"},
    "Yanyaxi": {"name_en": "Yanyaxi", "name_th": "ยานยาซิ", "group": "BBB"},
    "Yeoincheon": {"name_en": "Yeoincheonha", "name_th": "", "group": "BBB"},
    "YiFeiYang": {"name_en": "YiFeiYang", "name_th": "ยีเฟยหยาง", "group": "BBB"},
    "Yikai": {"name_en": "Yikai", "name_th": "", "group": "BBB"},
    "Yizhuang": {"name_en": "Yizhuang", "name_th": "อี้จวง", "group": "BBB"},
    "Zamian": {"name_en": "Zamian", "name_th": "ซาเมียน", "group": "BBB"},
    "Zamian.": {"name_en": "Zamian.", "name_th": "ซาเมียน", "group": "BBB"},
    "Zhenli": {"name_en": "Zhenli", "name_th": "เจินลี่", "group": "BBB"},
    "ZX": {"name_en": "ZHE X", "name_th": "ชีเอ็กซ์", "group": ""},
    "พีอิมเพรส": {"name_en": "P impression", "name_th": "พีอิมเพรสชั่น", "group": "BBB"},
    "เจียซั่ง": {"name_en": "เจียซั่งเหม่ย", "name_th": "เจียซั่งเหม่ย", "group": "BBB"},
    "เจ้าหญิง": {"name_en": "เจ้าหญิง", "name_th": "เจ้าหญิง", "group": "BBB"},
}


def fetch_brand_codes(engine: Engine, qualified_view: str) -> list[str]:
    """Distinct BRAND_CODE values a view has ever sold, for build_brand_context.

    Full history on purpose: a recent-only window drops brands that still have
    old sales (export: 68 -> 43 codes over 24 months), so questions about past
    years would come back as "brand not found". Takes ~3s (export) / ~18s (mkt).
    """
    with engine.connect() as conn:
        rows = conn.execute(
            text(f"SELECT DISTINCT BRAND_CODE FROM {qualified_view} WHERE BRAND_CODE IS NOT NULL")
        )
        return [row[0] for row in rows]


def sql_literal(code: str) -> str:
    """Oracle string literal matching a BRAND_CODE exactly as stored.

    Doubles single quotes (Is'SIE -> 'Is''SIE') and splices control characters
    in with CHR(), since the LLM can't be relied on to type a TAB.
    """
    parts: list[str] = []
    buf = ""
    for ch in code:
        if ord(ch) < 32:
            if buf:
                parts.append("'" + buf.replace("'", "''") + "'")
                buf = ""
            parts.append(f"CHR({ord(ch)})")
        else:
            buf += ch
    if buf or not parts:
        parts.append("'" + buf.replace("'", "''") + "'")
    return " || ".join(parts)


def brand_predicate(codes: Iterable[str], column: str = "BRAND_CODE") -> str:
    literals = [sql_literal(code) for code in codes]
    if len(literals) == 1:
        return f"{column} = {literals[0]}"
    return f"{column} IN ({', '.join(literals)})"


def build_brand_context(codes: Iterable[str] | None = None) -> str:
    """Prompt block that maps brand names to exact BRAND_CODE SQL.

    Pass the codes that actually occur in the agent's view to keep the prompt
    small; None renders every active brand (~370 lines).
    """
    selected = sorted(BRAND_CATALOG if codes is None else set(codes), key=str.lower)

    family_lines = "\n".join(
        f"- {spec['name_en']} / {spec['name_th']}: {brand_predicate(spec['brand_codes'])}"
        f"\n  ({spec['description']})"
        for spec in BRAND_FAMILIES.values()
    )
    brand_lines = "\n".join(
        f"- {sql_literal(code)}: {BRAND_CATALOG[code]['name_en']} / {BRAND_CATALOG[code]['name_th']}"
        if code in BRAND_CATALOG
        else f"- {sql_literal(code)}"
        for code in selected
    )
    return f"""BRAND_CODE (รหัสแบรนด์):
- กรองแบรนด์ด้วย BRAND_CODE เท่านั้น ใช้ค่าในรายการด้านล่างตามตัวอักษร ห้ามพิมพ์รหัสเอง
- ค่าบางตัวเป็นนิพจน์ SQL (เช่นมี || CHR(9)) ให้คัดลอกทั้งนิพจน์ไปใส่ใน = หรือ IN (...)
- ถ้าผู้ใช้พูดถึงแบรนด์ที่ไม่มีในรายการ ให้ตอบว่าไม่พบแบรนด์นั้น ห้ามเดารหัส
- BRAND_CODE อาจเป็น NULL เมื่อ GROUP BY แบรนด์ ให้แสดงเป็น "ไม่ระบุแบรนด์"

แบรนด์ที่มีหลายรหัส:
{family_lines}

รหัสแบรนด์ (literal SQL: ชื่ออังกฤษ / ชื่อไทย):
{brand_lines}
"""
