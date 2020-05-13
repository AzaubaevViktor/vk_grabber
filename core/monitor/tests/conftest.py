import pytest

from core.monitor import Monitoring


class MonitoringTestApi:
    pass


@pytest.fixture(scope='function')
def mon():
    conn = ('localhost', 9876)
    monitoring = Monitoring(*conn)

    await monitoring.warm_up()

    yield monitoring

    await monitoring.shutdown()

    # TODO: Check monitoring shutdowns


@pytest.fixture(scope='function')
def conn(mon: Monitoring):
    return MonitoringTestApi(mon)
