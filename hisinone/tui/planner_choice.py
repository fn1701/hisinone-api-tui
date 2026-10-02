"""Was im Studienplaner gewählt ist: Studiengang und Filterwerte."""

from dataclasses import dataclass, field

from hisinone.explore.planner_courses import Course
from hisinone.explore.planner_filter import filter_key


@dataclass
class PlannerChoice:
    """Studiengang über seinen Namen (die Link-ids hängen an der Seite)."""

    course: str = ""  # "" = der erste der Seite
    filters: dict[str, str] = field(default_factory=dict)

    def cache_key(self, stable_url: str) -> str:
        """Je Studiengang und Filter-Kombination ein eigener Cache-Eintrag."""
        return f"{stable_url}#course:{self.course}#filter:{filter_key(self.filters)}"

    def course_id(self, courses: list[Course]) -> str:
        """Link-id in dieser Seite; "" = nicht (mehr) da, dann der erste."""
        return next((course.link_id for course in courses if course.label == self.course), "")
