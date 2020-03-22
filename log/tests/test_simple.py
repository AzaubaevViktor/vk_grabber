def test_simple(log):
    log.info("Hello!")


def test_levels(log):
    log.deep("Deep debug")
    log.debug("Debug")
    log.info("Info")
    log.important("Important")
    log.warning("Warning")

    try:
        1 / 0
    except ZeroDivisionError:
        log.exception("Ow some exception!")

    log.error("OH MY GOD SOMETHING BAD HAPPENS")


def test_args(log):
    log.info(1, 2, 3, 4)
    log.info({1: 2, 3: 4}, [1, 2, 3, 4], (1, 2, 3, 4), {1, 2, 3})
    log.info("test", b"byte test")


def test_kwargs(log):
    log.info(a=1, b=2)
    log.info(test="test", tost=['t', 'o', 's', 't'])
    log.info(**{
        'dict': {1: 2, 3: 4},
        'list': [1, 2, 3, 4],
        'set': {1, 2, 3},
        'tuple': (1, 2, 3, 4),
        'str': "string",
        "byte_str": b"byte str",
    })


def test_args_kwargs(log):
    log.info({1: 2, 3: 4}, [1, 2, 3, 4], (1, 2, 3, 4), {1, 2, 3},
             **{
                 'dict': {1: 2, 3: 4},
                 'list': [1, 2, 3, 4],
                 'set': {1, 2, 3},
                 'tuple': (1, 2, 3, 4),
                 'str': "string",
                 "byte_str": b"byte str",
             })
