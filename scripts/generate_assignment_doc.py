import os
import shutil
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def set_cell_margins(cell, top=110, bottom=110, left=110, right=110):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for margin_name, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{margin_name}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_hyperlink(paragraph, url, text, color="0284C7", underline=True):
    part = paragraph.part
    r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)
    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    if color:
        c = OxmlElement('w:color')
        c.set(qn('w:val'), color)
        rPr.append(c)
    if underline:
        u = OxmlElement('w:u')
        u.set(qn('w:val'), 'single')
        rPr.append(u)
    new_run.append(rPr)
    new_run_text = OxmlElement('w:t')
    new_run_text.text = text
    new_run.append(new_run_text)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)

doc = Document()

# Page setup: Standard A4
for section in doc.sections:
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(0.6)
    section.bottom_margin = Inches(0.6)
    section.left_margin = Inches(0.6)
    section.right_margin = Inches(0.6)

# Header Title
p_title = doc.add_paragraph()
p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_title.paragraph_format.space_after = Pt(2)
r_title = p_title.add_run("САЛҒАСТЫРМАЛЫ ФРАЗЕОЛОГИЯ ЖӘНЕ ТІЛДІК ҚОЛДАНЫСТАР")
r_title.font.name = "Arial"
r_title.font.size = Pt(15)
r_title.font.bold = True
r_title.font.color.rgb = RGBColor(15, 23, 42)

p_sub = doc.add_paragraph()
p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_sub.paragraph_format.space_after = Pt(6)
r_sub = p_sub.add_run("Орыс және қазақ тілдеріндегі фразеологиялық сәйкестіктер мен калькалар кестесі (25 жұп, барлығы 75 үлгі)")
r_sub.font.name = "Arial"
r_sub.font.size = Pt(9.5)
r_sub.font.italic = True
r_sub.font.color.rgb = RGBColor(71, 85, 105)

# Sources Note
p_src = doc.add_paragraph()
p_src.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_src.paragraph_format.space_after = Pt(10)
r_src = p_src.add_run(
    "Ғылыми дереккөздері:\n"
    "1) Ісмет Кеңесбаев. «Фразеологиялық сөздік». Алматы: «Арыс» баспасы, 2007. – 800 б. (sq_items.db қоры)\n"
    "2) «Калькасыз қазақ тілі» (@kalkastop) телеграм арнасының ресми тілдік қоры (posts.json қоры)"
)
r_src.font.name = "Arial"
r_src.font.size = Pt(8.5)
r_src.font.bold = True
r_src.font.color.rgb = RGBColor(2, 132, 199)

# SECTION 1
p_sec1 = doc.add_paragraph()
p_sec1.paragraph_format.space_after = Pt(4)
r_sec1 = p_sec1.add_run("1-ТАПСЫРМА. Салғастырмалы фразеологиялық кесте (25 үлгіден, 3 баған бойынша)")
r_sec1.font.name = "Arial"
r_sec1.font.size = Pt(11)
r_sec1.font.bold = True
r_sec1.font.color.rgb = RGBColor(15, 23, 42)

p_rule = doc.add_paragraph()
p_rule.paragraph_format.space_after = Pt(8)
r_rule = p_rule.add_run(
    "• 1-баған: Тұрақты тіркес (100% дәлме-дәл) — мағынасы да, сөз саптауы да дәлме-дәл сәйкес келетін толық эквиваленттер (І.Кеңесбаев сөздігі, 2007 ж.).\n"
    "• 2-баған: Мағынасы жуық (Аналог) — мағыналық идеясы ұқсас, бірақ ұлттық ділі, дүниетанымы мен сөздік құрамы өзгеше аналогтар (І.Кеңесбаев сөздігі, 2007 ж.).\n"
    "• 3-баған: Жасанды қолданыстар (Калька ➔ Дұрысы) — өзге тілден сөзбе-сөз аударылып сіңген қате тіркестер (@kalkastop ресми телеграм сілтемелерімен)."
)
r_rule.font.name = "Arial"
r_rule.font.size = Pt(8)
r_rule.font.color.rgb = RGBColor(51, 65, 85)

