from mongoengine import *


class AnimateEpisode(EmbeddedDocument):
    number = IntField()
    chinese_name = StringField()
    japan_name = StringField()
    show_date = DateTimeField()


class AnimateCast(EmbeddedDocument):
    bangumi_id = StringField()
    chinese_name = StringField()
    japan_name = StringField()
    job = ListField()


class CharacterVoice(EmbeddedDocument):
    bangumi_id = StringField()
    japan_name = StringField()
    chinese_name = StringField()




class AnimateCharacter(EmbeddedDocument):
    bangumi_id = StringField()
    japan_name = StringField()
    chinese_name = StringField()
    job = StringField()
    info = MapField(StringField())
    cv = ListField(EmbeddedDocumentField(CharacterVoice))

class AnimateComment(EmbeddedDocument):
    user = StringField()
    score = FloatField()
    text = StringField()

class Animate(Document):
    name = StringField()
    animate_type = StringField()
    bangumi_id = StringField()
    summary = StringField()
    info = MapField(ListField())
    cast = ListField(EmbeddedDocumentField(AnimateCast))
    character = ListField(EmbeddedDocumentField(AnimateCharacter))
    tag = ListField()
    episode = MapField(ListField(EmbeddedDocumentField(AnimateEpisode)))
    comments = ListField(EmbeddedDocument(AnimateComment))
    start_play = DateTimeField()
    episode_count = IntField()
    chinese_name = StringField()
    score = FloatField()
    rank = StringField()
    created = DateTimeField()
    updated = DateTimeField()
