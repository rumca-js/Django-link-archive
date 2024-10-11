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
        from ..configuration import Configuration

        config_entry = Configuration.get_object().config_entry

        if not config_entry.enable_file_support:
            ModelFiles.objects.all().delete()
            return

        files = ModelFiles.objects.filter(file_name = file_name)
        if files.exists():
            file = files[0]
            file.contents = contents
            file.save()
        else:
            it = ModelFiles.objects.create(file_name=file_name, contents=contents)
            ModelFiles.cleanup()

    def cleanup():
        max_files = ModelFiles.get_max_files()

        all_files = ModelFiles.objects.all().order_by("date_created")
        if all_files.count() > max_files:
            how_many = all_files.count() - max_files
            for file_index in range(how_many):
                all_files[file_index].delete()

    def get_max_files():
        return 200

    def get_url(self):
        return reverse("{}:model-file".format(LinkDatabase.name), args=[str(self.id)])

    def get_size_bytes(self):
        if not self.contents:
            return 0

        return len(self.contents)
