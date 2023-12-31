import json
import aioredis

from .fast_storage import FastStorage
from ..schemas import (
    DashboardDexOverview,
    DashboardDex,
    DashboardBaseDex,
    DashboardExtendedDex,
    DashboardToken,
    DashboardBaseToken,
    DashboardExtendedToken,
    DashboardPair,
    DashboardBasePair,
    DashboardExtendedPair,
    DashboardAccount,
    DashboardBaseAccount,
    OraclePool,
    Pool,
)


class RedisStorage(FastStorage):
    def __init__(self, url: str) -> None:
        self._client: aioredis.Redis = aioredis.from_url(url, decode_responses=True, socket_timeout=30)

    async def _set_item(
        self,
        key: str,
        value: DashboardDexOverview | DashboardDex | DashboardExtendedToken | DashboardPair | DashboardAccount,
    ) -> None:
        await self._client.set(
            key,
            value.json(exclude_none=True),
        )

    async def _get_item(
        self,
        key: str,
        schema,
    ) -> DashboardDexOverview | DashboardDex | DashboardToken | DashboardPair | DashboardAccount | OraclePool | None:
        raw_value = await self._client.get(key)

        if not raw_value:
            return None

        return schema.parse_raw(raw_value)

    async def _set_list(
        self,
        key: str,
        item_list: list,
    ) -> None:
        await self._client.set(
            key,
            json.dumps([item.dict(exclude_none=True) for item in item_list]),
        )

    async def _get_list(
        self,
        key: str,
        schema,
    ) -> list:
        raw_list = await self._client.get(key)

        if not raw_list:
            return None

        return [schema.parse_obj(item) for item in json.loads(raw_list)]

    async def close(self) -> None:
        await self._client.close()

    async def set_price(self, key: str, price: dict[int, float]) -> None:
        await self._client.set(key, json.dumps(price))

    async def get_price(self, key: str) -> dict[int, float] | None:
        price = await self._client.get(key)

        if not price:
            return None

        return {int(key): value for key, value in json.loads(price).items()}

    async def set_ton_usd_price(self, price: dict[int, float]) -> None:
        await self.set_price(
            "ton_usd_price",
            price,
        )

    async def get_ton_usd_price(self) -> dict[int, float] | None:
        return await self.get_price("ton_usd_price")

    async def set_dashboard_dex_overview(self, dashboard_dex_overview: DashboardDexOverview) -> None:
        await self._set_item(
            "dashboard:dex_overview",
            dashboard_dex_overview,
        )

    async def get_dashboard_dex_overview(self) -> DashboardDexOverview | None:
        return await self._get_item(
            "dashboard:dex_overview",
            DashboardDexOverview,
        )

    async def set_dashboard_dex(self, dashboard_dex: DashboardExtendedDex) -> None:
        await self._set_item(
            f"dashboard:dex:{dashboard_dex.id}",
            dashboard_dex,
        )

    async def get_dashboard_dex(
        self,
        dex_id: int,
        is_extended: bool = False,
    ) -> DashboardDex | DashboardExtendedDex | None:
        return await self._get_item(
            f"dashboard:dex:{dex_id}",
            DashboardExtendedDex if is_extended else DashboardDex,
        )

    async def set_dashboard_token(self, dashboard_token: DashboardExtendedToken, dex_id: int | None) -> None:
        await self._set_item(
            f"dashboard:token:{dashboard_token.id}:{dex_id}",
            dashboard_token,
        )

    async def get_dashboard_token(
        self,
        token_id: int,
        dex_id: int | None,
        is_extended: bool = False,
    ) -> DashboardToken | DashboardExtendedToken | None:
        return await self._get_item(
            f"dashboard:token:{token_id}:{dex_id}",
            DashboardExtendedToken if is_extended else DashboardToken,
        )

    async def set_dashboard_pair(self, dashboard_pair: DashboardExtendedPair, dex_id: int | None) -> None:
        await self._set_item(
            f"dashboard:pair:{dashboard_pair.id}:{dex_id}",
            dashboard_pair,
        )

    async def get_dashboard_pair(
        self,
        pair_id: int,
        dex_id: int | None,
        is_extended: bool = False,
    ) -> DashboardPair | DashboardExtendedPair | None:
        return await self._get_item(
            f"dashboard:pair:{pair_id}:{dex_id}",
            DashboardExtendedPair if is_extended else DashboardPair,
        )

    async def set_dashboard_account(self, dashboard_account: DashboardAccount) -> None:
        ...

    async def get_dashboard_account(self, account_id: int) -> DashboardAccount | None:
        ...

    async def set_dashboard_dex_list(self, dex_list: list[DashboardBaseDex]) -> None:
        await self._set_list(
            "dashboard:dex_list",
            dex_list,
        )

    async def get_dashboard_dex_list(self) -> list[DashboardBaseDex] | None:
        return await self._get_list(
            "dashboard:dex_list",
            DashboardBaseDex,
        )

    async def set_dashboard_token_list(self, token_list: list[DashboardBaseToken], dex_id: int | None) -> None:
        await self._set_list(
            f"dashboard:token_list:{dex_id}",
            token_list,
        )

    async def get_dashboard_token_list(self, dex_id: int | None) -> list[DashboardBaseToken] | None:
        return await self._get_list(
            f"dashboard:token_list:{dex_id}",
            DashboardBaseToken,
        )

    async def set_dashboard_pair_list(self, pair_list: list[DashboardBasePair], dex_id: int | None) -> None:
        await self._set_list(
            f"dashboard:pair_list:{dex_id}",
            pair_list,
        )

    async def get_dashboard_pair_list(self, dex_id: int | None) -> list[DashboardBasePair]:
        return await self._get_list(
            f"dashboard:pair_list:{dex_id}",
            DashboardBasePair,
        )

    async def set_dashboard_account_list(self, account_list: list[DashboardBaseAccount], dex_id: int | None) -> None:
        await self._set_list(
            f"dashboard:account_list:{dex_id}",
            account_list,
        )

    async def get_dashboard_account_list(self, dex_id: int | None) -> list[DashboardBaseAccount]:
        return await self._get_list(
            f"dashboard:account_list:{dex_id}",
            DashboardBaseAccount,
        )

    async def set_oracle_pool(self, oracle_pool: OraclePool) -> None:
        await self._set_item(
            f"oracle:pool:{oracle_pool.id}",
            oracle_pool,
        )

    async def get_oracle_pool(self, pool_id: int) -> OraclePool | None:
        return await self._get_item(
            f"oracle:pool:{pool_id}",
            OraclePool,
        )

    async def set_pool_list(self, pool_list: list[Pool]) -> None:
        await self._set_list(
            "pool_list",
            pool_list,
        )

    async def get_pool_list(self) -> list[Pool] | None:
        return await self._get_list(
            "pool_list",
            Pool,
        )
