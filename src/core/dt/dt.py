class Time:
    """Класс для корректного отображения временных интервалов"""
    COEFS = [(1, "s"),
             (60, "m"),
             (60 * 60, "h"),
             (24 * 60 * 60, "d")]

    def __init__(self, time_stamp):
        self.time_stamp = time_stamp

    def __str__(self):
        for div, suf in self.COEFS[::-1]:
            if self.time_stamp >= div * 2:
                num = self.time_stamp / div
                break
        else:
            num, suf = self.time_stamp, "s"

        return f"{num:.1f} {suf}"
