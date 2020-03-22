from log import LogLevel


def test_levels(log, capsys):
    log.level = LogLevel.INFO

    debug_str = "DEBUG"
    info_str = "INFO"
    warning_str = "WARNING"

    assert debug_str != info_str
    assert debug_str != warning_str
    assert info_str != warning_str

    log.debug(debug_str)

    log.info(info_str)

    log.warning(warning_str)

    captured = capsys.readouterr()

    assert debug_str not in captured.out
    assert info_str in captured.out
    assert warning_str in captured.out
