import random
import string


def sizeof_fmt(num, suffix="B"):
    """Format size of file in a readable format."""
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


def urlencode(bytes):
    """Encode a byte array in URL format."""
    result = ""
    valids = (string.ascii_letters + "_.").encode("ascii")
    for b in bytes:
        if b in valids:
            result += chr(b)
        elif b == " ":
            result += "+"
        else:
            result += "%%%02X" % b
    return result


def random_id(length):
    """Generate a random ID of given length."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def humanbytes(B):
    """Return the given bytes as a human friendly KB, MB, GB, or TB string."""
    B = float(B)
    KB = float(1024)
    MB = float(KB**2)  # 1,048,576
    GB = float(KB**3)  # 1,073,741,824
    TB = float(KB**4)  # 1,099,511,627,776

    if B < KB:
        return "{0} {1}".format(
            int(B) if B.is_integer() else B, "B" if 0 == B > 1 else "B"
        )
    elif KB <= B < MB:
        return "{0} KB".format(
            int(B / KB)
            if (B / KB).is_integer()
            else "{0:.2f}".format(B / KB).rstrip("0").rstrip(".")
        )
    elif MB <= B < GB:
        return "{0} MB".format(
            int(B / MB)
            if (B / MB).is_integer()
            else "{0:.2f}".format(B / MB).rstrip("0").rstrip(".")
        )
    elif GB <= B < TB:
        return "{0} GB".format(
            int(B / GB)
            if (B / GB).is_integer()
            else "{0:.2f}".format(B / GB).rstrip("0").rstrip(".")
        )
    elif TB <= B:
        return "{0} TB".format(
            int(B / TB)
            if (B / TB).is_integer()
            else "{0:.2f}".format(B / TB).rstrip("0").rstrip(".")
        )


def convert_seconds_to_hours_mins_seconds(seconds):
    hours = seconds // 3600
    remaining_seconds = seconds % 3600
    mins = remaining_seconds // 60
    remaining_seconds = remaining_seconds % 60

    time_str = ""
    if hours > 0:
        time_str += f"{hours}h "
    if mins > 0:
        time_str += f"{mins}m "
    if remaining_seconds != 0:
        time_str += f"{remaining_seconds}s"

    return time_str


def add_kb(kb):
    return "{} kb".format(str(kb))


def add_percent(percent):
    return "{} %".format(str(percent))
