![DFakeSeeder screenshot](https://github.com/dmzoneill/dFakeSeeder/blob/main/d_fake_seeder/images/dfakeseeder.png)

# D' Fake Seeder

- If you are looking to start using this immediately, i'm afraid you are out of luck.
- Upload functionality is still disabled in this as it's in development.
- Fake seeding can get you banned from trackers.

![DFakeSeeder screenshot](https://github.com/dmzoneill/dFakeSeeder/blob/main/d_fake_seeder/images/screenshot.png)

# Typical setup
```
{
    "directory": "./torrents",
    "upload_speed": 50,
    "download_speed": 500,
    "total_upload_speed": 50,
    "total_download_speed": 500,
    "announce_interval": 1800,
    "torrents": {
    },
    "http_headers": {
        "Accept-Encoding": "gzip",
        "User-Agent": "Deluge/2.0.3 libtorrent/2.0.5.0"
    },
    "agents": [
        "Deluge/2.0.3 libtorrent/2.0.5.0",
        "qBittorrent/4.3.1",
        "Transmission/3.00",
        "uTorrent/3.5.5",
        "Vuze/5.7.6.0",
        "BitTorrent/7.10.5",
        "rTorrent/0.9.6"
    ],
    "proxies": {
        "http": "http://127.0.0.1:3128",
        "https": "http://127.0.0.1:3128"
    },
    "columns": "",
    "concurrent_http_connections": 2,
    "concurrent_peer_connections": 10,
    "cellrenderers": {
        "progress": "Gtk.CellRendererProgress"
    },
    "textrenderers": {
        "total_uploaded": "humanbytes",
        "total_downloaded": "humanbytes",
        "session_uploaded": "humanbytes",
        "session_downloaded": "humanbytes",
        "total_size": "humanbytes",
        "announce_interval": "convert_seconds_to_hours_mins_seconds",
        "next_update": "convert_seconds_to_hours_mins_seconds",
        "upload_speed": "add_kb",
        "download_speed": "add_kb",
        "threshold": "add_percent"
    },
    "threshold": 30,
    "tickspeed": 3,
    "editwidgets": {
        "active": "Gtk.Switch",
        "announce_interval": "Gtk.SpinButton",
        "download_speed": "Gtk.SpinButton",
        "next_update": "Gtk.SpinButton",
        "session_downloaded": "Gtk.SpinButton",
        "session_uploaded": "Gtk.SpinButton",
        "small_torrent_limit": "Gtk.SpinButton",
        "threshold": "Gtk.SpinButton",
        "total_downloaded": "Gtk.SpinButton",
        "total_uploaded": "Gtk.SpinButton",
        "upload_speed": "Gtk.SpinButton"
    }
}
```