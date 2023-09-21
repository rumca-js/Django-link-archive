import json


class KeywordExporter(object):
    def get_json(self, keywords):
        # JsonResponse
        return {"keywords": keywords}

    def get_text(self, domains):
        json_data = self.get_json(domains)
        return json.dumps(json_data)
