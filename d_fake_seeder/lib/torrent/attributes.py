class Attributes:
    # hodden attributes
    active: bool = True

    # viewable attributes
    id: int = 0
    announce_interval: int = 0
    download_speed: int = 300
    filepath: str = ""
    leechers: int = 0
    name: str = ""
    next_update: int = 0
    progress: int = 0
    seeders: int = 0
    session_downloaded: int = 0
    session_uploaded: int = 0
    small_torrent_limit: int = 0
    threshold: int = 0
    total_downloaded: int = 0
    total_size: int = 0
    total_uploaded: int = 0
    upload_speed: int = 30
    uploading: bool = False
