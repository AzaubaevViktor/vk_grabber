import aiohttp

from vk_utils import VKGroup


class VK:
    def __init__(self, config):
        self.config = config

        self.additional_params = {
            'access_token': self.config['token'],
            'lang': 'ru',
            'v': "5.103"
        }

        self.user_fields = ",".join([
            "first_name", "last_name", "deactivated", "verified",
            "sex", "bdate",
            "city",  # TODO: https://vk.com/dev/places.getCityById
            "country",  # TODO: https://vk.com/dev/places.getCountryById
            "home_town",
            "photo_400_orig",
            "online",
            "has_mobile",
            "contacts",
            "education",
            "universities",
            "schools",
            "last_seen",
            "occupation"
        ])

        self.group_fields = ",".join([
            'id', 'name', 'type', 'photo_200', 'city', 'description',
            'place'
        ])

        self.session: aiohttp.ClientSession = None

    async def warm_up(self):
        self.session = aiohttp.ClientSession()

    async def call_method(self, method, **params):
        assert self.session is not None, "call `await .warm_up()` first"
        response = await self.session.get(
            url=f"{self.config['api_host']}{method}",
            params={**params, **self.additional_params},
            timeout=10
        )

        result = await response.json()

        assert 'response' in result

        return result['response']

    async def me(self):
        return await self.call_method("account.getProfileInfo")

    async def group_info(self, group_id):
        answer = await self.call_method("groups.getById", group_id=group_id, )
        assert len(answer) == 1
        group = answer[0]
        return VKGroup(**group)

    async def shutdown(self):
        if self.session:
            await self.session.close()
