import streamlit as st

def run_HDJ():
    st.title("HDJ – Effets secondaires des traitements")

    # ---------------------------
    # Dictionnaire complet des médicaments
    # ---------------------------
    hdj_drugs = {
        "ENDOXAN® (Cyclophosphamide IV)": {
            "COURT TERME (heures → jours)": {
                "Mineurs": [
                    "Nausées, vomissements légers",
                    "Asthénie transitoire",
                    "Céphalées",
                    "Bouffées vasomotrices",
                    "Goût métallique",
                    "Douleurs au point de perfusion"
                ],
                "Modérés": [
                    "Vomissements incoercibles",
                    "Anorexie",
                    "Diarrhée",
                    "Alopécie précoce (dès 2–3 semaines)",
                    "Leucopénie modérée",
                    "Thrombopénie modérée"
                ],
                "Majeurs": [
                    "Réaction anaphylactique (rare)",
                    "Myélosuppression aiguë sévère",
                    "Neutropénie fébrile",
                    "Infections bactériennes sévères précoces",
                    "Toxicité cardiaque aiguë (rare mais grave, surtout fortes doses)"
                ]
            },
            "MOYEN TERME (semaines → mois)": {
                "Mineurs": [
                    "Alopécie persistante",
                    "Fatigue chronique",
                    "Troubles digestifs persistants",
                    "Infections bénignes récidivantes"
                ],
                "Modérés": [
                    "Leucopénie prolongée",
                    "Anémie / thrombopénie persistantes",
                    "Aménorrhée transitoire",
                    "Oligospermie",
                    "Cystite chimique modérée",
                    "Cytolyse hépatique modérée"
                ],
                "Majeurs": [
                    "Cystite hémorragique (acroléine)",
                    "Infections opportunistes",
                    "Insuffisance ovarienne prématurée",
                    "Infertilité masculine",
                    "Atteinte pulmonaire interstitielle toxique",
                    "Toxicité cardiaque retardée"
                ]
            },
            "LONG TERME (mois → années)": {
                "Mineurs": [
                    "Asthénie prolongée",
                    "Séquelles esthétiques (alopécie définitive rare)"
                ],
                "Modérés": [
                    "Insuffisance gonadique définitive",
                    "Hypogonadisme",
                    "Troubles endocriniens secondaires"
                ],
                "Majeurs": [
                    "Cancers secondaires : Leucémie aiguë myéloïde, Syndromes myélodysplasiques, Cancer de la vessie",
                    "Fibrose pulmonaire",
                    "Insuffisance cardiaque chronique",
                    "Atteinte vésicale chronique (fibrose, hématurie)"
                ]
            }
        },

        "MÉTHYLPREDNISOLONE": {
            "COURT TERME (heures → jours)": {
                "Mineurs": [
                    "Bouffées vasomotrices, chaleur faciale",
                    "Goût métallique (bolus)",
                    "Céphalées",
                    "Insomnie, agitation légère",
                    "Nausées, dyspepsie",
                    "Rétention hydrosodée modérée"
                ],
                "Modérés": [
                    "HTA transitoire",
                    "Hyperglycémie (fréquente)",
                    "Hypokaliémie modérée",
                    "Agitation, anxiété, irritabilité",
                    "Œdèmes périphériques",
                    "Leucocytose réactionnelle"
                ],
                "Majeurs": [
                    "Crise hypertensive",
                    "Déséquilibre diabétique / acidocétose",
                    "Troubles psychiatriques aigus (manie, délire)",
                    "Hémorragie digestive",
                    "Infection sévère révélée",
                    "Troubles du rythme cardiaque (rare)"
                ]
            },
            "MOYEN TERME (semaines → mois)": {
                "Mineurs": [
                    "Prise de poids",
                    "Visage lunaire débutant",
                    "Acné, peau grasse",
                    "Fatigue musculaire"
                ],
                "Modérés": [
                    "Diabète cortico-induit",
                    "HTA persistante",
                    "Myopathie cortisonique",
                    "Troubles de l’humeur",
                    "Retard de cicatrisation",
                    "Ostéopénie débutante"
                ],
                "Majeurs": [
                    "Infections opportunistes",
                    "Ulcère gastro-duodénal compliqué",
                    "Nécrose aseptique de la tête fémorale",
                    "Troubles psychiatriques sévères persistants"
                ]
            },
            "LONG TERME (mois → années)": {
                "Mineurs": [
                    "Fragilité cutanée",
                    "Vergetures",
                    "Cataracte débutante"
                ],
                "Modérés": [
                    "Ostéoporose",
                    "Cataracte",
                    "Glaucome",
                    "Hypogonadisme secondaire"
                ],
                "Majeurs": [
                    "Insuffisance surrénalienne secondaire",
                    "Fractures vertébrales",
                    "Infections graves récidivantes",
                    "Complications cardiovasculaires majeures"
                ]
            }
        }
    }

    # ---------------------------
    # Sélection du médicament
    # ---------------------------
    selected_drug = st.selectbox("Choisissez un médicament HDJ", list(hdj_drugs.keys()))

    # ---------------------------
    # Affichage des checkboxes
    # ---------------------------
    if selected_drug:
        st.write(f"Vous avez sélectionné : **{selected_drug}**")
        drug_data = hdj_drugs[selected_drug]
        all_checked = []

        for term, categories in drug_data.items():
            with st.expander(term):
                for severity, effects in categories.items():
                    st.markdown(f"**{severity} :**")

                    for effect in effects:

                        # Cas spécial : Cancers secondaires
                        if effect.startswith("Cancers secondaires"):
                            key_main = f"{selected_drug}_{term}_{severity}_cancers_secondaires"

                            if st.checkbox("Cancers secondaires", key=key_main):
                                cancer_options = [
                                    "Leucémie aiguë myéloïde",
                                    "Syndromes myélodysplasiques",
                                    "Cancer de la vessie"
                                ]

                                for cancer in cancer_options:
                                    key_sub = f"{selected_drug}_{term}_{severity}_{cancer}"

                                    if st.checkbox(f"↳ {cancer}", key=key_sub):
                                        all_checked.append(
                                            f"{term} - {severity} - Cancers secondaires : {cancer}"
                                        )

                        # Tous les autres effets
                        else:
                            key = f"{selected_drug}_{term}_{severity}_{effect}"

                            if st.checkbox(effect, key=key):
                                all_checked.append(f"{term} - {severity} - {effect}")

        if all_checked:
            st.markdown("---")
            st.write("### Effets secondaires sélectionnés :")
            for e in all_checked:
                st.write(f"- {e}")