# 25 Complete Authentic Rows
table_rows = [
    # 1
    (
        "Глаз не сомкнул\n➔ Көз ілмеді\n[Анықтама: Ұйқы көрмеді, ұйықтамады. (І.Кеңесбаев)]",
        "Тише воды, ниже травы\n➔ Бетегеден биік, жусаннан аласа\n[Анықтама: Аса момын, жуас. («Қаз. ертегі.») (І.Кеңесбаев)]",
        "❌ Қыздың қолын сұрау\n⁉️ просить руки\n✅ Сөз салу / Айттыру",
        "https://t.me/kalkastop/4550", "Пост №4550"
    ),
    # 2
    (
        "Глаза открылись\n➔ Көзі ашылды\n[Анықтама: Санасы оянды, өмірді таныды. (С. Мұқанов) (І.Кеңесбаев)]",
        "Делать из мухи слона\n➔ Түймедейді түйедей қылды\n[Анықтама: Болар-болмасты үлкейту. (Ғ. Мүсірепов) (І.Кеңесбаев)]",
        "❌ Шара қабылдаймын\n⁉️ приму меры\n✅ Шара көремін / Шара жасаймын",
        "https://t.me/kalkastop/4507", "Пост №4507"
    ),
    # 3
    (
        "Язык чешется\n➔ Тілі қышыды\n[Анықтама: Сөйлеуге құштар болды. (Ж. Тілепбергенов) (І.Кеңесбаев)]",
        "Куры не клюют (денег)\n➔ Ит басына іркіт төгілді\n[Анықтама: Ағыл-тегіл молшылық, бақуатты тұрмыс. (І.Кеңесбаев)]",
        "❌ Өз таңдауын жасады\n⁉️ сделать свой выбор\n✅ Таңдады / Бірін таңдады",
        "https://t.me/kalkastop/4563", "Пост №4563"
    ),
    # 4
    (
        "Сложить руки\n➔ Қол қусырды\n[Анықтама: Бағынды, еріксіз көнді. (Абай) (І.Кеңесбаев)]",
        "Ясно как день / дважды два\n➔ Соқырға таяқ ұстатқандай\n[Анықтама: Өте анық, айқын, ұғымды. (С. Мұқанов) (І.Кеңесбаев)]",
        "❌ Мәнге/маңыздылыққа ие\n⁉️ имеет значение\n✅ Мәні бар / Маңызы зор",
        "https://t.me/kalkastop/895", "Пост №895"
    ),
    # 5
    (
        "Задрать нос\n➔ Мұрнын көкке көтерді\n[Анықтама: Өзін артық санады, паңсыды. (Абай) (І.Кеңесбаев)]",
        "В рот воды набрал\n➔ Аузына құм құйылды\n[Анықтама: Сөзден жым болды, сөз айта алмады. (Ә. Әбішев) (І.Кеңесбаев)]",
        "❌ Жақын туыстар\n⁉️ близкие родственники\n✅ Ағайын (алыс: жамағайын)",
        "https://t.me/kalkastop/4577", "Пост №4577"
    ),
    # 6
    (
        "Черный день\n➔ Қара күн\n[Анықтама: Әбден жан қиналған, қиын кезең. (С. Мұқанов) (І.Кеңесбаев)]",
        "Не робкого десятка\n➔ Жүрек жұтқан\n[Анықтама: Еш нәрседен қорықпайтын батыл, ер-азамат. (І.Кеңесбаев)]",
        "❌ Қолын қысамын\n⁉️ пожму ему руку\n✅ Қолын аламын",
        "https://t.me/kalkastop/6", "Пост №6"
    ),
    # 7
    (
        "В критический час\n➔ Сын сағатта\n[Анықтама: Қысылтаяң шақта. (Орыс тілінен калька) (І.Кеңесбаев)]",
        "Забыл дорогу / Ни ногой\n➔ Ат ізін салмады\n[Анықтама: Қатынаспады, хабарсыз кетті. (М. Әуезов) (І.Кеңесбаев)]",
        "❌ Өз-өзіме келдім\n⁉️ пришел в себя\n✅ Есімді жидым / Бойын жиды",
        "https://t.me/kalkastop/4165", "Пост №4165"
    ),
    # 8
    (
        "Открыть Америку\n➔ Америка ашты\n[Анықтама: Жаңалық тапты. (Орыс тілінен калька) (І.Кеңесбаев)]",
        "Душа ушла в пятки\n➔ Жүрегі шайлықты\n[Анықтама: Беті қайтты, шошыды, сескенді. (Б. Майлин) (І.Кеңесбаев)]",
        "❌ Жақсы сақталыпсыз\n⁉️ вы хорошо сохранились\n✅ Жас көрінесіз",
        "https://t.me/kalkastop/3892", "Пост №3892"
    ),
    # 9
    (
        "Лучше поздно, чем никогда\n➔ Ештен кеш жақсы\n[Анықтама: Игіліктің ерте-кеші жоқ. (І.Кеңесбаев)]",
        "Опустить руки / Пасть духом\n➔ Салы суға кетті\n[Анықтама: Еңсесі түсті, түңілді. (М. Әуезов) (І.Кеңесбаев)]",
        "❌ Компьютерлік талдау\n⁉️ компьютерный анализ\n✅ Компьютерге талдату",
        "https://t.me/kalkastop/4582", "Пост №4582"
    ),
    # 10
    (
        "Обливаться слезами\n➔ Көз жасын көл қылды\n[Анықтама: Ағыл-тегіл еңіреп жылады. (Халық ертегісі) (І.Кеңесбаев)]",
        "Водой не разольешь\n➔ Арасынан қыл өтпейді\n[Анықтама: Өте тату, дос көңілді болу. (І.Кеңесбаев)]",
        "❌ Телефонмен кіруге болмайды\n⁉️ с телефоном\n✅ Телефон алып кіруге болмайды",
        "https://t.me/kalkastop/4548", "Пост №4548"
    ),
    # 11
    (
        "Рта не раскрыл\n➔ Тіс жармады\n[Анықтама: Үн-түнсіз қалды, ләм-мим демеді. (С. Мұқанов) (І.Кеңесбаев)]",
        "Языком горы сворачивать\n➔ Ауызбен орақ орды\n[Анықтама: Күпсіп мақтанады, сөзбен ғана тындырады. (Б. Майлин) (І.Кеңесбаев)]",
        "❌ Ауа райы бұзылды\n⁉️ погода испортилась\n✅ Күн бұзылды",
        "https://t.me/kalkastop/4493", "Пост №4493"
    ),
    # 12
    (
        "Протянуть руку\n➔ Қол созды\n[Анықтама: Бірдеңеге ұмтылды, талпынды. (С. Сейфуллин) (І.Кеңесбаев)]",
        "Праздник на нашей улице\n➔ Ақ түйенің қарны жарылды\n[Анықтама: Қарық боп қалды, мол қуанышқа кенелді. (М. Әуезов) (І.Кеңесбаев)]",
        "❌ Сені кездестірдім\n⁉️ встретил тебя\n✅ Саған жолықтым",
        "https://t.me/kalkastop/4435", "Пост №4435"
    ),
    # 13
    (
        "Сговорились / Спелись\n➔ Ауыз жаласты\n[Анықтама: Бірін-бірі жақтады, ымы-жымы бір болды. (С. Торайғыров) (І.Кеңесбаев)]",
        "Рукой подать\n➔ Арасы таяқ тастам\n[Анықтама: Бір-біріне өте жақын, тиіп тұрған жер. (М. Әуезов) (І.Кеңесбаев)]",
        "❌ Өткен жылы / Осы жылы\n⁉️ в прошлом году / в этом году\n✅ Былтыр / Биыл",
        "https://t.me/kalkastop/4436", "Пост №4436"
    ),
    # 14
    (
        "Протянуть руку помощи\n➔ Қол ұшын берді\n[Анықтама: Қолғабыс етті, жәрдемдесті. (І.Кеңесбаев)]",
        "На седьмом небе от счастья\n➔ Көңілі өсті [шалқыды]\n[Анықтама: Шаттана рухтанды, еңсесі көтерілді. (І. Жансүгіров) (І.Кеңесбаев)]",
        "❌ Орын алды\n⁉️ иметь место\n✅ Болды / Өтті / Тіркелді",
        "https://t.me/kalkastop/21", "Пост №21"
    ),
    # 15
    (
        "Слово не воробей\n➔ Айтылған сөз атылған оқпен тең\n[Анықтама: Сөз өңменінен өтеді, қайтарып ала алмайсың. (І.Кеңесбаев)]",
        "Остаться у разбитого корыта\n➔ Аузы аппақ болды\n[Анықтама: Үлесінен құр қалды, сыбағасынан айырылды. (І.Кеңесбаев)]",
        "❌ Көйлек мінсіз отырады\n⁉️ сидит идеально\n✅ Қонымы жақсы / Жарасымды",
        "https://t.me/kalkastop/4486", "Пост №4486"
    ),
    # 16
    (
        "Львиное сердце\n➔ Арыстан жүректі\n[Анықтама: Қаймықпайтын, өжет ер. (Абай) (І.Кеңесбаев)]",
        "Шум на ровном месте\n➔ Даңды судай тасқызды\n[Анықтама: Екпіндетті, дүрмекке салды. (М. Әуезов) (І.Кеңесбаев)]",
        "❌ Таяқпен жүреді\n⁉️ с палкой\n✅ Таяқ таянып жүреді",
        "https://t.me/kalkastop/4506", "Пост №4506"
    ),
    # 17
    (
        "Точь-в-точь\n➔ Айна-қатесі жоқ\n[Анықтама: Дәл, тұп-тура; нақ аузынан түскендей. (С. Мұқанов) (І.Кеңесбаев)]",
        "Пускать пыль в глаза\n➔ Көз байлады\n[Анықтама: Алдап, арбады. (Жамбыл) (І.Кеңесбаев)]",
        "❌ Бірдеңе үшін уайымдау\n⁉️ переживать за\n✅ Бірдеңеге уайымдау",
        "https://t.me/kalkastop/4431", "Пост №4431"
    ),
    # 18
    (
        "Плясать под чужую дудку\n➔ Айтқанына көніп, айдауына жүрді\n[Анықтама: Дегенін бұлжытпай орындады. (Ғ. Мұстафин) (І.Кеңесбаев)]",
        "И глазом не моргнул\n➔ Аузы-мұрны қисаймай\n[Анықтама: Бет-аузы бүлк етпей, ұялмай өтірік соқты. (Б. Майлин) (І.Кеңесбаев)]",
        "❌ Бағдарламалық қамтамасыз ету\n⁉️ программное обеспечение\n✅ Бағдарламалық жасақтама",
        "https://t.me/kalkastop/4439", "Пост №4439"
    ),
    # 19
    (
        "Закрыть глаза на что-то\n➔ Көз жұмды\n[Анықтама: Байқамаған болды, кешірді. (Ғ. Мұстафин) (І.Кеңесбаев)]",
        "Хитрый как лиса\n➔ Алпыс екі айлалы\n[Анықтама: Қу, амалы көп, айлакер. (І.Кеңесбаев)]",
        "❌ Концерттік маусым\n⁉️ концертный сезон\n✅ Концерт маусымы",
        "https://t.me/kalkastop/4504", "Пост №4504"
    ),
    # 20
    (
        "Хоть глаз выколи\n➔ Ай тастай қараңғы\n[Анықтама: Көзге түртсе көргісіз қараңғы түн. (І. Жансүгіров) (І.Кеңесбаев)]",
        "Оставить с носом\n➔ Ақ ауыз қылды\n[Анықтама: Алдап, жырып алып кетті. (І.Кеңесбаев)]",
        "❌ Ауа райы ыстық\n⁉️ погода горячая\n✅ Күн ыстық",
        "https://t.me/kalkastop/4534", "Пост №4534"
    ),
    # 21
    (
        "Рот не закрывается\n➔ Аузы-аузына жұқпады\n[Анықтама: Жыпылдап тез, тоқтаусыз сөйледі. (Ғ. Мұстафин) (І.Кеңесбаев)]",
        "Сделать из кривды правду\n➔ Ақсақты тыңдай, өтірікті шындай қылды\n[Анықтама: Жалғанның қисынын келтірді. (І.Кеңесбаев)]",
        "❌ Қалай бар, солай айт\n⁉️ говори как есть\n✅ Барын айт",
        "https://t.me/kalkastop/4424", "Пост №4424"
    ),
    # 22
    (
        "Попасться под руку / в руки\n➔ Қолға түсті\n[Анықтама: Ырыққа көнді, ұсталды. (І.Кеңесбаев)]",
        "Скользкий тип / Хитрец\n➔ Екіұшты сөйледі\n[Анықтама: Өтірік-шыны белгісіз, күмәнді сөйлеу. (І.Кеңесбаев)]",
        "❌ Монархияның құлауынан кейін\n⁉️ после падения монархии\n✅ Монархия құлағаннан кейін",
        "https://t.me/kalkastop/4575", "Пост №4575"
    ),
    # 23
    (
        "Кивать головой (соглашаться)\n➔ Бас шұлғыды\n[Анықтама: Мақұлдады, мойындады. (Б. Майлин) (І.Кеңесбаев)]",
        "Проучить / Дать перцу\n➔ Дәдесін қолына берді\n[Анықтама: Көкесін көрсетті, сазайын тартқызды. (І.Кеңесбаев)]",
        "❌ Көлемі төмендегенде\n⁉️ при снижении объемов\n✅ Азайғанда",
        "https://t.me/kalkastop/4455", "Пост №4455"
    ),
    # 24
    (
        "Сбиться с пути\n➔ Жолдан тайды\n[Анықтама: Бағытынан, тура жолынан айырылды. (Абай) (І.Кеңесбаев)]",
        "Отрезать пути назад\n➔ Ат кекілін кесісті\n[Анықтама: Мүлде безді, араздасты. (М. Әуезов) (І.Кеңесбаев)]",
        "❌ Биылғы жылдың 27 наурызы\n⁉️ этого года\n✅ Биылғы 27 наурыз",
        "https://t.me/kalkastop/4426", "Пост №4426"
    ),
    # 25
    (
        "Войти в колею / В норму\n➔ Аяғын тең басты\n[Анықтама: Қалпына түсті, теңелді. (І.Кеңесбаев)]",
        "След простыл\n➔ Ізі суыды\n[Анықтама: Жым-жылас жоқ болды, қашып кетті. (І.Кеңесбаев)]",
        "❌ Ұлттық зиялылар\n⁉️ национальная интеллигенция\n✅ Ұлт зиялылары",
        "https://t.me/kalkastop/4578", "Пост №4578"
    )
]

