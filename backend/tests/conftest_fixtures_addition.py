
# 以下内容需要添加到 conftest.py 的别名 Fixtures 部分

@pytest.fixture(scope="function")
def sample_active_account(test_ad_account):
    """
    活跃状态的广告账户 (test_ad_account 的别名)

    用于 mark_dead API 测试等需要活跃账户的场景
    """
    return test_ad_account


@pytest.fixture(scope="function")
def pitcher_token(media_buyer_token):
    """
    投手 token (media_buyer_token 的别名)

    技术角色映射: pitcher → media_buyer
    参考: MASTER.md v4.6 技术层角色定义
    """
    return media_buyer_token


@pytest.fixture(scope="function")
def pitcher_headers(media_buyer_headers):
    """
    投手 headers (media_buyer_headers 的别名)

    技术角色映射: pitcher → media_buyer
    """
    return media_buyer_headers


@pytest.fixture(scope="function")
def pitcher_user(media_buyer_user):
    """
    投手用户 (media_buyer_user 的别名)

    技术角色映射: pitcher → media_buyer
    """
    return media_buyer_user
