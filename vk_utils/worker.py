import asyncio
from time import time
from typing import List, Sequence

import aiohttp

from core import Log
from vk_utils import VKGroup, VKPost, VKUser, VKComment
from vk_utils.get_token import UpdateToken


class VKError(Exception):
    INVALID_SESSION = 5  # Need to reauthorize
    TOO_MANY_REQUESTS = 6

    def __init__(self, error):
        self.error = error

    @property
    def error_code(self):
        return self.error['error_code']

    @property
    def error_msg(self):
        return self.error['error_msg']

    def __str__(self):
        return f"VK Error#{self.error_code}: {self.error_msg}"


class VK:
    def __init__(self, config_vk):
        self.log = Log("VK")

        self.config = config_vk

        self.additional_params = {
            'access_token': self.config.token,
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

        self.last_call = 0
        self.threshold = 1 / 3

        self._update_token = None

    async def warm_up(self):
        self.session = aiohttp.ClientSession()

    async def call_method(self, method, **params):
        self.log.debug(method=method, params=params)
        while True:
            assert self.session is not None, "call `await .warm_up()` first"

            if time() - self.threshold < self.last_call:
                self.log.deep("Sleep", threshold=self.threshold)
                await asyncio.sleep(self.threshold)

            self.last_call = time()
            response = await self.session.get(
                url=f"{self.config['api_host']}{method}",
                params={**params, **self.additional_params},
                timeout=10
            )

            result = await response.json()

            if 'error' in result:
                vk_error = VKError(result['error'])
                if vk_error.error_code == VKError.TOO_MANY_REQUESTS:
                    self.threshold *= 1.01
                    if self.threshold > 1:
                        self.threshold = 1
                    self.log.warning("Too many requests", threshold=self.threshold)
                    continue

                if vk_error.error_code == VKError.INVALID_SESSION:
                    await self.do_auth()
                    continue

                raise vk_error
            else:
                assert 'response' in result
                self.threshold *= 0.999
                return result['response']

    async def users_info(self, *user_ids) -> Sequence[VKUser]:
        answer = await self.call_method(
            "users.get",
            user_ids=",".join(map(str, user_ids)),
            fields=self.user_fields
        )

        users = []

        for user_info in answer:
            users.append(VKUser(**user_info))

        return users

    async def me(self) -> VKUser:
        return (await self.users_info(self.config.user_id))[0]

    async def group_info(self, group_id) -> VKGroup:
        answer = await self.call_method(
            "groups.getById",
            group_id=group_id,
            fields=self.group_info_fields
        )
        assert len(answer) == 1
        group = answer[0]
        return VKGroup(**group)

    async def user_posts(self, user_id, count):
        return [post async for post in self._posts_count(user_id, count)]

    async def user_posts_iter(self, user_id, count=None):
        async for post in self._posts_count(user_id, count):
            yield post

    async def group_posts_iter(self, group_id, count=None):
        async for post in self._posts_count(-group_id, count):
            yield post

    async def comments_iter(self, owner_id, post_id, count=None):
        async for raw_data in self._offsetter(count, dict(
                method='wall.getComments',
                owner_id=owner_id,
                post_id=post_id,
                need_likes=1,
                preview_length=0,
                extended=0,
                thread_items_count=10,
        )):
            comment = VKComment(**raw_data)
            comment.post_id = post_id
            comment.owner_id = owner_id
            yield comment

    async def group_posts(self, group_id, count=None, from_ts=None):
        if count is not None and from_ts is not None:
            raise ValueError("Use one of attribute: `count` or `from_ts`")

        return [post async for post in self._posts_count(-group_id, count)]

    async def _posts_count(self, owner_id, count):
        async for post in self._offsetter(count, dict(
                method="wall.get",
                owner_id=owner_id,
                fields=self.post_fields
        )):
            yield VKPost(**post)

    async def _offsetter(self, count, params):
        # TODO: Can be optimized! Use asyncio.gather after first query, Luke!
        if count is None:
            count = float("+inf")

        if count < 1:
            raise ValueError(f"{count=} must be more than 0")

        offset = 0
        items_count = count

        while offset < items_count:
            to_download = min(items_count - offset, 100)

            try:
                answer = await self.call_method(
                    **params,
                    count=to_download,
                    offset=offset
                )
            except VKError:
                self.log.exception(params=params)
                return

            items_count = min(count, answer['count'])

            if to_download != len(answer['items']):
                if to_download < items_count:
                    self.log.warning("Downloaded items count:", wanted=to_download, actual=len(answer['items']))

            offset += to_download

            for item in answer['items']:
                yield item

    async def group_user_ids(self, group_id, count=None) -> Sequence[int]:
        users = []
        async for user_id in self.group_participants_iter(group_id, count):
            users.append(user_id)

        return users

    async def group_participants_iter(self, group_id, count=None):
        async for user_id in self._offsetter(count, dict(
                method="groups.getMembers",
                group_id=group_id
        )):
            yield user_id

    async def shutdown(self):
        if self.session:
            await self.session.close()

    async def do_auth(self):
        if self._update_token:
            await self._update_token.finished.wait()
            return

        self._update_token = UpdateToken(self.config)
        await self._update_token()
        self._update_token = None
