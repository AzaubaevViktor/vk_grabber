import asyncio
from collections import defaultdict
from time import time
from typing import Sequence

import aiohttp

from core import Log
from core.monitor import DictPage, PageAttribute
from vk_utils import VKGroup, VKPost, VKPerson, VKComment


class VKError(Exception):
    INVALID_SESSION = 5  # Need to reauthorize
    TOO_MANY_REQUESTS = 6
    DELETED_OR_BANNED = 18
    RATE_LIMIT_REACHED = 29
    PROFILE_PRIVATE = 30

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


class VKStats(DictPage):
    threshold = PageAttribute(default=0)
    call_methods_count = PageAttribute(default=0)
    success = PageAttribute(default=0)
    errors = PageAttribute(default=0)
    errors_too_many = PageAttribute(default=0)
    queries = PageAttribute(default=0)
    by_type = PageAttribute(default=lambda: defaultdict(int))

    # TODO: Add %


class VK:
    def __init__(self, config_vk):
        self.log = Log("VK")

        self.config = config_vk

        self.additional_params = {
            'access_token': self.config.token,
            'lang': 'ru',
            'v': "5.103"
        }

        self.person_fields = ",".join([
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
            "occupation",
            "hidden",
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

        self.query_lock = asyncio.Lock()

        self.stats = VKStats('vk', "VK API")

        self.auth_lock = asyncio.Lock()

    async def warm_up(self):
        self.session = aiohttp.ClientSession()

    async def call_method(self, method, **params):
        self.log.debug(method=method, params=params)

        self.stats.call_methods_count += 1

        try:
            while True:
                assert self.session is not None, "call `await .warm_up()` first"
                async with self.query_lock:
                    if time() - self.threshold < self.last_call:
                        self.log.deep("Sleep", threshold=self.threshold)
                        await asyncio.sleep(self.threshold)

                self.last_call = time()
                self.stats.queries += 1
                response = await self.session.get(
                    url=f"{self.config['api_host']}{method}",
                    params={**params, **self.additional_params},
                    timeout=10
                )
                self.stats.by_type[method] += 1

                result = await response.json()

                if 'error' in result:
                    self.stats.errors += 1
                    vk_error = VKError(result['error'])
                    if vk_error.error_code == VKError.TOO_MANY_REQUESTS:
                        self.stats.errors_too_many += 1
                        self.threshold *= 1.1
                        if self.threshold > 1:
                            self.threshold = 1
                        self.log.warning("Too many requests", threshold=self.threshold)
                        continue

                    if vk_error.error_code == VKError.INVALID_SESSION:
                        self.log.warning("Need auth. Please run <app> <config> auth")
                        break

                    if vk_error.error_code == VKError.PROFILE_PRIVATE:
                        self.log.warning("Profile private", method=method, params=params)
                        break

                    if vk_error.error_code == VKError.DELETED_OR_BANNED:
                        self.log.warning("Profile deleted or banned", method=method, params=params)
                        break

                    if vk_error.error_code == VKError.RATE_LIMIT_REACHED:
                        self.log.important("RATE LIMIT")

                    raise vk_error
                else:
                    self.stats.success += 1
                    assert 'response' in result
                    self.threshold *= 0.991
                    return result['response']
        finally:
            self.stats.call_methods_count -= 1
            self.stats.threshold = self.threshold

    async def persons_info(self, *user_ids) -> Sequence[VKPerson]:
        answer = await self.call_method(
            "users.get",
            user_ids=",".join(map(str, user_ids)),
            fields=self.person_fields
        )

        users = []

        for user_info in answer:
            users.append(VKPerson(**user_info))

        return users

    async def me(self) -> VKPerson:
        return (await self.persons_info(self.config.user_id))[0]

    async def group_info(self, group_id) -> VKGroup:
        answer = await self.call_method(
            "groups.getById",
            group_id=group_id,
            fields=self.group_info_fields
        )
        assert len(answer) == 1
        group = answer[0]
        return VKGroup(**group)

    async def person_posts(self, person_id, count):
        return [post async for post in self._posts_count(person_id, count)]

    async def person_posts_iter(self, person_id, count=None):
        async for post in self._posts_count(person_id, count):
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
                raise

            if answer is None:
                # Good error in call_method
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
