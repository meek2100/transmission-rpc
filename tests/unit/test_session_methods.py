from typing import Any

from transmission_rpc.session import Session, SessionStats, Stats, Units


def test_session_properties() -> None:
    fields: dict[str, Any] = {
        "alt-speed-down": 100,
        "alt-speed-enabled": True,
        "alt-speed-time-begin": 0,
        "alt-speed-time-day": 127,
        "alt-speed-time-enabled": True,
        "alt-speed-time-end": 0,
        "alt-speed-up": 100,
        "blocklist-enabled": True,
        "blocklist-size": 10,
        "blocklist-url": "url",
        "cache-size-mb": 10,
        "config-dir": "/config",
        "dht-enabled": True,
        "download-dir": "/downloads",
        "download-dir-free-space": 1000,
        "download-queue-enabled": True,
        "download-queue-size": 5,
        "encryption": "preferred",
        "idle-seeding-limit-enabled": True,
        "idle-seeding-limit": 30,
        "incomplete-dir-enabled": True,
        "incomplete-dir": "/incomplete",
        "lpd-enabled": True,
        "peer-limit-global": 200,
        "peer-limit-per-torrent": 50,
        "peer-port-random-on-start": False,
        "peer-port": 51413,
        "pex-enabled": True,
        "port-forwarding-enabled": True,
        "queue-stalled-enabled": True,
        "queue-stalled-minutes": 10,
        "rename-partial-files": True,
        "rpc-version-minimum": 15,
        "rpc-version": 17,
        "script-torrent-done-enabled": True,
        "script-torrent-done-filename": "done.sh",
        "seed-queue-enabled": True,
        "seed-queue-size": 5,
        "seedRatioLimit": 2.0,
        "seedRatioLimited": True,
        "speed-limit-down-enabled": True,
        "speed-limit-down": 1000,
        "speed-limit-up-enabled": True,
        "speed-limit-up": 1000,
        "start-added-torrents": True,
        "trash-original-torrent-files": True,
        "units": {
            "speed-units": ["KB/s"],
            "speed-bytes": 1000,
            "size-units": ["MB"],
            "size-bytes": 1024,
            "memory-units": ["GB"],
            "memory-bytes": 1024,
        },
        "utp-enabled": True,
        "version": "4.0.0",
        "default-trackers": "tracker1\ntracker2",
        "rpc-version-semver": "5.3.0",
        "script-torrent-added-enabled": True,
        "script-torrent-added-filename": "added.sh",
        "script-torrent-done-seeding-enabled": True,
        "script-torrent-done-seeding-filename": "seeding.sh",
    }
    s = Session(fields=fields)
    assert s.alt_speed_down == 100
    assert s.alt_speed_enabled is True
    assert s.alt_speed_time_begin == 0
    assert s.alt_speed_time_day == 127
    assert s.alt_speed_time_enabled is True
    assert s.alt_speed_time_end == 0
    assert s.alt_speed_up == 100
    assert s.blocklist_enabled is True
    assert s.blocklist_size == 10
    assert s.blocklist_url == "url"
    assert s.cache_size_mb == 10
    assert s.config_dir == "/config"
    assert s.dht_enabled is True
    assert s.download_dir == "/downloads"
    assert s.download_dir_free_space == 1000
    assert s.download_queue_enabled is True
    assert s.download_queue_size == 5
    assert s.encryption == "preferred"
    assert s.idle_seeding_limit_enabled is True
    assert s.idle_seeding_limit == 30
    assert s.incomplete_dir_enabled is True
    assert s.incomplete_dir == "/incomplete"
    assert s.lpd_enabled is True
    assert s.peer_limit_global == 200
    assert s.peer_limit_per_torrent == 50
    assert s.peer_port_random_on_start is False
    assert s.peer_port == 51413
    assert s.pex_enabled is True
    assert s.port_forwarding_enabled is True
    assert s.queue_stalled_enabled is True
    assert s.queue_stalled_minutes == 10
    assert s.rename_partial_files is True
    assert s.rpc_version_minimum == 15
    assert s.rpc_version == 17
    assert s.script_torrent_done_enabled is True
    assert s.script_torrent_done_filename == "done.sh"
    assert s.seed_queue_enabled is True
    assert s.seed_queue_size == 5
    assert s.seed_ratio_limit == 2.0
    assert s.seed_ratio_limited is True
    assert s.speed_limit_down_enabled is True
    assert s.speed_limit_down == 1000
    assert s.speed_limit_up_enabled is True
    assert s.speed_limit_up == 1000
    assert s.start_added_torrents is True
    assert s.trash_original_torrent_files is True
    assert isinstance(s.units, Units)
    assert s.units.speed_units == ["KB/s"]
    assert s.units.speed_bytes == 1000
    assert s.units.size_units == ["MB"]
    assert s.units.size_bytes == 1024
    assert s.units.memory_units == ["GB"]
    assert s.units.memory_bytes == 1024
    assert s.utp_enabled is True
    assert s.version == "4.0.0"
    assert s.default_trackers == ["tracker1", "tracker2"]
    assert s.rpc_version_semver == "5.3.0"
    assert s.script_torrent_added_enabled is True
    assert s.script_torrent_added_filename == "added.sh"
    assert s.script_torrent_done_seeding_enabled is True
    assert s.script_torrent_done_seeding_filename == "seeding.sh"


def test_session_default_trackers_list() -> None:
    s = Session(fields={"default-trackers": ["t1", "t2"]})
    assert s.default_trackers == ["t1", "t2"]


def test_session_default_trackers_none() -> None:
    s = Session(fields={})
    assert s.default_trackers is None


def test_session_stats_properties() -> None:
    fields: dict[str, Any] = {
        "activeTorrentCount": 1,
        "downloadSpeed": 100,
        "pausedTorrentCount": 0,
        "torrentCount": 1,
        "uploadSpeed": 100,
        "cumulative-stats": {
            "uploadedBytes": 1000,
            "downloadedBytes": 1000,
            "filesAdded": 1,
            "sessionCount": 1,
            "secondsActive": 10,
        },
        "current-stats": {
            "uploadedBytes": 100,
            "downloadedBytes": 100,
            "filesAdded": 0,
            "sessionCount": 1,
            "secondsActive": 1,
        },
    }
    ss = SessionStats(fields=fields)
    assert ss.active_torrent_count == 1
    assert ss.download_speed == 100
    assert ss.paused_torrent_count == 0
    assert ss.torrent_count == 1
    assert ss.upload_speed == 100
    assert isinstance(ss.cumulative_stats, Stats)
    assert ss.cumulative_stats.uploaded_bytes == 1000
    assert ss.cumulative_stats.downloaded_bytes == 1000
    assert ss.cumulative_stats.files_added == 1
    assert ss.cumulative_stats.session_count == 1
    assert ss.cumulative_stats.seconds_active == 10
    assert isinstance(ss.current_stats, Stats)
    assert ss.current_stats.uploaded_bytes == 100
    assert ss.current_stats.downloaded_bytes == 100
    assert ss.current_stats.files_added == 0
    assert ss.current_stats.session_count == 1
    assert ss.current_stats.seconds_active == 1
