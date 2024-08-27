from ..basictypes import fix_path_for_os
from webtools import Url, YouTubeVideoHandler


def fix_entry_link_name(link):
    link = link.replace("\\", "")
    link = link.replace("/", "")
    link = fix_path_for_os(link)
    link = link.replace(".", "")
    link = link.replace("-", "")
    return link+".html"


def get_youtube_style():
    return """
.youtube_player_container {
    position: relative;
    width: 50%;
    padding-bottom: 26.25%;
    /* background-color: yellow; */
}
.youtube_player_frame {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border: 0;
}
    """


class HtmlEntryExporter(object):
    def __init__(self, output_directory, entry):
        self.entry = entry
        self.output_directory = output_directory

    def write(self):
        text = self.get_entry_text()

        with open(self.get_entry_file_name(), "w", encoding="utf-8") as fh:
            fh.write(text)

    def get_entry_text(self):
        entry = self.entry

        # index.html entry text
        thumbnail = entry.thumbnail
        title = entry.title
        link = entry.link
        description = entry.description
        date_published = entry.date_published
        source = entry.source
        #source_title = entry.source

        show_thumbnail = True

        if thumbnail and description and description.find(thumbnail) >= 0:
            show_thumbnail = False

        if not thumbnail:
            show_thumbnail = False

        text = ""
        text = "<!DOCTYPE html>"
        text += "<html>"
        text += "<head>"
        text += "<style>"
        text += get_youtube_style()
        text += "</style>"
        text += "</head>"
        text += "<body>"
        text += '<a href="index.html"><h2>Index</h2></a>'
        text += f'<a href="{link}">'

        if show_thumbnail:
            text += self.get_preview()

        text += f'<h1>{title}</h1>'
        text += f'</a>'
        text += f'<div>{source}</div>'
        text += f'<div>{date_published}</div>'
        text += f'<div><pre>{description}</pre></div>'
        text += "</body>"
        text += "</html>"
        return text

    def get_preview(self):
        url = Url(self.entry.link)
        handler = url.get_handler()

        if type(handler) is Url.youtube_video_handler:
            h = YouTubeVideoHandler(url = self.entry.link)
            return '<div class="youtube_player_container"><iframe src="{0}" frameborder="0" allowfullscreen class="youtube_player_frame" referrerpolicy="no-referrer-when-downgrade"></iframe></div>'.format(
                h.get_link_embed()
            )
        else:
            thumbnail = self.entry.thumbnail
            return f'<div><img style="width:400px;height=300px" src="{thumbnail}" /></div>'

    def get_entry_file_name(self):
        link = self.entry.link
        return self.output_directory / fix_entry_link_name(link)


class HtmlExporter(object):
    def __init__(self, output_directory, entries):
        self.output_directory = output_directory
        self.entries = entries

    def write(self):
        text = "<!DOCTYPE html>"
        text += "<html>"
        text += "<head>"
        text += "<style>"
        text += get_youtube_style()
        text += "</style>"
        text += "</head>"
        text += "<body>"
        text += "<ul>"

        for entry in self.entries:
            print("Writing:{}".format(self.get_entry_file_name(entry)))
            self.write_entry_file(entry)
            text += self.get_entry_index_text(entry)

        text += "</body>"
        text += "</html>"

        with open(self.get_index_file_name(), "w", encoding="utf-8") as fh:
            fh.write(text)

    def write_entry_file(self, entry):
        # write entry file
        w = HtmlEntryExporter(self.output_directory, entry)
        w.write()

    def get_entry_index_text(self, entry):
        # index.html entry text
        thumbnail = entry.thumbnail
        title = entry.title
        link = entry.link
        description = entry.description
        date_published = entry.date_published
        source = entry.source
        #source_title = entry.source

        entry_file_name = self.get_entry_file_name(entry)

        text = ""
        text += f'<a href="{entry_file_name}">'
        if thumbnail:
            text += f'<div><img style="width:400px;height=300px" src="{thumbnail}" /></div>'

        text += f'<h1>{title}</h1>'
        text += f'</a>'
        text += f'<div>{source}</div>'
        text += f'<div>{date_published}</div>'
        text += f'<hr/>'
        return text

    def get_index_file_name(self):
        return self.output_directory / "index.html"

    def get_entry_file_name(self, entry):
        return fix_entry_link_name(entry.link)