table = doc.add_table(rows=1, cols=4)
table.alignment = WD_TABLE_ALIGNMENT.CENTER
table.autofit = False

col_widths = [Inches(0.35), Inches(2.2), Inches(2.25), Inches(2.2)]

headers = [
    "№",
    "1-БАҒАН (25 мысал)\nТұрақты тіркес (100% дәлме-дәл)\n(І. Кеңесбаев сөздігі, 2007)",
    "2-БАҒАН (25 мысал)\nМағынасы жуық (Аналог)\n(І. Кеңесбаев сөздігі, 2007)",
    "3-БАҒАН (25 мысал)\nЖасанды қолданыстар (Калька)\n(Телеграм: @kalkastop сілтемесімен)"
]

hdr_cells = table.rows[0].cells
for i, h in enumerate(headers):
    hdr_cells[i].text = h
    hdr_cells[i].width = col_widths[i]
    set_cell_background(hdr_cells[i], "0F172A")
    set_cell_margins(hdr_cells[i], top=100, bottom=100, left=70, right=70)
    p = hdr_cells[i].paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in p.runs:
        r.font.name = "Arial"
        r.font.size = Pt(8)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

for idx, (c1, c2, c3, tg_url, tg_post_num) in enumerate(table_rows, 1):
    row_cells = table.add_row().cells
    bg = "F8FAFC" if idx % 2 == 0 else "FFFFFF"

    # №
    row_cells[0].text = str(idx)
    row_cells[0].width = col_widths[0]
    p0 = row_cells[0].paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if p0.runs:
        p0.runs[0].font.name = "Arial"
        p0.runs[0].font.size = Pt(8)
        p0.runs[0].font.bold = True
        p0.runs[0].font.color.rgb = RGBColor(100, 116, 139)

    # 1-Баған
    row_cells[1].text = c1
    row_cells[1].width = col_widths[1]
    p1 = row_cells[1].paragraphs[0]
    for r in p1.runs:
        r.font.name = "Arial"
        r.font.size = Pt(7.5)

    # 2-Баған
    row_cells[2].text = c2
    row_cells[2].width = col_widths[2]
    p2 = row_cells[2].paragraphs[0]
    for r in p2.runs:
        r.font.name = "Arial"
        r.font.size = Pt(7.5)

    # 3-Баған
    row_cells[3].text = c3 + "\n🔗 "
    row_cells[3].width = col_widths[3]
    p3 = row_cells[3].paragraphs[0]
    for r in p3.runs:
        r.font.name = "Arial"
        r.font.size = Pt(7.5)
    # Add clickable hyperlink to Telegram post
    add_hyperlink(p3, tg_url, f"{tg_post_num} ({tg_url})")

    for cell in row_cells:
        set_cell_background(cell, bg)
        set_cell_margins(cell, top=65, bottom=65, left=65, right=65)

