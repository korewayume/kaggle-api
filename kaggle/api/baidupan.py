# -*- coding: utf-8 -*-
import os
import json
import hashlib
import binascii
import requests


class BaiDuPan(object):
    slice_chunk_size = 256 * 1024

    def __init__(self, filename):
        self.filename = filename
        self.content_length = 0
        self.md5 = None
        self.crc = None
        self.slice_md5 = None
        self.slice_chunk = b''

    def __enter__(self):
        self.content_length = 0
        self.md5 = hashlib.md5()
        self.crc = None
        self.slice_md5 = None
        self.slice_chunk = b''
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rapid_upload()

    def update(self, chunk):
        self.content_length += len(chunk)
        self.md5.update(chunk)
        if self.crc is None:
            self.crc = binascii.crc32(chunk)
        else:
            self.crc = binascii.crc32(chunk, self.crc)
        if len(self.slice_chunk) < self.slice_chunk_size:
            self.slice_chunk += chunk
        elif self.slice_md5 is None:
            self.slice_chunk = self.slice_chunk[:self.slice_chunk_size]
            self.slice_md5 = hashlib.md5()
            self.slice_md5.update(self.slice_chunk)

    def rapid_upload(self):
        try:
            with open(os.path.expanduser("~/.bypy/bypy.json")) as cfg:
                access_token = json.load(cfg)["access_token"]
        except (IOError, OSError, KeyError, ValueError):
            access_token = None

        params = {
            "method": "rapidupload",
            "access_token": access_token,
            "content-length": self.content_length,
            "content-md5": str(self.md5.hexdigest()),
            "slice-md5": str(self.slice_md5.hexdigest()),
            "content-crc32": str(hex(self.crc & 0xffffffff)),
            "path": os.path.join("/apps/bypy/", self.filename)
        }

        print("\nparams:\n")
        print(json.dumps(params, indent=2, sort_keys=True))

        print("\nresponse:\n")
        print(requests.post("https://pcs.baidu.com/rest/2.0/pcs/file", params=params).content)
