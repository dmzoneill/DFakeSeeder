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

                if b"announce" in self.torrent_header:
                    self.announce = self.torrent_header[b"announce"].decode("utf-8")

                if b"announce-list" in self.torrent_header:
                    announce_list = self.torrent_header[b"announce-list"]
                    if isinstance(announce_list, list):
                        # Extract announce URLs from the announce-list
                        announce_urls = [
                            url.decode("utf-8")
                            for sublist in announce_list
                            for url in sublist
                        ]
                        self.announce_list = announce_urls

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

    def get_announce(self):
        return self.torrent_header[b"announce"].decode("utf-8")

    def get_creation_date(self):
        if b"creation date" in self.torrent_header:
            creation_date = self.torrent_header[b"creation date"]
            creation_date = datetime.fromtimestamp(creation_date)
            return creation_date.strftime("%Y/%m/%d %H:%M:%S")
        return None

    def get_created_by(self):
        if b"created by" in self.torrent_header:
            return self.torrent_header[b"created by"].decode("utf-8")
        return None

    def get_encoding(self):
        if b"encoding" in self.torrent_header:
            return self.torrent_header[b"encoding"].decode("utf-8")
        return None

    def get_piece_length(self):
        return helpers.sizeof_fmt(self.torrent_header[b"info"][b"piece length"])

    def get_num_pieces(self):
        return len(self.torrent_header[b"info"][b"pieces"]) / 20

    def get_torrent_name(self):
        return self.torrent_header[b"info"][b"name"].decode("utf-8")

    def get_files(self):
        files = []
        if b"files" in self.torrent_header[b"info"]:
            for file_info in self.torrent_header[b"info"][b"files"]:
                fullpath = "/".join([x.decode("utf-8") for x in file_info[b"path"]])
                files.append((fullpath, helpers.sizeof_fmt(file_info[b"length"])))
        return files

    def get_single_file_info(self):
        if b"files" not in self.torrent_header[b"info"]:
            return helpers.sizeof_fmt(self.torrent_header[b"info"][b"length"])
        return None

    def get_md5sum(self):
        if b"md5sum" in self.torrent_header[b"info"]:
            return self.torrent_header[b"info"][b"md5sum"]
        return None