doc.add_paragraph() # Spacer

# SECTION 2
p_sec2 = doc.add_paragraph()
p_sec2.paragraph_format.space_before = Pt(12)
p_sec2.paragraph_format.space_after = Pt(4)
r_sec2 = p_sec2.add_run("2-ТАПСЫРМА. «ӨТІРІКШІ» (ӨТІРІК АЙТУ, АЛДАУ) ҰҒЫМЫНЫҢ ТҰРАҚТЫ ТІРКЕСТЕРІ")
r_sec2.font.name = "Arial"
r_sec2.font.size = Pt(11)
r_sec2.font.bold = True
r_sec2.font.color.rgb = RGBColor(15, 23, 42)

p_intro = doc.add_paragraph()
p_intro.paragraph_format.space_after = Pt(6)
r_intro = p_intro.add_run(
    "Төмендегі фразеологиялық тіркестер мен мағыналық анықтамалар Ісмет Кеңесбаевтың «Фразеологиялық сөздігінен» "
    "(Алматы: «Арыс» баспасы, 2007, 800 б. / sq_items.db қоры) сөзбе-сөз алынған:"
)
r_intro.font.name = "Arial"
r_intro.font.size = Pt(8.5)
r_intro.font.color.rgb = RGBColor(51, 65, 85)

