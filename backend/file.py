from datetime import datetime

class File:
    def __init__(self, cid, size, filename, creation_date=None):
        self.cid = cid  # IPFS CID
        self.size = size
        self.filename = filename
        self.creation_date = creation_date or datetime.now()

    def __repr__(self):
        return f"File({self.filename}, CID={self.cid}, Size={self.size} bytes, Created={self.creation_date})"

    def __eq__(self, other):
        if not isinstance(other, File):
            return False
        return (
                self.cid == other.cid and
                self.size == other.size and
                self.filename == other.filename and
                self.creation_date == other.creation_date
        )

    def __hash__(self):
        return hash((self.cid, self.size, self.filename, self.creation_date))
