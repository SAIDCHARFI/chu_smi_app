import streamlit as st
from supabase import create_client

# ---------------------------
# Supabase configuration
# ---------------------------
SUPABASE_URL = st.secrets["SUPABASE"]["URL"]  # Remplace par ton URL Supabase
SUPABASE_KEY = st.secrets["SUPABASE"]["KEY"]             # Remplace par ta clé API
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        },

        "RITUXIMAB": {
            "COURT TERME (pendant la perfusion → 48 h)": {
                "Mineurs": [
                    "Céphalées",
                    "Prurit léger, rash discret",
                    "Bouffées vasomotrices",
                    "Nausées légères",
                    "Asthénie transitoire",
                    "Sensation de gorge serrée légère"
                ],
                "Modérés": [
                    "Réaction liée à la perfusion (fièvre, frissons, rash, dyspnée modérée)",
                    "Hypotension transitoire",
                    "Bronchospasme léger",
                    "Douleurs thoraciques non ischémiques",
                    "HTA transitoire"
                ],
                "Majeurs": [
                    "Réaction anaphylactique (rare)",
                    "Syndrome de relargage cytokinique sévère",
                    "Bronchospasme sévère / détresse respiratoire",
                    "Arythmie grave",
                    "Choc"
                ]
            },
            "MOYEN TERME (semaines → mois)": {
                "Mineurs": [
                    "Asthénie prolongée",
                    "Infections ORL bénignes",
                    "Céphalées récurrentes"
                ],
                "Modérés": [
                    "Infections bactériennes récidivantes",
                    "Hypogammaglobulinémie modérée",
                    "Leucopénie modérée",
                    "Réactivation herpétique (HSV, zona)"
                ],
                "Majeurs": [
                    "Infections sévères (pneumonie, septicémie)",
                    "Réactivation virale (hépatite B)",
                    "Neutropénie tardive",
                    "Colite sévère (rare)"
                ]
            },
            "LONG TERME (mois → années)": {
                "Mineurs": [
                    "Fatigue chronique",
                    "Hypogammaglobulinémie asymptomatique"
                ],
                "Modérés": [
                    "Déficit immunitaire prolongé",
                    "Infections répétées nécessitant ATB"
                ],
                "Majeurs": [
                    "LEMP (JC virus)",
                    "Infections opportunistes graves",
                    "Hypogammaglobulinémie sévère nécessitant Ig IV"
                ]
            }
        },

        "Infliximab": {
            "COURT TERME (pendant la perfusion → 48 h)": {
                "Mineurs": [
                    "Céphalées, fatigue",
                    "Nausées légères",
                    "Prurit, rash discret",
                    "Bouffées vasomotrices",
                    "Douleurs musculo-articulaires transitoires"
                ],
                "Modérés": [
                    "Réaction à la perfusion (fièvre, frissons, rash, dyspnée modérée)",
                    "Hypotension ou HTA transitoire",
                    "Douleur thoracique non ischémique",
                    "Bronchospasme léger"
                ],
                "Majeurs": [
                    "Réaction anaphylactique",
                    "Choc",
                    "Bronchospasme sévère / détresse respiratoire",
                    "Arythmie grave"
                ]
            },
            "MOYEN TERME (semaines → mois)": {
                "Mineurs": [
                    "Asthénie persistante",
                    "Infections ORL bénignes",
                    "Réactions cutanées modérées"
                ],
                "Modérés": [
                    "Infections bactériennes récidivantes",
                    "Réactivation herpétique (HSV, zona)",
                    "Cytopénies modérées",
                    "Anticorps anti-infliximab → perte d’efficacité",
                    "Réactions retardées type “maladie sérique”"
                ],
                "Majeurs": [
                    "Tuberculose active",
                    "Infections opportunistes sévères",
                    "Hépatite sévère",
                    "Décompensation d’insuffisance cardiaque"
                ]
            },
            "LONG TERME (mois → années)": {
                "Mineurs": [
                    "Fatigue chronique",
                    "Réactions cutanées persistantes"
                ],
                "Modérés": [
                    "Maladies auto-immunes induites",
                    "Hypogammaglobulinémie modérée"
                ],
                "Majeurs": [
                    "Infections graves récidivantes",
                    "Cancers (lymphomes, cancers cutanés)",
                    "Insuffisance cardiaque aggravée"
                ]
            }
        },

        "ADALIMUMAB": {
            "COURT TERME (heures → jours)": {
                "Mineurs": [
                    "Réaction au site d’injection",
                    "Céphalées",
                    "Fatigue transitoire",
                    "Nausées légères"
                ],
                "Modérés": [
                    "Réaction locale étendue ou douloureuse persistante",
                    "Fièvre modérée",
                    "Arthralgies/myalgies",
                    "Rash cutané diffus"
                ],
                "Majeurs": [
                    "Réaction allergique sévère / anaphylaxie (rare)",
                    "Infection aiguë sévère révélée",
                    "Troubles neurologiques aigus (très rare)"
                ]
            },
            "MOYEN TERME (semaines → mois)": {
                "Mineurs": [
                    "Infections ORL bénignes récidivantes",
                    "Asthénie persistante"
                ],
                "Modérés": [
                    "Infections bactériennes récidivantes",
                    "Réactivation herpétique",
                    "Cytopénies modérées",
                    "Anticorps anti-adalimumab → perte d’efficacité",
                    "Réactions paradoxales (psoriasis, eczéma)"
                ],
                "Majeurs": [
                    "Tuberculose active",
                    "Infections opportunistes",
                    "Hépatite sévère",
                    "Décompensation d’insuffisance cardiaque"
                ]
            },
            "LONG TERME (mois → années)": {
                "Mineurs": [
                    "Fatigue chronique",
                    "Réactions cutanées persistantes"
                ],
                "Modérés": [
                    "Maladies auto-immunes induites",
                    "Hypogammaglobulinémie modérée"
                ],
                "Majeurs": [
                    "Infections graves récidivantes",
                    "Cancers",
                    "Atteinte neurologique démyélinisante (rare)"
                ]
            }
        },

        "ACTEMRA": {
            "COURT TERME (pendant → 48 h)": {
                "Mineurs": [
                    "Céphalées",
                    "Fatigue transitoire",
                    "Nausées légères",
                    "Réaction locale au site d’injection (SC)",
                    "Bouffées vasomotrices"
                ],
                "Modérés": [
                    "Réaction à la perfusion (IV) : fièvre, frissons, rash",
                    "HTA transitoire",
                    "Cytolyse hépatique modérée",
                    "Neutropénie modérée"
                ],
                "Majeurs": [
                    "Réaction allergique sévère / anaphylaxie (rare)",
                    "Infection aiguë sévère révélée",
                    "Trouble hématologique sévère (neutropénie profonde)"
                ]
            },
            "MOYEN TERME (semaines → mois)": {
                "Mineurs": [
                    "Asthénie persistante",
                    "Infections ORL bénignes"
                ],
                "Modérés": [
                    "Infections bactériennes récidivantes",
                    "Élévation persistante des transaminases",
                    "Hyperlipidémie",
                    "Neutropénie / thrombopénie modérées",
                    "Réactivation herpétique (HSV/zona)"
                ],
                "Majeurs": [
                    "Infections sévères",
                    "Perforation digestive",
                    "Hépatite sévère"
                ]
            },
            "LONG TERME (mois → années)": {
                "Mineurs": [
                    "Hyperlipidémie asymptomatique",
                    "Fatigue chronique"
                ],
                "Modérés": [
                    "Déficit immunitaire fonctionnel",
                    "Infections répétées"
                ],
                "Majeurs": [
                    "Infections graves récidivantes",
                    "Complications digestives sévères",
                    "Atteinte hépatique chronique (rare)"
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
                        # Cas cancers secondaires
                        if effect.startswith("Cancers secondaires"):
                            key_main = f"{selected_drug}_{term}_{severity}_cancers"
                            if st.checkbox("Cancers secondaires", key=key_main):
                                for cancer in [
                                    "Leucémie aiguë myéloïde",
                                    "Syndromes myélodysplasiques",
                                    "Cancer de la vessie"
                                ]:
                                    key_sub = f"{selected_drug}_{term}_{severity}_{cancer}"
                                    if st.checkbox(f"↳ {cancer}", key=key_sub):
                                        all_checked.append({
                                            "periode": term,
                                            "gravite": severity,
                                            "effet": "Cancers secondaires",
                                            "detail": cancer
                                        })
                        else:
                            key = f"{selected_drug}_{term}_{severity}_{effect}"
                            if st.checkbox(effect, key=key):
                                all_checked.append({
                                    "periode": term,
                                    "gravite": severity,
                                    "effet": effect,
                                    "detail": None
                                })

        # ---------------------------
        # Affichage sélection + sauvegarde
        # ---------------------------
        if all_checked:
            st.markdown("---")
            if st.button("💾 Enregistrer"):
                supabase.table("hdj_sessions").insert({
                    "medicament": selected_drug,
                    "selections": all_checked
                }).execute()
                st.success("✅ Session enregistrée avec tous les détails")
