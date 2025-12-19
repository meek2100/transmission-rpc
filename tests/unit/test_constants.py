from transmission_rpc.constants import Args, RpcMethod, get_torrent_arguments


def test_args_repr() -> None:
    a = Args(
        type="type",
        added_version=1,
        removed_version=2,
        previous_argument_name="prev",
        next_argument_name="next",
        description="desc",
    )
    assert repr(a) == "Args('type', 1, 2, 'prev', 'next', 'desc')"


def test_args_str() -> None:
    a = Args(
        type="type",
        added_version=1,
        removed_version=2,
        previous_argument_name="prev",
        next_argument_name="next",
        description="desc",
    )
    # Expected: "Args<type=type, 1, description='desc')"
    assert str(a) == "Args<type=type, 1, description='desc')"


def test_get_torrent_arguments() -> None:
    # Mock TORRENT_GET_ARGS temporarily if needed, but we can test logic with real data
    # Case 1: rpc_version < added_version (should not include)
    # Case 2: rpc_version >= added_version (should include)
    # Case 3: removed_version present and <= rpc_version (should not include)

    # "id": added 1, removed None -> should be in 1
    args = get_torrent_arguments(1)
    assert "id" in args

    # "group": added 17
    args = get_torrent_arguments(16)
    assert "group" not in args
    args = get_torrent_arguments(17)
    assert "group" in args

    # "downloadLimitMode": added 1, removed 5
    args = get_torrent_arguments(4)
    assert "downloadLimitMode" in args
    args = get_torrent_arguments(5)
    assert "downloadLimitMode" not in args


def test_rpc_method_str() -> None:
    assert RpcMethod.SessionGet.value == "session-get"
