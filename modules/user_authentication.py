"""user authentication"""

import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

import streamlit as st
import streamlit_authenticator as stauth
from deta import Deta
from dotenv import load_dotenv
from loguru import logger

from modules.general_functions import func_timer


@dataclass
class MessageLog:
    """Represents an access type with a message and an optional until date."""

    message: str
    log: str | None = None
    until: str | None = (
        (
            st.session_state.get("access_until")
            or f"{st.session_state['access_until']:%d.%m.%Y}"
        )
        if st.session_state.get("access_until")
        else None
    )


class Err:
    """Contains instances of the Access class for each access type."""

    no_access: MessageLog = MessageLog(
        message=(
            "Mit diesem Benutzerkonto haben Sie keinen Zugriff auf dieses Modul."
            "\n\n"
            "Bitte nehmen Sie Kontakt mit UTEC auf."
        ),
        log="no access to page (module)",
    )

    no_login: MessageLog = MessageLog(
        message="Bitte anmelden! (login auf der linken Seite)", log="not logged in"
    )
    too_late: MessageLog = MessageLog(
        message=(
            f"""
                Zugriff war nur bis {MessageLog.until} gestattet.  \n  \n
                Bitte nehmen Sie Kontakt mit UTEC auf.
            """
        ),
        log="access for user expired",
    )
    access_UTEC: MessageLog = MessageLog(
        message=(
            """
                Du bist mit dem allgemeinen UTEC-Account angemeldet.  \n  \n
                Viel Spaß mit den Tools!
            """
        )
    )
    access_other: MessageLog = MessageLog(
        message=(f"Angemeldet als '{st.session_state.get('name')}'.")
    )
    access_until: MessageLog = MessageLog(
        message=(
            f"""
                Mit diesem Account kann auf folgende Module bis zum 
                {MessageLog.until} zugegriffen werden:
            """
        )
    )
    access_level: MessageLog = MessageLog(
        message=("Mit diesem Account kann auf folgende Module zugegriffen werden:")
    )


def warnings(type: str) -> str:
    logger.error(getattr(Err, type, None).log)
    st.error(getattr(Err, type, None).message, type)


def infos_warnings_errors(key: str) -> str:
    """Messages concerning user authentication"""
    until: str | None = (
        st.session_state.get("access_until")
        or f"{st.session_state['access_until']:%d.%m.%Y}"
    )

    dic: dict[str, dict[str, str]] = {
        "no_access": {
            "message": """
                Mit diesem Benutzerkonto haben Sie keinen Zugriff auf dieses Modul. \n\n
                Bitte nehmen Sie Kontakt mit UTEC auf.
            """,
            "log": "no access to page (module)",
        },
        "no_login": {
            "message": "Bitte anmelden! (login auf der linken Seite)",
            "log": "not logged in",
        },
        "too_late": {
            "message": f"""
                Zugriff war nur bis {until} gestattet.  \n  \n
                Bitte nehmen Sie Kontakt mit UTEC auf.
            """,
            "log": "access for user expired",
        },
        "access_UTEC": {
            "message": """
                Du bist mit dem allgemeinen UTEC-Account angemeldet.  \n  \n
                Viel Spaß mit den Tools!
            """
        },
        "access_other": {
            "message": f"Angemeldet als '{st.session_state.get('name')}'."
        },
        "access_until": {
            "message": f"""
                Mit diesem Account kann auf folgende Module bis zum 
                {until} zugegriffen werden:
            """
        },
        "access_level": {
            "message": "Mit diesem Account kann auf folgende Module zugegriffen werden:"
        },
    }

    if dic[key].get("log"):
        logger.error(dic[key]["log"])

    return dic[key]["message"]


def authentication(page: str) -> bool:
    """Authentication object"""

    if not st.session_state.get("authentication_status"):
        st.warning(infos_warnings_errors("no_login"))
        return False
    if page not in st.session_state["access_pages"]:
        st.error(infos_warnings_errors("no_access"))
        return False
    if st.session_state["access_until"] < date.today():
        st.error(infos_warnings_errors("too_late"))
        return False

    return True


@func_timer
def connect_database(database: str = "UTEC_users") -> Any:
    """Connection to a Deta database.

    The default is the "users" database,
    which holds the user information (like username, access level, etc.)

    Args:
        - database (str, optional): The database to connect. Defaults to "UTEC_users".

    Returns:
        - _Base: Database connection
    """
    load_dotenv(".streamlit/secrets.toml")
    deta_key: str | None = os.getenv("DETA_KEY")
    deta: Deta = Deta(str(deta_key))

    logger.success("Deta-Database connection established")

    return deta.Base(database)


@func_timer
def get_all_user_data() -> dict[str, dict[str, Any]]:
    """Liste aller gespeicherter Benutzerdaten - je Benutzer ein dictionary

    Returns:
        - cont.DicStrNest: {
            - "key": {
                - "key" -> Benutzername für login (z.B. "fl")
                - "name" -> Klartext Name (z.B. "Florian")
                - "email" -> E-Mail-Adresse (z.B. ludwig@utec-bremen.de)
                - "password" -> verschlüsseltes Passwort
                - "access_lvl" -> Zugangsberechtigung
                    ("god" oder "full" oder liste von Seiten z.B. ["graph", "meteo"])
                - "access_until" -> Datum des Endes der Zugangsberechtigung
            }
        }
    """

    deta_db: Any = connect_database()

    # delete old entries if found
    for entry in deta_db.fetch().items:
        if datetime.strptime(entry["access_until"], "%Y-%m-%d") < datetime.now():
            deta_db.delete(entry["key"])

    users: dict[str, dict[str, Any]] = {
        list_entry["key"]: list_entry for list_entry in deta_db.fetch().items
    }

    logger.success("Collected all user data from Database")

    return users


