from typing import List

import aiohttp

from vk_utils import VKGroup, VKPost


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

        self.group_info_fields = ",".join([
            'id', 'name', 'type', 'photo_200', 'city', 'description',
            'place'
        ])

        self.post_fields = ",".join([

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
        answer = await self.call_method(
            "groups.getById",
            group_id=group_id,
            fields=self.group_info_fields
        )
        assert len(answer) == 1
        group = answer[0]
        return VKGroup(**group)

    async def group_posts(self, group_id, count=None, from_ts=None):
        if count is not None and from_ts is not None:
            raise ValueError("Use one of attribute: `count` or `from_ts`")

        if count is None and from_ts is None:
            raise ValueError("USe one of attribute: `count` or `from_ts`")

        if count is not None:
            return list(await self._group_posts_count(group_id, count))

        if from_ts is not None:
            raise NotImplementedError()

    async def _group_posts_count(self, group_id, count):
        async for post in self._offsetter(count, dict(
                method="wall.get",
                owner_id=-group_id,
                fields=self.post_fields
        )):
            yield VKPost(**post)

    async def _offsetter(self, count, params):
        if count < 1:
            raise ValueError(f"{count=} must be more than 0")

        offset = 0
        posts_count = count

        while offset < posts_count:
            answer = await self.call_method(
                **params,
                count=min(posts_count - offset, 100),
                offset=offset
            )

            posts_count = min(count, answer['count'])

            offset += len(answer['items'])

            for item in answer['items']:
                yield item

    async def group_user_ids(self, group_id, count=None) -> List[int]:
        users = []
        async for user_id in self._offsetter(count, dict(
                method="groups.getMembers",
                group_id=group_id
        )):
            users.append(user_id)

        return users

    async def shutdown(self):
        if self.session:
            await self.session.close()
