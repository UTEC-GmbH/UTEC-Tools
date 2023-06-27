"""Streamlit menus for user authentication"""


import datetime
import secrets

import pandas as pd
from modules import constants as cont
from modules import general_functions as gf
from modules import streamlit_functions as sf
from modules import user_authentication as uauth


import streamlit as st


@gf.func_timer
def delete_user_form() -> None:
    """Benutzer löschen"""

    users: dict[str, dict[str, str]] = uauth.get_all_user_data()
    with st.form("Benutzer löschen"):
        st.multiselect(
            label="Benutzer wählen, die gelöscht werden sollen",
            options=[
                f"{user['key']} ({user['name']})"
                for user in users.values()
                if user["key"] not in ("utec", "fl")
            ],
            key="ms_del_users",
        )

        st.markdown("###")
        st.form_submit_button("Knöpfle")


@gf.func_timer
def new_user_form() -> None:
    """Neuen Benutzer hinzufügen"""
    with st.form("Neuer Benutzer"):
        st.text_input(
            label="Benutzername",
            key="new_user_user",
            help=("Benutzername, wei er für den login benutzt wird - z.B. fl"),
        )
        st.text_input(
            label="Passwort",
            key="new_user_pw",
            help=("...kann ruhig auch etwas 'merkbares' sein."),
            value=secrets.token_urlsafe(8),
        )
        st.date_input(
            label="Benutzung erlaubt bis:",
            key="new_user_until",
            min_value=datetime.date.today(),
            value=datetime.date.today() + datetime.timedelta(weeks=3),
        )
        st.text_input(
            label="Name oder Firma",
            key="new_user_name",
            help=("z.B. Florian"),
            value="UTEC",
        )
        st.text_input(
            label="E-Mail Adresse",
            key="new_user_email",
            help=("z.B. info@utec-bremen.de"),
            value="info@utec-bremen.de",
        )
        st.multiselect(
            label="Zugriffsrechte",
            key="new_user_access",
            help=("Auswahl der Module, auf die dieser Benutzer zugreifen darf."),
            options=[
                key for key in cont.ST_PAGES.get_all_short() if key not in ("login")
            ],
            default=[
                key for key in cont.ST_PAGES.get_all_short() if key not in ("login")
            ],
        )

        st.markdown("###")
        st.form_submit_button("Knöpfle")


@gf.func_timer
def list_all_accounts() -> None:
    """Liste aller Benutzerkonten"""
    users: dict[str, dict[str, str]] = uauth.get_all_user_data()

    df_users = pd.DataFrame()
    df_users["Benutzername"] = [user["key"] for user in users.values()]
    df_users["Name"] = [user["name"] for user in users.values()]
    df_users["Verfallsdatum"] = [user["access_until"] for user in users.values()]
    df_users["Zugriffsrechte"] = [str(user["access_lvl"]) for user in users.values()]

    st.dataframe(df_users)
    st.button("ok")


@gf.func_timer
def user_accounts() -> None:
    """Benutzerkontensteuerung"""

    st.markdown("###")
    st.markdown("---")

    lis_butt: list[str] = [
        "butt_add_new_user",
        "butt_del_user",
    ]

    # Knöpfle für neuen Benutzer, Benutzer löschen...
    if not any(sf.st_get(butt) for butt in lis_butt):
        st.button("Liste aller Konten", "butt_list_all")
        st.button("Neuen Benutzer hinzufügen", "butt_add_new_user")
        st.button("Benutzer löschen", "butt_del_user")
        st.button("Benutzerdaten ändern", "butt_change_user", disabled=True)
        st.markdown("###")

    # Menu für neuen Benutzer
    if sf.st_get("butt_add_new_user"):
        new_user_form()
        st.button("abbrechen")
    st.session_state["butt_sub_new_user"] = sf.st_get(
        "FormSubmitter:Neuer Benutzer-Knöpfle"
    )

    # Menu zum Löschen von Benutzern
    if sf.st_get("butt_del_user"):
        delete_user_form()
        st.button("abbrechen")
    st.session_state["butt_sub_del_user"] = sf.st_get(
        "FormSubmitter:Benutzer löschen-Knöpfle"
    )

    if sf.st_get("butt_list_all"):
        st.markdown("---")
        list_all_accounts()
