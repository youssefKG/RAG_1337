from django.db.models import CharField, Model


class QueryModel(Model):
    content: str = CharField()
