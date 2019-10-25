class MetadataNotFound(Exception):
    pass


class MetadataError(Exception):
    pass


class DatasetNotFound(MetadataNotFound):
    pass


class EditionNotFound(MetadataError):
    pass
