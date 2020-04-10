import pytest



async def good_item(item: int):
    yield item


async def good_items(*items: int):
    for item in items:
        yield item


def wrong_ont_async(item: int):
    pass


async def wrong_two_params(a, b):
    pass


async def wrong_kwargs(*items, **kwargs):
    pass


async def wrong_kwargs2(item, **kwargs):
    pass


@pytest.mark.parametrize(
    'good',
    (None, good_item, good_items)
)
@pytest.mark.parametrize(
    'method',
    (wrong_ont_async, wrong_two_params, wrong_kwargs, wrong_kwargs2)
)
def test_wrong(good, method):
    chaos = Chaos()

    if good:
        chaos >> good

    with pytest.raises(TypeError):
        chaos >> method
