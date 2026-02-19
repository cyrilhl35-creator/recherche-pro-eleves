import re
import io
from datetime import datetime
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st
from fpdf import FPDF


APP_NAME = "Recherche Pro - Anti-Flemme Edition"


def init_state() -> None:
    """Initialise les variables de session."""
    defaults = {
        "student_name": "",
        "student_class": "",
        "topic": "",
        "questions": [],
        "keywords": [],
        "custom_sources": [],
        "note_intro": "",
        "note_facts": "",
        "note_expl": "",
        "note_examples": "",
        "note_cons": "",
        "note_sources": "",
        "start_time": datetime.now(),
        "dark_mode": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def apply_theme(dark_mode: bool) -> None:
    """Applique un style clair/sombre léger en CSS."""
    if dark_mode:
        bg = "#101417"
        card = "#1b2329"
        text = "#f3f6f8"
        accent = "#39d98a"
        warn = "#ffb020"
    else:
        bg = "#f6fbff"
        card = "#ffffff"
        text = "#14212b"
        accent = "#0068c9"
        warn = "#af6300"

    st.markdown(
        f"""
        <style>
        .stApp {{ background: {bg}; color: {text}; }}
        .block-container {{ padding-top: 1.2rem; }}
        .stMarkdown, .stText, .stCaption, p, li, label {{ color: {text} !important; }}
        .kpibox {{
            border-radius: 14px;
            background: {card};
            border: 1px solid rgba(120,120,120,0.25);
            padding: 0.75rem 1rem;
            margin-bottom: 0.8rem;
        }}
        .badge {{
            display: inline-block;
            border-radius: 999px;
            padding: 0.2rem 0.6rem;
            background: rgba(57,217,138,0.14);
            color: {accent};
            font-weight: 700;
            margin-right: 0.4rem;
        }}
        .warning-note {{ color: {warn}; font-weight: 700; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def tokenize(text: str) -> list[str]:
    """Découpe un texte en mots normalisés."""
    return re.findall(r"[a-zA-ZÀ-ÿ0-9']+", text.lower())


def word_count(text: str) -> int:
    return len(tokenize(text))


def generate_questions(topic: str) -> list[str]:
    """Génère des questions guidées pour structurer la recherche."""
    cleaned = topic.strip().rstrip(".?!")
    if not cleaned:
        return []
    return [
        f"Quel est le contexte historique/scientifique de \"{cleaned}\" ?",
        f"Quelles sont les causes ou origines principales de \"{cleaned}\" ?",
        f"Quels acteurs, auteurs ou éléments clés interviennent dans \"{cleaned}\" ?",
        f"Quelles dates, périodes ou étapes importantes faut-il retenir pour \"{cleaned}\" ?",
        f"Quelles conséquences (sociales, économiques, environnementales...) observe-t-on ?",
        f"Peut-on relier \"{cleaned}\" à des enjeux actuels en France ou dans le monde ?",
    ]


def generate_keywords(topic: str) -> list[str]:
    """Génère des mots-clés FR + EN pour élargir les recherches."""
    base_words = [w for w in tokenize(topic) if len(w) > 3]
    base_words = list(dict.fromkeys(base_words))
    seed = " ".join(base_words[:3]) if base_words else topic.lower()

    generic_fr = [
        f"{seed} définition",
        f"{seed} causes",
        f"{seed} conséquences",
        f"{seed} date clé",
        f"{seed} acteurs",
        f"{seed} chiffres INSEE",
        f"{seed} dossier pédagogique",
    ]
    generic_en = [
        f"{seed} overview",
        f"{seed} key facts",
        f"{seed} academic article",
        f"{seed} open access",
        f"{seed} case study",
    ]

    combined = []
    for kw in generic_fr + generic_en:
        cleaned = " ".join(kw.split())
        if cleaned and cleaned not in combined:
            combined.append(cleaned)
    return combined[:12]


def safe_latin(text: str) -> str:
    """Évite les erreurs d'encodage dans le PDF."""
    return text.encode("latin-1", errors="replace").decode("latin-1")


def similarity_ratio(note: str, source_bank: str) -> float:
    """Heuristique: proportion des mots de la note présents dans les sources."""
    note_words = tokenize(note)
    src_words = set(tokenize(source_bank))
    if not note_words or not src_words:
        return 0.0
    overlap = sum(1 for w in note_words if w in src_words)
    return overlap / max(len(note_words), 1)


def build_pdf_bytes(topic: str, reliability_stars: int, reliability_msg: str) -> bytes:
    """Construit un PDF récapitulatif téléchargeable."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.multi_cell(0, 10, safe_latin(APP_NAME))

    pdf.set_font("Arial", size=11)
    dt = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(0, 8, safe_latin(f"Date: {dt}"), ln=True)

    student = st.session_state["student_name"].strip() or "Non renseigné"
    sclass = st.session_state["student_class"].strip() or "Non renseignée"
    pdf.cell(0, 8, safe_latin(f"Élève: {student} | Classe: {sclass}"), ln=True)

    pdf.ln(3)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, safe_latin("Sujet"), ln=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7, safe_latin(topic))

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, safe_latin("Questions de recherche"), ln=True)
    pdf.set_font("Arial", size=11)
    for i, q in enumerate(st.session_state["questions"], start=1):
        pdf.multi_cell(0, 7, safe_latin(f"{i}. {q}"))

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, safe_latin("Mots-clés"), ln=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7, safe_latin("; ".join(st.session_state["keywords"])))

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, safe_latin("Notes"), ln=True)
    sections = {
        "Introduction": st.session_state["note_intro"],
        "Faits principaux": st.session_state["note_facts"],
        "Explications": st.session_state["note_expl"],
        "Exemples": st.session_state["note_examples"],
        "Conséquences": st.session_state["note_cons"],
        "Sources utilisées": st.session_state["note_sources"],
    }
    pdf.set_font("Arial", size=11)
    for title, content in sections.items():
        pdf.set_font("Arial", "B", 11)
        pdf.multi_cell(0, 7, safe_latin(title))
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 7, safe_latin(content or "(vide)"))

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, safe_latin("Sources listées"), ln=True)
    pdf.set_font("Arial", size=10)
    source_rows = default_sources(topic) + st.session_state["custom_sources"]
    for src in source_rows:
        pdf.multi_cell(0, 6, safe_latin(f"- {src['name']} : {src['url']}"))

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, safe_latin("Score fiabilité"), ln=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7, safe_latin(f"{reliability_stars}/5 étoiles - {reliability_msg}"))

    return bytes(pdf.output(dest="S"))


def default_sources(topic: str) -> list[dict]:
    """Sources fiables et liens pré-remplis."""
    q = quote_plus(topic)
    return [
        {"name": "BnF Gallica", "url": "https://gallica.bnf.fr", "tag": "archives"},
        {"name": "Persée", "url": "https://www.persee.fr", "tag": "revues"},
        {"name": "Cairn.info", "url": "https://www.cairn.info", "tag": "articles"},
        {"name": "Encyclopædia Universalis", "url": "https://www.universalis.fr", "tag": "encyclopédie"},
        {"name": "Google Scholar", "url": f"https://scholar.google.fr/scholar?q={q}", "tag": "académique"},
        {"name": "Semantic Scholar", "url": f"https://www.semanticscholar.org/search?q={q}", "tag": "académique"},
        {"name": "Éducation.gouv.fr", "url": "https://www.education.gouv.fr", "tag": "institutionnel"},
        {"name": "INSEE", "url": "https://www.insee.fr", "tag": "données"},
        {"name": "Wikipedia (départ uniquement ⚠️)", "url": f"https://fr.wikipedia.org/wiki/{q}", "tag": "starter"},
        {"name": "YouTube EDU", "url": "https://www.youtube.com/education", "tag": "vidéo"},
        {"name": "Lumni", "url": "https://www.lumni.fr", "tag": "vidéo"},
        {"name": "Kartable", "url": "https://www.kartable.fr", "tag": "soutien"},
    ]


def render_note_area(label: str, key: str, source_bank: str) -> None:
    """Affiche une zone de note avec compteur et alerte anti copier-coller."""
    st.session_state[key] = st.text_area(label, value=st.session_state[key], key=f"ta_{key}", height=150)
    wc = word_count(st.session_state[key])
    st.caption(f"📝 {wc} mots")

    ratio = similarity_ratio(st.session_state[key], source_bank)
    if ratio >= 0.70 and wc >= 40:
        st.error("⚠️ Cette section ressemble fortement à du copier-coller (>70% de mots similaires). Reformule avec tes propres mots.")
    elif wc >= 220:
        st.warning("⚠️ Paragraphe très long : pense à découper et reformuler pour rester clair.")


def reliability_block() -> tuple[int, str]:
    """Checklist anti-fake avec score final."""
    st.subheader("🛡️ Checklist anti-fake news")

    c1 = st.radio("Auteur identifié et date récente ?", ["👍 Oui", "👎 Non"], horizontal=True, key="chk1")
    c2 = st.radio("Le site paraît fiable (.gouv, .fr institutionnel, .edu, .org sérieux) ?", ["👍 Oui", "👎 Non"], horizontal=True, key="chk2")
    c3 = st.radio("Le contenu semble bourré de pubs/sponsorisé ?", ["👎 Oui", "👍 Non"], horizontal=True, key="chk3")
    c4 = st.radio("Plusieurs sources disent la même chose ?", ["👍 Oui", "👎 Non"], horizontal=True, key="chk4")

    score = 0
    score += 1 if c1 == "👍 Oui" else 0
    score += 1 if c2 == "👍 Oui" else 0
    score += 1 if c3 == "👍 Non" else 0
    score += 2 if c4 == "👍 Oui" else 0

    stars = max(1, min(5, score))
    star_line = "⭐" * stars + "☆" * (5 - stars)

    if stars >= 5:
        msg = "🚀 T'es un boss de la doc !"
        st.success(f"Fiabilité: {star_line} ({stars}/5) - {msg}")
    elif stars >= 3:
        msg = "🙂 Pas mal, encore un petit recoupement et c'est solide."
        st.info(f"Fiabilité: {star_line} ({stars}/5) - {msg}")
    else:
        msg = "⚠️ Attention, ça sent le fake news de TikTok... retape !"
        st.warning(f"Fiabilité: {star_line} ({stars}/5) - {msg}")

    return stars, msg


def main() -> None:
    st.set_page_config(page_title=APP_NAME, page_icon="📚", layout="wide")
    init_state()

    with st.sidebar:
        st.title("⚙️ Tableau de bord")
        dark = st.toggle("Mode sombre", value=st.session_state["dark_mode"])
        st.session_state["dark_mode"] = dark

        elapsed = datetime.now() - st.session_state["start_time"]
        mins = int(elapsed.total_seconds() // 60)
        secs = int(elapsed.total_seconds() % 60)
        st.markdown(f"### ⏱️ Temps passé\n**{mins:02d}:{secs:02d}**")
        st.caption("Clique n'importe où pour actualiser le timer en live.")

        st.markdown("### 💡 Tips rapides")
        tips = [
            "Toujours vérifier la date de publication.",
            "Recouper une info avec au moins 2 sources.",
            "Ne cite pas Wikipedia comme source finale.",
            "Note les URLs exactes dès que tu trouves une info utile.",
        ]
        for t in tips:
            st.write(f"- {t}")

    apply_theme(st.session_state["dark_mode"])

    st.title("📚 Recherche Pro - Anti-Flemme Edition")
    st.caption("Respire, pas de panique, on structure ça ensemble !")

    col_a, col_b, col_c = st.columns([2, 1, 1])
    with col_a:
        topic = st.text_input(
            "🎯 Ton sujet scolaire",
            value=st.session_state["topic"],
            placeholder="Ex: Les causes de la Première Guerre mondiale",
        )
    with col_b:
        student_name = st.text_input("👤 Nom / Prénom (optionnel)", value=st.session_state["student_name"])
    with col_c:
        student_class = st.text_input("🏫 Classe (optionnel)", value=st.session_state["student_class"], placeholder="Ex: 3e B")

    st.session_state["topic"] = topic
    st.session_state["student_name"] = student_name
    st.session_state["student_class"] = student_class

    if st.button("🚀 Générer mon plan de recherche", use_container_width=True):
        if topic.strip():
            st.session_state["questions"] = generate_questions(topic)
            st.session_state["keywords"] = generate_keywords(topic)
            st.success("T'es en train de cartonner ta recherche !")
        else:
            st.error("Indique d'abord un sujet.")

    if st.session_state["topic"].strip() and not st.session_state["questions"]:
        st.session_state["questions"] = generate_questions(st.session_state["topic"])
        st.session_state["keywords"] = generate_keywords(st.session_state["topic"])

    if st.session_state["questions"]:
        st.subheader("🧭 Questions guidées (5-7)")
        for i, q in enumerate(st.session_state["questions"], start=1):
            st.markdown(f"<div class='kpibox'><span class='badge'>Q{i}</span>{q}</div>", unsafe_allow_html=True)

        st.subheader("🔎 Mots-clés utiles (FR + EN)")
        st.write(" | ".join([f"`{k}`" for k in st.session_state["keywords"]]))

        st.subheader("🌐 Sources fiables recommandées")
        sources = default_sources(st.session_state["topic"])
        df = pd.DataFrame(sources)
        st.dataframe(df[["name", "tag", "url"]], use_container_width=True, hide_index=True)

        for src in sources:
            if "Wikipedia" in src["name"]:
                st.markdown(f"- [{src['name']}]({src['url']}) - **⚠️ juste pour démarrer, pas citer !**")
            else:
                st.markdown(f"- [{src['name']}]({src['url']})")

        with st.expander("➕ Ajoute ta source perso"):
            custom_name = st.text_input("Nom de la source", placeholder="Ex: Article Le Monde")
            custom_url = st.text_input("URL de la source", placeholder="https://...")
            custom_excerpt = st.text_area(
                "Extrait de la source (optionnel, pour détecter le copier-coller)",
                placeholder="Colle ici un petit extrait du texte consulté.",
                height=110,
            )
            if st.button("Ajouter cette source"):
                if custom_url.strip():
                    st.session_state["custom_sources"].append(
                        {
                            "name": custom_name.strip() or "Source perso",
                            "url": custom_url.strip(),
                            "tag": "perso",
                            "excerpt": custom_excerpt.strip(),
                        }
                    )
                    st.success("Source ajoutée ✅")
                else:
                    st.warning("Ajoute au moins une URL.")

        if st.session_state["custom_sources"]:
            st.markdown("**Tes sources perso :**")
            for i, src in enumerate(st.session_state["custom_sources"], start=1):
                st.markdown(f"{i}. [{src['name']}]({src['url']})")

        st.subheader("🧠 Prise de notes structurée")
        source_text_bank = " ".join([s.get("excerpt", "") for s in st.session_state["custom_sources"]])

        tabs = st.tabs(
            [
                "Introduction",
                "Faits principaux",
                "Explications",
                "Exemples",
                "Conséquences",
                "Sources utilisées",
            ]
        )

        with tabs[0]:
            render_note_area("Rédige ton introduction", "note_intro", source_text_bank)
        with tabs[1]:
            render_note_area("Liste les faits principaux", "note_facts", source_text_bank)
        with tabs[2]:
            render_note_area("Explique le phénomène", "note_expl", source_text_bank)
        with tabs[3]:
            render_note_area("Ajoute des exemples concrets", "note_examples", source_text_bank)
        with tabs[4]:
            render_note_area("Note les conséquences", "note_cons", source_text_bank)
        with tabs[5]:
            render_note_area("Trace les sources réellement utilisées", "note_sources", source_text_bank)

        st.subheader("🖼️ Bonus image (facultatif)")
        st.caption("Option 100% gratuite: colle un lien image libre ou utilise Unsplash Source (internet requis).")
        img_url = st.text_input(
            "URL image (optionnel)",
            placeholder="https://images.unsplash.com/... ou https://source.unsplash.com/1600x900/?histoire",
        )
        if img_url.strip():
            st.image(img_url.strip(), caption="Illustration du sujet", use_container_width=True)

        stars, msg = reliability_block()

        st.subheader("📄 Export final")
        if st.button("Génère mon dossier PDF", use_container_width=True):
            pdf_bytes = build_pdf_bytes(st.session_state["topic"], stars, msg)
            filename = f"dossier_recherche_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            st.download_button(
                "⬇️ Télécharger le PDF",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
            )

    st.markdown("---")
    st.caption("App locale/offline-friendly: aucune API payante obligatoire.")


if __name__ == "__main__":
    main()
