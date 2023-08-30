import json


class DomainJsonExporter(object):
    def __init__(self):
        pass

    def get_json(self, domains):
        json_data = []
        for domain in domains:
            json_data.append(domain.get_map())

        # JsonResponse
        return {"domains": json_data}

    def get_text(self, domains):
        json_data = self.get_json(domains)
        return json.dumps(json_data)
