# Standard Nigerian 5.0 scale
SCALE = [(70, "A", 5), (60, "B", 4), (50, "C", 3), (45, "D", 2), (40, "E", 1), (0, "F", 0)]


def grade_for(total: float):
    for floor, letter, points in SCALE:
        if total >= floor:
            return letter, points


def gpa(rows):
    """rows: iterable of (points, units). Returns weighted GPA rounded to 2 dp."""
    units = sum(u for _, u in rows)
    if not units:
        return 0.0
    return round(sum(p * u for p, u in rows) / units, 2)
