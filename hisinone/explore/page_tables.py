"""Tabellen einer Seite, egal welches Markup: klassische Baum-Tabellen
(``treeTableWithIcons``) oder der Studienplaner."""

import requests

from .custom_columns import is_data_table
from .expand import can_expand_all, expand_tree_tables
from .planner import PlannerLoader, Progress, is_study_planner, no_progress
from .table_model import TreeTable
from .tree_tables import TREE_TABLE


def has_tables(html: str) -> bool:
    return bool(TREE_TABLE.search(html)) or is_study_planner(html)


def has_data_tables(html: str, tables: list[TreeTable]) -> bool:
    """False für reine Navigations-Bäume (die bleiben Links); tables = die
    (ggf. aufgeklappten) Tabellen der Seite."""
    return is_study_planner(html) or any(is_data_table(table) for table in tables)


def can_expand(html: str) -> bool:
    return is_study_planner(html) or can_expand_all(html)


def load_tables(
    session: requests.Session, page_url: str, html: str, timeout: int, expand: bool = True,
    filters: dict[str, str] | None = None, progress: Progress = no_progress,
    course_id: str = "",
) -> tuple[list[TreeTable], str]:  # fmt: skip
    """(Tabellen, HTML das sie enthält); Studienplaner: 2-4 Requests, mit Filtern."""
    if is_study_planner(html):
        return PlannerLoader(session, page_url, html, timeout).load(expand, filters, progress,
                                                                         course_id)  # fmt: skip
    return expand_tree_tables(session, page_url, html, timeout, expand)
