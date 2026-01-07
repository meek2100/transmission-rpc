from transmission_rpc.constants import Args, Type, get_torrent_arguments


def test_args_repr_str() -> None:
    arg = Args(Type.number, 1, description="desc")
    assert repr(arg) == "Args('number', 1, None, None, None, 'desc')"
    assert str(arg) == "Args<type=number, 1, description='desc')"


def test_get_torrent_arguments() -> None:
    args = get_torrent_arguments(1)
    assert "id" in args
    assert "group" not in args  # added in 17
