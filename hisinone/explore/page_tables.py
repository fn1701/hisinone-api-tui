"""Tabellen einer Seite, egal welches Markup: klassische Baum-Tabellen
(``treeTableWithIcons``) oder der Studienplaner."""

import requests

from .custom_columns import is_data_table
from .expand import can_expand_all, expand_tree_tables
from .planner import PlannerLoader, is_study_planner
from .table_model import TreeTable
from .tree_tables import TREE_TABLE, parse_tree_tables


def has_tables(html: str) -> bool:
    return bool(TREE_TABLE.search(html)) or is_study_planner(html)


def has_data_tables(html: str) -> bool:
    """False fuer reine Navigations-Baeume (die bleiben Links)."""
    if is_study_planner(html):
        return True
    return any(is_data_table(table) for table in parse_tree_tables(html))


def can_expand(html: str) -> bool:
    return is_study_planner(html) or can_expand_all(html)


def load_tables(
    session: requests.Session, page_url: str, html: str, timeout: int, expand: bool = True
) -> tuple[list[TreeTable], str]:
    """(Tabellen, HTML das sie enthaelt); Studienplaner: 1-2 Requests."""
    if is_study_planner(html):
        return PlannerLoader(session, page_url, html, timeout).load(expand)
    return expand_tree_tables(session, page_url, html, timeout, expand)
