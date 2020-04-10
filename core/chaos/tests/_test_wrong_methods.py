import pytest

from core.chaos import Chaos


async def good_item(item: int):
    yield item


async def good_items(*items: int):
    for item in items:
        yield item


class GoodItem:
    async def __call__(self, item):
        yield item


class GoodItems:
    async def __call__(self, *items):
        for item in items:
            yield item


def wrong_not_async(item: int):
    pass


async def wrong_two_params(a, b):
    pass


async def wrong_kwargs(*items, **kwargs):
    pass


async def wrong_kwargs2(item, **kwargs):
    pass


class WrongNotAsync:
    def __call__(self, item):
        pass


class WrongTwoParams:
    async def __call__(self, a, b):
        pass


class WrongKwargs:
    async def __call__(self, *items, **kwargs):
        pass


class WrongKwargs2:
    async def __call__(self, item, **kwargs):
        pass


@pytest.mark.parametrize(
    'good',
    (None, good_item, good_items, GoodItem(), GoodItems())
)
@pytest.mark.parametrize(
    'method',
    (wrong_not_async, wrong_two_params, wrong_kwargs, wrong_kwargs2,
     WrongNotAsync(), WrongTwoParams(), WrongKwargs(), WrongKwargs2(),
     [], (1, 2, 3), None
     )
)
def test_wrong(good, method):
    chaos = Chaos()

    if good is not None:
        chaos >> good

    with pytest.raises(TypeError):
        chaos >> method
