from django.db import models
from django.urls import reverse
from ..apps import LinkDatabase


class ModelFiles(models.Model):
    file_name = models.CharField(max_length=2000, unique=True)
    contents = models.BinaryField(max_length=1000000, null=True)  # 1MB max
    date_created = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Date when entry was created in the database",
    )

    class Meta:
        ordering = ["file_name"]

    def add(file_name, contents):
        ModelFiles.objects.create(file_name=file_name, contents=contents)

        all_files = ModelFiles.objects.all().order_by("date_created")
        if all_files.count() > 200:
            how_many = all_files.count() - 200
            for file_index in range(how_many):
                all_files[file_index].delete()

    def get_url(self):
        return reverse("{}:model-file".format(LinkDatabase.name), args=[str(self.id)])

    def cleanup():
        from ..configuration import Configuration

        config_entry = Configuration.get_object().config_entry

        if not config_entry.enable_file_support:
            ModelFiles.objects.all().delete()

    def get_size_bytes(self):
        if not self.contents:
            return 0

        return len(self.contents)