def format_user_credentials() -> dict[str, dict[str, Any]]:
    """Create a dictionary out of all the user data in the database
    in the format, the authenticator-class needs

    Returns:
        - dict[str, dict[str, Any]]: dictionalry with
            - "usernames":
                - "key": Benutzername
                    - "name": Klartext Name
                    - "email": E-Mail
                    - "password": verschlüsseltes Passwort
    """
    return {
        "usernames": {
            user["key"]: {
                "name": user["name"],
                "email": user["email"],
                "password": user["password"],
            }
            for user in st.session_state["all_user_data"].values()
        }
    }


@func_timer
def insert_new_user(
    username: str, password: str, access_lvl: str | list, **kwargs
) -> None:
    """Neuen Benutzer hinzufügen.

    Bei Aufrufen der Funktion, Passwort als Klartext angeben -> wird in hash umgewandelt

    kwargs:
        name: str,
        email: str,
        access_until: str = "",
    """
    access_until: str = kwargs.get("access_until") or str(
        date.today() + timedelta(weeks=3)
    )
    name: str = kwargs.get("name") or username.replace("_", " ").title()
    email: str = kwargs.get("email") or ""

    # password muss eine liste sein,
    # deshalb wird hier für einezelnen user das pw in eine liste geschrieben
    hashed_pw: list = stauth.Hasher([password]).generate()
    deta_db: Any = connect_database()
    deta_db.put(
        {
            "key": username,  # Benutzername für login
            "name": name,  # Klartext name
            "email": email,  # e-Mail-Adresse
            "password": hashed_pw[0],  # erstes Element aus der Passwort-"liste"
            "access_lvl": access_lvl,  # "god" or "full" or list of allowed pages
            # e.g. ["graph", "meteo"] ...page options: dics.pages.keys()
            "access_until": access_until,
        }
    )

    st.markdown("###")
    st.info(
        f'Benutzer "{st.session_state.get("new_user_username")}" '
        "zur Datenbank hinzugefügt."
        f'("{st.session_state.get("new_user_name")}" hat Zugriff bis zum'
        f'{st.session_state.get("new_user_until"):%d.%m.%Y})  \n'
        "Achtung: Passwort merken (wird nicht wieder angezeigt):  \n"
        f"__{st.session_state.get('new_user_pw')}__"
    )

    st.button("ok", key="insert_ok_butt")


@func_timer
def update_user(username: str, updates: dict) -> Any:
    """Existierendes Benutzerkonto ändern"""
    deta_db: Any = connect_database()
    return deta_db.update(updates, username)


@func_timer
def delete_user(usernames: str | None = None) -> None:
    """Benutzer löschen"""
    deta_db: Any = connect_database()
    all_users: list[dict[str, Any]] = st.session_state["all_user_data"]

    if (
        usernames is None
        and any(
            admin in st.session_state["ms_del_user"]
            for admin in ["utec (UTEC Allgemein)", "fl (Florian)"]
        )
        or (usernames is not None and any(user in ["utec", "fl"] for user in usernames))
    ):
        st.warning("Admin-Konten können nicht gelöscht werden!")
        logger.error("tried to delete admin account")

    if usernames is not None:
        del_users: list[str] = [
            user for user in usernames if user not in ["utec", "fl"]
        ]
    else:
        del_users = [
            user["key"]
            for user in all_users
            if f"{user['key']} ({user['name']})" in st.session_state["ms_del_user"]
            and user["key"] not in ["utec", "fl"]
        ]

    # del_users = (
    #     [user for user in usernames if user not in ["utec", "fl"]]
    #     if usernames is not None
    #     else [
    #         user["key"]
    #         for user in all_users
    #         if f"{user['key']} ({user['name']})" in st.session_state.get("ms_del_user")
    #         and user["key"] not in ["utec", "fl"]
    #     ]
    # )

    if not del_users:
        st.error("Es wurden keine Benutzerkonten gelöscht.")
    else:
        for user in del_users:
            deta_db.delete(user)

        st.markdown("###")

        if len(del_users) > 1:
            users = {
                [user["name"] for user in all_users if user["key"] == del_users[0]][0]
            }
            lis_u: str = f"  \n- {del_users[0]} {users})"
            for inst in range(1, len(del_users)):
                lis_u += f"  \n- {del_users[inst]} ({[user['name'] for user in all_users if user['key'] == del_users[inst]][0]})"

            st.info(
                f"""
                Folgende Benutzer wurden aus der Datenbank entfernt: {lis_u}"
                """
            )
        else:
            st.info(
                f"""
                Der Benutzer 
                {del_users[0]} ({[user['name'] for user in all_users if user['key'] == del_users[0]][0]}) 
                wurde aus der Datenbank entfernt.
                """
            )

    st.button("ok", key="del_ok_butt")


# neuer Benutzer: Kommentar einer der Funktionen entfernen,
# Passwort (als Klartext) nicht vergessen und
# Datei in Terminal ausführen
# -> neuer Benutzer wird in Datenbank geschrieben

# insert_new_user(username="utec", name="UTEC allgemein", password="", access_lvl="full")
# insert_new_user("fl", "Florian", "", "god")

# insert_new_user("some_username", "some_name", "some_password", ["meteo"])


# update_user("fl", {"access_until": str(datetime.date.max)})
# update_user("utec", {"access_until": str(datetime.date.max)})