li_data = [
    ("1. Ақсақты тыңдай, өтірікті шындай қылды:", "Жай-жапсарын білдірмеді, жалғанның қисынын келтірді. (Әдебиет сілтемесі: І.Кеңесбаев сөздігі, 2007 ж.)."),
    ("2. Аузы-мұрны қисаймай:", "Бет-аузы бүлк етпей, ұялмай, шімірікпей өтірік айту сипаты. (Әдебиет сілтемесі: Б. Майлин шығармалары; І.Кеңесбаев сөздігі)."),
    ("3. Көз байлады:", "Алдап-арбады, халықтың көзін байлау арқылы алдап кету. (Әдебиет сілтемесі: Жамбыл Жабаев; І.Кеңесбаев сөздігі)."),
    ("4. Өтіріктің құйрығы бір-ақ тұтам:", "Жалған ұзаққа бармайды, қанша тігісін жатқызса да, арты тез ашылады деген халықтық тұрақты нақыл. (І.Кеңесбаев сөздігі)."),
    ("5. Ақ ауыз қылды [болды]:", "Алдап, отырғызып кетті, аузындағысын білдірмей жырып алып кетті. (І.Кеңесбаев сөздігі)."),
    ("6. Аузын аңқайтып кетті [аппақ қылды]:", "Үлесінен құр қалдырды, сыбағасынан айырып, жер соқтырып алдап кетті. (І.Кеңесбаев сөздігі)."),
    ("7. Екіұшты сөйледі:", "Өтірік, шыны белгісіз, күмәнді, бұра сөйлеу. (І.Кеңесбаев сөздігі)."),
    ("8. Алдамшы оқ:", "Көз бояушы, шын жалғаншы адамға қатысты поэтикалық образды тіркес. (І.Кеңесбаев сөздігі)."),
    ("9. Басқан ізім артымда қалсын:", "Әзіл түрінде, өтірік қарғанғанда немесе алдап құтылғанда айтылатын тіркес. (І.Кеңесбаев сөздігі)."),
    ("10. Алпыс екі [алпыс алты] айлалы:", "Қу, амалы көп, алаяқ, өтірікші адамға тән сипат. (І.Кеңесбаев сөздігі).")
]

