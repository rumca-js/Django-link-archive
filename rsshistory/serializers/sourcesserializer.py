from pathlib import Path
from ..controllers import SourceDataController

from .converters import (
    ModelCollectionConverter,
    JsonConverter,
    PageSystem,
)


class SourceStandardSerializer(object):
    def __init__(self, export_dir, file_name):
        self.export_dir = export_dir
        self.file_name = file_name

    def export(self, sources):
        text = self.get_json_text(sources)

        if not self.export_dir.exists():
            self.export_dir.mkdir(parents=True, exist_ok=True)

        full_file_name = self.export_dir / self.file_name
        full_file_name.write_text(text)

    def get_json_text(self, sources):
        cc = ModelCollectionConverter(sources)
        items = cc.get_map()

        converter = JsonConverter(items)
        converter.set_export_columns(SourceDataController.get_export_names())
        text = converter.export()

        return text


class SourceBatchSerializer(object):
    def __init__(self, export_dir, file_name):
        self.export_dir = export_dir
        self.file_name = file_name

    def export(self, sources):
        # TODO remove hardcoded value?
        page_system = PageSystem(sources.count(), 1000)

        for page in range(page_system.no_pages):
            slice_limits = page_system.get_slice_limits(page)

            sliced_sources = sources[slice_limits[0] : slice_limits[1]]

            self.export_inner(page, sliced_sources)

    def export_inner(self, page, sources):
        page_dir = self.get_page_dir(page)
        inner_serializer = SourceStandardSerializer(page_dir, self.file_name)
        inner_serializer.export(sources)

    def get_page_dir(self, page):
        return self.export_dir / Path("sources") / "{page:05d}".format(page=page)


class SourceSerializerWrapper(object):
    def export(self, export_dir, file_name):
        self.export_dir = export_dir
        self.file_name = file_name

        sources = SourceDataController.objects.filter(export_to_cms=True)

        if sources.count() <= 1000:
            serializer = SourceStandardSerializer(export_dir, file_name)
        else:
            serializer = SourceBatchSerializer(export_dir, file_name)

        return serializer.export(sources)
