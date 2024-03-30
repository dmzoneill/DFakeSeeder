import hashlib
from datetime import datetime

import lib.torrent.bencoding as bencoding
import lib.util.helpers as helpers
from lib.logger import logger


class File:
    def __init__(self, filepath):
        logger.info("File Startup", extra={"class_name": self.__class__.__name__})
        while True:
            try:
                self.filepath = filepath
                f = open(filepath, "rb")
                self.raw_torrent = f.read()
                f.close()
                self.torrent_header = bencoding.decode(self.raw_torrent)

                if b"announce" not in self.torrent_header:
                    return

                self.announce = self.torrent_header[b"announce"].decode("utf-8")

                torrent_info = self.torrent_header[b"info"]
                m = hashlib.sha1()
                m.update(bencoding.encode(torrent_info))
                self.file_hash = m.digest()
                break
            except Exception as e:
                logger.info(
                    "File read error: " + str(e),
                    extra={"class_name": self.__class__.__name__},
                )

    @property
    def total_size(self):
        logger.debug("File size", extra={"class_name": self.__class__.__name__})
        size = 0
        torrent_info = self.torrent_header[b"info"]
        if b"files" in torrent_info:
            # Multiple File Mode
            for file_info in torrent_info[b"files"]:
                size += file_info[b"length"]
        else:
            # Single File Mode
            size = torrent_info[b"length"]

        return size

    @property
    def name(self):
        logger.debug("File name", extra={"class_name": self.__class__.__name__})
        torrent_info = self.torrent_header[b"info"]
        return torrent_info[b"name"].decode("utf-8")

    def __str__(self):
        logger.debug("File attribute", extra={"class_name": self.__class__.__name__})
        announce = self.torrent_header[b"announce"].decode("utf-8")
        result = "Announce: %s\n" % announce

        if b"creation date" in self.torrent_header:
            creation_date = self.torrent_header[b"creation date"]
            creation_date = datetime.fromtimestamp(creation_date)
            result += "Date: %s\n" % creation_date.strftime("%Y/%m/%d %H:%M:%S")

        if b"created by" in self.torrent_header:
            created_by = self.torrent_header[b"created by"].decode("utf-8")
            result += "Created by: %s\n" % created_by

        if b"encoding" in self.torrent_header:
            encoding = self.torrent_header[b"encoding"].decode("utf-8")
            result += "Encoding:   %s\n" % encoding

        torrent_info = self.torrent_header[b"info"]
        piece_len = torrent_info[b"piece length"]
        result += "Piece len: %s\n" % helpers.sizeof_fmt(piece_len)
        pieces = len(torrent_info[b"pieces"]) / 20
        result += "Pieces: %d\n" % pieces

        torrent_name = torrent_info[b"name"].decode("utf-8")
        result += "Name: %s\n" % torrent_name
        piece_len = torrent_info[b"piece length"]

        if b"files" in torrent_info:
            # Multiple File Mode
            result += "Files:\n"
            for file_info in torrent_info[b"files"]:
                fullpath = "/".join([x.decode("utf-8") for x in file_info[b"path"]])
                result += "  '%s' (%s)\n" % (
                    fullpath,
                    helpers.sizeof_fmt(file_info[b"length"]),
                )
        else:
            # Single File Mode
            result += "Length: %s\n" % helpers.sizeof_fmt(torrent_info[b"length"])
            if b"md5sum" in torrent_info:
                result += "Md5: %s\n" % torrent_info[b"md5sum"]

        return result