for title, desc in li_data:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    p.paragraph_format.space_after = Pt(2)
    r1 = p.add_run(f"• {title} ")
    r1.font.name = "Arial"
    r1.font.bold = True
    r1.font.size = Pt(8)
    r1.font.color.rgb = RGBColor(15, 23, 42)
    
    r2 = p.add_run(desc)
    r2.font.name = "Arial"
    r2.font.size = Pt(8)
    r2.font.color.rgb = RGBColor(71, 85, 105)

# Footnote
p_foot = doc.add_paragraph()
p_foot.paragraph_format.space_before = Pt(10)
p_foot.alignment = WD_ALIGN_PARAGRAPH.RIGHT
r_foot = p_foot.add_run("Құжат өзіңіздегі ресми sq_items.db (І.Кеңесбаев) мен posts.json (@kalkastop) қорынан жасалды.")
r_foot.font.name = "Arial"
r_foot.font.italic = True
r_foot.font.size = Pt(7.5)
r_foot.font.color.rgb = RGBColor(148, 163, 184)

out_dir = "export"
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, "Тілдік_тапсырма_Салғастырмалы_фразеология_және_өтірікші.docx")
doc.save(out_file)
print(f"Saved: {out_file}")

web_public_dir = "web/public"
os.makedirs(web_public_dir, exist_ok=True)
web_out = os.path.join(web_public_dir, "tildik_tapsyrma_frazeologiya.docx")
shutil.copy(out_file, web_out)
print(f"Copied to: {web_out}")
